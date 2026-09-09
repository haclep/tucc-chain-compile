#!/usr/bin/env python
"""k1c_warmstart.py -- K1c cost harness: race proposals in ROTATIONS.

A thin wrapper over the frozen K1b-T4 harness (k1b_warmstart.py, loaded
as a module so its rotation accounting, plateau rule, gate and report
are reused unchanged). Two additions, both K1c protocol knobs:

  --pred-file PATH   read the proposal from any frozen file in the
                     harness's own format ({"preds": {seed: (word, th)}})
                     for ANY stem, instead of the hard-wired h8_chain
                     Split-C file. k1c_model.py --write-proposals emits
                     these for model seeds and for the no-learning
                     baselines (TANGENT at predicted scale, POOL-ALL).
  --insert post-joint  run the joint Gauss-Newton solve on the routed
                     chain BEFORE appending the proposal, then give the
                     seeded chain a fresh joint budget. The proposer's
                     features live at that state (k1c_pool.py). The
                     pre-insertion joint solve is identical in every arm
                     and is recorded UNCHARGED, like routing and greedy
                     (its rotations appear as rot_prep_uncharged in the
                     summary). Run cold with the same --insert so every
                     arm shares the same uncharged prefix.

Everything else -- gate 1e-12, plateau 0.01, growth, restarts, the
per-column 2x2 rotation count -- is the frozen harness's code.

Outputs go to k1c_runs/<tag>_{state.pkl,trace.jsonl,summary.json};
the chain .npz and the results/ report follow the frozen harness's
paths inside THIS checkout (never the campaign checkout).

Usage (H6, dense target, seconds to minutes per arm):
    python k1c_warmstart.py k1_h6_chain_19 --arm cold --insert post-joint --target dense
    python k1c_warmstart.py k1_h6_chain_19 --arm pred --insert post-joint --target dense \
        --pred-file k1c_proposals/k1_h6_chain_19_model_s0.pkl --pred-tag model_s0
    python k1c_warmstart.py k1_h6_chain_19 --arm oracle_content --insert post-joint --target dense
"""
import argparse
import importlib.util as iu
import inspect
import os
import pickle
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "src"))


def _load(name, fn):
    spec = iu.spec_from_file_location(name, os.path.join(HERE, fn))
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kb = _load("k1b_warmstart", "k1b_warmstart.py")      # installs the counters
from chaincompile.compile import _gauss_newton        # noqa: E402

RUNS = os.path.join(HERE, "k1c_runs")
CFG = {"insert": "greedy", "pred_file": None, "pred_tag": None,
       "plateau": kb.PLATEAU_DEFAULT}


# ------------------------------------------------------------ proposals
_build_seed_frozen = kb.build_seed


def build_seed(stem, arm, order, pred_seed, n_routed, routed_word):
    if arm == "pred" and CFG["pred_file"]:
        with open(CFG["pred_file"], "rb") as fh:
            P = pickle.load(fh)
        word, th = P["preds"][pred_seed]
        word = [tuple(map(tuple, x)) for x in word]
        cnt = kb.kh.counts(word)
        weights = [cnt[L] + 1e-3 * abs(t) for L, t in zip(word, th)]
        pairs = kb._round_robin(word, th, weights)
        prov = {"arm": arm, "order": order,
                "source": os.path.basename(CFG["pred_file"]),
                "pred_seed": pred_seed, "config": P.get("config"),
                "insert": CFG["insert"], "n": len(word),
                "n_distinct": len(cnt)}
        if order == "shuffle":
            pairs = kb._shuffle(pairs)
        return pairs, None, prov
    pairs, routed_theta, prov = _build_seed_frozen(
        stem, arm, order, pred_seed, n_routed, routed_word)
    prov["insert"] = CFG["insert"]
    return pairs, routed_theta, prov


kb.build_seed = build_seed


# ------------------------------------------------------------ insertion
_solve_frozen = kb.big.solve_resumable


def solve_resumable(*args, **kw):
    """Post-joint insertion: after the frozen driver stops at the greedy
    state, run the joint phase exactly as the driver would (slices of
    10, plateau rule, 300-iteration budget), then hand the state back
    at phase 'joint' with a fresh budget so the frozen run_arm appends
    the proposal and re-solves the seeded chain. Signature-agnostic:
    the driver recurses into this name positionally."""
    b = inspect.signature(_solve_frozen).bind(*args, **kw)
    b.apply_defaults()
    A = b.arguments
    ct, basis, pivot_mask, state = A["ct"], A["basis"], A["pivot_mask"], A["state"]
    log, save = A["log"], A["save"]
    stop = bool(A.get("stop_after_greedy", False))
    if not (CFG["insert"] == "post-joint" and stop):
        return _solve_frozen(*args, **kw)
    if state["phase"] in ("route", "greedy"):
        r = _solve_frozen(*args, **kw)
        if state["phase"] != "joint":
            return r
    if state["phase"] == "joint" and not state.get("k1c_prejoint_done"):
        plateau = CFG["plateau"]
        while True:
            budget = min(state["iters_left"], 10)
            if budget <= 0:
                break
            rn_before = state["rn"]
            state["thetas"], state["rn"] = _gauss_newton(
                state["thetas"], state["seq"], basis, pivot_mask, ct,
                tol=1e-13, max_iter=budget, bound=kb.big.BOUND)
            state["iters_left"] -= budget
            log("prejoint: |r| %.3e (iters left %d, len %d)"
                % (state["rn"], state["iters_left"], len(state["seq"])))
            if state["rn"] ** 2 < kb.GATE:
                break
            if plateau is not None and rn_before > 0 and \
                    (rn_before - state["rn"]) < plateau * rn_before:
                log("prejoint: plateau exit (slice gain %.2e < %s)"
                    % ((rn_before - state["rn"]) / rn_before, plateau))
                break
        state["k1c_prejoint_done"] = True
        state["rn_prejoint"] = float(state["rn"])
        state["phase"] = "joint"
        state["iters_left"] = 300
        save()
        log("post-joint insertion point: |r| %.3e after the uncharged joint "
            "solve; proposal appended next" % state["rn"])
    return False


kb.big.solve_resumable = solve_resumable


# ------------------------------------------------------------ paths
def _paths(stem, arm, pred_seed, order):
    tag = "%s_%s" % (stem, arm)
    if arm == "pred":
        tag += "_%s" % (CFG["pred_tag"] or "s%d" % pred_seed)
    if order != kb._default_order(arm):
        tag += "_" + order
    if CFG["insert"] == "post-joint":
        tag += "_pj"
    os.makedirs(RUNS, exist_ok=True)
    return (tag, os.path.join(RUNS, tag + "_state.pkl"),
            os.path.join(RUNS, tag + "_trace.jsonl"),
            os.path.join(RUNS, tag + "_summary.json"))


kb._paths = _paths


# ------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stem")
    ap.add_argument("--arm", choices=kb.ARMS, default="cold")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--order", choices=("rank", "shuffle"), default=None)
    ap.add_argument("--plateau", default=str(kb.PLATEAU_DEFAULT))
    ap.add_argument("--deadline", type=float, default=14400)
    ap.add_argument("--target", choices=("checkpoint", "dense"),
                    default="dense")
    ap.add_argument("--insert", choices=("greedy", "post-joint"),
                    default="post-joint")
    ap.add_argument("--pred-file", default=None)
    ap.add_argument("--pred-tag", default=None)
    ap.add_argument("--translate", action="store_true")
    a = ap.parse_args()
    a.plateau = None if str(a.plateau).lower() == "none" else float(a.plateau)
    if a.order is None:
        a.order = kb._default_order(a.arm)
    if a.arm == "pred" and not a.pred_file and a.stem != "h8_chain":
        raise SystemExit("--arm pred needs --pred-file for stems other "
                         "than h8_chain")
    CFG.update({"insert": a.insert, "pred_file": a.pred_file,
                "pred_tag": a.pred_tag, "plateau": a.plateau})
    a.score = False
    kb.run_arm(a)


if __name__ == "__main__":
    main()

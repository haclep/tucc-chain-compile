#!/usr/bin/env python
"""k1c_warmstart.py -- K1c cost harness: race proposals in ROTATIONS.

A thin wrapper over the frozen K1b-T4 harness (k1b_warmstart.py, loaded
as a module so its rotation accounting, plateau rule, gate and report
are reused unchanged). Additions, all K1c protocol knobs:

  --pred-file PATH     read the proposal from any frozen file in the
                       harness's own format ({"preds": {seed: (word, th)}})
                       for ANY stem.
  --pred-source        file (default) | tangent | poolall | topk. With a live
                       source the proposal is computed at the actual
                       insertion state: the round-one pool from the TOP
                       largest-residual determinants, allocated in
                       proportion to the compiler's first-order fidelity
                       gradient (tangent), one copy each (poolall), or the
                       top-K distinct letters by gradient, one copy each
                       (topk), all at zero angle. No file, no parameters.
  --prejoint-iters N   cap on the pre-insertion joint solve (default 300;
                       the plateau rule still applies). Non-default values
                       are appended to the run tag.
  --scale N            tangent: total letters to propose (default: the
                       pool size); --scale-mult m: multiple of pool size.
  --top K              pool seeds (default k1c_pool.TOP).
  --insert post-joint  run the joint Gauss-Newton solve on the routed chain
                       BEFORE appending the proposal, then give the seeded
                       chain a fresh joint budget. The pre-insertion solve
                       is identical in every arm and recorded UNCHARGED
                       (rot_prep_uncharged in the summary). Live sources
                       require this insertion point.

Everything else -- gate 1e-12, plateau 0.01, growth, restarts, the
per-column 2x2 rotation count -- is the frozen harness's code. The
proposal construction itself (pool enumeration and scoring) is not
counted as rotations; it is O(pool x dim) vector work and is reported
in provenance.

Outputs go to k1c_runs/<tag>_{state.pkl,trace.jsonl,summary.json};
the chain .npz and the results/ report follow the frozen harness's
paths inside THIS checkout (never the campaign checkout).

Usage (H6, dense target):
    python k1c_warmstart.py k1_h6_ring_19 --arm cold --insert post-joint --target dense
    python k1c_warmstart.py k1_h6_ring_19 --arm pred --pred-source tangent --insert post-joint --target dense
    python k1c_warmstart.py k1_h6_ring_19 --arm pred --pred-source tangent --scale-mult 0.5 --pred-tag tangent_half --insert post-joint --target dense
    python k1c_warmstart.py k1_h6_ring_19 --arm pred --pred-file k1c_proposals/k1_h6_ring_19_model_s0.pkl --pred-tag model_s0 --insert post-joint --target dense
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
kp = _load("kp", "k1c_pool.py")                      # pool + TOP
p1 = kp.p1                                           # tangent_scores
from chaincompile.compile import _gauss_newton, _prep   # noqa: E402

RUNS = os.path.join(HERE, "k1c_runs")
CFG = {"insert": "greedy", "pred_file": None, "pred_tag": None,
       "pred_source": "file", "scale": None, "scale_mult": 1.0,
       "top": kp.TOP, "plateau": kb.PLATEAU_DEFAULT, "live": None,
       "prejoint_iters": 300}


def allocate(scores, total):
    """Largest-remainder allocation of `total` copies proportional to
    scores (letters with zero score get nothing)."""
    scores = np.asarray(scores, float)
    out = np.zeros(len(scores), int)
    idx = np.where(scores > 0)[0]
    if total < 1 or len(idx) == 0:
        return out
    s = scores[idx] / scores[idx].sum() * total
    fl = np.floor(s).astype(int)
    rem = int(total - fl.sum())
    fl[np.argsort(-(s - fl))[:max(0, rem)]] += 1
    out[idx] = fl
    return out


# ------------------------------------------------------------ proposals
_build_seed_frozen = kb.build_seed


def _live_proposal():
    L = CFG["live"]
    if L is None:
        raise SystemExit("live proposal source needs --insert post-joint "
                         "(the insertion state was not captured)")
    psi = _prep(L["thetas"], L["seq"], L["basis"], L["pivot"])
    resv = psi - L["ct"]
    kp.TOP = int(CFG["top"])
    pool = kp.round_one_pool(L["basis"], resv)
    keys = sorted(pool)
    if CFG["pred_source"] == "poolall":
        counts = np.ones(len(keys), int)
        n_target = len(keys)
    elif CFG["pred_source"] == "topk":
        ts = p1.tangent_scores({"basis": L["basis"], "psi": psi,
                                "resv": resv}, keys)
        n_target = int(CFG["scale"]) if CFG["scale"] else \
            int(round(CFG["scale_mult"] * len(keys)))
        counts = np.zeros(len(keys), int)
        counts[np.argsort(-ts)[:max(1, n_target)]] = 1
    else:
        ts = p1.tangent_scores({"basis": L["basis"], "psi": psi,
                                "resv": resv}, keys)
        n_target = int(CFG["scale"]) if CFG["scale"] else \
            int(round(CFG["scale_mult"] * len(keys)))
        counts = allocate(ts, n_target)
    word = [k for k, c in zip(keys, counts) for _ in range(int(c))]
    th = [0.0] * len(word)
    cnt = kb.kh.counts(word)
    weights = [float(cnt[w]) for w in word]
    return word, th, weights, {"pool": len(keys), "top": int(CFG["top"]),
                               "scale_target": n_target,
                               "prejoint_iters": int(CFG["prejoint_iters"]),
                               "rn_at_insertion": float(np.linalg.norm(resv))}


def build_seed(stem, arm, order, pred_seed, n_routed, routed_word):
    if arm == "pred" and CFG["pred_source"] in ("tangent", "poolall", "topk"):
        word, th, weights, info = _live_proposal()
        pairs = kb._round_robin(word, th, weights)
        if order == "shuffle":
            pairs = kb._shuffle(pairs)
        prov = {"arm": arm, "order": order, "source": CFG["pred_source"],
                "insert": CFG["insert"], "n": len(word),
                "n_distinct": len(set(word)), "theta": "zero"}
        prov.update(info)
        return pairs, None, prov
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
    10, plateau rule, 300-iteration budget), capture the state for live
    proposals, then hand it back at phase 'joint' with a fresh budget so
    the frozen run_arm appends the proposal and re-solves. Signature-
    agnostic: the driver recurses into this name positionally."""
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
        state["iters_left"] = min(int(state["iters_left"]),
                                  int(CFG["prejoint_iters"]))
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
    CFG["live"] = {"basis": basis, "pivot": pivot_mask, "ct": ct,
                   "thetas": np.asarray(state["thetas"], float),
                   "seq": list(state["seq"])}
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
        if int(CFG["prejoint_iters"]) != 300:
            tag += str(int(CFG["prejoint_iters"]))
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
    ap.add_argument("--pred-source",
                    choices=("file", "tangent", "poolall", "topk"),
                    default="file")
    ap.add_argument("--pred-tag", default=None)
    ap.add_argument("--scale", type=int, default=None)
    ap.add_argument("--scale-mult", type=float, default=1.0)
    ap.add_argument("--top", type=int, default=kp.TOP)
    ap.add_argument("--prejoint-iters", type=int, default=300)
    ap.add_argument("--translate", action="store_true")
    a = ap.parse_args()
    a.plateau = None if str(a.plateau).lower() == "none" else float(a.plateau)
    if a.order is None:
        a.order = kb._default_order(a.arm)
    if a.arm == "pred":
        if a.pred_source == "file" and not a.pred_file and a.stem != "h8_chain":
            raise SystemExit("--arm pred needs --pred-file (or --pred-source "
                             "tangent|poolall) for stems other than h8_chain")
        if a.pred_source != "file" and a.insert != "post-joint":
            raise SystemExit("--pred-source %s requires --insert post-joint"
                             % a.pred_source)
        if a.pred_source != "file" and not a.pred_tag:
            a.pred_tag = a.pred_source + "_live"
    CFG.update({"insert": a.insert, "pred_file": a.pred_file,
                "pred_tag": a.pred_tag, "pred_source": a.pred_source,
                "scale": a.scale, "scale_mult": a.scale_mult,
                "top": a.top, "plateau": a.plateau, "live": None,
                "prejoint_iters": a.prejoint_iters})
    a.score = False
    kb.run_arm(a)


if __name__ == "__main__":
    main()

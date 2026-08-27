#!/usr/bin/env python
"""k1b_warmstart.py -- K1b-T4 warm-start harness (registered follow-up).

Races several ARMS of the sd_routed compiler on ONE certified target
under identical rules and reports the optimizer cost of each arm. An
arm is a proposal for the letters that the cold compiler would
otherwise have to discover by growth: the proposal is appended to the
routed chain (after the greedy ordering, before the first Gauss-Newton
solve) and the compiler then runs to the certification gate exactly as
it would cold. The compiler stays in the loop, so every arm's output is
a certified chain; only the cost differs.

Arms
  cold            no proposal (the comparator).
  pred            the FROZEN Split-C predictions
                  (k1_corpus/predictions_splitC_h8.pkl, --seed N).
  b2              the physics baseline: all pivot-referenced S/D
                  letters ranked by |MP2 t|, theta = sign * arctan(t)
                  with the sign frozen with the predictions.
  oracle_full     the certified chain itself (letters AND angles,
                  routed angles included): the known-answer ceiling.
  oracle_content  the certified chain's grown multiset at theta = 0
                  (--order shuffle by default): the content ceiling.

Seed ordering (--order): 'rank' = round-robin over copies, each pass
ordered by descending proposal weight (pred: predicted multiplicity,
then |theta|; b2: |t|); 'shuffle' = fixed-seed permutation (seed 1).
Duplicates never sit adjacent under either rule.

Cost currency (deterministic, platform-independent): the number of
elementary 2x2 rotations executed by the optimizer -- one rotation per
(letter block pair x vector column) -- counted from the first
Gauss-Newton solve to the certification gate. Also recorded: Gauss-
Newton iterations, growth rounds, wall-clock of the optimizer phases.

Usage (repeat each arm until it prints DONE, like run_big_sd.py):
  python -u k1b_warmstart.py h8_chain --arm cold
  python -u k1b_warmstart.py h8_chain --arm pred --seed 0
  python -u k1b_warmstart.py h8_chain --arm b2
  python -u k1b_warmstart.py h8_chain --arm oracle_full
  python -u k1b_warmstart.py h8_chain --score      (scoreboard + verdict)

State lives in k1b/<stem>_<arm>_state.pkl (delete it to restart that
arm); the per-slice trace in k1b/<stem>_<arm>_trace.jsonl; the arm
summary in k1b/<stem>_<arm>_summary.json; reports in results/.
The target is the certified vector stored in data/<stem>_bigsd.pkl
(the finished campaign checkpoint), so every arm compiles the
identical state. --target dense (small systems only) diagonalizes the
dump instead, for tests and shakedowns.
"""
import argparse
import importlib.util
import json
import os
import pickle
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import chaincompile.compile as CC                               # noqa: E402
from chaincompile.compile import _normalize_target, _prep       # noqa: E402
from chaincompile.dets import Substitution                      # noqa: E402
from chaincompile.diagnostics import write_text                 # noqa: E402
from chaincompile.molecular import (build_h_sector, freeze_core,  # noqa: E402
                                    load_integral_dump)
from chaincompile.sector import SectorBasis                     # noqa: E402

HARNESS_VERSION = "k1b-warmstart-1"
GATE = 1e-12                  # certification gate on 1 - fid^2 (= rn^2)
PLATEAU_DEFAULT = 0.01        # per-slice relative gain below which a
                              # GN phase ends (registered protocol value)
ARMS = ("cold", "pred", "b2", "oracle_full", "oracle_content")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


big = _load("run_big_sd", os.path.join(HERE, "examples", "run_big_sd.py"))
kh = _load("k1_harness", os.path.join(HERE, "k1_harness.py"))

# ---------------------------------------------------------------- work counter
WORK = {"rot": 0, "gn_iters": 0}
_apply, _apply_cols = CC.apply_ucc_factor, CC.apply_ucc_factor_cols


def _counted_apply(vec, basis, sub, theta):
    WORK["rot"] += len(basis.block_arrays(sub)[0])
    return _apply(vec, basis, sub, theta)


def _counted_apply_cols(M, basis, sub, theta):
    WORK["rot"] += len(basis.block_arrays(sub)[0]) * M.shape[1]
    if M.shape[1] == 1:
        # _gauss_newton builds one Jacobian per iteration; the build's
        # first propagation call carries exactly one column (k = 1).
        WORK["gn_iters"] += 1
    return _apply_cols(M, basis, sub, theta)


CC.apply_ucc_factor = _counted_apply
CC.apply_ucc_factor_cols = _counted_apply_cols
big.apply_ucc_factor = _counted_apply


def _git_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=HERE,
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:  # pragma: no cover
        return "unknown"


# ------------------------------------------------------------------- target
def load_target(stem, target_mode):
    n_core = kh._ncore(stem)
    dump = kh._dumppath(stem)
    h, e, e_nuc, e_scf, na, nb, meta = load_integral_dump(dump)
    h, e, e_core = freeze_core(h, e, n_core)
    basis = SectorBasis(h.shape[0], na - n_core, nb - n_core)
    info = {"dump": os.path.basename(dump), "n_core": n_core,
            "e_shift": float(e_nuc + e_core), "dim": basis.dim,
            "nmo": int(h.shape[0]), "na": na - n_core, "nb": nb - n_core}
    ck_path = os.path.join(HERE, "data", stem + "_bigsd.pkl")
    if target_mode == "checkpoint" and os.path.exists(ck_path):
        with open(ck_path, "rb") as fh:
            ck = pickle.load(fh)
        ct, pivot_mask = np.asarray(ck["ct"], float), int(ck["pivot_mask"])
        assert ct.size == basis.dim, (ct.size, basis.dim)
        info.update({"target": "checkpoint " + os.path.basename(ck_path),
                     "support_tol": float(ck.get("support_tol", 1e-10)),
                     "e0": float(ck.get("e0", float("nan"))),
                     "campaign_len": len(ck.get("seq", [])),
                     "campaign_grown": int(ck.get("grown", 0)),
                     "campaign_rounds": int(ck.get("round", 0)),
                     "campaign_residual": float(ck.get("residual",
                                                       float("nan")))})
    else:
        if target_mode == "checkpoint":
            raise SystemExit("no finished checkpoint %s; use --target dense "
                             "(small systems only)" % ck_path)
        if basis.dim > 6000:
            raise SystemExit("dense target refused at dim %d" % basis.dim)
        H = build_h_sector(h, e, basis)
        w, V = np.linalg.eigh(H)
        ct, pivot_mask, _ = _normalize_target(V[:, 0], basis, None)
        info.update({"target": "dense eigh of the dump (root 0)",
                     "support_tol": 1e-10, "e0": float(w[0] + info["e_shift"]),
                     "campaign_len": None})
    return ct, pivot_mask, basis, (h, e), info


# --------------------------------------------------------------------- seeds
def _round_robin(letters, thetas, weights):
    """One copy of every distinct letter per pass (descending weight,
    canonical tie-break), then second copies, ... -- duplicates never
    adjacent."""
    groups = {}
    for L, t, w in zip(letters, thetas, weights):
        groups.setdefault(L, []).append((t, w))
    ranked = sorted(groups, key=lambda L: (-max(w for _, w in groups[L]), L))
    out = []
    for k in range(max(len(v) for v in groups.values())):
        for L in ranked:
            if k < len(groups[L]):
                out.append((L, groups[L][k][0]))
    return out


def _shuffle(pairs, seed=1):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(pairs))
    return [pairs[i] for i in idx]


def build_seed(stem, arm, order, pred_seed, n_routed, routed_word):
    """Return (list of ((holes, parts), theta_init), routed_theta_override
    or None, provenance dict)."""
    prov = {"arm": arm, "order": order}
    if arm == "cold":
        return [], None, prov
    labs = kh.load_labels()
    if arm == "pred":
        ppath = os.path.join(HERE, "k1_corpus", "predictions_splitC_h8.pkl")
        if stem != "h8_chain":
            raise SystemExit("the frozen predictions are for h8_chain only")
        with open(ppath, "rb") as fh:
            P = pickle.load(fh)
        word, th = P["preds"][pred_seed]
        cnt = kh.counts(word)
        weights = [cnt[L] + 1e-3 * abs(t) for L, t in zip(word, th)]
        pairs = _round_robin(word, th, weights)
        prov.update({"source": os.path.basename(ppath), "pred_seed": pred_seed,
                     "config": P.get("config"), "n": len(word),
                     "n_distinct": len(cnt)})
    elif arm == "b2":
        b2w, b2t = kh.b2_physics(stem, labs)
        sign = 1.0
        ppath = os.path.join(HERE, "k1_corpus", "predictions_splitC_h8.pkl")
        if os.path.exists(ppath):
            with open(ppath, "rb") as fh:
                sign = float(pickle.load(fh).get("b2_sign", 1.0))
        th = [sign * t for t in b2t]
        pairs = _round_robin(b2w, th, [abs(t) for t in b2t])
        prov.update({"source": "k1_harness.b2_physics (MP2 window)",
                     "b2_sign": sign, "n": len(b2w)})
    elif arm in ("oracle_full", "oracle_content"):
        lab = labs[stem]
        word = [tuple(map(tuple, x)) for x in lab["word"]]
        th = [float(x) for x in lab["th"]]
        if word[:n_routed] != routed_word:
            raise SystemExit("certified chain's routed prefix differs from "
                             "this run's routed chain -- target mismatch")
        gw, gt = word[n_routed:], th[n_routed:]
        if arm == "oracle_full":
            pairs = list(zip(gw, gt))
            prov.update({"source": "certified chain (label)", "n": len(gw),
                         "routed_theta": "certified"})
            return pairs, np.array(th[:n_routed]), prov
        pairs = [(L, 0.0) for L in gw]
        prov.update({"source": "certified chain grown multiset, theta 0",
                     "n": len(gw)})
    else:
        raise SystemExit("unknown arm %s" % arm)
    if order == "shuffle":
        pairs = _shuffle(pairs)
    return pairs, None, prov


# ------------------------------------------------------------------ running
def _default_order(arm):
    return "shuffle" if arm == "oracle_content" else "rank"


def _paths(stem, arm, pred_seed, order):
    tag = "%s_%s" % (stem, arm) + ("_s%d" % pred_seed if arm == "pred" else "")
    if order != _default_order(arm):
        tag += "_" + order
    d = os.path.join(HERE, "k1b")
    os.makedirs(d, exist_ok=True)
    return (tag, os.path.join(d, tag + "_state.pkl"),
            os.path.join(d, tag + "_trace.jsonl"),
            os.path.join(d, tag + "_summary.json"))


def run_arm(a):
    stem = a.stem
    tag, spath, tpath, jpath = _paths(stem, a.arm, a.seed, a.order)
    ct, pivot_mask, basis, (h, e), info = load_target(stem, a.target)
    t_end = time.time() + a.deadline
    t_inv = time.time()

    if os.path.exists(spath):
        with open(spath, "rb") as fh:
            state = pickle.load(fh)
        print("resuming %s at phase '%s' (len %d)"
              % (tag, state["phase"], len(state.get("seq", []))), flush=True)
    else:
        state = {"phase": "route", "support_tol": info["support_tol"],
                 "k1b": {"harness": HARNESS_VERSION, "git": _git_hash(),
                         "stem": stem, "arm": a.arm, "order": a.order,
                         "plateau": a.plateau, "target": info["target"],
                         "rot": 0, "gn_iters": 0, "wall_opt": 0.0,
                         "invocations": 0, "seeded": False}}
        print("new run %s: %s, dim %d" % (tag, info["target"], basis.dim),
              flush=True)
    K = state["k1b"]
    K["invocations"] += 1
    WORK["rot"] = 0
    WORK["gn_iters"] = 0
    rot_mark = [0, 0]

    def save():
        # fold this invocation's counters into the persisted totals
        K["rot"] += WORK["rot"] - rot_mark[0]
        K["gn_iters"] += WORK["gn_iters"] - rot_mark[1]
        rot_mark[0], rot_mark[1] = WORK["rot"], WORK["gn_iters"]
        if K["seeded"]:
            K["wall_opt"] += time.time() - save.t_last
        save.t_last = time.time()
        with open(spath + ".tmp", "wb") as fh:
            pickle.dump(state, fh)
        os.replace(spath + ".tmp", spath)
    save.t_last = time.time()

    def log(msg):
        rec = {"t_inv": round(time.time() - t_inv, 1),
               "wall_opt": round(K["wall_opt"] + (time.time() - save.t_last
                                                  if K["seeded"] else 0.0), 1),
               "rot": K["rot"] + WORK["rot"] - rot_mark[0],
               "gn_iters": K["gn_iters"] + WORK["gn_iters"] - rot_mark[1],
               "phase": state["phase"], "round": state.get("round", 0),
               "len": len(state.get("seq", [])), "rn": state.get("rn"),
               "msg": msg}
        with open(tpath, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print("[%7.0fs wall_opt %8.0fs it %6d rot %.3e] %s"
              % (rec["t_inv"], rec["wall_opt"], rec["gn_iters"], rec["rot"],
                 msg), flush=True)

    try:
        # ---- phase 1: routing + greedy ordering (identical in every arm)
        if not K["seeded"]:
            big.solve_resumable(ct, basis, pivot_mask, state, t_end, log=log,
                                save=save, stop_after_greedy=True)
            if state["phase"] != "joint":
                save()
                print("CHECKPOINT phase '%s' -- rerun the same command"
                      % state["phase"], flush=True)
                return
            n_routed = len(state["seq"])
            routed_word = [(tuple(s.holes), tuple(s.parts))
                           for s, _, _ in state["seq"]]
            rn_cold = float(state["rn"])
            # ---- phase 2: the proposal is appended (compile-outermost)
            pairs, routed_theta, prov = build_seed(
                stem, a.arm, a.order, a.seed, n_routed, routed_word)
            if routed_theta is not None:
                state["thetas"] = np.asarray(routed_theta, float).copy()
            for (hh, pp), th in pairs:
                state["seq"].append((Substitution(tuple(hh), tuple(pp)),
                                     None, None))
            if pairs:
                state["thetas"] = np.concatenate(
                    [state["thetas"], np.array([t for _, t in pairs], float)])
            state["rn"] = float(np.linalg.norm(
                _prep(state["thetas"], state["seq"], basis, pivot_mask) - ct))
            K.update({"seeded": True, "n_routed": n_routed,
                      "n_seed": len(pairs), "rn_routed": rn_cold,
                      "rn_seeded": float(state["rn"]),
                      "seed_provenance": prov,
                      "seed_letters": [(list(hh), list(pp), float(th))
                                       for (hh, pp), th in pairs]})
            # the optimizer clock starts here: routing + greedy work
            # (identical in every arm) is recorded but not charged
            K["rot_prep"] = int(K["rot"] + WORK["rot"] - rot_mark[0])
            K["rot"], K["gn_iters"] = 0, 0
            WORK["rot"], WORK["gn_iters"] = 0, 0
            rot_mark[0], rot_mark[1] = 0, 0
            save.t_last = time.time()
            save()
            log("seeded arm %s: routed %d (+ greedy), proposal +%d letters; "
                "|r| routed %.3e -> seeded %.3e"
                % (a.arm, n_routed, len(pairs), rn_cold, state["rn"]))
        # ---- phase 3: joint solve, growth, restarts -- the cold rules
        if state["phase"] not in ("noc", "done"):
            big.solve_resumable(ct, basis, pivot_mask, state, t_end, log=log,
                                save=save, plateau=a.plateau)
        if state["phase"] == "noc" and a.translate:
            occ = frozenset(q for q in range(2 * info["nmo"])
                            if (pivot_mask >> q) & 1)
            state["_save"] = save
            big.noc_resumable(state, occ, t_end, log=log)
    finally:
        state.pop("_save", None)
        save()
        print("[state saved: phase '%s']" % state["phase"], flush=True)

    finished = state["phase"] == "done" or \
        (state["phase"] == "noc" and not a.translate)
    if not finished:
        print("CHECKPOINT phase '%s' -- rerun the same command to continue"
              % state["phase"], flush=True)
        return
    # ---- certificate + summary
    psi = _prep(state["thetas"], state["seq"], basis, pivot_mask)
    deficit = float(max(0.0, 1.0 - abs(float(ct @ psi)) ** 2))
    if deficit > GATE:
        raise RuntimeError("arm finished above the gate: %.3e" % deficit)
    e_chain = None
    try:
        from chaincompile.fastpath import SparseH
        sp = SparseH(h, e, basis)
        e_chain = float(psi @ sp.matvec(psi)) + info["e_shift"]
    except Exception as ex:  # pragma: no cover
        print("energy check skipped (%s)" % ex, flush=True)
    word = [s for s, _, _ in state["seq"]]
    ranks = {}
    for s in word:
        ranks[len(s.holes)] = ranks.get(len(s.holes), 0) + 1
    summary = {
        "harness": HARNESS_VERSION, "git": K["git"], "stem": stem,
        "arm": a.arm, "order": a.order, "pred_seed": a.seed,
        "plateau": a.plateau, "target": info["target"],
        "n_routed": K["n_routed"], "n_seed": K["n_seed"],
        "rn_routed": K["rn_routed"], "rn_seeded": K["rn_seeded"],
        "final_len": len(word), "ranks": {str(k): v for k, v in ranks.items()},
        "grown": int(state.get("grown", 0)), "rounds": int(state.get("round", 0)),
        "restarts": int(state.get("tries", 0)),
        "max_abs_theta": float(np.max(np.abs(state["thetas"]))),
        "residual": float(state.get("residual", deficit)),
        "deficit_recheck": deficit,
        "e0_target": info["e0"], "e_chain": e_chain,
        "rot_prep_uncharged": int(K.get("rot_prep", 0)),
        "cost_rot": int(K["rot"]), "cost_gn_iters": int(K["gn_iters"]),
        "cost_wall_opt_s": round(K["wall_opt"], 1),
        "invocations": K["invocations"],
        "campaign_len": info.get("campaign_len"),
        "seed_provenance": K["seed_provenance"],
    }
    with open(jpath, "w") as fh:
        json.dump(summary, fh, indent=1)
    np.savez(os.path.join(HERE, "k1b", tag + "_chain.npz"),
             subs_h=np.array([s.holes for s in word], dtype=object),
             subs_p=np.array([s.parts for s in word], dtype=object),
             th=state["thetas"], pivot=pivot_mask)
    write_text(os.path.join(HERE, "results", "k1b_t4_%s.md" % tag),
               arm_report(summary, info))
    print("DONE: %s len %d rounds %d GN iters %d rotations %.4e "
          "wall_opt %.0f s residual %.1e -> results/k1b_t4_%s.md"
          % (tag, len(word), summary["rounds"], summary["cost_gn_iters"],
             summary["cost_rot"], summary["cost_wall_opt_s"],
             summary["residual"], tag), flush=True)


def arm_report(s, info):
    de = ("%.2e" % (s["e_chain"] - s["e0_target"])
          if s["e_chain"] is not None else "n/a")
    return (
        "# K1b-T4 warm-start arm -- %s / %s\n\n"
        "Source: target %s; dump %s; sector (%d,%d) dim %d; harness %s at "
        "commit %s.\n"
        "Provenance: invocation k1b_warmstart.py %s --arm %s --order %s"
        "%s --plateau %s (repeated to completion, %d invocations).\n\n"
        "Proposal: %d letters appended after the %d routed (greedy-ordered) "
        "letters; |r| routed %.3e -> seeded %.3e. Seed provenance: %s.\n\n"
        "Cost (from the first Gauss-Newton solve to the gate): %d rotations "
        "(2x2, per column), %d GN iterations, %d growth rounds, %d restarts, "
        "wall %.0f s.\n\n"
        "Certificate: final chain %d letters (grown %d), ranks %s, "
        "max|theta| %.6f, residual (1-fid^2) %.1e (recheck %.1e), "
        "E(chain) - E0 = %s.\n"
        % (s["stem"], s["arm"], s["target"], info["dump"], info["na"],
           info["nb"], info["dim"], s["harness"], s["git"], s["stem"],
           s["arm"], s["order"],
           (" --seed %d" % s["pred_seed"]) if s["arm"] == "pred" else "",
           s["plateau"], s["invocations"], s["n_seed"], s["n_routed"],
           s["rn_routed"], s["rn_seeded"], json.dumps(s["seed_provenance"]),
           s["cost_rot"], s["cost_gn_iters"], s["rounds"], s["restarts"],
           s["cost_wall_opt_s"], s["final_len"], s["grown"], s["ranks"],
           s["max_abs_theta"], s["residual"], s["deficit_recheck"], de))


# ------------------------------------------------------------------- scoring
def score(a):
    stem = a.stem
    d = os.path.join(HERE, "k1b")
    sums = {}
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.startswith(stem + "_") and f.endswith("_summary.json"):
            with open(os.path.join(d, f)) as fh:
                s = json.load(fh)
            sums[f[len(stem) + 1:-len("_summary.json")]] = s
    if "cold" not in sums:
        raise SystemExit("no finished cold arm for %s" % stem)
    cold = sums["cold"]
    lines = ["# K1b-T4 warm-start scoreboard -- %s\n" % stem,
             "Governing currency: rotations (2x2, per column) from the first "
             "Gauss-Newton solve to the certification gate; every arm under "
             "harness %s, plateau %s, identical target (%s).\n"
             % (cold["harness"], cold["plateau"], cold["target"]),
             "| arm | proposal | final len | rounds | GN iters | rotations | "
             "wall s | savings (rot) | savings (iters) | savings (wall) | "
             "residual |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    sav = {}
    for tag, s in sums.items():
        r = 1 - s["cost_rot"] / cold["cost_rot"]
        i = 1 - s["cost_gn_iters"] / max(1, cold["cost_gn_iters"])
        w = 1 - s["cost_wall_opt_s"] / max(1e-9, cold["cost_wall_opt_s"])
        sav[tag] = r
        lines.append("| %s | %d | %d | %d | %d | %.4e | %.0f | %+.1f%% | "
                     "%+.1f%% | %+.1f%% | %.1e |"
                     % (tag, s["n_seed"], s["final_len"], s["rounds"],
                        s["cost_gn_iters"], s["cost_rot"],
                        s["cost_wall_opt_s"], 100 * r, 100 * i, 100 * w,
                        s["residual"]))
    pred_tags = sorted(t for t in sav if t.startswith("pred"))
    if "pred_s0" in pred_tags:            # the registered arm is seed 0
        pred_tags.remove("pred_s0")
        pred_tags.insert(0, "pred_s0")
    verdict = "PENDING (pred and b2 arms both required)"
    if pred_tags and "b2" in sav:
        sp_ = sav[pred_tags[0]]
        sb_ = sav["b2"]
        g1 = sp_ >= 0.30
        g2 = sp_ >= 1.3 * sb_
        verdict = ("PASS" if (g1 and g2) else "FAIL") + \
            (" -- pred savings %+.1f%% (gate >= 30%%: %s); b2 savings "
             "%+.1f%%, 1.3x b2 = %+.1f%% (gate: %s)"
             % (100 * sp_, "met" if g1 else "not met", 100 * sb_,
                130 * sb_, "met" if g2 else "not met"))
    lines += ["", "Registered thresholds (docs/k1_verdict.md, K1b-T4): pred "
              "savings >= 30% vs cold AND >= 1.3x the b2 savings.", "",
              "VERDICT: " + verdict, ""]
    for tag, s in sums.items():
        if tag.startswith("oracle"):
            lines.append("Ceiling (%s): %+.1f%% savings -- what a perfect "
                         "proposal of this kind is worth on this target."
                         % (tag, 100 * sav[tag]))
    out = "\n".join(lines) + "\n"
    write_text(os.path.join(HERE, "results", "k1b_t4_%s.md" % stem), out)
    print(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stem")
    ap.add_argument("--arm", choices=ARMS, default="cold")
    ap.add_argument("--seed", type=int, default=0,
                    help="prediction seed for --arm pred (0..4)")
    ap.add_argument("--order", choices=("rank", "shuffle"), default=None,
                    help="seed ordering; default rank (oracle_content: shuffle)")
    ap.add_argument("--plateau", default=str(PLATEAU_DEFAULT),
                    help="per-slice relative-gain floor, or 'none'")
    ap.add_argument("--deadline", type=float, default=14400,
                    help="seconds per invocation before checkpointing")
    ap.add_argument("--target", choices=("checkpoint", "dense"),
                    default="checkpoint")
    ap.add_argument("--translate", action="store_true",
                    help="also run the constructive translation (NOC) "
                    "after the gate (not part of the cost)")
    ap.add_argument("--score", action="store_true")
    a = ap.parse_args()
    a.plateau = None if str(a.plateau).lower() == "none" else float(a.plateau)
    if a.order is None:
        a.order = _default_order(a.arm)
    if a.score:
        score(a)
    else:
        run_arm(a)


if __name__ == "__main__":
    main()

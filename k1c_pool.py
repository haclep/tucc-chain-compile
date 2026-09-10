#!/usr/bin/env python
"""k1c_pool.py -- K1c step 1c: the round-one pool at the post-joint state.

What growth actually does (read from run_big_sd._grow_once and measured
on the corpus, 2026-09-08): after the joint solve, each round takes the
twelve largest-residual determinants, enumerates every S/D edge from
them (the "pool"), scores each edge by its first-order fidelity gain
|<residual, kappa_e psi>|, appends the best max(4, len/8) at theta = 0,
and re-solves. The same substitution direction is often re-selected in
later rounds, each time as a tiny correction (on h8_chain the letters
with >= 10 copies carry a median TOTAL rotation of 0.02 rad). On every
H6 system probed, 100% of the new grown letters lie inside the
round-one pool. So the proposer's universe is that pool, and the
target is how many times each pool letter is selected across rounds.

This module reproduces the state the compiler is in at the start of
growth (phase 1 via k1c_phase1, then the joint Gauss-Newton solve with
the harness's settings: tol 1e-13, 300 iterations, angle bound), builds
the round-one pool, and featurizes every pool letter with:

  compiler-native : tangent score at the post-joint state, its log and
                    its rank within the pool, how many of the top-12
                    residual determinants the letter connects, the
                    residual mass on those determinants, support
                    connectivity (into support / into fill-in).
  routed          : whether the key is already a routed letter, its
                    routed occurrences, and its post-joint |theta|.
  invariant       : k1c_universe structural + physics features.

Cost: one joint solve per system, the same ~1% of cold cost the arm
would spend anyway. Cached to k1c_cache/<name>_pool.pkl.

Usage:
    python k1c_pool.py k1_h6_chain_19          # build + report
    python k1c_pool.py --all-h6                 # cache the H6 set
"""
import argparse
import importlib.util as iu
import os
import pickle
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "src"))

from chaincompile.compile import _gauss_newton, _prep                # noqa: E402
from chaincompile.dets import (Substitution, popcount,               # noqa: E402
                               substitution_between)


def _load(name, fn):
    spec = iu.spec_from_file_location(name, os.path.join(HERE, fn))
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kh = _load("kh", "k1_harness.py")
ku = _load("ku", "k1c_universe.py")
p1 = _load("p1", "k1c_phase1.py")
BOUND = p1.BOUND
CACHE = p1.CACHE
TOP = 24                      # residual determinants that seed the pool
JOINT_ITERS = 300             # the harness's joint-phase budget

POOL_NAMES = ["tangent", "log_tangent", "tangent_rel", "tangent_rank",
              "n_top_dets", "res_mass", "supp_in", "supp_out",
              "is_routed", "routed_n", "routed_abs_th", "routed_sat"]


def joint_state(P):
    """Joint Gauss-Newton solve from the greedy init, harness settings."""
    th, rn = _gauss_newton(P["theta0"], P["seq"], P["basis"], P["pivot"],
                           P["ct"], tol=1e-13, max_iter=JOINT_ITERS,
                           bound=BOUND)
    psi = _prep(th, P["seq"], P["basis"], P["pivot"])
    return np.asarray(th, float), psi, psi - P["ct"], float(rn)


def round_one_pool(basis, resv):
    """Edges from the TOP largest-residual determinants, as _grow_once.
    Returns key -> (n_top_dets connected, residual mass on them)."""
    top = sorted(range(basis.dim), key=lambda i: -abs(resv[i]))[:TOP]
    pool = {}
    for i in top:
        mi = basis.masks[i]
        w = abs(float(resv[i]))
        for j in range(basis.dim):
            if j == i:
                continue
            mj = basis.masks[j]
            if popcount(mi & ~mj) > 2:
                continue
            a, b = (mi, mj) if mi < mj else (mj, mi)
            sub = substitution_between(a, b)
            key = (tuple(sub.holes), tuple(sub.parts))
            n, m = pool.get(key, (0, 0.0))
            pool[key] = (n + 1, m + w)
    return pool


def build(name, force=False):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name + "_pool.pkl")
    if os.path.exists(path) and not force:
        with open(path, "rb") as fh:
            return pickle.load(fh)
    P = p1.phase1(name)
    S = ku.load_system(name)
    mp2 = kh.mp2_letter_score(name)
    th, psi, resv, rn = joint_state(P)
    pool = round_one_pool(P["basis"], resv)
    keys = sorted(pool)
    Pj = dict(P)
    Pj["psi"], Pj["resv"] = psi, resv
    ts = p1.tangent_scores(Pj, keys)
    n_in, n_out = p1.support_connectivity(P, keys)
    rset = {}
    for k, t in zip(P["routed_word"], th):
        d = rset.setdefault(k, [0, 0.0, 0])
        d[0] += 1
        d[1] = max(d[1], abs(float(t)))
        d[2] += int(abs(t) >= 0.92 * BOUND)
    order = np.argsort(-ts)
    rank = np.empty(len(keys))
    rank[order] = np.arange(len(keys)) / max(1, len(keys) - 1)
    tmax = float(ts.max()) if len(ts) else 1.0
    sysf = ku.system_features(S, mp2[0])
    rows = []
    for n, k in enumerate(keys):
        st, ph = ku.letter_features(S, k, mp2[0], mp2[1])
        ntop, rmass = pool[k]
        r = rset.get(k, [0, 0.0, 0])
        rows.append(sysf + st + ph + [
            float(ts[n]), float(np.log10(ts[n] + 1e-16)),
            float(ts[n] / max(tmax, 1e-16)), float(rank[n]),
            float(ntop), float(rmass), float(n_in[n]), float(n_out[n]),
            float(r[0] > 0), float(r[0]), float(r[1]), float(r[2])])
    names = ku.SYS_NAMES + ku.STRUCT_NAMES + ku.PHYS_NAMES + POOL_NAMES
    cnt = kh.counts(P["grown"])
    y = np.array([cnt.get(k, 0) for k in keys], float)
    out = {"name": name, "keys": keys, "X": np.array(rows, float),
           "names": names, "y": y, "grown": P["grown"],
           "n_routed": P["n_routed"], "routed_word": P["routed_word"],
           "rn_greedy": P["rn"], "rn_joint": rn,
           "in_pool_mass": float(sum(cnt[k] for k in cnt if k in pool)
                                 / max(1, len(P["grown"]))),
           "in_pool_distinct": float(sum(1 for k in cnt if k in pool)
                                     / max(1, len(cnt))),
           "target_src": P["target_src"]}
    with open(path, "wb") as fh:
        pickle.dump(out, fh)
    return out


def report(F):
    cnt = kh.counts(F["grown"])
    y = F["y"]
    j = F["names"].index("tangent")
    ts = F["X"][:, j]
    n_true_d = int((y > 0).sum())
    order = np.argsort(-ts)
    topn = set(order[:n_true_d])
    hit = sum(1 for i in range(len(y)) if y[i] > 0 and i in topn)
    mass_hit = sum(y[i] for i in topn)
    print("%-16s |r| greedy %.2e -> joint %.2e | pool %d letters | grown %d "
          "(%d distinct): in-pool mass %.3f distinct %.3f | tangent top-N: "
          "%d/%d distinct, %.0f%% mass"
          % (F["name"], F["rn_greedy"], F["rn_joint"], len(F["keys"]),
             len(F["grown"]), len(cnt), F["in_pool_mass"],
             F["in_pool_distinct"], hit, n_true_d,
             100.0 * mass_hit / max(1, y.sum())))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--all-h6", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    labs = kh.load_labels()
    names = list(a.names)
    if a.all_h6:
        names += sorted(n for n in labs if n.startswith("k1_h6")
                        and not labs[n].get("mixed", False))
    for n in names:
        report(build(n, force=a.force))


if __name__ == "__main__":
    main()

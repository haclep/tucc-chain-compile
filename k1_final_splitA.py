#!/usr/bin/env python
"""k1_final_splitA.py -- the FINAL banked Split-A evaluation (rev D.2).

Model: v1 = C1C2K (frozen on inner folds, rev E.3). Five seeds, outer
LOGO folds from k1_corpus/splits.json, every held-out system evaluated
exactly once. Adjudication per rev E.2: pooled across ALL folds,
fold-level Delta-theta (model minus STRONGEST of B0/B1/B2) and
Delta-F1 (model minus B1), CI over folds; per-family table published
alongside. Per-family results cached under /tmp/k1_final so the
evaluation is computed once.

Usage:  python k1_final_splitA.py --fam h6_ring     (one family)
        python k1_final_splitA.py --aggregate       (assemble verdict)
"""
import json
import os
import pickle
import sys

import numpy as np

import importlib.util as iu
spec = iu.spec_from_file_location("kh", "k1_harness.py")
kh = iu.module_from_spec(spec); spec.loader.exec_module(kh)
spec2 = iu.spec_from_file_location("dv", "k1_dev_m1.py")
dv = iu.module_from_spec(spec2); spec2.loader.exec_module(dv)

dv.DEV_SEEDS = (0, 1, 2, 3, 4)          # full seeds for the banked run
CFG = "C1C2K"
OUT = "/tmp/k1_final"
os.makedirs(OUT, exist_ok=True)
FAMS = ["h4_chain", "h4_ring", "h6_chain", "h6_ring",
        "lih", "h2o_fc_series", "n2_series", "c2_singlet"]


def run_family(fam, labs, splits):
    cache = {}
    rows = []
    for fold in splits["split_A_interpolation"][fam]:
        held, train = fold["held_out"], fold["train"]
        if not train:
            continue
        per_seed = dv.run_fold(train, held, labs, cache, CFG)
        mR2 = float(np.mean([s["R2"] for s in per_seed]))
        mF1 = float(np.mean([s["F1"] for s in per_seed]))
        s2 = dv.m1.fit_sign(train, labs, cache)
        b1w, b1t, _ = kh.b1_copy(train, held, labs)
        b0w, b0t = kh.b0_freq(train, labs)
        b2w, b2t = kh.b2_physics(held, labs)
        b2t = [s2 * t for t in b2t]
        bR2 = max(kh.eval_pred(b0w, b0t, labs[held])["R2"],
                  kh.eval_pred(b1w, b1t, labs[held])["R2"],
                  kh.eval_pred(b2w, b2t, labs[held])["R2"])
        b1F1 = kh.eval_pred(b1w, b1t, labs[held])["F1"]
        rows.append({"held": held, "mR2": mR2, "mF1": mF1,
                     "bestR2": bR2, "b1F1": b1F1})
        print("  %-18s model thR2 %+.3f F1 %.3f | best-base thR2 %+.3f "
              "B1 F1 %.3f" % (held, mR2, mF1, bR2, b1F1))
    with open(os.path.join(OUT, fam + ".pkl"), "wb") as fh:
        pickle.dump(rows, fh)
    return rows


def aggregate():
    allrows, table = [], []
    for fam in FAMS:
        p = os.path.join(OUT, fam + ".pkl")
        if not os.path.exists(p):
            print("MISSING family cache: %s -- run it first" % fam)
            return
        rows = pickle.load(open(p, "rb"))
        allrows += rows
        dR2 = np.array([r["mR2"] - r["bestR2"] for r in rows])
        dF1 = np.array([r["mF1"] - r["b1F1"] for r in rows])
        ci = lambda x: 1.96 * x.std(ddof=1) / np.sqrt(len(x))
        table.append((fam, len(rows), float(np.mean([r["mR2"] for r in rows])),
                      float(np.mean([r["bestR2"] for r in rows])),
                      float(dR2.mean()), float(ci(dR2)),
                      float(np.mean([r["mF1"] for r in rows])),
                      float(np.mean([r["b1F1"] for r in rows])),
                      float(dF1.mean()), float(ci(dF1))))
    print("FINAL Split-A (v1 = C1C2K, 5 seeds) -- per family:")
    for t in table:
        print("  %-13s n=%2d thR2 %+.3f/best %+.3f dR2 %+.3f+-%.3f | "
              "F1 %.3f/B1 %.3f dF1 %+.3f+-%.3f" % t)
    dR2 = np.array([r["mR2"] - r["bestR2"] for r in allrows])
    dF1 = np.array([r["mF1"] - r["b1F1"] for r in allrows])
    n = len(allrows)
    ciR = 1.96 * dR2.std(ddof=1) / np.sqrt(n)
    ciF = 1.96 * dF1.std(ddof=1) / np.sqrt(n)
    print("E.2 AGGREGATE over %d folds:" % n)
    print("  Delta-theta-R2 = %+.4f +- %.4f  -> %s"
          % (dR2.mean(), ciR,
             "BEATS strongest baseline (CI-separated)" if dR2.mean() - ciR > 0
             else ("CI-separated BELOW" if dR2.mean() + ciR < 0
                   else "not separated")))
    print("  Delta-F1       = %+.4f +- %.4f  -> %s"
          % (dF1.mean(), ciF,
             "match/exceeds B1" if dF1.mean() + ciF >= 0
             else "CI-separated undershoot (failed match)"))


def main():
    labs = kh.load_labels()
    splits = json.load(open(os.path.join("k1_corpus", "splits.json")))
    if "--aggregate" in sys.argv:
        aggregate()
        return
    fam = sys.argv[sys.argv.index("--fam") + 1]
    run_family(fam, labs, splits)


if __name__ == "__main__":
    main()

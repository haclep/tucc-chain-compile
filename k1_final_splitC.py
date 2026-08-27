#!/usr/bin/env python
"""k1_final_splitC.py -- Split C, the decisive cross-size evaluation.

Train: ALL non-mixed H4 + H6 systems (98), per the FROZEN protocol
Sec. 4. NOTE, recorded: splits.json's split_C train field ("all
non-mixed") would include the test system itself; the frozen text
governs and this runner implements Sec. 4 verbatim. Test: h8_chain,
never seen, four sites larger than anything in training, no copy
baseline exists.

Model: v1 = C1C2K, five seeds. Predictions for every seed are FROZEN
to k1_corpus/predictions_splitC_h8.pkl before scoring; content (T1)
and theta (T2) are scored immediately against the frozen P1 gates;
warm-start (T4) is scored later from the SAME frozen predictions once
the compile-side harness exists -- one touch of the test system,
staged scoring, per rev D.2.

Run in the seneca-ml environment (sklearn):
    python -u k1_final_splitC.py            (the banked final)
    python -u k1_final_splitC.py --dry      (mechanics only: trains,
                                             predicts, freezes, does
                                             NOT score against truth)
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

dv.DEV_SEEDS = (0, 1, 2, 3, 4)
CFG = "C1C2K"
TEST = "h8_chain"
PRED = os.path.join("k1_corpus", "predictions_splitC_h8.pkl")

# rev E.1 size-slope inputs from the banked Split-A final
# (results/k1_splitA_final.md): fold-weighted family means.
SLOPE_A = {4: {"dR2": -0.067, "dF1": +0.016},
           6: {"dR2": -0.147, "dF1": +0.039}}


def main():
    dry = "--dry" in sys.argv
    labs = kh.load_labels()
    train = sorted(n for n in labs
                   if (n.startswith("k1_h4") or n.startswith("k1_h6"))
                   and not labs[n]["mixed"])
    print("Split C | train %d (Sec. 4: all non-mixed H4+H6; splits.json"
          " field superseded by frozen text, recorded) | test %s"
          % (len(train), TEST))
    cache = {}
    uni = set()
    for m in train:
        uni |= set(labs[m]["word"])
        if m not in cache:
            cache[m] = kh.mp2_letter_score(m)
    cache[TEST] = kh.mp2_letter_score(TEST)
    uni |= set(cache[TEST][0])          # B2 window of the test system
    uni = sorted(uni)
    print("candidate universe %d letters (train vocab + B2 window)"
          % len(uni))
    Xs, yks, yts = [], [], []
    for m in train:
        X, yk, yt, _ = dv.build(m, labs, uni, cache, CFG, train)
        Xs.append(X); yks.append(yk); yts.append(yt)
    Xtr = np.vstack(Xs); yktr = np.hstack(yks); yttr = np.hstack(yts)
    Xh, _, _, keys = dv.build(TEST, labs, uni, cache, CFG, train)
    nb = dv.m1.build_rows(train[0], labs, uni, cache)[0].shape[1]
    kcols = np.arange(Xtr.shape[1])
    tcols = np.arange(0, nb)
    present = yktr > 0
    s2 = dv.m1.fit_sign(train, labs, cache)
    preds = {}
    for seed in dv.DEV_SEEDS:
        mk = dv.gbm(CFG, seed).fit(Xtr[:, kcols], yktr)
        mt = dv.gbm(CFG, seed).fit(Xtr[present][:, tcols], yttr[present])
        khat = np.clip(np.round(mk.predict(Xh[:, kcols])), 0,
                       None).astype(int)
        that = mt.predict(Xh[:, tcols])
        pw, pt = [], []
        for key, kk, tt in zip(keys, khat, that):
            pw += [key] * int(kk)
            pt += [float(tt)] * int(kk)
        preds[seed] = (pw, pt)
        print("  seed %d: predicted %d letters (%d distinct)"
              % (seed, len(pw), len(set(pw))))
    with open(PRED, "wb") as fh:
        pickle.dump({"config": CFG, "train_n": len(train),
                     "universe_n": len(uni), "b2_sign": s2,
                     "preds": preds}, fh)
    print("predictions FROZEN -> %s" % PRED)
    if dry:
        print("DRY RUN: scoring skipped; the banked final has not been "
              "spent.")
        return
    # ---- scoring (T1 content, T2 theta) against the frozen P1 gates
    scores = [kh.eval_pred(pw, pt, labs[TEST]) for pw, pt in
              preds.values()]
    F1 = np.array([s["F1"] for s in scores])
    R2 = np.array([s["R2"] for s in scores])
    b2w, b2t = kh.b2_physics(TEST, labs)
    b2t = [s2 * t for t in b2t]
    b2 = kh.eval_pred(b2w, b2t, labs[TEST])
    print("MODEL  F1 %.3f +- %.3f (seed spread) | theta R2 %+.3f +- %.3f"
          % (F1.mean(), F1.std(ddof=1), R2.mean(), R2.std(ddof=1)))
    print("B2     F1 %.3f | theta R2 %+.3f" % (b2["F1"], b2["R2"]))
    print("P1 gates: content F1 >= 0.60: %s | >= B2+0.10 (%.3f): %s | "
          "theta R2 >= 0.5: %s"
          % ("PASS" if F1.mean() >= 0.60 else "FAIL",
             b2["F1"] + 0.10,
             "PASS" if F1.mean() >= b2["F1"] + 0.10 else "FAIL",
             "PASS" if R2.mean() >= 0.5 else "FAIL"))
    print("T4 warm-start: PENDING (scored later from the frozen "
          "predictions; harness not yet built)")
    dR2_8 = R2.mean() - b2["R2"]
    dF1_8 = F1.mean() - b2["F1"]
    print("rev E.1 size-slope (Delta model - strongest available "
          "baseline):")
    for n in (4, 6):
        print("  n=%d : dR2 %+.3f  dF1 %+.3f   (Split-A final, "
              "fold-weighted)" % (n, SLOPE_A[n]["dR2"],
                                  SLOPE_A[n]["dF1"]))
    print("  n=8 : dR2 %+.3f  dF1 %+.3f   (vs B2, the only defined "
          "baseline; single system, seed spread only)" % (dR2_8, dF1_8))


if __name__ == "__main__":
    main()

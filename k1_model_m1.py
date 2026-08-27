#!/usr/bin/env python
"""k1_model_m1.py -- M1-v0: equivariant per-letter model, Split A only.

Model family M1 (protocol Sec 6), simplest member: one shared function
scores every candidate letter of a system from physical features --
permutation-equivariant by construction. Two heads (gradient-boosted
trees): multiplicity k (0 = absent) and theta. Candidate universe per
fold = letters seen in TRAINING systems union B2's occ->virt window;
the model never sees the held-out chain. Features include B2's MP2
score and seed, so beating B2 means learning beyond B2's own inputs.

Discipline: folds from k1_corpus/splits.json only; 5 seeds; each
held-out system evaluated once per seed; B2's global sign fitted on
training folds only (rev B.2). Prints per-family P2-shaped verdicts:
theta vs the STRONGEST baseline, content vs B1 copy.
"""
import json
import os
import pickle
import sys

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

import importlib.util as iu
spec = iu.spec_from_file_location("kh", "k1_harness.py")
kh = iu.module_from_spec(spec)
spec.loader.exec_module(kh)

SEEDS = (0, 1, 2, 3, 4)


def spacing_of(name):
    tail = name.split("_")[-1]
    if tail == "sto3g":
        return 3.0
    try:
        return int(tail) / 10.0
    except ValueError:
        return 0.0


def sysfeat(name, lab, sc):
    vals = np.array(list(sc.values()))
    return [spacing_of(name), lab["dim"] ** 0.5, len(lab["support"]),
            float(vals.max()), float(vals.mean())]


def letfeat(key, scores, thetas):
    (hh, pp) = key
    r = len(hh)
    sspin = 1.0 if len(set(q % 2 for q in hh)) == 1 else 0.0
    return [r, sspin, scores.get(key, 0.0), thetas.get(key, 0.0),
            min(hh + pp), max(hh + pp),
            float(np.mean([abs(a - b) for a in hh for b in pp]))]


def build_rows(name, labs, universe, cache):
    if name not in cache:
        cache[name] = kh.mp2_letter_score(name)
    scores, thetas = cache[name]
    lab = labs[name]
    tm = kh.theta_map(lab["word"], lab["th"])
    cnt = kh.counts(lab["word"])
    sf = sysfeat(name, lab, scores)
    X, yk, yt, keys = [], [], [], []
    for key in universe:
        X.append(sf + letfeat(key, scores, thetas))
        yk.append(cnt.get(key, 0))
        yt.append(tm.get(key, 0.0))
        keys.append(key)
    return np.array(X), np.array(yk, float), np.array(yt), keys


def fit_sign(train, labs, cache):
    agree = tot = 0
    for m in train:
        if m not in cache:
            cache[m] = kh.mp2_letter_score(m)
        sc, th = cache[m]
        tm = kh.theta_map(labs[m]["word"], labs[m]["th"])
        for k, t in tm.items():
            if k in th and abs(th[k]) > 1e-6:
                tot += 1
                agree += (np.sign(th[k]) == np.sign(t))
    return 1.0 if tot and agree >= tot / 2 else -1.0


def run_family(fam, splits, labs):
    cache = {}
    folds = splits["split_A_interpolation"][fam]
    rows = []
    for fold in folds:
        held, train = fold["held_out"], fold["train"]
        if not train:
            continue
        uni = set()
        for m in train:
            uni |= set(labs[m]["word"])
            if m not in cache:
                cache[m] = kh.mp2_letter_score(m)
            uni |= set(cache[m][0])
        uni = sorted(uni)
        Xs, yks, yts = [], [], []
        for m in train:
            X, yk, yt, _ = build_rows(m, labs, uni, cache)
            Xs.append(X); yks.append(yk); yts.append(yt)
        Xtr = np.vstack(Xs); yktr = np.hstack(yks); yttr = np.hstack(yts)
        Xh, _, _, keys = build_rows(held, labs, uni, cache)
        s2 = fit_sign(train, labs, cache)
        per_seed = []
        for seed in SEEDS:
            mk = GradientBoostingRegressor(random_state=seed).fit(Xtr, yktr)
            mt = GradientBoostingRegressor(random_state=seed).fit(Xtr, yttr)
            khat = np.clip(np.round(mk.predict(Xh)), 0, None).astype(int)
            that = mt.predict(Xh)
            pw, pt = [], []
            for key, kk, tt in zip(keys, khat, that):
                pw += [key] * int(kk)
                pt += [float(tt)] * int(kk)
            per_seed.append(kh.eval_pred(pw, pt, labs[held]))
        b1w, b1t, _ = kh.b1_copy(train, held, labs)
        b0w, b0t = kh.b0_freq(train, labs)
        b2w, b2t = kh.b2_physics(held, labs)
        b2t = [s2 * t for t in b2t]
        base = {"B0": kh.eval_pred(b0w, b0t, labs[held]),
                "B1": kh.eval_pred(b1w, b1t, labs[held]),
                "B2": kh.eval_pred(b2w, b2t, labs[held])}
        rows.append((held, per_seed, base))
    return rows


def summarize(fam, rows):
    mR2 = np.array([[s["R2"] for s in ps] for _, ps, _ in rows])
    mF1 = np.array([[s["F1"] for s in ps] for _, ps, _ in rows])
    bbest = np.array([max(b[k]["R2"] for k in b) for _, _, b in rows])
    b1F1 = np.array([b["B1"]["F1"] for _, _, b in rows])
    dR2 = mR2.mean(1) - bbest
    dF1 = mF1.mean(1) - b1F1
    ci = lambda x: 1.96 * x.std(ddof=1) / np.sqrt(len(x))
    print("%-10s folds %2d | model thR2 %+.3f vs best-base %+.3f "
          "-> dR2 %+.3f+-%.3f | F1 %.3f vs B1 %.3f -> dF1 %+.3f+-%.3f"
          % (fam, len(rows), mR2.mean(), bbest.mean(),
             dR2.mean(), ci(dR2), mF1.mean(), b1F1.mean(),
             dF1.mean(), ci(dF1)))


def main():
    labs = kh.load_labels()
    splits = json.load(open(os.path.join("k1_corpus", "splits.json")))
    fams = sys.argv[1:] or ["lih"]
    for fam in fams:
        rows = run_family(fam, splits, labs)
        summarize(fam, rows)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""k1_dev_m1.py -- M1 development runner (rev D.1 compliant).

DEV CONSTRUCTION (recorded per D.1): for each family the dev anchor
is the outer fold whose held-out system has the MEDIAN spacing
(deterministic). Development scores are inner leave-one-out over that
fold's TRAINING list only; the outer held-out system is never loaded
into any inner evaluation. Config decisions are made on inner means;
dev seeds = (0, 1) -- final banked runs keep the full 5.

Configs raced (cumulative):
  v0  : as banked (theta head trained on all universe rows).
  C1  : theta head trained ONLY on rows with count > 0
        (removes the zero-target pollution diagnosed at v0).
  C2  : baseline-subsumption features: per-letter pool frequency and
        pool-mean theta, plus nearest- and second-nearest-spacing
        neighbor count and theta. Train rows are featurized with
        leave-self-out pool stats; held rows with full-pool stats.
  C3  : GBM budget 300 trees, depth 3, lr 0.05 (both heads).
"""
import json
import os
import sys

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

import importlib.util as iu
spec = iu.spec_from_file_location("kh", "k1_harness.py")
kh = iu.module_from_spec(spec)
spec.loader.exec_module(kh)
spec2 = iu.spec_from_file_location("m1", "k1_model_m1.py")
m1 = iu.module_from_spec(spec2)
spec2.loader.exec_module(m1)

DEV_SEEDS = (0, 1)


def pool_stats(pool, labs, cache, exclude=None):
    freq, thsum, nsys = {}, {}, 0
    for m in pool:
        if m == exclude:
            continue
        nsys += 1
        cnt = kh.counts(labs[m]["word"])
        tm = kh.theta_map(labs[m]["word"], labs[m]["th"])
        for k, c in cnt.items():
            freq[k] = freq.get(k, 0) + c
            thsum[k] = thsum.get(k, 0.0) + tm[k]
    return ({k: v / max(1, nsys) for k, v in freq.items()},
            {k: thsum[k] / max(1, freq[k] and nsys) for k in thsum}, nsys)


def neighbor_stats(pool, labs, target, k=2):
    ordered = sorted(pool, key=lambda n: abs(m1.spacing_of(n)
                                             - m1.spacing_of(target)))
    out = []
    for m in ordered[:k]:
        out.append((kh.counts(labs[m]["word"]),
                    kh.theta_map(labs[m]["word"], labs[m]["th"])))
    while len(out) < k:
        out.append(({}, {}))
    return out


def build(name, labs, uni, cache, cfg, pool):
    X, yk, yt, keys = m1.build_rows(name, labs, uni, cache)
    if "C2" in cfg or "C2K" in cfg:
        ex = name if name in pool else None
        fr, tp, _ = pool_stats(pool, labs, cache, exclude=ex)
        nb = neighbor_stats([m for m in pool if m != name], labs, name)
        extra = []
        for key in keys:
            row = [fr.get(key, 0.0), tp.get(key, 0.0)]
            for cnt, tm in nb:
                row += [cnt.get(key, 0), tm.get(key, 0.0)]
            extra.append(row)
        X = np.hstack([X, np.array(extra)])
    if "SG" in cfg:
        others = [m for m in pool if m != name]
        maps = [(m1.spacing_of(m), kh.theta_map(labs[m]["word"], labs[m]["th"]))
                for m in others]
        sg = []
        s0 = m1.spacing_of(name)
        for key in keys:
            vals = [(abs(s - s0), tm[key]) for s, tm in maps if key in tm]
            if len(vals) >= 2 and len(set(np.sign(v) for _, v in vals)) == 1:
                gate, near = 1.0, sorted(vals)[0][1]
            else:
                gate, near = 0.0, 0.0
            sg.append([gate, gate * near])
        X = np.hstack([X, np.array(sg)])
    return X, yk, yt, keys


def gbm(cfg, seed):
    if "C3" in cfg:
        return GradientBoostingRegressor(n_estimators=300, max_depth=3,
                                         learning_rate=0.05,
                                         random_state=seed)
    return GradientBoostingRegressor(random_state=seed)


def run_fold(train, held, labs, cache, cfg):
    uni = set()
    for m in train:
        uni |= set(labs[m]["word"])
        if m not in cache:
            cache[m] = kh.mp2_letter_score(m)
        uni |= set(cache[m][0])
    uni = sorted(uni)
    Xs, yks, yts = [], [], []
    for m in train:
        X, yk, yt, _ = build(m, labs, uni, cache, cfg, train)
        Xs.append(X); yks.append(yk); yts.append(yt)
    Xtr = np.vstack(Xs); yktr = np.hstack(yks); yttr = np.hstack(yts)
    Xh, _, _, keys = build(held, labs, uni, cache, cfg, train)
    nb = m1.build_rows(train[0], labs, uni, cache)[0].shape[1]
    ncols = Xtr.shape[1]
    nsg = 2 if "SG" in cfg else 0
    kcols = np.arange(0, ncols - nsg)            # content: physics + C2
    if "C2K" in cfg:
        tcols = np.r_[np.arange(0, nb), np.arange(ncols - nsg, ncols)]
    else:
        tcols = np.arange(0, ncols)
    kslice, tslice = kcols, tcols
    present = yktr > 0
    out = []
    for seed in DEV_SEEDS:
        mk = gbm(cfg, seed).fit(Xtr[:, kslice], yktr)
        if "C1" in cfg:
            mt = gbm(cfg, seed).fit(Xtr[present][:, tslice], yttr[present])
        else:
            mt = gbm(cfg, seed).fit(Xtr[:, tslice], yttr)
        khat = np.clip(np.round(mk.predict(Xh[:, kslice])), 0, None).astype(int)
        that = mt.predict(Xh[:, tslice])
        pw, pt = [], []
        for key, kk, tt in zip(keys, khat, that):
            pw += [key] * int(kk)
            pt += [float(tt)] * int(kk)
        out.append(kh.eval_pred(pw, pt, labs[held]))
    return out


def dev_anchor(fam, splits):
    folds = splits["split_A_interpolation"][fam]
    folds = sorted(folds, key=lambda f: m1.spacing_of(f["held_out"]))
    return folds[len(folds) // 2]


def main():
    labs = kh.load_labels()
    splits = json.load(open(os.path.join("k1_corpus", "splits.json")))
    fam = sys.argv[1]
    cfgs = sys.argv[2:] or ["v0"]
    anchor = dev_anchor(fam, splits)
    pool = anchor["train"]
    print("dev %s | anchor outer-held %s (untouched) | inner LOGO over %d"
          % (fam, anchor["held_out"], len(pool)))
    cache = {}
    for cfg in cfgs:
        R2s, F1s = [], []
        for held in pool:
            inner_train = [m for m in pool if m != held]
            res = run_fold(inner_train, held, labs, cache, cfg)
            R2s.append(np.mean([r["R2"] for r in res]))
            F1s.append(np.mean([r["F1"] for r in res]))
        print("  cfg %-10s inner thR2 %+.3f+-%.3f  F1 %.3f+-%.3f"
              % (cfg, np.mean(R2s),
                 1.96 * np.std(R2s, ddof=1) / np.sqrt(len(R2s)),
                 np.mean(F1s),
                 1.96 * np.std(F1s, ddof=1) / np.sqrt(len(F1s))))


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""k1c_model.py -- K1c step 2: a proposer over the round-one pool.

Universe: the compiler's own round-one edge pool at the post-joint
state (k1c_pool.py), which on H6 contains 88-98% of the grown multiset.
Target: how many times each pool letter is selected across all growth
rounds (its multiplicity in word[n_routed:]). Angles are not predicted
(theta = 0): grown letters are tiny corrections and Gauss-Newton prices
them for free.

Model (same family as the frozen model, gradient-boosted trees, one
shared function per letter, permutation-equivariant):
  presence  classifier  p(count > 0)
  count     regressor   log1p(count) on present rows
  scale     log-log power law of total grown letters across systems
            (trees cannot extrapolate counts; a power law can)
  counts = largest-remainder allocation of scale over letters with
           p >= p_thresh, proportional to p * expm1(count_hat).
  --mode direct  : single count regressor (ablation).

No-learning baselines at the SAME state, all with the oracle total N
(the concession the frozen protocol gave B2):
  TANGENT   N copies allocated proportional to the tangent score.
  TOPD      the top n_true_distinct letters by tangent, one copy each.
  POOL-ALL  every pool letter once (what proposing the whole pool costs).
  B2        MP2-window ranking, top n_true_distinct (the old baseline).

Feature-group ablations (--drop, repeatable):
  physics   the k1c_universe physics block (B4).
  compiler  tangent score, rank, residual mass, connectivity.
  routed    is-routed, routed occurrences, post-joint |theta|.

Splits (h8_chain is never scored unless --split C --score):
  devD (default)  train h6_chain -> test h6_ring, and the reverse.
  devA            leave-one-out within each H6 family (interpolation).
  C               train all cached H6 (+H4 if cached) -> h8_chain;
                  requires k1c_cache/h8_chain_pool.pkl (one joint solve
                  on the campaign machine, ~1 h single-threaded);
                  freezes predictions; scores ONLY with --score.

Usage:
    python k1c_model.py                    # devD, both directions
    python k1c_model.py --drop compiler    # what the compiler features buy
    python k1c_model.py --drop physics     # B4
    python k1c_model.py --scale-oracle     # shape quality alone (dev)
    python k1c_model.py --split C          # freeze H8 proposal (no score)
"""
import argparse
import importlib.util as iu
import os
import pickle
import sys

import numpy as np
from sklearn.ensemble import (GradientBoostingClassifier,
                              GradientBoostingRegressor)

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, fn):
    spec = iu.spec_from_file_location(name, os.path.join(HERE, fn))
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kh = _load("kh", "k1_harness.py")
ku = _load("ku", "k1c_universe.py")
kp = _load("kp", "k1c_pool.py")
TEST_C = "h8_chain"
GROUPS = {"physics": set(ku.PHYS_NAMES),
          "compiler": {"tangent", "log_tangent", "tangent_rel",
                       "tangent_rank", "n_top_dets", "res_mass",
                       "supp_in", "supp_out"},
          "routed": {"is_routed", "routed_n", "routed_abs_th", "routed_sat"}}


# ------------------------------------------------------------ data
def pool_of(name):
    path = os.path.join(kp.CACHE, name + "_pool.pkl")
    if not os.path.exists(path):
        raise SystemExit("no pool cache for %s -- run: python k1c_pool.py %s"
                         % (name, name))
    with open(path, "rb") as fh:
        return pickle.load(fh)


def columns(names, drop):
    banned = set()
    for g in drop:
        banned |= GROUPS[g]
    return [j for j, n in enumerate(names) if n not in banned]


def scale_table(pools, names):
    rows, tgt = [], []
    for n in names:
        F = pools[n]
        g = len(F["grown"])
        if g < 1:
            continue
        lab = kh.load_labels()[n] if False else None
        rows.append(scale_row(F))
        tgt.append(np.log(g))
    return np.array(rows), np.array(tgt)


def scale_row(F):
    sysf = F["X"][0, :len(ku.SYS_NAMES)]
    d = dict(zip(ku.SYS_NAMES, sysf))
    return np.array([1.0, d["log_support"], np.log(max(F["rn_joint"], 1e-12)),
                     np.log(max(1, len(F["keys"])))])


# ------------------------------------------------------------ model
def allocate(scores, total, keep):
    out = np.zeros(len(scores), int)
    idx = np.where(keep & (scores > 0))[0]
    if total < 1 or len(idx) == 0:
        return out
    s = scores[idx] / scores[idx].sum() * total
    fl = np.floor(s).astype(int)
    rem = int(total - fl.sum())
    fl[np.argsort(-(s - fl))[:max(0, rem)]] += 1
    out[idx] = fl
    return out


class Proposer:
    def __init__(self, mode, seed, trees, pu, cap=64):
        self.mode, self.seed, self.trees, self.pu, self.cap = \
            mode, seed, trees, pu, cap

    def fit(self, X, y):
        w = np.where(y > 0, 1.0, self.pu)
        if self.mode == "direct":
            self.reg = GradientBoostingRegressor(
                n_estimators=self.trees, max_depth=3, learning_rate=0.05,
                subsample=0.8, random_state=self.seed).fit(X, y, sample_weight=w)
            return self
        self.clf = GradientBoostingClassifier(
            n_estimators=self.trees, max_depth=3, learning_rate=0.05,
            subsample=0.8, random_state=self.seed).fit(
                X, (y > 0).astype(int), sample_weight=w)
        pres = y > 0
        self.reg = GradientBoostingRegressor(
            n_estimators=self.trees, max_depth=3, learning_rate=0.05,
            subsample=0.8, random_state=self.seed).fit(X[pres], np.log1p(y[pres]))
        return self

    def predict(self, X, scale, p_thresh):
        if self.mode == "direct":
            return np.clip(np.round(self.reg.predict(X)), 0, self.cap).astype(int)
        p = self.clf.predict_proba(X)[:, 1]
        c = np.expm1(self.reg.predict(X)).clip(0, self.cap)
        keep = p >= p_thresh
        if not keep.any():
            keep = np.zeros(len(p), bool)
            keep[np.argsort(-p)[:max(1, int(scale / max(1.0, c.mean())))]] = 1
        return allocate(p * c, int(round(scale)), keep).clip(0, self.cap)


def words_from(keys, counts):
    return [k for k, c in zip(keys, counts) for _ in range(int(c))]


def baselines(F, n_total, n_distinct):
    names, X, keys = F["names"], F["X"], F["keys"]
    ts = X[:, names.index("tangent")]
    tang = words_from(keys, allocate(ts, n_total, np.ones(len(ts), bool)))
    topd = [keys[i] for i in np.argsort(-ts)[:n_distinct]]
    pool_all = list(keys)
    sc, _ = kh.mp2_letter_score(F["name"])
    b2 = sorted(sc, key=lambda k: -sc[k])[:n_distinct]
    return {"TANGENT": tang, "TOPD": topd, "POOL-ALL": pool_all, "B2": b2}


def _write_proposals(d, t, F, frozen, scale_hat, seeds):
    os.makedirs(d, exist_ok=True)
    ts = F["X"][:, F["names"].index("tangent")]
    props = {"tangent": words_from(F["keys"], allocate(
        ts, int(round(scale_hat)), np.ones(len(ts), bool))),
             "poolall": list(F["keys"])}
    for s in seeds:
        props["model_s%d" % s] = frozen[s][t]
    for name, w in props.items():
        with open(os.path.join(d, "%s_%s.pkl" % (t, name)), "wb") as fh:
            pickle.dump({"config": "K1c-" + name, "insert": "post-joint",
                         "scale_hat": scale_hat, "theta": "zero",
                         "preds": {0: (list(w), [0.0] * len(w))}}, fh)


def ci95(x):
    x = np.asarray(x, float)
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else 0.0


# ------------------------------------------------------------ runs
def run(train, tests, pools, a, score=True):
    cols = None
    Xs, ys = [], []
    for n in train:
        F = pools[n]
        if cols is None:
            cols = columns(F["names"], a.drop)
        Xs.append(F["X"][:, cols]); ys.append(F["y"])
    Xtr, ytr = np.vstack(Xs), np.hstack(ys)
    srows, stgt = scale_table(pools, train)
    coef, *_ = np.linalg.lstsq(srows, stgt, rcond=None)
    print("train %d systems | %d rows x %d features | present %.1f%% | "
          "drop %s | mode %s | pu %.2f | scale fit on %d systems"
          % (len(train), *Xtr.shape, 100.0 * (ytr > 0).mean(),
             ",".join(a.drop) or "none", a.mode, a.pu_weight, len(stgt)))
    models = {s: Proposer(a.mode, s, a.trees, a.pu_weight).fit(Xtr, ytr)
              for s in a.seeds}
    results, frozen = [], {}
    for t in tests:
        F = pools[t]
        X = F["X"][:, cols]
        true = F["grown"]
        n_true, n_d = len(true), len(set(true))
        scale_hat = float(np.exp(scale_row(F) @ coef))
        scale_use = float(n_true) if a.scale_oracle else scale_hat
        per_seed = {}
        for s, m in models.items():
            pw = words_from(F["keys"], m.predict(X, scale_use, a.p_thresh))
            frozen.setdefault(s, {})[t] = pw
            if score:
                sc = kh.content_scores(pw, true)
                sc["n_pred"], sc["n_distinct"] = len(pw), len(set(pw))
                per_seed[s] = sc
        if a.write_proposals:
            _write_proposals(a.write_proposals, t, F, frozen, scale_hat, a.seeds)
        if not score:
            continue
        base = {k: kh.content_scores(w, true)
                for k, w in baselines(F, n_true, n_d).items()}
        base["POOL-ALL"]["n"] = len(F["keys"])
        results.append({"test": t, "n_true": n_true, "n_true_d": n_d,
                        "pool": len(F["keys"]), "in_pool": F["in_pool_mass"],
                        "scale_hat": scale_hat, "seeds": per_seed,
                        "base": base})
    return results, frozen


def summarize(results, seeds, label):
    if not results:
        return
    fam = lambda r: r["test"].rsplit("_", 1)[0]
    fams = sorted(set(fam(r) for r in results))
    print("\n[%s]" % label)
    print("%-13s %3s | %-22s | %-7s %-7s %-7s %-7s | %-7s | %-6s | %s"
          % ("family", "n", "MODEL F1 (+-CI)  P  R", "TANGENT", "TOPD",
             "POOL", "B2", "in-pool", "pool", "scale pred/true"))
    allF, allT = [], []
    for f in fams:
        rs = [r for r in results if fam(r) == f]
        F = np.array([np.mean([r["seeds"][s]["F1"] for s in seeds]) for r in rs])
        P = np.array([np.mean([r["seeds"][s]["P"] for s in seeds]) for r in rs])
        R = np.array([np.mean([r["seeds"][s]["R"] for s in seeds]) for r in rs])
        B = {k: np.array([r["base"][k]["F1"] for r in rs])
             for k in ("TANGENT", "TOPD", "POOL-ALL", "B2")}
        inp = np.array([r["in_pool"] for r in rs])
        pool = np.array([r["pool"] for r in rs])
        ratio = np.array([r["scale_hat"] / max(1, r["n_true"]) for r in rs])
        print("%-13s %3d | %.3f+-%.3f %.3f %.3f | %.3f   %.3f   %.3f   %.3f   | %.3f   | %4.0f   | %.2f (x%.1f..%.1f)"
              % (f, len(rs), F.mean(), ci95(F), P.mean(), R.mean(),
                 B["TANGENT"].mean(), B["TOPD"].mean(), B["POOL-ALL"].mean(),
                 B["B2"].mean(), inp.mean(), pool.mean(),
                 float(np.exp(np.mean(np.log(ratio)))), ratio.min(),
                 ratio.max()))
        allF += list(F); allT += list(B["TANGENT"])
    allF, allT = np.array(allF), np.array(allT)
    d = allF - allT
    print("%-13s %3d | F1 %.3f+-%.3f | model - TANGENT %+.3f+-%.3f"
          % ("ALL", len(allF), allF.mean(), ci95(allF), d.mean(), ci95(d)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["devD", "devA", "C"], default="devD")
    ap.add_argument("--mode", choices=["shape_scale", "direct"],
                    default="shape_scale")
    ap.add_argument("--drop", action="append", default=[],
                    choices=list(GROUPS))
    ap.add_argument("--pu-weight", type=float, default=1.0)
    ap.add_argument("--p-thresh", type=float, default=0.5)
    ap.add_argument("--trees", type=int, default=200)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--scale-oracle", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--write-proposals", default=None, metavar="DIR",
                    help="dev splits: write harness-format proposal files "
                         "for model seeds, TANGENT (predicted scale) and "
                         "POOL-ALL, per test system, into DIR")
    a = ap.parse_args()
    cached = sorted(f[:-9] for f in os.listdir(kp.CACHE)
                    if f.endswith("_pool.pkl")) if os.path.isdir(kp.CACHE) else []
    h6c = [n for n in cached if n.startswith("k1_h6_chain")]
    h6r = [n for n in cached if n.startswith("k1_h6_ring")]
    pools = {n: pool_of(n) for n in cached if n != TEST_C}
    if a.split == "devD":
        print("K1c devD | cached H6: %d chain, %d ring | h8_chain untouched"
              % (len(h6c), len(h6r)))
        r1, _ = run(h6c, h6r, pools, a)
        summarize(r1, a.seeds, "train h6_chain -> test h6_ring")
        r2, _ = run(h6r, h6c, pools, a)
        summarize(r2, a.seeds, "train h6_ring -> test h6_chain")
        return
    if a.split == "devA":
        for famname, fam in (("h6_chain", h6c), ("h6_ring", h6r)):
            res = []
            for held in fam:
                r, _ = run([n for n in fam if n != held], [held], pools, a)
                res += r
            summarize(res, a.seeds, "leave-one-out within " + famname)
        return
    if a.scale_oracle:
        raise SystemExit("--scale-oracle reads the test label; refused on C")
    train = [n for n in cached if n != TEST_C]
    pools[TEST_C] = pool_of(TEST_C)
    tag = a.tag or ("pool_%s%s%s" % (a.mode, "".join("_no" + g for g in a.drop),
                                     "_pu%.2f" % a.pu_weight if a.pu_weight != 1
                                     else ""))
    out = os.path.join(HERE, "k1_corpus", "predictions_k1c_h8_%s.pkl" % tag)
    print("K1c Split C | train %d cached systems -> %s | freeze -> %s"
          % (len(train), TEST_C, out))
    results, frozen = run(train, [TEST_C], pools, a, score=a.score)
    preds = {s: (frozen[s][TEST_C], [0.0] * len(frozen[s][TEST_C]))
             for s in a.seeds}
    with open(out, "wb") as fh:
        pickle.dump({"config": "K1c-" + tag, "train_n": len(train),
                     "universe_n": len(pools[TEST_C]["keys"]),
                     "insertion": "post-joint", "b2_sign": 1.0,
                     "theta": "zero", "preds": preds}, fh)
    for s in a.seeds:
        print("  seed %d: proposed %d letters (%d distinct) from a pool of %d"
              % (s, len(preds[s][0]), len(set(preds[s][0])),
                 len(pools[TEST_C]["keys"])))
    print("predictions FROZEN -> %s" % out)
    if a.score:
        print("\n*** SCORING AGAINST h8_chain spends a touch of the Split-C "
              "test system ***")
        summarize(results, a.seeds, "Split C")
    else:
        print("NOT SCORED (h8_chain untouched).")


if __name__ == "__main__":
    main()

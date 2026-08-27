#!/usr/bin/env python
"""k1_harness.py -- metrics + baselines for the K1 test (v1: B0, B1).

Scoring conventions (frozen with the corpus):
  - content: multiset precision/recall/F1 and multiset Jaccard over
    letter counts.
  - theta: letters are matched by label; each side's theta per letter
    is the MEAN over its occurrences; MAE / R^2 / sign accuracy over
    letters present on both sides.
  - order: Kendall tau over first-occurrence positions of shared
    letters.
B2 (physics: MP2-ranked letters + perturbative theta) lands in v2.
"""
import glob
import json
import os
import pickle

import numpy as np


def load_labels():
    labs = {}
    for p in glob.glob(os.path.join("k1_corpus", "labels", "*.pkl")) + \
             glob.glob(os.path.join("k1_corpus", "labels_tierB", "*.pkl")):
        with open(p, "rb") as fh:
            d = pickle.load(fh)
        labs[d["name"]] = d
    return labs


def counts(word):
    c = {}
    for x in word:
        c[x] = c.get(x, 0) + 1
    return c


def content_scores(pred_word, true_word):
    cp, ct = counts(pred_word), counts(true_word)
    inter = sum(min(cp.get(k, 0), ct.get(k, 0)) for k in set(cp) | set(ct))
    union = sum(max(cp.get(k, 0), ct.get(k, 0)) for k in set(cp) | set(ct))
    p = inter / max(1, sum(cp.values()))
    r = inter / max(1, sum(ct.values()))
    f1 = 0.0 if p + r == 0 else 2 * p * r / (p + r)
    return {"msetJ": inter / max(1, union), "P": p, "R": r, "F1": f1}


def theta_map(word, th):
    m = {}
    for x, t in zip(word, th):
        m.setdefault(x, []).append(t)
    return {k: float(np.mean(v)) for k, v in m.items()}


def theta_scores(pw, pt, tw, tt):
    a, b = theta_map(pw, pt), theta_map(tw, tt)
    keys = [k for k in a if k in b]
    if len(keys) < 3:
        return {"n": len(keys), "MAE": float("nan"), "R2": float("nan"),
                "sign": float("nan")}
    xa = np.array([a[k] for k in keys]); xb = np.array([b[k] for k in keys])
    ss = float(np.sum((xb - xb.mean()) ** 2))
    r2 = 1.0 - float(np.sum((xa - xb) ** 2)) / ss if ss > 0 else float("nan")
    return {"n": len(keys), "MAE": float(np.mean(np.abs(xa - xb))),
            "R2": r2, "sign": float(np.mean(np.sign(xa) == np.sign(xb)))}


def kendall_first(pw, tw):
    fa, fb = {}, {}
    for i, x in enumerate(pw):
        fa.setdefault(x, i)
    for i, x in enumerate(tw):
        fb.setdefault(x, i)
    keys = [k for k in fa if k in fb]
    n = len(keys)
    if n < 3:
        return float("nan"), n
    ra = np.argsort(np.argsort([fa[k] for k in keys]))
    rb = np.argsort(np.argsort([fb[k] for k in keys]))
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (ra[i] - ra[j]) * (rb[i] - rb[j])
            conc += s > 0; disc += s < 0
    return float((conc - disc) / (0.5 * n * (n - 1))), n


def spacing_of(name):
    tail = name.split("_root")[0].split("_")[-1]
    if tail == "sto3g":
        return 30
    try:
        return int(tail)
    except ValueError:
        return 0


def b1_copy(train_names, held, labs):
    # folds are family-scoped by construction: the train list IS the pool
    src = min(train_names,
              key=lambda n: abs(spacing_of(n) - spacing_of(held)))
    return labs[src]["word"], labs[src]["th"], src


def b0_freq(train_names, labs):
    agg, n = {}, len(train_names)
    for m in train_names:
        for x, t in zip(labs[m]["word"], labs[m]["th"]):
            agg.setdefault(x, []).append(t)
    word, th = [], []
    for x, ts in agg.items():
        k = int(round(len(ts) / n))
        word += [x] * k
        th += [float(np.mean(ts))] * k
    return word, th


def eval_pred(pw, pt, lab):
    out = content_scores(pw, lab["word"])
    out.update(theta_scores(pw, pt, lab["word"], lab["th"]))
    tau, ntau = kendall_first(pw, lab["word"])
    out["tau"], out["n_tau"] = tau, ntau
    return out


def fmt(name, s):
    return ("%-22s msetJ %.3f F1 %.3f | th n %3d MAE %.4f R2 %+.3f "
            "sign %.2f | tau %+.2f (%d)"
            % (name, s["msetJ"], s["F1"], s["n"], s["MAE"], s["R2"],
               s["sign"], s["tau"], s["n_tau"]))


def main():
    labs = load_labels()
    splits = json.load(open(os.path.join("k1_corpus", "splits.json")))
    print("harness smoke test -- %d labels loaded" % len(labs))
    for fam in ("h6_chain", "h6_ring"):
        fold = [f for f in splits["split_A_interpolation"][fam]
                if f["held_out"].endswith("_19")][0]
        lab = labs[fold["held_out"]]
        for bname, (pw, pt) in (
                ("B1 copy", b1_copy(fold["train"], fold["held_out"], labs)[:2]),
                ("B0 freq", b0_freq(fold["train"], labs))):
            print(fmt("%s @ %s" % (bname, fold["held_out"]),
                      eval_pred(pw, pt, lab)))
    ch, rg = labs["k1_h6_chain_19"], labs["k1_h6_ring_19"]
    print(fmt("D chain->ring @19 copy", eval_pred(ch["word"], ch["th"], rg)))


if __name__ == "__main__":
    main()


# ---------------- B2: physics baseline (MP2-ranked, oracle length) ------
NCORE = {"c2": 2, "n2": 2, "h2o_15re": 1, "h2o_20re": 1, "h2o_sto3g_fc": 1}


def _ncore(name):
    for k, v in NCORE.items():
        if name.startswith(k):
            return v
    return 0


def _dumpstem(name):
    s = name.split("_root")[0]
    for suf in ("_fc", "_full"):
        if s.endswith(suf):
            s = s[: -len(suf)]
    return s


def _dumppath(name):
    s = _dumpstem(name)
    for p in (s + ".npz", os.path.join("k1_corpus", s + ".npz")):
        if os.path.exists(p):
            return p
    raise FileNotFoundError(s)


def _labpath(name):
    for sub in ("labels", "labels_tierB"):
        p = os.path.join("k1_corpus", sub, name + ".pkl")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def mp2_letter_score(name):
    """Score every rank-1/2 pivot-referenced letter from MP2 amplitudes.
    eri is chemist (pq|rs). Orbital energies are COMPUTED from the dump
    (canonical Fock diagonal: eps_p = h_pp + sum_j 2(pp|jj)-(pj|jp)),
    so no stored key is trusted. Rank-2 score |t2| (antisymmetrized for
    same spin); rank-1 proxy = 0.1 * sum |t2| contraction (true MP2
    singles vanish for canonical HF). theta seed = arctan(t2). Letters
    outside the occ->virt window score 0 and are never nominated.
    """
    lab = pickle.load(open(_labpath(name), "rb"))
    d = np.load(_dumppath(name), allow_pickle=True)
    eri = np.asarray(d["eri_mo"], float)
    h = np.asarray(d["h_mo"], float)
    nmo_d = h.shape[0]
    nc = _ncore(name)
    occ_sp = sorted(q for q in range(2 * nmo_d) if (lab["pivot"] >> q) & 1)
    ndocc_d = len(occ_sp) // 2 + nc
    docc = range(ndocc_d)
    eps = np.array([h[p, p] + sum(2 * eri[p, p, j, j] - eri[p, j, j, p]
                                  for j in docc) for p in range(nmo_d)])
    nact = nmo_d - nc
    virt_sp = [q for q in range(2 * nact) if q not in occ_sp]
    sp = lambda q: (q // 2 + nc, q % 2)
    scores, thetas = {}, {}
    for i in occ_sp:
        I, si = sp(i)
        for a in virt_sp:
            A, sa = sp(a)
            if si != sa:
                continue
            prox = 0.0
            for j in occ_sp:
                J, sj = sp(j)
                for b in virt_sp:
                    B, sb = sp(b)
                    if sj != sb:
                        continue
                    den = eps[I] + eps[J] - eps[A] - eps[B]
                    if abs(den) < 1e-9:
                        continue
                    t2 = eri[I, A, J, B] / den
                    if si == sj:
                        t2 -= eri[I, B, J, A] / den
                    prox += abs(t2)
            scores[((i,), (a,))] = 0.1 * prox
            thetas[((i,), (a,))] = 0.0
    for i in occ_sp:
        I, si = sp(i)
        for j in occ_sp:
            if j <= i:
                continue
            J, sj = sp(j)
            for a in virt_sp:
                A, sa = sp(a)
                for b in virt_sp:
                    if b <= a:
                        continue
                    B, sb = sp(b)
                    if sorted((si, sj)) != sorted((sa, sb)):
                        continue
                    den = eps[I] + eps[J] - eps[A] - eps[B]
                    if abs(den) < 1e-9:
                        continue
                    if si == sj:
                        t2 = (eri[I, A, J, B] - eri[I, B, J, A]) / den
                    elif (si, sj) == (sa, sb):
                        t2 = eri[I, A, J, B] / den
                    else:
                        t2 = -eri[I, B, J, A] / den
                    scores[((i, j), (a, b))] = abs(t2)
                    thetas[((i, j), (a, b))] = float(np.arctan(t2))
    return scores, thetas


def b2_physics(name, labs):
    """Oracle-length concession: B2 receives the true chain length."""
    N = len(labs[name]["word"])
    scores, thetas = mp2_letter_score(name)
    ranked = sorted(scores, key=lambda k: -scores[k])[:N]
    return ranked, [thetas[k] for k in ranked]

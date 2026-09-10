#!/usr/bin/env python
"""k1c_canon.py -- exact canonicalization and multi-way comparison of
certified chains of the same state.

Two factors exp(t1 k1) exp(t2 k2) commute exactly when their spin-orbital
index sets are disjoint. That gives an exact, learning-free gauge fix for
the commuting part of the ordering convention: every chain has a unique
lexicographic normal form under reordering of commuting neighbors, and
two chains that differ only by such reorderings have the same normal
form. Whatever disagreement survives canonicalization is the real gauge
(different content, or non-commuting reorderings with compensating
changes).

For one state this script gathers every certified chain available --
the campaign label plus any harness chain files -- and reports:

  per member : length, grown letters, circuit depth (raw and canonical;
               depth = number of layers when commuting factors run in
               parallel, the resource-estimation by-product), max |theta|
  content    : pairwise multiset precision / recall / F1 / Jaccard on the
               grown portion (unchanged by canonicalization: reordering
               does not change content)
  order      : agreement of the relative order of shared letters, raw
               versus canonical (Spearman on normalized first positions)
  angles     : agreement of total |theta| per shared letter (Pearson)
  core       : the multiset intersection across all members and the
               fraction of each member's grown mass inside it
  verify     : with --verify, applies raw and canonical chains to the
               reference and checks (a) canonical == raw to machine
               precision (the commutation claim) and (b) raw == target

Chain sources: the label (campaign) and every <name>_*_chain.npz in the
given directories (default: this checkout's k1b/, where the frozen
harness writes race chains). --extra-dir may point at the campaign
checkout's k1b/ read-only.

Usage:
    python k1c_canon.py k1_h6_ring_19
    python k1c_canon.py k1_h6_ring_19 --verify
    python k1c_canon.py --raced                       # the 12 raced H6 systems
    python k1c_canon.py h8_chain --extra-dir C:\\...\\tucc-chain-compile\\k1b
Results: printed, and saved to k1c_runs/canon_<name>.json
"""
import argparse
import glob
import importlib.util as iu
import json
import os
import pickle
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "src"))


def _load(name, fn):
    spec = iu.spec_from_file_location(name, os.path.join(HERE, fn))
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kh = _load("kh", "k1_harness.py")
RUNS = os.path.join(HERE, "k1c_runs")
RACED = ["k1_h6_chain_14", "k1_h6_chain_19", "k1_h6_chain_22",
         "k1_h6_chain_26", "k1_h6_chain_30", "k1_h6_chain_34",
         "k1_h6_ring_14", "k1_h6_ring_19", "k1_h6_ring_22",
         "k1_h6_ring_26", "k1_h6_ring_30", "k1_h6_ring_34"]


# ------------------------------------------------------------ loading
def load_label_chain(name):
    lab = pickle.load(open(kh._labpath(name), "rb"))
    word = [tuple(map(tuple, x)) for x in lab["word"]]
    th = [float(t) for t in lab["th"]]
    return word, th, len(lab["support"]) - 1


def load_npz_chain(path):
    d = np.load(path, allow_pickle=True)
    word = [(tuple(int(q) for q in h), tuple(int(q) for q in p))
            for h, p in zip(d["subs_h"], d["subs_p"])]
    th = [float(t) for t in d["th"]]
    return word, th


def gather(name, dirs):
    word, th, n_routed = load_label_chain(name)
    members = {"campaign": (word, th)}
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for path in sorted(glob.glob(os.path.join(d, name + "_*_chain.npz"))):
            tag = os.path.basename(path)[len(name) + 1:-len("_chain.npz")]
            members[tag] = load_npz_chain(path)
    return members, n_routed


# ------------------------------------------------------------ algebra
def mask_of(key):
    hh, pp = key
    m = 0
    for q in hh:
        m |= 1 << q
    for q in pp:
        m |= 1 << q
    return m


def canonicalize(word, th):
    """Lexicographic normal form of the chain under reordering of
    commuting (index-disjoint) neighbors. Insert each letter after the
    last letter it does not commute with, then slide right past commuting
    letters with smaller keys. The result has no adjacent commuting pair
    out of key order, which characterizes the normal form."""
    out_w, out_t, out_m = [], [], []
    for x, t in zip(word, th):
        mx = mask_of(x)
        i = len(out_w) - 1
        while i >= 0 and (out_m[i] & mx) == 0:
            i -= 1
        p = i + 1
        n = len(out_w)
        while p < n and out_w[p] < x:
            p += 1
        out_w.insert(p, x)
        out_t.insert(p, t)
        out_m.insert(p, mx)
    return out_w, out_t


def is_normal(word):
    """Check: no adjacent commuting pair with the left key greater."""
    for a, b in zip(word, word[1:]):
        if (mask_of(a) & mask_of(b)) == 0 and a > b:
            return False
    return True


def depth(word):
    """Layers when commuting factors run in parallel: each factor sits one
    layer after the latest earlier factor sharing an index with it."""
    last = {}
    d = 0
    for hh, pp in word:
        S = hh + pp
        layer = 1 + max((last.get(q, 0) for q in S), default=0)
        for q in S:
            last[q] = layer
        if layer > d:
            d = layer
    return d


# ------------------------------------------------------------ metrics
def first_positions(word):
    pos = {}
    for i, k in enumerate(word):
        if k not in pos:
            pos[k] = i / max(1, len(word) - 1)
    return pos


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return float("nan")
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def angle_totals(word, th):
    tot = {}
    for k, t in zip(word, th):
        tot[k] = tot.get(k, 0.0) + abs(t)
    return tot


def compare_pair(A, B):
    """A, B: dicts with keys word_raw, th_raw, word_can, th_can (portion)."""
    out = {}
    sc = kh.content_scores(A["word_raw"], B["word_raw"])
    out.update({"P": sc["P"], "R": sc["R"], "F1": sc["F1"],
                "msetJ": sc["msetJ"]})
    shared = set(A["word_raw"]) & set(B["word_raw"])
    out["n_shared_distinct"] = len(shared)
    if shared:
        pa, pb = first_positions(A["word_raw"]), first_positions(B["word_raw"])
        ca, cb = first_positions(A["word_can"]), first_positions(B["word_can"])
        keys = sorted(shared)
        out["order_raw"] = spearman([pa[k] for k in keys], [pb[k] for k in keys])
        out["order_can"] = spearman([ca[k] for k in keys], [cb[k] for k in keys])
        ta, tb = angle_totals(A["word_raw"], A["th_raw"]), \
            angle_totals(B["word_raw"], B["th_raw"])
        out["angle_pearson"] = pearson([ta[k] for k in keys],
                                       [tb[k] for k in keys])
    else:
        out["order_raw"] = out["order_can"] = out["angle_pearson"] = float("nan")
    return out


# ------------------------------------------------------------ verification
def apply_chain(word, th, basis, pivot):
    from chaincompile.dets import Substitution
    index = {int(m): i for i, m in enumerate(basis.masks)}
    psi = np.zeros(basis.dim)
    psi[index[int(pivot)]] = 1.0
    for (hh, pp), t in zip(word, th):
        ii, jj, ss = basis.block_arrays(Substitution(tuple(hh), tuple(pp)))
        if len(ii) == 0:
            continue
        c, s = np.cos(t), np.sin(t)
        a = psi[ii].copy()
        b = psi[jj].copy()
        psi[ii] = c * a - ss * s * b
        psi[jj] = c * b + ss * s * a
    return psi


def verify(name, members_full):
    p1 = _load("p1", "k1c_phase1.py")
    ct, pivot, basis, _, src = p1.load_target(name)
    rows = {}
    for tag, M in members_full.items():
        raw = apply_chain(M["word_raw"], M["th_raw"], basis, pivot)
        can = apply_chain(M["word_can"], M["th_can"], basis, pivot)
        d_rc = float(np.linalg.norm(can - raw))
        d_rt = float(min(np.linalg.norm(raw - ct), np.linalg.norm(raw + ct)))
        rows[tag] = {"canon_vs_raw": d_rc, "raw_vs_target": d_rt}
    return rows, src


# ------------------------------------------------------------ driver
def analyze(name, dirs, portion, do_verify):
    members, n_routed = gather(name, dirs)
    if len(members) < 2:
        print("%s: only the campaign chain found; nothing to compare "
              "(looked in %s)" % (name, ", ".join(d for d in dirs if d)))
        return None
    ref_prefix = members["campaign"][0][:n_routed]
    full, port = {}, {}
    print("\n=== %s: %d members, routed prefix %d ===" % (name, len(members),
                                                         n_routed))
    print("%-24s %6s %6s %7s %7s %8s %6s" % ("member", "len", "grown",
                                            "depth", "d_can", "max|th|",
                                            "prefix"))
    for tag, (word, th) in members.items():
        same_prefix = (word[:n_routed] == ref_prefix)
        wc, tc = canonicalize(word, th)
        assert is_normal(wc), "normal-form check failed for %s" % tag
        assert Counter(wc) == Counter(word), "content changed for %s" % tag
        full[tag] = {"word_raw": word, "th_raw": th, "word_can": wc,
                     "th_can": tc}
        if portion == "grown" and same_prefix:
            # canonical form of the grown portion alone, for order metrics
            gw, gt = canonicalize(word[n_routed:], th[n_routed:])
            port[tag] = {"word_raw": word[n_routed:], "th_raw": th[n_routed:],
                         "word_can": gw, "th_can": gt}
        else:
            port[tag] = full[tag]
        print("%-24s %6d %6d %7d %7d %8.3f %6s"
              % (tag, len(word), len(word) - n_routed, depth(word), depth(wc),
                 max(abs(t) for t in th) if th else 0.0,
                 "same" if same_prefix else "DIFF"))
    tags = list(members)
    pairs = {}
    print("\npairwise on the %s portion (F1 | order raw -> canonical | angle r):"
          % portion)
    for i, a in enumerate(tags):
        for b in tags[i + 1:]:
            r = compare_pair(port[a], port[b])
            pairs["%s|%s" % (a, b)] = r
            print("  %-22s %-22s F1 %.3f | order %5.2f -> %5.2f | angle %5.2f"
                  % (a, b, r["F1"], r["order_raw"], r["order_can"],
                     r["angle_pearson"]))
    cnts = [Counter(port[t]["word_raw"]) for t in tags]
    core = cnts[0]
    for c in cnts[1:]:
        core = core & c
    union = Counter()
    for c in cnts:
        union = union | c
    core_mass = sum(core.values())
    print("\ninvariant core across %d members: %d letters (%d distinct); "
          "union %d letters (%d distinct)"
          % (len(tags), core_mass, len(core), sum(union.values()), len(union)))
    frac = {}
    for t, c in zip(tags, cnts):
        m = sum(c.values())
        frac[t] = core_mass / m if m else float("nan")
        print("  %-22s grown mass in core %.3f" % (t, frac[t]))
    vrows, vsrc = ({}, None)
    if do_verify:
        vrows, vsrc = verify(name, full)
        print("\nverification (target from %s): canonical vs raw | raw vs "
              "target (|r| ~ 1e-6 at the gate):" % vsrc)
        for t, r in vrows.items():
            print("  %-22s %.2e | %.2e" % (t, r["canon_vs_raw"],
                                         r["raw_vs_target"]))
        print("  (canonical == raw to ~1e-14 confirms commutation; raw far "
              "from target means the applier's angle convention differs "
              "from the compiler's, which does not affect the first check)")
    os.makedirs(RUNS, exist_ok=True)
    out = {"name": name, "n_routed": n_routed, "portion": portion,
           "members": {t: {"len": len(members[t][0]),
                           "grown": len(members[t][0]) - n_routed,
                           "depth": depth(members[t][0]),
                           "depth_canonical": depth(full[t]["word_can"]),
                           "grown_mass_in_core": frac[t]} for t in tags},
           "pairs": pairs, "core_mass": core_mass, "core_distinct": len(core),
           "union_mass": sum(union.values()), "union_distinct": len(union),
           "verify": vrows}
    with open(os.path.join(RUNS, "canon_%s.json" % name), "w") as fh:
        json.dump(out, fh, indent=1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--raced", action="store_true",
                    help="analyze the twelve raced H6 systems")
    ap.add_argument("--dirs", nargs="*", default=[os.path.join(HERE, "k1b")],
                    help="directories holding <name>_*_chain.npz")
    ap.add_argument("--extra-dir", default=None,
                    help="one more directory, e.g. the campaign checkout's k1b")
    ap.add_argument("--portion", choices=["grown", "all"], default="grown")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    names = list(a.names) + (RACED if a.raced else [])
    if not names:
        raise SystemExit("give system names or --raced")
    dirs = list(a.dirs) + ([a.extra_dir] if a.extra_dir else [])
    summary = []
    for n in names:
        r = analyze(n, dirs, a.portion, a.verify)
        if r:
            f1s = [p["F1"] for p in r["pairs"].values()]
            oc = [p["order_can"] for p in r["pairs"].values()
                  if p["order_can"] == p["order_can"]]
            orw = [p["order_raw"] for p in r["pairs"].values()
                   if p["order_raw"] == p["order_raw"]]
            summary.append((n, len(r["members"]), float(np.mean(f1s)),
                            float(np.mean(orw)) if orw else float("nan"),
                            float(np.mean(oc)) if oc else float("nan"),
                            r["core_mass"], r["union_mass"]))
    if len(summary) > 1:
        print("\n%-16s %3s %7s %10s %10s %6s %6s" % ("system", "n", "meanF1",
                                                    "order_raw", "order_can",
                                                    "core", "union"))
        for s in summary:
            print("%-16s %3d %7.3f %10.2f %10.2f %6d %6d" % s)


if __name__ == "__main__":
    main()

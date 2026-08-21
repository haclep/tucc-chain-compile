#!/usr/bin/env python
"""lih_smoothness.py -- is the map geometry -> chain smooth? (item 4)

Recompiles the five committed LiH scan chains (R = 3.0, 4.5, 6.0,
7.5, 9.0 bohr; sd_routed; dim 225) from their dumps, CALIBRATES each
against the committed report numbers, then measures how much of the
chain survives from one geometry to the next:

  [2] support-set identity (is the pinned 69 the SAME 69?)
  [3] letter overlap (set and multiset Jaccard), ordered-sequence
      similarity (LCS / max len), positional agreement
  [4] theta continuity on letters shared by adjacent chains
  [5] the backbone: letters present at all five geometries, with
      their theta trajectories across R

This is the first leg of the decisive experiment (strategy memo
sec 11, kill criterion K1): if adjacent chains barely resemble each
other, no model can learn the map. Read-only: writes nothing.
"""
import os
import sys

import numpy as np

from chaincompile.compile import compile_chain
from chaincompile.molecular import (build_h_sector, load_integral_dump,
                                    freeze_core, dominant_block_projection)
from chaincompile.sector import SectorBasis
from chaincompile import normalorder as NO

SCAN = [
    # stem, R/bohr, committed: len, ranks, max|theta|, monomials
    ("lih_sto3g", 3.0, 95,  {2: 81, 1: 14}, 0.874574, 69),
    ("lih_45",    4.5, 85,  {2: 75, 1: 10}, 0.596952, 69),
    ("lih_60",    6.0, 106, {2: 93, 1: 13}, 1.009879, 69),
    ("lih_75",    7.5, 95,  {2: 83, 1: 12}, 1.331698, 69),
    ("lih_90",    9.0, 127, {2: 91, 1: 36}, 1.531031, 69),
]


def fail(msg):
    print("STOP:", msg)
    sys.exit(1)


def compile_one(stem):
    h_mo, eri_mo, e_shift, e_scf, na, nb, meta = load_integral_dump(
        stem + ".npz")
    h_mo, eri_mo, e_core = freeze_core(h_mo, eri_mo, 0)
    nmo = h_mo.shape[0]
    sb = SectorBasis(nmo, na, nb)
    H = build_h_sector(h_mo, eri_mo, sb)
    w, Vv = np.linalg.eigh(H)
    v0 = Vv[:, 0]
    v0, seen2, mixed = dominant_block_projection(v0, H)
    floor = np.sqrt(1e-12) / sb.dim
    sup_mask = np.abs(v0) > floor
    res = compile_chain(v0, sb, mode="sd_routed")
    word = [s for s, _ in res.selected()]
    th = [float(t) for _, t in res.selected()]
    occ = frozenset(p for p in range(2 * nmo) if (res.pivot_mask >> p) & 1)
    U, sizes = NO.compose_numeric(word, th, occ)
    c0, amps = NO.numeric_ref_amplitudes(U, occ)
    supp = frozenset(int(m) for m, keep in
                     zip(sb.masks, sup_mask) if keep)
    return {"word": word, "th": th, "resid": float(res.final_residual),
            "namps": len(amps) + 1, "support": supp,
            "e_fci": float(w[0] + e_shift), "mixed": mixed}


def label(sub):
    return (sub.holes, sub.parts)


def lcs_len(a, b):
    n, m = len(a), len(b)
    prev = [0] * (m + 1)
    for i in range(1, n + 1):
        cur = [0] * (m + 1)
        ai = a[i - 1]
        for j in range(1, m + 1):
            cur[j] = (prev[j - 1] + 1 if ai == b[j - 1]
                      else max(prev[j], cur[j - 1]))
        prev = cur
    return prev[m]


def multiset(seq):
    d = {}
    for x in seq:
        d[x] = d.get(x, 0) + 1
    return d


def mjaccard(a, b):
    da, db = multiset(a), multiset(b)
    inter = sum(min(da.get(k, 0), db.get(k, 0)) for k in set(da) | set(db))
    union = sum(max(da.get(k, 0), db.get(k, 0)) for k in set(da) | set(db))
    return inter / union, inter


def main():
    print("lih_smoothness: geometry -> chain continuity (writes nothing)")
    chains = {}
    print("[1] recompile + calibration against committed reports")
    for stem, R, L_exp, ranks_exp, mx_exp, nam_exp in SCAN:
        if not os.path.exists(stem + ".npz"):
            fail("missing dump %s.npz" % stem)
        c = compile_one(stem)
        ranks = {}
        for s in c["word"]:
            ranks[s.rank] = ranks.get(s.rank, 0) + 1
        mx = max(abs(t) for t in c["th"])
        ok = (len(c["word"]) == L_exp and ranks == ranks_exp
              and abs(mx - mx_exp) < 5e-7 and c["namps"] == nam_exp
              and len(c["support"]) == 69)
        print("    R %.1f : len %3d (exp %3d)  ranks %s  max|theta| "
              "%.6f (exp %.6f)  resid %.1e  monomials %d  support %d  "
              "E_FCI %.8f  %s"
              % (R, len(c["word"]), L_exp, ranks, mx, mx_exp,
                 c["resid"], c["namps"], len(c["support"]), c["e_fci"],
                 "MATCH" if ok else "MISMATCH"))
        if not ok:
            print("    NOTE: continuing, but treat downstream numbers "
                  "as provisional.")
        chains[R] = c

    Rs = [R for _, R, *_ in SCAN]
    print("[2] support-set identity across the scan")
    base = chains[Rs[0]]["support"]
    same = all(chains[R]["support"] == base for R in Rs[1:])
    for a, b in zip(Rs, Rs[1:]):
        inter = len(chains[a]["support"] & chains[b]["support"])
        print("    R %.1f -> %.1f : |S_a ^ S_b| = %d of 69" % (a, b, inter))
    print("    support SET invariant across all five geometries: %s"
          % same)

    print("[3] adjacent-chain similarity")
    print("    pair        | set J | mset J (n)  | LCS/max | same-pos")
    for a, b in zip(Rs, Rs[1:]):
        wa = [label(s) for s in chains[a]["word"]]
        wb = [label(s) for s in chains[b]["word"]]
        sa, sbn = set(wa), set(wb)
        setj = len(sa & sbn) / len(sa | sbn)
        mj, inter = mjaccard(wa, wb)
        l = lcs_len(wa, wb) / max(len(wa), len(wb))
        pos = sum(1 for x, y in zip(wa, wb) if x == y) / min(len(wa),
                                                            len(wb))
        print("    %.1f -> %.1f  | %.3f | %.3f (%3d) |  %.3f  |  %.3f"
              % (a, b, setj, mj, inter, l, pos))

    print("[4] theta continuity (labels unique in both chains)")
    print("    pair        |  n  | Pearson r | max|dTheta| | sign flips")
    for a, b in zip(Rs, Rs[1:]):
        da = multiset([label(s) for s in chains[a]["word"]])
        db = multiset([label(s) for s in chains[b]["word"]])
        ia = {label(s): t for s, t in zip(chains[a]["word"],
                                          chains[a]["th"])}
        ib = {label(s): t for s, t in zip(chains[b]["word"],
                                          chains[b]["th"])}
        keys = [k for k in ia if k in ib
                and da.get(k) == 1 and db.get(k) == 1]
        xa = np.array([ia[k] for k in keys])
        xb = np.array([ib[k] for k in keys])
        r = float(np.corrcoef(xa, xb)[0, 1]) if len(keys) > 2 else float("nan")
        mx = float(np.max(np.abs(xa - xb))) if len(keys) else 0.0
        fl = int(np.sum(np.sign(xa) != np.sign(xb)))
        print("    %.1f -> %.1f  | %3d |   %.4f  |   %.4f   |   %d"
              % (a, b, len(keys), r, mx, fl))

    print("[5] the backbone: letters at all five geometries")
    sets = [set(label(s) for s in chains[R]["word"]) for R in Rs]
    back = set.intersection(*sets)
    uni = set.union(*sets)
    print("    backbone %d letters; union %d; backbone/union %.3f"
          % (len(back), len(uni), len(back) / len(uni)))
    # top-|theta| backbone trajectories (unique occurrences only)
    traj = []
    for k in back:
        ths = []
        okk = True
        for R in Rs:
            d = multiset([label(s) for s in chains[R]["word"]])
            if d.get(k) != 1:
                okk = False
                break
            ths.append({label(s): t for s, t in
                        zip(chains[R]["word"], chains[R]["th"])}[k])
        if okk:
            traj.append((max(abs(t) for t in ths), k, ths))
    traj.sort(reverse=True)
    print("    top-5 backbone theta(R) trajectories "
          "(R = 3.0, 4.5, 6.0, 7.5, 9.0):")
    for mxt, k, ths in traj[:5]:
        print("      %-28s : " % (k,)
              + "  ".join("%+.4f" % t for t in ths))
    print("done. read-only: nothing was written.")


if __name__ == "__main__":
    main()

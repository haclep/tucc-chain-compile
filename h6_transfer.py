#!/usr/bin/env python
"""h6_transfer.py -- cross-topology transfer + ordering gauge (item 4b).

Recompiles the twelve committed H6 scan chains (chain and ring at
spacings 1.4/1.8/1.9/2.4/3.0/3.6 bohr, sd_routed, dim 400) from
freshly minted s-only dumps, calibrating each against the numbers
parsed out of its committed report in results/. Then measures:

  [2] support-set relations: within-topology invariance, and whether
      the ring's 160 sits inside the chain's 200 at matched spacing
  [3] WITHIN-topology adjacent-spacing similarity (as in the LiH
      probe: set/multiset Jaccard, LCS, positions, Kendall tau on
      first occurrences of shared letters)
  [4] CROSS-topology similarity at matched spacing (same metrics)
  [5] theta transfer chain -> ring on shared letters (Pearson)
  [6] the gauge verdict: order churn within topology vs across

Reads committed reports for calibration; writes nothing.
"""
import os
import re
import sys

import numpy as np

from chaincompile.compile import compile_chain
from chaincompile.molecular import (build_h_sector, load_integral_dump,
                                    freeze_core, dominant_block_projection)
from chaincompile.sector import SectorBasis
from chaincompile import normalorder as NO

SPACINGS = ["14", "18", "19", "24", "30", "36"]
TOPOS = ["chain", "ring"]


def fail(msg):
    print("STOP:", msg)
    sys.exit(1)


def committed(stem):
    path = os.path.join("results", "psi4_%s.md" % stem)
    txt = open(path, encoding="utf-8").read()
    sup = int(re.search(r"ground support (\d+)", txt).group(1))
    m = re.search(r"sd_routed: length (\d+), ranks ({[^}]*}), "
                  r"max\|theta\| ([0-9.]+), residual", txt)
    length = int(m.group(1))
    ranks = eval(m.group(2))
    mx = float(m.group(3))
    nam = int(re.search(r"(\d+) creator monomials", txt).group(1))
    return length, ranks, mx, nam, sup


def compile_one(stem):
    cache = os.path.join("/tmp", "h6cache", stem + ".pkl")
    if os.path.exists(cache):
        import pickle
        with open(cache, "rb") as fh:
            return pickle.load(fh)
    h_mo, eri_mo, e_shift, e_scf, na, nb, meta = load_integral_dump(
        stem + ".npz")
    h_mo, eri_mo, e_core = freeze_core(h_mo, eri_mo, 0)
    sb = SectorBasis(h_mo.shape[0], na, nb)
    H = build_h_sector(h_mo, eri_mo, sb)
    w, Vv = np.linalg.eigh(H)
    v0, seen2, mixed = dominant_block_projection(Vv[:, 0], H)
    floor = np.sqrt(1e-12) / sb.dim
    supp = frozenset(int(m_) for m_, k in
                     zip(sb.masks, np.abs(v0) > floor) if k)
    res = compile_chain(v0, sb, mode="sd_routed")
    word = [s for s, _ in res.selected()]
    th = [float(t) for _, t in res.selected()]
    occ = frozenset(p for p in range(2 * sb.L * 1) if (res.pivot_mask >> p) & 1) \
        if False else frozenset(p for p in range(2 * h_mo.shape[0])
                                if (res.pivot_mask >> p) & 1)
    U, sizes = NO.compose_numeric(word, th, occ)
    c0, amps = NO.numeric_ref_amplitudes(U, occ)
    out = {"word": word, "th": th, "resid": float(res.final_residual),
           "namps": len(amps) + 1, "support": supp,
           "e_fci": float(w[0] + e_shift), "mixed": mixed}
    os.makedirs(os.path.join("/tmp", "h6cache"), exist_ok=True)
    import pickle
    with open(cache, "wb") as fh:
        pickle.dump(out, fh)
    return out


def label(s):
    return (s.holes, s.parts)


def multiset(seq):
    d = {}
    for x in seq:
        d[x] = d.get(x, 0) + 1
    return d


def lcs_len(a, b):
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            cur[j] = (prev[j - 1] + 1 if ai == b[j - 1]
                      else max(prev[j], cur[j - 1]))
        prev = cur
    return prev[-1]


def kendall_first_occ(wa, wb):
    """Kendall tau between the first-occurrence orders of shared labels."""
    fa, fb = {}, {}
    for i, x in enumerate(wa):
        fa.setdefault(x, i)
    for i, x in enumerate(wb):
        fb.setdefault(x, i)
    keys = [k for k in fa if k in fb]
    if len(keys) < 3:
        return float("nan"), len(keys)
    ra = np.argsort(np.argsort([fa[k] for k in keys]))
    rb = np.argsort(np.argsort([fb[k] for k in keys]))
    n = len(keys)
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (ra[i] - ra[j]) * (rb[i] - rb[j])
            conc += s > 0
            disc += s < 0
    tau = (conc - disc) / (0.5 * n * (n - 1))
    return float(tau), n


def pair_metrics(ca, cb):
    wa = [label(s) for s in ca["word"]]
    wb = [label(s) for s in cb["word"]]
    sa, sbn = set(wa), set(wb)
    setj = len(sa & sbn) / len(sa | sbn)
    da, db = multiset(wa), multiset(wb)
    inter = sum(min(da.get(k, 0), db.get(k, 0)) for k in sa | sbn)
    union = sum(max(da.get(k, 0), db.get(k, 0)) for k in sa | sbn)
    l = lcs_len(wa, wb) / max(len(wa), len(wb))
    pos = sum(1 for x, y in zip(wa, wb) if x == y) / min(len(wa), len(wb))
    tau, ntau = kendall_first_occ(wa, wb)
    ia = {label(s): t for s, t in zip(ca["word"], ca["th"])}
    ib = {label(s): t for s, t in zip(cb["word"], cb["th"])}
    keys = [k for k in ia if k in ib and da.get(k) == 1 and db.get(k) == 1]
    if len(keys) > 2:
        xa = np.array([ia[k] for k in keys])
        xb = np.array([ib[k] for k in keys])
        r = float(np.corrcoef(xa, xb)[0, 1])
        fl = int(np.sum(np.sign(xa) != np.sign(xb)))
    else:
        r, fl = float("nan"), 0
    return setj, inter / union, l, pos, tau, ntau, r, len(keys), fl


def main():
    print("h6_transfer: cross-topology transfer + ordering gauge "
          "(writes nothing)")
    if len(sys.argv) > 1:          # compile-only chunk: stems as args
        for stem in sys.argv[1:]:
            c = compile_one(stem)
            print("    cached %-12s len %3d  resid %.1e"
                  % (stem, len(c["word"]), c["resid"]))
        return
    ch = {}
    print("[1] recompile + calibration against committed reports")
    for topo in TOPOS:
        for s in SPACINGS:
            stem = "h6_%s_%s" % (topo, s)
            L_exp, ranks_exp, mx_exp, nam_exp, sup_exp = committed(stem)
            c = compile_one(stem)
            ranks = {}
            for sub in c["word"]:
                ranks[sub.rank] = ranks.get(sub.rank, 0) + 1
            mx = max(abs(t) for t in c["th"])
            ok = (len(c["word"]) == L_exp and ranks == ranks_exp
                  and abs(mx - mx_exp) < 5e-7
                  and c["namps"] == nam_exp
                  and len(c["support"]) == sup_exp)
            print("    %-12s len %3d/%3d  max|th| %.6f/%.6f  mono %3d  "
                  "sup %3d  %s"
                  % (stem, len(c["word"]), L_exp, mx, mx_exp,
                     c["namps"], len(c["support"]),
                     "MATCH" if ok else "MISMATCH"))
            ch[(topo, s)] = c

    print("[2] support-set relations")
    for topo in TOPOS:
        sets = [ch[(topo, s)]["support"] for s in SPACINGS]
        inv = all(x == sets[0] for x in sets)
        print("    %s support set invariant across spacings: %s "
              "(sizes %s)" % (topo, inv, [len(x) for x in sets]))
    for s in SPACINGS:
        a, b = ch[("chain", s)]["support"], ch[("ring", s)]["support"]
        print("    spacing %s: |ring ^ chain| = %d of %d; "
              "ring subset of chain: %s"
              % (s, len(a & b), len(b), b <= a))

    hdr = ("    pair            | setJ | msetJ |  LCS  |  pos  | "
           "tau (n) |  r_th (n) | flips")

    print("[3] WITHIN-topology adjacent spacings")
    print(hdr)
    within_tau = []
    for topo in TOPOS:
        for a, b in zip(SPACINGS, SPACINGS[1:]):
            m = pair_metrics(ch[(topo, a)], ch[(topo, b)])
            within_tau.append(m[4])
            print("    %-15s | %.3f | %.3f | %.3f | %.3f | %+.2f (%2d) "
                  "| %+.3f (%2d) | %d"
                  % ("%s %s->%s" % (topo, a, b), *m))

    print("[4] CROSS-topology at matched spacing (chain -> ring)")
    print(hdr)
    cross_tau = []
    for s in SPACINGS:
        m = pair_metrics(ch[("chain", s)], ch[("ring", s)])
        cross_tau.append(m[4])
        print("    %-15s | %.3f | %.3f | %.3f | %.3f | %+.2f (%2d) "
              "| %+.3f (%2d) | %d"
              % ("c->r @ %s" % s, *m))

    print("[5] gauge verdict inputs")
    wt = [t for t in within_tau if t == t]
    ct = [t for t in cross_tau if t == t]
    print("    mean Kendall tau WITHIN topology : %+.3f (n=%d)"
          % (float(np.mean(wt)), len(wt)))
    print("    mean Kendall tau ACROSS topology : %+.3f (n=%d)"
          % (float(np.mean(ct)), len(ct)))
    print("done. read-only: nothing was written.")


if __name__ == "__main__":
    main()

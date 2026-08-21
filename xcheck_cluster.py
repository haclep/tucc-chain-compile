#!/usr/bin/env python
"""xcheck_cluster.py -- independent cross-check of the CC translator.

Item 3 of the 2026-08-20 audit plan. Three questions, one flagship:

  [A] THEIR route: chaincompile.translate.cluster_analysis on the
      stored Davidson eigenvector ct (data/c2_2348_bigsd.pkl).
  [B] MY route: a from-scratch reimplementation of intermediate-
      normalized cluster analysis (T = ln(1 + C) by exact rank
      recursion), sharing NOTHING with [A] except the determinant
      list, the coefficient vector, and the (holes, parts) labels.
      Fermionic signs come from an independent popcount parity;
      the operator products and the exp bookkeeping are re-derived.
      A per-amplitude sign-conversion map between the two
      conventions is COMPUTED and reported, never assumed.
  [C] Two-input check: replay the committed 3202-factor chain
      (data/c2_2348_chain.npz) through the Stage-1 kernel to get the
      chain state, run THEIR cluster analysis on it, and bound the
      amplitude drift produced by the state deficit 6.4e-15.

Read-only in the probe tradition: run it, paste the output, do not
commit results. Writes nothing.
"""
import os
import pickle
import sys
import time

import numpy as np

from chaincompile.sector import SectorBasis
from chaincompile.dets import Substitution, substitution_between
from chaincompile.translate import cluster_analysis, rank_table
from chaincompile import disentangle as dz

PKL = os.path.join("data", "c2_2348_bigsd.pkl")
NPZ = os.path.join("data", "c2_2348_chain.npz")
L, NA, NB = 8, 4, 4          # active space of the flagship dump
EXP_SUPPORT = 1108
EXP_C0 = 0.816517            # |ct| at the pivot, from the floor probe


def fail(msg):
    print("STOP:", msg)
    sys.exit(1)


# ----------------------------------------------------------------------
# independent fermionic bookkeeping (mine; numpy popcount parity)
# ----------------------------------------------------------------------
def _below(p):
    return (1 << p) - 1


def my_action(masks, holes, parts):
    """Vectorized action of A = c_{h1}..c_{hk} cd_{p1}..cd_{pk} on every
    determinant in `masks` (int64 array), annihilators on the sorted
    holes applied first (ascending, first element first), then creators
    on the sorted parts (ascending). Returns (ok, out, sign) arrays.
    Parity: for each elementary operator at position p, (-1)^(number of
    occupied spin-orbitals strictly below p at the moment it acts).
    """
    m = masks.astype(np.int64).copy()
    ok = np.ones(m.shape, dtype=bool)
    par = np.zeros(m.shape, dtype=np.int64)
    for h in holes:                       # annihilate, ascending
        bit = np.int64(1 << h)
        ok &= (m & bit) != 0
        par += np.bitwise_count(m & np.int64(_below(h)))
        m = np.where(ok, m & ~bit, m)
    for p in parts:                       # create, ascending
        bit = np.int64(1 << p)
        ok &= (m & bit) == 0
        par += np.bitwise_count(m & np.int64(_below(p)))
        m = np.where(ok, m | bit, m)
    sign = np.where(ok, 1 - 2 * (par & 1), 0).astype(np.float64)
    return ok, m, sign


def my_cluster_analysis(psi, basis, pivot_mask):
    """T = ln(1 + C), exact rank recursion, in MY convention.

    For each rank n (ascending): d = exp(T_{<n}) |pivot>, computed as a
    finite vector series with T applied through my_action scatter maps;
    then t_mu = (ctil[det] - d[det]) / s_mine(mu on pivot) for every
    rank-n determinant in the support of ctil.
    """
    masks = np.asarray(basis.masks, dtype=np.int64)
    index = {int(mk): i for i, mk in enumerate(masks)}
    p = index[int(pivot_mask)]
    if abs(psi[p]) < 1e-12:
        fail("pivot weight ~ 0")
    ctil = psi / psi[p]
    rank_of = np.array([basis.rank_between(int(mk), int(pivot_mask))
                        for mk in masks])
    live = np.abs(ctil) > 1e-13
    maxrank = int(rank_of[live].max())

    # precompute my scatter map for every label in the live support
    labels, actions = [], []
    for i in np.nonzero(live)[0]:
        if rank_of[i] == 0:
            continue
        sub = substitution_between(int(pivot_mask), int(masks[i]))
        ok, out, sg = my_action(masks, sub.holes, sub.parts)
        src = np.nonzero(ok)[0]
        dst = np.array([index[int(x)] for x in out[src]], dtype=np.int64)
        labels.append((int(rank_of[i]), sub.holes, sub.parts, i))
        actions.append((src, dst, sg[src]))

    dim = masks.size
    tmine = {}
    coeff = {}                       # label idx -> t (my convention)
    for n in range(1, maxrank + 1):
        # exp(T_{<n}) |pivot> by series; T has ranks < n only
        v = np.zeros(dim)
        v[p] = 1.0
        d = v.copy()
        term = v.copy()
        for k in range(1, maxrank + 1):
            nxt = np.zeros(dim)
            for (rk, hh, pp, i), (src, dst, sg) in zip(labels, actions):
                t = coeff.get((hh, pp))
                if t is None:
                    continue
                np.add.at(nxt, dst, t * sg * term[src])
            term = nxt / k
            d += term
            if np.linalg.norm(term) < 1e-16:
                break
        tn = {}
        for (rk, hh, pp, i), (src, dst, sg) in zip(labels, actions):
            if rk != n:
                continue
            resid = ctil[i] - d[i]
            ok1, out1, s1 = my_action(
                np.array([pivot_mask], dtype=np.int64), hh, pp)
            if not ok1[0] or int(out1[0]) != int(masks[i]):
                fail("my_action does not map pivot -> det for %r" % ((hh, pp),))
            t = float(resid / s1[0])
            if abs(t) >= 1e-14:
                tn[(hh, pp)] = t
                coeff[(hh, pp)] = t
        if tn:
            tmine[n] = tn
    # verify my rebuild
    v = np.zeros(dim)
    v[p] = 1.0
    d = v.copy()
    term = v.copy()
    for k in range(1, maxrank + 1):
        nxt = np.zeros(dim)
        for (rk, hh, pp, i), (src, dst, sg) in zip(labels, actions):
            t = coeff.get((hh, pp))
            if t is None:
                continue
            np.add.at(nxt, dst, t * sg * term[src])
        term = nxt / k
        d += term
    err = float(np.linalg.norm(d - ctil))
    return tmine, maxrank, err


# ----------------------------------------------------------------------
def compare(tA, tB, basis, pivot_mask, tagA, tagB):
    """Per-rank comparison with an explicit sign-conversion map."""
    print("    conversion map (s_theirs/s_mine on the pivot):")
    conv_vals = set()
    rows = []
    ranks = sorted(set(tA) | set(tB))
    worst = 0.0
    for n in ranks:
        a = tA.get(n, {})
        b = tB.get(n, {})
        keys = set(a) | set(b)
        dmax, cmax = 0.0, 0
        for kk in keys:
            sub = Substitution(kk[0], kk[1])
            _, s_th = sub.apply_a(int(pivot_mask))
            ok1, out1, s_my = my_action(
                np.array([pivot_mask], dtype=np.int64), kk[0], kk[1])
            conv = float(s_th) / float(s_my[0])
            conv_vals.add(conv)
            va = a.get(kk, 0.0)
            vb = b.get(kk, 0.0) * conv
            dmax = max(dmax, abs(va - vb))
        worst = max(worst, dmax)
        rows.append((n, len(a), len(b), dmax))
    print("      distinct conversion factors: %s" % sorted(conv_vals))
    print("    rank |  n(%s)  n(%s) |  max|delta t|" % (tagA, tagB))
    for n, na_, nb_, dmax in rows:
        print("      %2d |  %5d  %5d |  %.3e" % (n, na_, nb_, dmax))
    print("    WORST over all ranks: %.3e" % worst)
    return worst


def main():
    t0 = time.time()
    print("xcheck_cluster: independent CC-translator cross-check "
          "(writes nothing)")
    if not (os.path.exists(PKL) and os.path.exists(NPZ)):
        fail("flagship artifacts not found; run from the repo root")
    with open(PKL, "rb") as fh:
        ck = pickle.load(fh)
    d = np.load(NPZ, allow_pickle=True)
    pivot = int(d["pivot"])
    th = np.asarray(d["th"], float).ravel()
    subs = [Substitution(tuple(h), tuple(p))
            for h, p in zip(d["subs_h"], d["subs_p"])]
    ct = np.asarray(ck["ct"], float)
    basis = SectorBasis(L, NA, NB)
    if basis.dim != ct.size:
        fail("basis dim %d != ct size %d" % (basis.dim, ct.size))
    p = basis.index[pivot]

    print("[1] calibration anchors")
    supp = int(np.count_nonzero(np.abs(ct) > 1e-10))
    print("    support %d (expect %d); |c_pivot| %.6f (expect %.6f); "
          "chain len %d (expect 3202)"
          % (supp, EXP_SUPPORT, abs(ct[p]), EXP_C0, len(subs)))
    if supp != EXP_SUPPORT or abs(abs(ct[p]) - EXP_C0) > 5e-7:
        fail("calibration failed -- wrong artifacts?")

    print("[2] route A: in-package cluster_analysis on ct")
    tA, TA, mrA, errA = cluster_analysis(ct, basis, pivot)
    nA = sum(len(v) for v in tA.values())
    print("    maxrank %d, amplitudes %d, rebuild err %.3e  (%.1f s)"
          % (mrA, nA, errA, time.time() - t0))

    print("[3] route B: independent reimplementation on ct")
    t1 = time.time()
    tB, mrB, errB = my_cluster_analysis(ct, basis, pivot)
    nB = sum(len(v) for v in tB.values())
    print("    maxrank %d, amplitudes %d, rebuild err %.3e  (%.1f s)"
          % (mrB, nB, errB, time.time() - t1))

    print("[4] A vs B, amplitude by amplitude")
    worstAB = compare(tA, tB, basis, pivot, "A", "B")

    print("[5] route C: chain-replayed state -> in-package analysis")
    t2 = time.time()
    ref = tuple(sorted(q for q in range(2 * L) if (pivot >> q) & 1))
    st = {ref: 1.0}
    for sub, tt in zip(subs, th):
        st = dz.apply_factor(sub, float(tt), st, tol=0.0)
    psi_chain = np.zeros(basis.dim)
    for det, w in st.items():
        mk = 0
        for q in det:
            mk |= 1 << q
        psi_chain[basis.index[mk]] = w
    fid = float(abs(psi_chain @ ct)
                / (np.linalg.norm(psi_chain) * np.linalg.norm(ct)))
    print("    replayed %d factors; |<chain|ct>| = %.15f; "
          "deficit %.3e  (%.1f s)"
          % (len(subs), fid, 1.0 - fid * fid, time.time() - t2))
    tC, TC, mrC, errC = cluster_analysis(psi_chain, basis, pivot)
    nC = sum(len(v) for v in tC.values())
    print("    maxrank %d, amplitudes %d, rebuild err %.3e" % (mrC, nC, errC))

    print("[6] A vs C (log-conditioning of the state deficit)")
    worst = 0.0
    for n in sorted(set(tA) | set(tC)):
        a, c = tA.get(n, {}), tC.get(n, {})
        keys = set(a) | set(c)
        dmax = max((abs(a.get(k, 0.0) - c.get(k, 0.0)) for k in keys),
                   default=0.0)
        worst = max(worst, dmax)
        print("      rank %2d : n %5d vs %5d, max|delta t| %.3e"
              % (n, len(a), len(c), dmax))
    print("    WORST over all ranks: %.3e" % worst)

    print("[7] flagship T anatomy (route A, exact)")
    print("    rank | n_amps |   ||T_n||   |  max|t|")
    for r in rank_table(tA):
        print("      %2d | %6d | %.6e | %.6e"
              % (r["rank"], r["n_amps"], r["norm2"], r["max_abs_t"]))

    print("done in %.1f s. read-only: nothing was written." % (time.time() - t0))


if __name__ == "__main__":
    main()

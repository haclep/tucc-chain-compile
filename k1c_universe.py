#!/usr/bin/env python
"""k1c_universe.py -- K1c step 1: the compiler's own letter universe.

The frozen Split-C model scored a universe assembled from training
vocabulary (raw spin-orbital keys, which do not mean the same thing
across system sizes) plus the MP2 occ->virt window of the test system.
On h8_chain that universe reached 35% of the distinct grown letters
and 48% of the grown multiset mass (milestone 2026-08-30 Sec. 8.2a):
the recall ceiling was set before any learning happened.

This module enumerates what the compiler's growth step can actually
choose from -- every spin-conserving rank-1 and rank-2 substitution
over the active spin-orbitals -- and featurizes each letter with
quantities that mean the same thing in H4, H6 and H8:

  structural : rank, spin pattern, how many holes sit in the pivot's
               occupied space and how many particles in its virtual
               space, orbital offsets from the Fermi level (in orbital
               count, normalized by n_act), index span.
  physics    : orbital energies relative to the Fermi level, the
               energy denominator, the two-electron coupling in the
               letter's spin pattern (defined for ANY occupancy, not
               only occ->virt), the generalized perturbative amplitude
               coupling/denominator and its arctan, and the frozen
               MP2 score/theta from k1_harness (0 outside the window)
               kept for continuity and for the B4 ablation.

Nothing here touches the compiler package or any k1b artifact.

Usage:
    python k1c_universe.py h8_chain            # coverage + feature audit
    python k1c_universe.py k1_h6_chain_19 --old-vocab k1_h4   # compare
"""
import argparse
import importlib.util as iu
import os
import pickle
import sys

import numpy as np

_spec = iu.spec_from_file_location("kh", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "k1_harness.py"))
kh = iu.module_from_spec(_spec)
_spec.loader.exec_module(kh)


# ------------------------------------------------------------ system data
def load_system(name):
    """Label + dump + canonical orbital energies, in k1_harness's
    conventions (active spin-orbital q -> dump spatial q//2 + n_core)."""
    lab = pickle.load(open(kh._labpath(name), "rb"))
    d = np.load(kh._dumppath(name), allow_pickle=True)
    eri = np.asarray(d["eri_mo"], float)
    h = np.asarray(d["h_mo"], float)
    nmo_d = h.shape[0]
    nc = kh._ncore(name)
    nact = nmo_d - nc
    n_so = 2 * nact
    occ = sorted(q for q in range(n_so) if (lab["pivot"] >> q) & 1)
    ndocc_d = len(occ) // 2 + nc
    docc = range(ndocc_d)
    eps = np.array([h[p, p] + sum(2 * eri[p, p, j, j] - eri[p, j, j, p]
                                  for j in docc) for p in range(nmo_d)])
    n_occ_sp = len(occ) // 2          # spatial occupied count (closed shell)
    e_act = eps[nc:]
    fermi = 0.5 * (e_act[n_occ_sp - 1] + e_act[n_occ_sp]) \
        if n_occ_sp < nact else float(e_act[-1])
    e_scf = lab.get("e_scf")
    e_corr = (lab["e_fci"] - e_scf) if e_scf is not None else 0.0
    n_routed = len(lab["support"]) - 1
    word = [tuple(map(tuple, x)) for x in lab["word"]]
    return {"name": name, "lab": lab, "eri": eri, "h": h, "eps": eps,
            "nc": nc, "nact": nact, "n_so": n_so, "occ": set(occ),
            "n_occ_sp": n_occ_sp, "fermi": float(fermi),
            "gap": float(e_act[n_occ_sp] - e_act[n_occ_sp - 1])
            if n_occ_sp < nact else 0.0,
            "e_corr": float(e_corr), "n_routed": n_routed,
            "word": word, "grown": word[n_routed:],
            "routed": word[:n_routed]}


# ------------------------------------------------------------ the universe
def full_universe(n_so):
    """All spin-conserving rank-1 and rank-2 substitutions over n_so
    spin-orbitals: holes and particles disjoint, sorted tuples, spin
    multiset conserved. This is what the compiler's edge pool can
    return, up to the residual-top filter, so it contains every grown
    letter by construction."""
    sp = lambda q: q % 2
    out = []
    for i in range(n_so):
        for a in range(n_so):
            if a != i and sp(a) == sp(i):
                out.append(((i,), (a,)))
    for i in range(n_so):
        for j in range(i + 1, n_so):
            sh = sorted((sp(i), sp(j)))
            for a in range(n_so):
                if a in (i, j):
                    continue
                for b in range(a + 1, n_so):
                    if b in (i, j):
                        continue
                    if sorted((sp(a), sp(b))) != sh:
                        continue
                    out.append(((i, j), (a, b)))
    return out


def old_universe(train_names, labs, test_name, cache):
    """The frozen Split-C universe: training vocabulary (raw keys) plus
    the test system's MP2 occ->virt window."""
    uni = set()
    for m in train_names:
        uni |= set(tuple(map(tuple, x)) for x in labs[m]["word"])
    if test_name not in cache:
        cache[test_name] = kh.mp2_letter_score(test_name)
    uni |= set(cache[test_name][0])
    return uni


# ------------------------------------------------------------ features
STRUCT_NAMES = ["rank", "same_spin", "n_hole_occ", "n_part_virt", "is_ref",
                "off_h_min", "off_h_max", "off_p_min", "off_p_max",
                "offn_h_mean", "offn_p_mean", "span_norm"]
PHYS_NAMES = ["e_h_rel", "e_p_rel", "den", "abs_den", "coupling",
              "abs_coupling", "amp", "abs_amp", "theta_seed", "e_dist",
              "mp2_score", "mp2_theta"]
SYS_NAMES = ["spacing", "sqrt_dim", "support", "log_support", "nact",
             "n_elec", "gap", "e_corr", "mp2_max", "mp2_mean"]


def _coupling(S, key):
    """Two-electron coupling of a letter in its spin pattern, defined for
    any occupancy. Rank 1: Fock-like element in the dump's closed-shell
    reference plus the MP2-singles proxy generalized off the window."""
    eri, eps, nc = S["eri"], S["eps"], S["nc"]
    hh, pp = key
    sp = lambda q: (q // 2 + nc, q % 2)
    if len(hh) == 2:
        (i, j), (a, b) = hh, pp
        (I, si), (J, sj), (A, sa), (B, sb) = sp(i), sp(j), sp(a), sp(b)
        den = eps[I] + eps[J] - eps[A] - eps[B]
        if si == sj:
            c = eri[I, A, J, B] - eri[I, B, J, A]
        elif (si, sj) == (sa, sb):
            c = eri[I, A, J, B]
        else:
            c = -eri[I, B, J, A]
        return float(c), float(den)
    (i,), (a,) = hh, pp
    (I, si), (A, sa) = sp(i), sp(a)
    den = eps[I] - eps[A]
    docc = range(S["n_occ_sp"] + nc)
    fock = S["h"][I, A] + sum(2 * eri[I, A, j, j] - eri[I, j, j, A]
                              for j in docc)
    prox = 0.0
    occ, n_so = S["occ"], S["n_so"]
    for jq in occ:
        J, sj = sp(jq)
        for bq in range(n_so):
            if bq in occ:
                continue
            B, sb = sp(bq)
            if sj != sb:
                continue
            d2 = eps[I] + eps[J] - eps[A] - eps[B]
            if abs(d2) < 1e-9:
                continue
            t2 = eri[I, A, J, B] / d2
            if si == sj:
                t2 -= eri[I, B, J, A] / d2
            prox += abs(t2)
    return float(fock + 0.1 * prox), float(den)


def letter_features(S, key, mp2s, mp2t):
    hh, pp = key
    r = len(hh)
    nact, nc, occ = S["nact"], S["nc"], S["occ"]
    n_occ = S["n_occ_sp"]
    same = 1.0 if len(set(q % 2 for q in hh)) == 1 else 0.0
    nho = sum(q in occ for q in hh)
    npv = sum(q not in occ for q in pp)
    is_ref = 1.0 if (nho == r and npv == r) else 0.0
    off = lambda q: (q // 2) - n_occ
    oh = [off(q) for q in hh]
    op = [off(q) for q in pp]
    span = (max(hh + pp) - min(hh + pp)) / 2.0 / max(1, nact)
    struct = [r, same, nho, npv, is_ref, min(oh), max(oh), min(op),
              max(op), float(np.mean(oh)) / nact,
              float(np.mean(op)) / nact, span]
    e = lambda q: S["eps"][q // 2 + nc] - S["fermi"]
    eh = sum(e(q) for q in hh)
    ep = sum(e(q) for q in pp)
    c, den = _coupling(S, key)
    amp = c / den if abs(den) > 1e-9 else 0.0
    edist = float(np.mean([abs(e(a) - e(b)) for a in hh for b in pp]))
    phys = [eh, ep, den, abs(den), c, abs(c), amp, abs(amp),
            float(np.arctan(amp)), edist,
            mp2s.get(key, 0.0), mp2t.get(key, 0.0)]
    return struct, phys


def system_features(S, mp2s):
    vals = np.array(list(mp2s.values())) if mp2s else np.zeros(1)
    lab = S["lab"]
    return [kh.spacing_of(S["name"]) / 10.0, lab["dim"] ** 0.5,
            len(lab["support"]), float(np.log(len(lab["support"]))),
            S["nact"], len(S["occ"]), S["gap"], S["e_corr"],
            float(vals.max()), float(vals.mean())]


def featurize(S, universe, mp2, physics=True):
    """Rows for every letter of the universe. Returns X, names, keys."""
    mp2s, mp2t = mp2
    sf = system_features(S, mp2s)
    rows = []
    for key in universe:
        st, ph = letter_features(S, key, mp2s, mp2t)
        rows.append(sf + st + (ph if physics else []))
    names = SYS_NAMES + STRUCT_NAMES + (PHYS_NAMES if physics else [])
    return np.array(rows, float), names, list(universe)


# ------------------------------------------------------------ diagnostics
def coverage(word, universe):
    """Multiset mass and distinct-letter coverage of word by universe."""
    U = set(universe)
    cnt = kh.counts(word)
    mass = sum(c for k, c in cnt.items() if k in U) / max(1, len(word))
    dist = sum(1 for k in cnt if k in U) / max(1, len(cnt))
    return mass, dist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?", default="h8_chain")
    ap.add_argument("--old-vocab", default="k1_h4,k1_h6",
                    help="comma-separated name prefixes forming the OLD "
                         "training vocabulary (default: frozen Split C)")
    a = ap.parse_args()
    labs = kh.load_labels()
    S = load_system(a.name)
    uni = full_universe(S["n_so"])
    mp2 = kh.mp2_letter_score(a.name)
    print("%s: n_so %d | pivot-occupied %d | support %d | routed %d | "
          "grown %d (%d distinct)"
          % (a.name, S["n_so"], len(S["occ"]), len(S["lab"]["support"]),
             S["n_routed"], len(S["grown"]), len(set(S["grown"]))))
    r1 = sum(1 for k in uni if len(k[0]) == 1)
    print("full S/D universe: %d letters (%d rank-1, %d rank-2)"
          % (len(uni), r1, len(uni) - r1))
    m, dd = coverage(S["grown"], uni)
    print("  coverage of GROWN multiset: mass %.3f  distinct %.3f"
          % (m, dd))
    prefixes = [p for p in a.old_vocab.split(",") if p]
    train = sorted(n for n in labs if any(n.startswith(p) for p in prefixes)
                   and n != a.name and not labs[n].get("mixed", False))
    if train:
        cache = {a.name: mp2}
        old = old_universe(train, labs, a.name, cache)
        m0, d0 = coverage(S["grown"], old)
        print("old universe (%d train systems' vocab + MP2 window): %d "
              "letters | coverage of GROWN: mass %.3f  distinct %.3f"
              % (len(train), len(old), m0, d0))
    ref = sum(1 for k in S["grown"] if letter_features(S, k, *mp2)[0][4])
    print("  grown letters pivot-referenced (occ->virt): %d of %d "
          "(%.1f%%); MP2 window nominates only these"
          % (ref, len(S["grown"]), 100.0 * ref / max(1, len(S["grown"]))))
    X, names, keys = featurize(S, uni, mp2)
    print("feature matrix %s | %d system + %d structural + %d physics"
          % (X.shape, len(SYS_NAMES), len(STRUCT_NAMES), len(PHYS_NAMES)))
    if not np.all(np.isfinite(X)):
        bad = [names[j] for j in np.where(~np.isfinite(X).all(0))[0]]
        print("  WARNING non-finite features:", bad)
    cnt = kh.counts(S["grown"])
    present = np.array([cnt.get(k, 0) > 0 for k in keys])
    j = names.index("abs_amp")
    print("  |amp| median present %.3e vs absent %.3e (separation check)"
          % (np.median(X[present, j]) if present.any() else 0.0,
             np.median(X[~present, j])))


if __name__ == "__main__":
    main()

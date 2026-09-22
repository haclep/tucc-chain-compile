#!/usr/bin/env python
"""k1c_fcc.py -- whole-chain UCC -> CC translation, Freericks route.

Reads a certified chain and returns, for EVERY factor, the conventional
coupled-cluster content that factor contributes IN CONTEXT: its own
amplitude, the correction it applies retroactively to earlier factors,
and the new excitation operators it generates. The sum over factors is
the chain's full cluster operator T.

----------------------------------------------------------------------
What this computes, and why it is the chain's property not the state's
----------------------------------------------------------------------
Freericks (Symmetry 14, 494 (2022)) disentangles each UCC factor by the
SL(2,C) identity (Eq. 15),

    exp(theta (A - Adag)) = exp(tan(theta) A)
                          . exp(-ln cos(theta) (A Adag - Adag A))
                          . exp(-tan(theta) Adag),

and then reorders the whole product with the Hadamard lemma so that all
excitations stand to the left and all de-excitations annihilate the
reference. Two things come out: a scalar prod_k cos(theta_k), and a
product of exponentials of excitation operators whose amplitudes are
dressed by the factors around them -- "the factorized form of the
conventional coupled cluster." A later factor changes an EARLIER
factor's CC amplitude; that retroactive dressing is the operator-valued
content the paper is about, and it is why the answer depends on the
chain and not only on the state it prepares.

This module performs that reordering exactly, without hand-deriving the
commutator rules, by working in the algebra the reordering lives in.

Excitation operators relative to a fixed pivot commute (moving one
occ->vir pair past another costs four fermionic transpositions), and
they are nilpotent-graded by rank, so:

  * the wave operator Omega, defined by U|pivot> = c_pivot . Omega|pivot>
    with Omega monic, is a polynomial in excitation monomials, and its
    coefficients are read straight off the normalized state (each
    determinant is reached from the pivot by exactly one monomial);
  * products, inverses and logarithms in that algebra are FINITE -- no
    BCH series, no truncation -- because the grading terminates at the
    maximum rank present;
  * the partial products give Omega_0 = 1, Omega_1, ..., Omega_N, and
    the factorized form is Omega = prod_k G_k with G_k = Omega_{k-1}^-1
    Omega_k. Writing G_k = exp(g_k) gives the exact per-factor CC
    contribution g_k = T_k - T_{k-1}, where T_k = log Omega_k.

The logarithm is unavoidable: extracting a cluster operator from a wave
operator means inverting an exponential, and the rank-graded series is
the only finite way to do it. That inversion is shared with cluster
analysis and is credited as such. What is new here, and what cluster
analysis cannot produce, is the PER-FACTOR attribution: cluster analysis
answers "what is T for this state," this module answers "what does each
factor of this chain contribute to T, given its neighbours."

----------------------------------------------------------------------
Guards
----------------------------------------------------------------------
  * |theta| < pi/2 for every factor (the identity's domain; cos theta
    is the weight the factor leaves on the reference, and the CC-side
    amplitude tan theta diverges at the bound).
  * the pivot weight of every PARTIAL state must stay above a floor:
    the CC reading is relative to the reference, and a reference with
    no weight has no cluster expansion.
Both are reported, never silently skipped.

Usage:
    python k1c_fcc.py --self-test
    python k1c_fcc.py k1b/k1_h6_ring_19_cold_pj_chain.npz --dump k1_corpus/k1_h6_ring_19.npz
    python k1c_fcc.py <chain.npz> --dump <dump.npz> --top 20 --json out.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "src"))

from chaincompile.dets import Substitution, substitution_between   # noqa: E402
from chaincompile.factors import apply_ucc_factor                  # noqa: E402
from chaincompile.sector import SectorBasis                        # noqa: E402

BOUND_TOL = 1e-9        # |theta| must be under pi/2 by at least this
PIVOT_FLOOR = 1e-10     # partial-state pivot weight floor
KEEP = 1e-14            # coefficient keep-floor in the algebra


# ======================================================================
# The commutative algebra of excitation monomials relative to a pivot
# ======================================================================
class ExcAlgebra:
    """Polynomials in excitation monomials, keyed by the determinant each
    monomial reaches from the pivot.

    A monomial mu is the primitive substitution taking the pivot to its
    determinant; A_mu|pivot> = s_mu |det_mu>. Elements are stored by
    STATE coefficient c_mu = a_mu s_mu (a_mu the operator coefficient),
    so the wave operator of a state is literally the state's normalized
    coefficient vector and no conversion is needed to read it in or out.

    The product then carries the structure constant s'/s_mu, where s' is
    the sign of applying A_mu to det_nu:

        (A B)_c = sum_{mu nu} c_mu c_nu (s' / s_mu),  det_c = A_mu det_nu

    which is exact fermionic bookkeeping, reusing dets.Substitution.
    """

    def __init__(self, basis: SectorBasis, pivot: int):
        self.basis = basis
        self.pivot = int(pivot)
        self._sub = {}      # mask -> (Substitution, sign from pivot)
        self._rank = {}

    def sub_of(self, mask):
        if mask not in self._sub:
            if mask == self.pivot:
                self._sub[mask] = (None, 1.0)
            else:
                s = substitution_between(self.pivot, mask)
                up, sg = s.apply_a(self.pivot)
                assert up == mask, "substitution does not reach its determinant"
                self._sub[mask] = (s, float(sg))
        return self._sub[mask]

    def rank_of(self, mask):
        if mask not in self._rank:
            self._rank[mask] = self.basis.rank_between(mask, self.pivot)
        return self._rank[mask]

    # -- elements are dicts {mask: coeff}; the pivot entry is the scalar --
    def one(self):
        return {self.pivot: 1.0}

    def mul(self, A, B):
        out = {}
        for ma, ca in A.items():
            if abs(ca) < KEEP:
                continue
            sub_a, s_a = self.sub_of(ma)
            for mb, cb in B.items():
                if abs(cb) < KEEP:
                    continue
                if sub_a is None:               # identity monomial
                    mc, sg = mb, 1.0
                else:
                    r = sub_a.apply_a(mb)
                    if r is None:               # Pauli: the product vanishes
                        continue
                    mc, sg = r
                    sg = float(sg)
                v = ca * cb * sg / s_a
                if v:
                    out[mc] = out.get(mc, 0.0) + v
        return {k: v for k, v in out.items() if abs(v) > KEEP}

    def add(self, A, B, sign=1.0):
        out = dict(A)
        for m, c in B.items():
            out[m] = out.get(m, 0.0) + sign * c
        return {k: v for k, v in out.items() if abs(v) > KEEP}

    def scale(self, A, f):
        return {k: v * f for k, v in A.items() if abs(v * f) > KEEP}

    def maxrank(self, A):
        return max((self.rank_of(m) for m in A if abs(A[m]) > KEEP), default=0)

    def sector_maxrank(self):
        """Highest excitation rank the sector admits relative to the pivot.
        Any product of n excitations has rank >= n, so every series here
        terminates at or before this order: the algebra is nilpotent and
        the logarithm and exponential are finite, not truncated."""
        if not hasattr(self, "_smr"):
            self._smr = max(self.rank_of(int(m)) for m in self.basis.masks)
        return self._smr

    def log(self, Omega):
        """log of a monic element. x = Omega - 1 has no constant term and
        is rank-graded, so x^n vanishes once n exceeds the maximum rank:
        the series is finite and exact, with no truncation."""
        c0 = Omega.get(self.pivot, 0.0)
        if abs(c0 - 1.0) > 1e-9:
            raise ValueError("log needs a monic element (pivot coeff 1), "
                             "got %.3e" % c0)
        x = {k: v for k, v in Omega.items() if k != self.pivot}
        if not x:
            return {}
        nmax = self.sector_maxrank()
        out, xn = {}, self.one()
        for n in range(1, nmax + 1):
            xn = self.mul(xn, x)
            if not xn:
                break
            out = self.add(out, self.scale(xn, ((-1.0) ** (n + 1)) / n))
        out.pop(self.pivot, None)
        return out

    def exp(self, g):
        """exp of a element with no constant term; finite for the same
        reason. Used to verify the decomposition, never to produce it."""
        out, term = self.one(), self.one()
        nmax = self.sector_maxrank()
        for n in range(1, nmax + 1):
            term = self.scale(self.mul(term, g), 1.0 / n)
            if not term:
                break
            out = self.add(out, term)
        return out

    def to_vector(self, A):
        v = np.zeros(self.basis.dim)
        for m, c in A.items():
            v[self.basis.index[m]] = c
        return v

    def from_vector(self, v, tol=KEEP):
        return {int(self.basis.masks[i]): float(v[i])
                for i in range(self.basis.dim) if abs(v[i]) > tol}

    def label(self, mask):
        sub, _ = self.sub_of(mask)
        if sub is None:
            return "(ref)"
        return "%s->%s" % (",".join(map(str, sub.holes)),
                           ",".join(map(str, sub.parts)))


# ======================================================================
# The translation
# ======================================================================
def translate_chain(word, th, basis, pivot, keep_partials=False,
                    pivot_floor=PIVOT_FLOOR, decompose=True):
    """Freericks whole-chain translation.

    word : list of (holes, parts) tuples, applied left to right
    th   : the angle of each factor
    Returns a dict with the scalar, the cluster operator T, the per-factor
    contributions, and the verification residuals.
    """
    alg = ExcAlgebra(basis, pivot)
    N = len(word)
    for k, t in enumerate(th):
        if abs(t) >= math.pi / 2 - BOUND_TOL:
            raise ValueError(
                "factor %d has |theta| = %.6f, at or past pi/2: the "
                "disentangling identity is undefined there (the reference "
                "weight cos(theta) = %.2e vanishes)" % (k, abs(t), math.cos(t)))

    psi = basis.basis_vector(pivot)
    ip = basis.index[pivot]
    T_prev, per_factor, partials = {}, [], []
    scalar_running = 1.0
    for k in range(N):
        hh, pp = word[k]
        psi = apply_ucc_factor(psi, basis, Substitution(tuple(hh), tuple(pp)),
                               float(th[k]))
        c0 = float(psi[ip])
        if abs(c0) < pivot_floor:
            raise ValueError(
                "after factor %d the pivot weight is %.2e, under the floor: "
                "the CC reading is relative to the reference and a reference "
                "with no weight has no cluster expansion" % (k, c0))
        if not decompose and k < N - 1:
            scalar_running = c0
            continue
        Omega = alg.from_vector(psi / c0)
        T_k = alg.log(Omega)
        g_k = alg.add(T_k, T_prev, sign=-1.0)
        own_mask = None
        r = Substitution(tuple(hh), tuple(pp)).apply_a(pivot)
        if r is not None:
            own_mask = r[0]
        dressed = {m: c for m, c in g_k.items()
                   if m != own_mask and m in T_prev}
        generated = {m: c for m, c in g_k.items()
                     if m != own_mask and m not in T_prev}
        per_factor.append({
            "k": k, "letter": (tuple(hh), tuple(pp)), "theta": float(th[k]),
            "tan": math.tan(float(th[k])), "cos": math.cos(float(th[k])),
            "own": float(g_k.get(own_mask, 0.0)) if own_mask is not None
                   else None,
            "own_is_pivot_referenced": own_mask is not None,
            "n_dressed": len(dressed), "n_generated": len(generated),
            "dress_l1": float(sum(abs(v) for v in dressed.values())),
            "gen_l1": float(sum(abs(v) for v in generated.values())),
            "g": g_k if keep_partials else None,
        })
        if keep_partials:
            partials.append(T_k)
        T_prev = T_k
        scalar_running = c0
    T = T_prev
    # prod cos(theta) equals the pivot weight only when every factor's block
    # is reference-active; a factor whose block misses the reference leaves it
    # untouched. Reported as a diagnostic, never as a pass/fail.
    scalar_pred = float(np.prod([math.cos(float(t)) for t in th]))
    tmax = max((abs(c / alg.sub_of(m)[1]) for m, c in T_prev.items()),
               default=0.0)
    # verification: rebuild from T alone and from the per-factor sum
    rebuilt = alg.to_vector(alg.exp(T)) * scalar_running
    g_sum = {}
    for e in per_factor:
        if e["g"] is not None:
            g_sum = alg.add(g_sum, e["g"])
    res_state = float(np.linalg.norm(rebuilt - psi))
    res_sum = (float(np.linalg.norm(alg.to_vector(alg.add(g_sum, T, -1.0))))
               if keep_partials else None)
    return {"alg": alg, "T": T, "scalar": scalar_running,
            "scalar_prod_cos": scalar_pred,
            "scalar_match": abs(scalar_running - scalar_pred),
            "per_factor": per_factor, "psi": psi,
            "residual_rebuild": res_state, "residual_gsum": res_sum,
            "max_amplitude": tmax, "per_factor_done": decompose,
            "maxrank": alg.maxrank(T), "n_amplitudes": len(T)}


# ======================================================================
# Self-test: the paper's own three-singles example, Eq. (46)
# ======================================================================
def self_test(verbose=True):
    """Freericks Eq. (46). Three singles applied in the order (a,i), (b,j),
    (a,j) give

      cos(th_bj) cos(th_aj) cos(th_ai) exp[ tan(th_aj) A(a;j)
        + tan(th_bj) sec(th_aj) A(b;j) + tan(th_ai) sec(th_aj) A(a;i)
        + tan(th_aj) tan(th_bj) tan(th_ai) A(b;i) ] |Psi0>

    Note the paper's own content: the third factor DRESSES the first two
    with a secant, and a fourth excitation A(b;i) -- absent from the
    chain -- is generated with a product-of-tangents amplitude. Both are
    predictions this module must reproduce with no formula built in.
    """
    basis = SectorBasis(4, 2, 2)              # 8 spin-orbitals, 2 up 2 down
    pivot = 0b00001111                        # spin-orbitals 0,1,2,3
    i, j, a, b = 0, 2, 4, 6                   # all same spin (even indices)
    A_ai, A_bj, A_aj, A_bi = ((i,), (a,)), ((j,), (b,)), ((j,), (a,)), ((i,), (b,))
    word = [A_ai, A_bj, A_aj]
    th = [0.31, -0.47, 0.23]
    r = translate_chain(word, th, basis, pivot, keep_partials=True)
    alg, T = r["alg"], r["T"]
    t_ai, t_bj, t_aj = (math.tan(x) for x in th)
    sec_aj = 1.0 / math.cos(th[2])
    want = {A_aj: t_aj, A_bj: t_bj * sec_aj, A_ai: t_ai * sec_aj,
            A_bi: t_aj * t_bj * t_ai}
    ok = True
    if verbose:
        print("Freericks Eq. (46), three singles, order (a,i) (b,j) (a,j)")
        print("  angles: th_ai %+.4f  th_bj %+.4f  th_aj %+.4f" % tuple(th))
        print("  %-10s %16s %16s %10s" % ("operator", "paper", "this module",
                                          "|diff|"))
    for sub_t, expect in want.items():
        m = Substitution(sub_t[0], sub_t[1]).apply_a(pivot)[0]
        got_state = T.get(m, 0.0)
        _, s_mu = alg.sub_of(m)
        got = got_state / s_mu                # operator coefficient
        d = abs(got - expect)
        ok = ok and d < 1e-12
        if verbose:
            print("  %-10s %16.10f %16.10f %10.1e"
                  % ("%s->%s" % (sub_t[0][0], sub_t[1][0]), expect, got, d))
    extra = [m for m in T
             if m not in [Substitution(s[0], s[1]).apply_a(pivot)[0]
                          for s in want]]
    if verbose:
        print("  operators beyond the four predicted: %d" % len(extra))
        print("  scalar: prod cos = %.12f, measured = %.12f, |diff| %.1e"
              % (r["scalar_prod_cos"], r["scalar"], r["scalar_match"]))
        print("  rebuild residual %.1e | sum_k g_k vs T %.1e"
              % (r["residual_rebuild"], r["residual_gsum"]))
        print("  retroactive dressing, factor by factor:")
        for e in r["per_factor"]:
            print("    factor %d %s: own %+.8f, dresses %d earlier, "
                  "generates %d new"
                  % (e["k"], "%s->%s" % (e["letter"][0][0], e["letter"][1][0]),
                     e["own"] if e["own"] is not None else float("nan"),
                     e["n_dressed"], e["n_generated"]))
    ok = ok and not extra and r["residual_rebuild"] < 1e-12 \
        and r["residual_gsum"] < 1e-12
    if verbose:
        print("  SELF-TEST %s" % ("PASSED" if ok else "FAILED"))
    return ok


# ======================================================================
# CLI
# ======================================================================
def load_chain(path):
    d = np.load(path, allow_pickle=True)
    word = [(tuple(int(q) for q in h), tuple(int(q) for q in p))
            for h, p in zip(d["subs_h"], d["subs_p"])]
    return word, [float(t) for t in d["th"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chain", nargs="?", help="<stem>_<tag>_chain.npz")
    ap.add_argument("--nmo", type=int, default=None,
                    help="spatial orbitals (default: inferred from the chain)")
    ap.add_argument("--nup", type=int, default=None)
    ap.add_argument("--ndn", type=int, default=None)
    ap.add_argument("--pivot", type=lambda s: int(s, 0), default=None)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--json", default=None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--per-factor", action="store_true",
                    help="also decompose T factor by factor (N logarithms "
                         "instead of one; small systems only)")
    a = ap.parse_args()
    if a.self_test or not a.chain:
        raise SystemExit(0 if self_test() else 1)
    word, th = load_chain(a.chain)
    nso = max(max(h + p) for h, p in word) + 1
    nmo = a.nmo or (nso + 1) // 2
    if a.nup is None or a.ndn is None:
        raise SystemExit("give --nup and --ndn (and --pivot for a "
                         "non-aufbau reference)")
    basis = SectorBasis(nmo, a.nup, a.ndn)
    pivot = a.pivot if a.pivot is not None else int(basis.masks[0])
    r = translate_chain(word, th, basis, pivot, keep_partials=a.per_factor,
                        decompose=a.per_factor)
    alg, T = r["alg"], r["T"]
    print("%s: %d factors, sector dim %d" % (os.path.basename(a.chain),
                                             len(word), basis.dim))
    print("scalar prod cos(theta) = %.12e (measured %.12e, |diff| %.1e)"
          % (r["scalar_prod_cos"], r["scalar"], r["scalar_match"]))
    print("cluster operator: %d amplitudes, max rank %d"
          % (r["n_amplitudes"], r["maxrank"]))
    print("rebuild residual %.2e | largest |t| %.3e%s"
          % (r["residual_rebuild"], r["max_amplitude"],
             "" if r["residual_gsum"] is None
             else " | sum_k g_k vs T %.2e" % r["residual_gsum"]))
    amps = sorted(T.items(), key=lambda kv: -abs(kv[1]))[:a.top]
    print("\nlargest CC amplitudes (operator coefficients):")
    for m, c in amps:
        _, s = alg.sub_of(m)
        print("  %-22s rank %d  t = %+.8e" % (alg.label(m), alg.rank_of(m),
                                              c / s))
    pf = r["per_factor"]
    if not a.per_factor:
        print("\n(per-factor decomposition skipped; pass --per-factor)")
        pf = []
    n_dress = sum(1 for e in pf if e["n_dressed"])
    n_gen = sum(1 for e in pf if e["n_generated"])
    if pf:
        print("\nper-factor: %d of %d factors dress an earlier amplitude, "
              "%d generate new operators" % (n_dress, len(pf), n_gen))
    worst = sorted(pf, key=lambda e: -e["dress_l1"])[:a.top] if pf else []
    if worst:
        print("factors with the largest retroactive dressing:")
    for e in worst:
        print("  factor %4d %-18s theta %+.5f  own %+.4e  dress L1 %.3e "
              "(%d ops)  gen L1 %.3e (%d ops)"
              % (e["k"], "%s->%s" % (",".join(map(str, e["letter"][0])),
                                     ",".join(map(str, e["letter"][1]))),
                 e["theta"], e["own"] if e["own"] is not None else float("nan"),
                 e["dress_l1"], e["n_dressed"], e["gen_l1"], e["n_generated"]))
    if a.json:
        out = {"chain": os.path.basename(a.chain), "n_factors": len(word),
               "dim": basis.dim, "scalar": r["scalar"],
               "scalar_prod_cos": r["scalar_prod_cos"],
               "n_amplitudes": r["n_amplitudes"], "maxrank": r["maxrank"],
               "residual_rebuild": r["residual_rebuild"],
               "amplitudes": [{"op": alg.label(m), "rank": alg.rank_of(m),
                               "t": c / alg.sub_of(m)[1]} for m, c in T.items()],
               "per_factor": [{k: v for k, v in e.items() if k != "g"}
                              for e in pf]}
        with open(a.json, "w") as fh:
            json.dump(out, fh, indent=1)
        print("\nwrote %s" % a.json)


if __name__ == "__main__":
    main()

"""Constructive normal-ordered composer (translation stage i).

Composes a word of UCC factors into an EXACT normal-ordered operator
polynomial -- the algebraic half of the Freericks operator relation,
built constructively rather than extracted numerically.

The finiteness insight: no BCH series is ever needed. Each factor is
exactly the degree-2 polynomial

    exp(theta kappa) = I + sin(theta) kappa + (cos(theta)-1) (A Adag + Adag A),

so a word of N factors is a FINITE product of small operator
polynomials. Normal ordering (all quasiparticle creators left of all
quasiparticle annihilators, relative to a reference occupation) is
exact Wick algebra: integer signs, contractions from {a_p, a_p^dag}=1,
and coefficients that are exact integer polynomials in the variables
{s_k = sin theta_k, c_k = cos theta_k}.

Conventions (pinned to chaincompile.dets):
- An elementary op is (p, dag). Operator STRINGS are stored in MATH
  order: the leftmost op acts LAST on the ket.
- Relative to a reference occupation set `occ`, the quasiparticle
  CREATORS are {a_p^dag : p not in occ} and {a_p : p in occ}; the rest
  are quasiparticle annihilators. A normal-ordered monomial is
  (cre, ann): two tuples of elementary ops, each sorted by (p, dag),
  with all of `cre` to the left of all of `ann`.
- A for Substitution(holes, parts) follows dets.a_ops (annihilate holes
  ascending, then create parts ascending, applied first-listed-first),
  i.e. the MATH string is reversed(a_ops); Adag is the exact adjoint.
  Section-1 test: the composed operator matrix must equal the product
  of chaincompile.factors.apply_ucc_factor matrices to 1e-12.

Reference projection: acting on |ref>, every monomial with a nonempty
`ann` part vanishes, so U|ref> is read off from the cre-only monomials;
`ref_amplitudes` returns {(holes, parts): Poly} plus the vacuum
coefficient (which must equal prod_k c_k when every factor's block is
ref-active, and is checked exactly in tests).
"""
from __future__ import annotations

import numpy as np

from .dets import Substitution


# --------------------------------------------------------------------------
# exact integer polynomials in (s_1..s_N, c_1..c_N)
# --------------------------------------------------------------------------
class Poly:
    __slots__ = ("n", "terms")

    def __init__(self, n, terms=None):
        self.n = n                       # number of factors in the word
        self.terms = dict(terms or {})   # {exponent tuple (len 2n): int}

    @classmethod
    def const(cls, n, k=1):
        return cls(n, {(0,) * (2 * n): k} if k else {})

    @classmethod
    def var(cls, n, which, k):
        """which: 's' or 'c'; k: 0-based factor index."""
        e = [0] * (2 * n)
        e[k if which == "s" else n + k] = 1
        return cls(n, {tuple(e): 1})

    def __add__(self, other):
        out = dict(self.terms)
        for e, w in other.terms.items():
            out[e] = out.get(e, 0) + w
            if out[e] == 0:
                del out[e]
        return Poly(self.n, out)

    def __mul__(self, other):
        if isinstance(other, int):
            if other == 0:
                return Poly(self.n)
            return Poly(self.n, {e: w * other for e, w in self.terms.items()})
        out = {}
        for e1, w1 in self.terms.items():
            for e2, w2 in other.terms.items():
                e = tuple(a + b for a, b in zip(e1, e2))
                out[e] = out.get(e, 0) + w1 * w2
                if out[e] == 0:
                    del out[e]
        return Poly(self.n, out)

    __rmul__ = __mul__

    def is_zero(self):
        return not self.terms

    def __eq__(self, other):
        return self.n == other.n and self.terms == other.terms

    def eval(self, thetas):
        s = np.sin(thetas)
        c = np.cos(thetas)
        tot = 0.0
        for e, w in self.terms.items():
            v = float(w)
            for k in range(self.n):
                if e[k]:
                    v *= s[k] ** e[k]
                if e[self.n + k]:
                    v *= c[k] ** e[self.n + k]
            tot += v
        return tot


# --------------------------------------------------------------------------
# exact Wick normal ordering of elementary-op strings (math order)
# --------------------------------------------------------------------------
def _is_qcre(op, occ):
    p, dag = op
    return (p not in occ) if dag else (p in occ)


def normal_order(ops, occ):
    """ops: tuple of (p, dag) in MATH order. Returns
    {(cre_tuple, ann_tuple): int_sign_count} of the exact normal-ordered
    expansion (creators sorted left, annihilators sorted right)."""
    out = {}

    def emit(seq, sign):
        # seq is fully class-ordered (all q-cre left of all q-ann);
        # canonical-sort within each class with parity; kill repeats.
        kc = [op for op in seq if _is_qcre(op, occ)]
        ka = [op for op in seq if not _is_qcre(op, occ)]

        def sort_par(lst):
            lst = list(lst)
            sg, n = 1, len(lst)
            for i in range(n):
                for j in range(n - 1 - i):
                    if lst[j] > lst[j + 1]:
                        lst[j], lst[j + 1] = lst[j + 1], lst[j]
                        sg = -sg
            return tuple(lst), sg

        tc, sc = sort_par(kc)
        ta, sa = sort_par(ka)
        if len(set(tc)) != len(tc) or len(set(ta)) != len(ta):
            return
        key = (tc, ta)
        out[key] = out.get(key, 0) + sign * sc * sa
        if out[key] == 0:
            del out[key]

    def rec(seq, sign):
        for i in range(len(seq) - 1):
            x, y = seq[i], seq[i + 1]
            if (not _is_qcre(x, occ)) and _is_qcre(y, occ):
                # move the annihilator right: x y = -y x + {x, y}
                rest = seq[:i] + seq[i + 2:]
                rec(seq[:i] + (y, x) + seq[i + 2:], -sign)
                if x[0] == y[0] and x[1] != y[1]:
                    rec(rest, sign)
                return
        emit(seq, sign)

    rec(tuple(ops), 1)
    return out


# --------------------------------------------------------------------------
# operator polynomials: {(cre, ann): Poly}
# --------------------------------------------------------------------------
def _monomial_math_string(mono):
    cre, ann = mono
    return tuple(cre) + tuple(ann)


def op_mul(P1, P2, occ, n):
    """Exact product of two normal-ordered operator polynomials."""
    out = {}
    for m1, p1 in P1.items():
        s1 = _monomial_math_string(m1)
        for m2, p2 in P2.items():
            w = normal_order(s1 + _monomial_math_string(m2), occ)
            pp = p1 * p2
            for mono, sg in w.items():
                q = out.get(mono)
                r = (pp * sg) if q is None else (q + pp * sg)
                if r.is_zero():
                    out.pop(mono, None)
                else:
                    out[mono] = r
    return out


def _a_math_string(sub: Substitution):
    """A per dets.a_ops (first-listed acts first) in MATH order."""
    ops = [(i, 0) for i in sub.holes] + [(a, 1) for a in sub.parts]
    return tuple(reversed(ops))


def factor_poly(sub: Substitution, k: int, n: int, occ):
    """Exact normal-ordered polynomial of exp(theta_k kappa_sub)."""
    A = _a_math_string(sub)
    Ad = tuple((p, 1 - dag) for p, dag in reversed(A))
    s = Poly.var(n, "s", k)
    cm1 = Poly.var(n, "c", k) + Poly.const(n, -1)
    out = {((), ()): Poly.const(n, 1)}

    def acc(string, coeff):
        for mono, sg in normal_order(string, occ).items():
            q = out.get(mono)
            r = (coeff * sg) if q is None else (q + coeff * sg)
            if r.is_zero():
                out.pop(mono, None)
            else:
                out[mono] = r

    acc(A, s)
    acc(Ad, -1 * s)
    acc(A + Ad, cm1)     # A Adag  (math order: A left of Adag)
    acc(Ad + A, cm1)     # Adag A
    return out


def compose(word, occ, prune_ann=False):
    """word: [Substitution] in PREPARATION order (first applied first).
    Returns (op_poly, sizes): the exact normal-ordered operator
    polynomial and the term count after each multiplication.

    prune_ann=True keeps only creator-only monomials after every step.
    This is EXACT for the reference projection U|ref>: left-
    multiplication Wick-contracts the new factor's annihilators only
    against U's creators, so a monomial with a nonempty annihilator part
    can never later become creator-only (tested)."""
    n = len(word)
    U = {((), ()): Poly.const(n, 1)}
    sizes = []
    for k, sub in enumerate(word):
        F = factor_poly(sub, k, n, occ)
        U = op_mul(F, U, occ, n)   # later factor multiplies on the LEFT
        if prune_ann:
            U = {m: p for m, p in U.items() if not m[1]}
        sizes.append(len(U))
    return U, sizes


def compose_numeric(word, thetas, occ, prune_ann=True, tol=1e-15):
    """Same Wick algebra with coefficients evaluated at fixed thetas:
    exact for the given chain, and scalable -- the operator-monomial
    count saturates at the state support while symbolic pathway
    counting is avoided (METHOD.md section 16). Returns
    ({monomial: float}, sizes)."""
    U = {((), ()): 1.0}
    sizes = []
    for k, (sub, th) in enumerate(zip(word, thetas)):
        s, c = float(np.sin(th)), float(np.cos(th))
        A = _a_math_string(sub)
        Ad = tuple((p, 1 - d) for p, d in reversed(A))
        F = {((), ()): 1.0}
        for string, w in ((A, s), (Ad, -s),
                          (A + Ad, c - 1.0), (Ad + A, c - 1.0)):
            for mono, sg in normal_order(string, occ).items():
                F[mono] = F.get(mono, 0.0) + w * sg
        out = {}
        for m1, w1 in F.items():
            s1 = _monomial_math_string(m1)
            for m2, w2 in U.items():
                for mono, sg in normal_order(
                        s1 + _monomial_math_string(m2), occ).items():
                    if prune_ann and mono[1]:
                        continue
                    out[mono] = out.get(mono, 0.0) + w1 * w2 * sg
        U = {m: w for m, w in out.items() if abs(w) > tol}
        sizes.append(len(U))
    return U, sizes


def numeric_ref_amplitudes(U, occ):
    """Reference projection of a numeric composition: (c0,
    {(holes, parts): amplitude}) in the A|ref> sign convention."""
    c0, amps = 0.0, {}
    for (cre, ann), w in U.items():
        if ann:
            continue
        holes = tuple(sorted(q for q, d in cre if d == 0))
        parts = tuple(sorted(q for q, d in cre if d == 1))
        if not (holes or parts):
            c0 = w
            continue
        target = tuple(reversed([(i, 0) for i in holes]
                                + [(a, 1) for a in parts]))
        cur, par = list(cre), 1
        for pos, opt in enumerate(target):
            j = cur.index(opt, pos)
            while j > pos:
                cur[j], cur[j - 1] = cur[j - 1], cur[j]
                par = -par
                j -= 1
        amps[(holes, parts)] = par * w
    return c0, amps


# --------------------------------------------------------------------------
# evaluation and readout
# --------------------------------------------------------------------------
def _apply_elem(op, mask):
    p, dag = op
    occ_p = (mask >> p) & 1
    if dag:
        if occ_p:
            return None
        sign = -1 if (bin(mask & ((1 << p) - 1)).count("1") & 1) else 1
        return mask | (1 << p), sign
    if not occ_p:
        return None
    sign = -1 if (bin(mask & ((1 << p) - 1)).count("1") & 1) else 1
    return mask & ~(1 << p), sign


def apply_monomial(mono, mask):
    """Apply a normal-ordered monomial (MATH order) to a determinant."""
    m, sign = mask, 1
    for op in reversed(_monomial_math_string(mono)):
        r = _apply_elem(op, m)
        if r is None:
            return None
        m, s = r
        sign *= s
    return m, sign


def op_matrix(U, thetas, nso):
    """Dense matrix of the operator polynomial on the full Fock space of
    nso spin-orbitals (verification-scale only)."""
    dim = 1 << nso
    M = np.zeros((dim, dim))
    vals = {mono: p.eval(np.asarray(thetas, float)) for mono, p in U.items()}
    for mask in range(dim):
        for mono, v in vals.items():
            if v == 0.0:
                continue
            r = apply_monomial(mono, mask)
            if r is not None:
                M[r[0], mask] += r[1] * v
    return M


def ref_amplitudes(U, occ):
    """Project onto |ref>: cre-only monomials survive. Returns
    (c0_poly, {(holes, parts): Poly}) with holes/parts the excitation
    content relative to the reference."""
    c0 = None
    amps = {}
    for (cre, ann), p in U.items():
        if ann:
            continue
        holes = tuple(sorted(q for q, dag in cre if dag == 0))
        parts = tuple(sorted(q for q, dag in cre if dag == 1))
        # sign to match dets convention: amplitude of A(holes,parts)|ref>
        # where A = annihilate holes ascending then create parts
        # ascending. Our canonical cre ordering is (p, dag)-sorted;
        # compute the reordering parity between the two conventions.
        target = tuple(reversed([(i, 0) for i in holes]
                                + [(a, 1) for a in parts]))
        cur = list(cre)
        sg = 1
        for pos, opt in enumerate(target):
            j = cur.index(opt, pos)
            while j > pos:
                cur[j], cur[j - 1] = cur[j - 1], cur[j]
                sg = -sg
                j -= 1
        q = sg * p
        if not (holes or parts):
            c0 = p
            continue
        amps[(holes, parts)] = q
    return c0, amps

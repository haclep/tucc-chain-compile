"""Fast path (rung three, part one): Hamiltonian application without
the dense matrix, plus the Davidson iterative eigensolver.

Physics summary. Dense diagonalization builds the full dim x dim matrix
and asks for every eigenvalue -- fine to a few thousand determinants,
impossible at a million. The Davidson method never builds the matrix:
it repeatedly applies H to a small set of trial vectors and converges
only the lowest few roots, which is how large-scale CI has worked for
decades. The one ingredient it needs is a fast "apply H to a vector"
routine; here that routine walks the second-quantized terms
(one-electron h_pq and two-electron (pq|rs) strings) over the
determinant bitmasks directly, and is compiled to machine code by
numba when available.

Discipline: numba is OPTIONAL (`pip install numba`, or the
`[fast]` extra). Without it everything still runs through the same
algorithms in pure numpy/Python, slower. The compiled and pure paths
are held equal to machine precision by tests/test_fastpath.py, and the
matvec is certified against the dense builder (build_h_sector) on
committed systems.
"""
from __future__ import annotations

import numpy as np

try:  # optional dependency
    from numba import njit
    HAVE_NUMBA = True
except Exception:  # pragma: no cover
    HAVE_NUMBA = False

    def njit(*a, **k):
        def wrap(f):
            return f
        return wrap if not (len(a) == 1 and callable(a[0])) else a[0]


def status(verbose=True):
    """Report whether the compiled fast path is active. The pure-Python
    fallback is CORRECT but roughly 40x slower on kernel-bound work --
    check this before launching anything long."""
    msg = ("fast path: numba ACTIVE (compiled kernels)" if HAVE_NUMBA
           else "fast path: numba MISSING -- pure-Python fallback, "
                "~40x slower on kernel-bound work. Install with: "
                "pip install numba")
    if verbose:
        print(msg, flush=True)
    return HAVE_NUMBA


def hamiltonian_terms(h_mo, eri_mo):
    """Flatten H = sum h_pq a+_p a_q + 1/2 sum (pq|rs) a+_p a+_r a_s a_q
    (chemists' notation, spin-orbital index 2m+s) into fixed-width
    integer op strings + coefficients for the kernel. Each term is 4
    ops (p, dag); one-electron terms are padded with sentinel (-1, 0)
    in the leading slots. MATH order (leftmost acts last)."""
    nmo = h_mo.shape[0]
    ops, coef = [], []
    for m in range(nmo):
        for n in range(nmo):
            w = float(h_mo[m, n])
            if w == 0.0:
                continue
            for s in (0, 1):
                ops.append(((-1, 0), (-1, 0),
                            (2 * m + s, 1), (2 * n + s, 0)))
                coef.append(w)
    for i in range(nmo):
        for j in range(nmo):
            for k in range(nmo):
                for l_ in range(nmo):
                    w = 0.5 * float(eri_mo[i, j, k, l_])
                    if w == 0.0:
                        continue
                    for s in (0, 1):
                        for t in (0, 1):
                            ops.append(((2 * i + s, 1), (2 * k + t, 1),
                                        (2 * l_ + t, 0), (2 * j + s, 0)))
                            coef.append(w)
    return (np.array(ops, np.int64).reshape(len(ops), 4, 2),
            np.array(coef, float))


@njit(cache=True)
def _matvec_kernel(masks, order, sorted_masks, ops, coef, v, out):
    dim = masks.shape[0]
    nt = ops.shape[0]
    for col in range(dim):
        amp = v[col]
        if amp == 0.0:
            continue
        m0 = masks[col]
        for t in range(nt):
            m = m0
            sign = 1
            ok = True
            for q in range(3, -1, -1):      # apply MATH string right-first
                p = ops[t, q, 0]
                if p < 0:
                    continue
                dag = ops[t, q, 1]
                bit = (m >> p) & 1
                if dag == 1:
                    if bit == 1:
                        ok = False
                        break
                    par = 0
                    mm = m & ((np.int64(1) << p) - 1)
                    while mm:
                        par ^= 1
                        mm &= mm - 1
                    if par:
                        sign = -sign
                    m = m | (np.int64(1) << p)
                else:
                    if bit == 0:
                        ok = False
                        break
                    par = 0
                    mm = m & ((np.int64(1) << p) - 1)
                    while mm:
                        par ^= 1
                        mm &= mm - 1
                    if par:
                        sign = -sign
                    m = m & ~(np.int64(1) << p)
            if not ok:
                continue
            j = np.searchsorted(sorted_masks, m)
            if j < dim and sorted_masks[j] == m:
                out[order[j]] += sign * coef[t] * amp


class HOperator:
    """Matrix-free H over a SectorBasis: y = H @ v via the term walk.
    Also provides the diagonal (for the Davidson preconditioner) and a
    pure-Python reference path used by the equivalence tests."""

    def __init__(self, h_mo, eri_mo, basis):
        self.basis = basis
        self.masks = np.array(basis.masks, np.int64)
        self.order = np.argsort(self.masks)
        self.sorted_masks = self.masks[self.order]
        inv = np.empty_like(self.order)
        inv[self.order] = np.arange(len(self.order))
        self.order = self.order  # sorted -> basis position
        self.ops, self.coef = hamiltonian_terms(h_mo, eri_mo)
        self.dim = len(self.masks)

    def matvec(self, v, pure_python=False):
        out = np.zeros(self.dim)
        if HAVE_NUMBA and not pure_python:
            _matvec_kernel(self.masks, self.order, self.sorted_masks,
                           self.ops, self.coef, np.asarray(v, float), out)
            return out
        return self._matvec_py(v, out)

    def _matvec_py(self, v, out):
        idx = {int(m): i for i, m in enumerate(self.masks)}
        for col in range(self.dim):
            amp = float(v[col])
            if amp == 0.0:
                continue
            m0 = int(self.masks[col])
            for t in range(self.ops.shape[0]):
                m, sign, ok = m0, 1, True
                for q in range(3, -1, -1):
                    p = int(self.ops[t, q, 0])
                    if p < 0:
                        continue
                    dag = int(self.ops[t, q, 1])
                    bit = (m >> p) & 1
                    if (dag == 1 and bit) or (dag == 0 and not bit):
                        ok = False
                        break
                    if bin(m & ((1 << p) - 1)).count("1") & 1:
                        sign = -sign
                    m = (m | (1 << p)) if dag else (m & ~(1 << p))
                if ok:
                    j = idx.get(m)
                    if j is not None:
                        out[j] += sign * self.coef[t] * amp
        return out

    def diagonal(self):
        d = np.zeros(self.dim)
        for col in range(self.dim):
            e = np.zeros(self.dim)
            # cheap direct walk: apply diagonal-preserving terms only
        # exact diagonal via one pass of the python walker on unit
        # amplitudes restricted to mask-preserving terms:
        idx = {int(m): i for i, m in enumerate(self.masks)}
        for col in range(self.dim):
            m0 = int(self.masks[col])
            tot = 0.0
            for t in range(self.ops.shape[0]):
                m, sign, ok = m0, 1, True
                for q in range(3, -1, -1):
                    p = int(self.ops[t, q, 0])
                    if p < 0:
                        continue
                    dag = int(self.ops[t, q, 1])
                    bit = (m >> p) & 1
                    if (dag == 1 and bit) or (dag == 0 and not bit):
                        ok = False
                        break
                    if bin(m & ((1 << p) - 1)).count("1") & 1:
                        sign = -sign
                    m = (m | (1 << p)) if dag else (m & ~(1 << p))
                if ok and m == m0:
                    tot += sign * self.coef[t]
            d[col] = tot
        return d


def davidson(op: HOperator, nroots=1, tol=1e-9, max_iter=200,
             max_space=None, v0=None, verbose=False):
    """Davidson iteration for the lowest nroots eigenpairs of a
    matrix-free symmetric operator. Returns (evals, evecs, n_matvec)."""
    dim = op.dim
    max_space = max_space or min(dim, max(24, 12 * nroots))
    diag = op.diagonal()
    if v0 is None:
        v0 = np.zeros((dim, nroots))
        seeds = np.argsort(diag)[:nroots]
        for r, s in enumerate(seeds):
            v0[s, r] = 1.0
    V = np.linalg.qr(v0)[0]
    AV = np.column_stack([op.matvec(V[:, i]) for i in range(V.shape[1])])
    nmv = V.shape[1]
    for it in range(max_iter):
        Hs = V.T @ AV
        Hs = 0.5 * (Hs + Hs.T)
        w, U = np.linalg.eigh(Hs)
        w, U = w[:nroots], U[:, :nroots]
        X = V @ U
        AX = AV @ U
        res = AX - X * w[None, :]
        rn = np.linalg.norm(res, axis=0)
        if verbose:
            print(f"  davidson it {it}: E {w} |r| {rn}", flush=True)
        if np.all(rn < tol):
            return w, X, nmv
        if V.shape[1] >= max_space:             # thick restart on Ritz
            V, AV = X.copy(), AX.copy()
        added = 0
        for r in range(nroots):
            if rn[r] < tol:
                continue
            denom = diag - w[r]
            denom = np.where(np.abs(denom) < 1e-8,
                             np.sign(denom + 1e-30) * 1e-8, denom)
            t = -res[:, r] / denom
            # orthogonalize ONLY the newcomer (twice, for stability);
            # existing (V, AV) column pairs are never touched, so their
            # pairing can never desynchronize.
            for _ in range(2):
                t = t - V @ (V.T @ t)
            n = np.linalg.norm(t)
            if n > 1e-10:
                t = t / n
                V = np.column_stack([V, t])
                AV = np.column_stack([AV, op.matvec(t)])
                nmv += 1
                added += 1
        if added == 0:
            return w, X, nmv
    return w, X, nmv


@njit(cache=True)
def _count_and_fill(masks, order, sorted_masks, ops, coef, rows, cols,
                    vals, fill, col_lo, col_hi):
    dim = masks.shape[0]
    nt = ops.shape[0]
    n = 0
    for col in range(col_lo, col_hi):
        m0 = masks[col]
        for t in range(nt):
            m = m0
            sign = 1
            ok = True
            for q in range(3, -1, -1):
                p = ops[t, q, 0]
                if p < 0:
                    continue
                dag = ops[t, q, 1]
                bit = (m >> p) & 1
                if (dag == 1 and bit == 1) or (dag == 0 and bit == 0):
                    ok = False
                    break
                par = 0
                mm = m & ((np.int64(1) << p) - 1)
                while mm:
                    par ^= 1
                    mm &= mm - 1
                if par:
                    sign = -sign
                m = (m | (np.int64(1) << p)) if dag == 1 \
                    else (m & ~(np.int64(1) << p))
            if not ok:
                continue
            j = np.searchsorted(sorted_masks, m)
            if j < dim and sorted_masks[j] == m:
                if fill:
                    rows[n] = order[j]
                    cols[n] = col
                    vals[n] = sign * coef[t]
                n += 1
    return n


@njit(cache=True)
def _csr_matvec(indptr, indices, data, v, out):
    for i in range(indptr.shape[0] - 1):
        acc = 0.0
        for k in range(indptr[i], indptr[i + 1]):
            acc += data[k] * v[indices[k]]
        out[i] = acc


class SparseH:
    """Precomputed sparse H over a SectorBasis: the term walk runs ONCE
    to store every nonzero coupling; each subsequent application is a
    compressed-row multiply over the stored entries. Same interface as
    HOperator (matvec / diagonal / dim), plus the adjacency needed by
    the block walk and degenerate-mixture projection."""

    def __init__(self, h_mo, eri_mo, basis, chunk=2048, progress=False):
        masks = np.array(basis.masks, np.int64)
        order0 = np.argsort(masks)
        sorted_masks = masks[order0]
        ops, coef = hamiltonian_terms(h_mo, eri_mo)
        dim = len(masks)
        R, C, Vl = [], [], []
        for lo in range(0, dim, chunk):
            hi = min(dim, lo + chunk)
            n = _count_and_fill(masks, order0, sorted_masks, ops, coef,
                                np.empty(0, np.int64),
                                np.empty(0, np.int64),
                                np.empty(0), False, lo, hi)
            rows = np.empty(n, np.int64)
            cols = np.empty(n, np.int64)
            vals = np.empty(n)
            _count_and_fill(masks, order0, sorted_masks, ops, coef,
                            rows, cols, vals, True, lo, hi)
            # duplicates only ever share a source column, so per-chunk
            # deduplication is exact
            key = rows * dim + cols
            srt = np.argsort(key, kind="stable")
            key, rows, cols, vals = (key[srt], rows[srt], cols[srt],
                                     vals[srt])
            uniq, start = np.unique(key, return_index=True)
            acc = np.add.reduceat(vals, start)
            keep = np.abs(acc) > 1e-14
            R.append((uniq // dim)[keep].astype(np.int64))
            C.append((uniq % dim)[keep].astype(np.int64))
            Vl.append(acc[keep])
            if progress:
                print(f"  sparse build: {hi}/{dim} cols, "
                      f"nnz so far {sum(len(x) for x in Vl)}", flush=True)
        self.rows = np.concatenate(R)
        self.cols = np.concatenate(C)
        self.vals = np.concatenate(Vl)
        self.dim = dim
        # CSR
        o = np.argsort(self.rows, kind="stable")
        r, self.indices, self.data = \
            self.rows[o], self.cols[o], self.vals[o]
        self.indptr = np.zeros(self.dim + 1, np.int64)
        np.add.at(self.indptr, r + 1, 1)
        self.indptr = np.cumsum(self.indptr)
        self.nnz = len(self.data)

    def matvec(self, v):
        out = np.empty(self.dim)
        _csr_matvec(self.indptr, self.indices, self.data,
                    np.asarray(v, float), out)
        return out

    def diagonal(self):
        d = np.zeros(self.dim)
        on = self.rows == self.cols
        d[self.rows[on]] = self.vals[on]
        return d

    def adjacency_lists(self, thr=1e-10):
        """Neighbor lists for block walks (BFS) on |H| > thr."""
        keep = np.abs(self.data) > thr
        return self.indptr, self.indices, keep

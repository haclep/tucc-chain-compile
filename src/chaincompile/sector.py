"""Fixed-(N_up, N_dn) sector basis and dense operator builders.

Dimensions targeted here are tiny (<= a few thousand); everything is
dense numpy by design ("exact where exact is affordable"). Per-root
diagnostics carry total momentum K and <S^2> in the spirit of ADR-003
(no bare single-root references).
"""
from __future__ import annotations

from itertools import combinations

import numpy as np

from .dets import Substitution, bits, popcount


class SectorBasis:
    def __init__(self, L: int, nup: int, ndn: int):
        self.L = int(L)
        self.nup = int(nup)
        self.ndn = int(ndn)
        ups = [2 * m for m in range(L)]
        dns = [2 * m + 1 for m in range(L)]
        masks = []
        for cu in combinations(ups, nup):
            mu = 0
            for p in cu:
                mu |= 1 << p
            for cd in combinations(dns, ndn):
                md = mu
                for p in cd:
                    md |= 1 << p
                masks.append(md)
        masks.sort()
        self.masks = masks
        self.index = {m: i for i, m in enumerate(masks)}
        self.dim = len(masks)

    # ------------------------------------------------------------------
    def rank_between(self, a: int, b: int) -> int:
        """Number of electrons that differ between determinants a and b."""
        return popcount(a & ~b)

    def total_momentum(self, mask: int) -> int:
        return sum(p // 2 for p in bits(mask)) % self.L

    def basis_vector(self, mask: int) -> np.ndarray:
        v = np.zeros(self.dim)
        v[self.index[mask]] = 1.0
        return v

    # dense builders ----------------------------------------------------
    def op_matrix(self, action) -> np.ndarray:
        """Dense matrix of an operator given `action(mask) -> (mask', sign)`
        (sign 0 / mask' None when annihilated). Column = source det."""
        M = np.zeros((self.dim, self.dim))
        for j, m in enumerate(self.masks):
            m2, s = action(m)
            if m2 is not None and s != 0:
                i = self.index.get(m2)
                if i is not None:
                    M[i, j] += s
        return M

    def substitution_matrix(self, sub: Substitution) -> np.ndarray:
        return self.op_matrix(sub.apply_a)

    def generator_matrix(self, sub: Substitution) -> np.ndarray:
        """kappa = A - Adag (real antisymmetric)."""
        A = self.substitution_matrix(sub)
        return A - A.T

    # spin ---------------------------------------------------------------
    def s2_matrix(self) -> np.ndarray:
        """S^2 restricted to this sector: S^2 = S- S+ + Sz (Sz + 1)."""
        sz = 0.5 * (self.nup - self.ndn)
        S2 = sz * (sz + 1.0) * np.eye(self.dim)
        if self.ndn >= 1 and self.nup < self.L:
            target = SectorBasis(self.L, self.nup + 1, self.ndn - 1)
            M = np.zeros((target.dim, self.dim))
            from .dets import apply_ops

            for j, m in enumerate(self.masks):
                for orb in range(self.L):
                    m2, s = apply_ops(m, [("c", 2 * orb + 1), ("cd", 2 * orb)])
                    if m2 is not None and s != 0:
                        M[target.index[m2], j] += s
            S2 = S2 + M.T @ M
        return S2

    # pretty --------------------------------------------------------------
    def det_label(self, mask: int) -> str:
        occ = []
        for p in bits(mask):
            occ.append(f"{p // 2}{'u' if p % 2 == 0 else 'd'}")
        return "|" + " ".join(occ) + ">"


def _block_arrays(self, sub):
    """Cached (i_low, i_up, sign) index arrays for the 2x2 blocks of `sub`.

    The Gauss-Newton solve applies the same few hundred factors thousands
    of times; caching + fancy indexing makes that vectorized.
    """
    cache = getattr(self, "_block_cache", None)
    if cache is None:
        cache = self._block_cache = {}
    hit = cache.get(sub)
    if hit is not None:
        return hit
    ii, jj, ss = [], [], []
    for i, m in enumerate(self.masks):
        if sub.is_lower(m):
            up, s = sub.apply_a(m)
            j = self.index.get(up)
            if j is not None and s != 0:
                ii.append(i)
                jj.append(j)
                ss.append(s)
    import numpy as _np

    arrs = (
        _np.asarray(ii, dtype=_np.intp),
        _np.asarray(jj, dtype=_np.intp),
        _np.asarray(ss, dtype=float),
    )
    cache[sub] = arrs
    return arrs


SectorBasis.block_arrays = _block_arrays

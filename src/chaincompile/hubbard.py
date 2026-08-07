"""Momentum-space Hubbard model on an L-site ring (the P2 setting).

H = sum_{k,sigma} eps_k n_{k sigma}
  + (U/L) sum_{k1,k2,q} cdag_{k1+q,up} cdag_{k2-q,dn} c_{k2,dn} c_{k1,up}

eps_k = -2 t cos(2 pi k / L), momenta k = 0..L-1 (units of 2 pi / L).
Total momentum K = sum of occupied k modulo L is conserved; the builder
is verified Hermitian and K-block-diagonal in tests.
"""
from __future__ import annotations

import numpy as np

from .dets import annihilate, apply_ops, bits, create
from .sector import SectorBasis


def eps(m: int, L: int, t: float = 1.0) -> float:
    return -2.0 * t * np.cos(2.0 * np.pi * m / L)


def hamiltonian(basis: SectorBasis, U: float, t: float = 1.0) -> np.ndarray:
    L = basis.L
    dim = basis.dim
    H = np.zeros((dim, dim))
    # kinetic (diagonal)
    for j, m in enumerate(basis.masks):
        H[j, j] += sum(eps(p // 2, L, t) for p in bits(m))
    # interaction
    pref = U / L
    for j, m in enumerate(basis.masks):
        ups = [p // 2 for p in bits(m) if p % 2 == 0]
        dns = [p // 2 for p in bits(m) if p % 2 == 1]
        for k1 in ups:
            for k2 in dns:
                for q in range(L):
                    k1p = (k1 + q) % L
                    k2p = (k2 - q) % L
                    ops = [
                        ("c", 2 * k1),
                        ("c", 2 * k2 + 1),
                        ("cd", 2 * k2p + 1),
                        ("cd", 2 * k1p),
                    ]
                    m2, s = apply_ops(m, ops)
                    if m2 is not None and s != 0:
                        H[basis.index[m2], j] += pref * s
    return H


def fermi_sea_mask(L: int, nup: int, ndn: int, t: float = 1.0):
    """Fill the lowest-eps momenta per spin (deterministic tie-break by k).

    Returns (mask, degenerate_flag). degenerate_flag is True when the
    highest filled level is degenerate with the lowest empty one for
    either spin (open-shell Fermi sea, e.g. L=4 half filling).
    """
    order = sorted(range(L), key=lambda m: (eps(m, L, t), m))
    degenerate = False
    mask = 0
    for n, spin in ((nup, 0), (ndn, 1)):
        for m in order[:n]:
            mask |= 1 << (2 * m + spin)
        if 0 < n < L:
            if abs(eps(order[n - 1], L, t) - eps(order[n], L, t)) < 1e-12:
                degenerate = True
    return mask, degenerate

"""Hydrogen-systems scaling: 6-31G anchor, identities, rank-cost law,
and off-lattice direct compiles with fill-in."""
import numpy as np

from chaincompile.compile import compile_chain
from chaincompile.dets import Substitution
from chaincompile.molecular import (build_h_sector, hydrogen_integrals,
                                    mo_integrals, rhf)
from chaincompile.sector import SectorBasis
from chaincompile import normalorder as NO


def test_h2_631g_anchor_and_identity():
    cent = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.4]])
    S, T, V, ERI, enuc = hydrogen_integrals(cent, "6-31g")
    C, eps, e_el, conv = rhf(S, T + V, ERI, 1)
    assert conv
    e_rhf = e_el + enuc
    assert abs(e_rhf - (-1.126743)) < 1e-4
    h, e = mo_integrals(C, T + V, ERI)
    b = SectorBasis(4, 1, 1)
    H = build_h_sector(h, e, b)
    w = np.linalg.eigh(H)[0]
    assert abs(w[0] + enuc - (-1.151679)) < 1e-4
    i = b.index[0b11]
    assert abs(H[i, i] + enuc - e_rhf) < 1e-10


def test_factor_rank_cost_law():
    occ = frozenset(range(6))
    for r, sub in ((1, Substitution((0,), (6,))),
                   (2, Substitution((0, 1), (6, 7))),
                   (3, Substitution((0, 1, 2), (6, 7, 8)))):
        assert len(NO.factor_poly(sub, 0, 1, occ)) == 4 ** r + 2


def test_h6_ring_direct_exact_with_fill_in():
    R = 1.9
    cent = np.array([[np.cos(2*np.pi*k/6), np.sin(2*np.pi*k/6), 0.0]
                     for k in range(6)]) * (R / (2*np.sin(np.pi/6)))
    S, T, V, ERI, enuc = hydrogen_integrals(cent, "sto-3g")
    C, eps, e_el, conv = rhf(S, T + V, ERI, 3, damp=0.3)
    assert conv
    h, e = mo_integrals(C, T + V, ERI)
    sb = SectorBasis(6, 3, 3)
    H = build_h_sector(h, e, sb)
    i = sb.index[0b111111]
    assert abs(H[i, i] + enuc - (e_el + enuc)) < 1e-10
    w, Vv = np.linalg.eigh(H)
    v0 = Vv[:, 0]
    res = compile_chain(v0, sb, mode="direct")
    assert res.final_residual < 1e-12
    sup = int(np.sum(np.abs(v0) > np.sqrt(1e-12) / sb.dim))
    assert res.length > sup  # fill-in is real off-lattice

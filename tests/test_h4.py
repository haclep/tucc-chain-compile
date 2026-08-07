"""H4 molecular validation: literature anchor, the integrals-to-H
certification identity, and the full compile + constructive-translation
stack off-lattice."""
import numpy as np

from chaincompile.compile import compile_chain, prepare_state
from chaincompile.dets import Substitution
from chaincompile.molecular import (build_h_sector, h4_integrals,
                                    mo_integrals, rhf)
from chaincompile.sector import SectorBasis
from chaincompile import disentangle as dz
from chaincompile import normalorder as NO


def _h2():
    cent = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.4]])
    S, T, V, ERI, enuc = h4_integrals(cent)
    C, eps, e_el, conv = rhf(S, T + V, ERI, 1)
    h_mo, eri_mo = mo_integrals(C, T + V, ERI)
    b = SectorBasis(2, 1, 1)
    H = build_h_sector(h_mo, eri_mo, b)
    return b, H, enuc, e_el + enuc, conv


def test_h2_literature_anchor_and_identity():
    b, H, enuc, e_rhf, conv = _h2()
    assert conv
    assert abs(e_rhf - (-1.116714)) < 1e-4      # Szabo-Ostlund values
    w = np.linalg.eigh(H)[0]
    assert abs(w[0] + enuc - (-1.137276)) < 1e-4
    i = b.index[0b11]
    assert abs(H[i, i] + enuc - e_rhf) < 1e-10  # <HF|H|HF> = E_RHF
    assert float(np.max(np.abs(H - H.T))) < 1e-12


def _h4_rect():
    cent = np.array([[0, 0, 0], [2.0, 0, 0], [0, 2.5, 0], [2.0, 2.5, 0]],
                    float)
    S, T, V, ERI, enuc = h4_integrals(cent)
    C, eps, e_el, conv = rhf(S, T + V, ERI, 2, damp=0.2)
    assert conv
    h_mo, eri_mo = mo_integrals(C, T + V, ERI)
    basis = SectorBasis(4, 2, 2)
    H = build_h_sector(h_mo, eri_mo, basis)
    w, V_ = np.linalg.eigh(H)
    i = basis.index[0b1111]
    assert abs(H[i, i] + enuc - (e_el + enuc)) < 1e-10
    return basis, V_[:, 0]


def test_h4_compile_and_translate_off_lattice():
    basis, v0 = _h4_rect()
    S2 = basis.s2_matrix()
    assert abs(float(v0 @ S2 @ v0)) < 1e-8      # singlet ground state
    for mode in ("sd_routed", "direct", "sd_paired"):
        res = compile_chain(v0, basis, mode=mode)
        assert res.final_residual < 1e-12
        assert res.max_abs_theta() < np.pi / 2
        if mode != "direct":
            assert all(s.rank <= 2 for s, _ in res.selected())
        psi = prepare_state(res, basis)
        assert abs(abs(float(res.target @ psi))
                   - res.ledger[-1].fid_after) < 1e-9
        # constructive translation acceptance
        word = [s for s, _ in res.selected()]
        th = [t for _, t in res.selected()]
        occ = frozenset(p for p in range(8) if (res.pivot_mask >> p) & 1)
        U, _ = NO.compose_numeric(word, th, occ)
        c0, amps = NO.numeric_ref_amplitudes(U, occ)
        ref = tuple(sorted(occ))
        state = {ref: 1.0}
        for sub, t in zip(word, th):
            state = dz.apply_factor(sub, float(t), state, tol=0.0)
        dev = abs(c0 - state.get(ref, 0.0))
        for (h, p), w_ in amps.items():
            det, sg = dz.apply_A(Substitution(h, p), ref)
            dev = max(dev, abs(w_ - sg * state.get(det, 0.0)))
        assert dev < 1e-12, (mode, dev)

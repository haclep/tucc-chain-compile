"""Round-trip certification of the integral-dump contract using the
self-contained integrals: save -> load -> build -> identity."""
import numpy as np

from chaincompile.molecular import (build_h_sector, hydrogen_integrals,
                                    load_integral_dump, mo_integrals, rhf,
                                    save_integral_dump)
from chaincompile.sector import SectorBasis


def test_dump_roundtrip_identity(tmp_path):
    cent = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.4]])
    S, T, V, ERI, enuc = hydrogen_integrals(cent, "6-31g")
    C, eps, e_el, conv = rhf(S, T + V, ERI, 1)
    h_mo, eri_mo = mo_integrals(C, T + V, ERI)
    path = tmp_path / "h2_631g.npz"
    save_integral_dump(path, h_mo, eri_mo, enuc, e_el + enuc, 1, 1,
                       basis="6-31g", molecule="H2", source="selftest")
    h2, e2, en2, escf2, na, nb, meta = load_integral_dump(path)
    assert np.array_equal(h2, h_mo) and np.array_equal(e2, eri_mo)
    assert (na, nb) == (1, 1) and str(meta["molecule"]) == "H2"
    b = SectorBasis(h2.shape[0], na, nb)
    H = build_h_sector(h2, e2, b)
    i = b.index[0b11]
    assert abs(H[i, i] + en2 - escf2) < 1e-10


def test_freeze_core_identity(tmp_path):
    """Freezing occupied RHF orbitals must preserve the certification
    identity exactly: <HF_act|H_act|HF_act> + E_core + E_nuc = E_RHF."""
    from chaincompile.molecular import freeze_core

    cent = np.array([[0, 0, 0], [2.0, 0, 0], [0, 2.5, 0], [2.0, 2.5, 0]],
                    float)
    S, T, V, ERI, enuc = hydrogen_integrals(cent, "6-31g")
    C, eps, e_el, conv = rhf(S, T + V, ERI, 2, damp=0.2)
    h_mo, eri_mo = mo_integrals(C, T + V, ERI)
    e_rhf = e_el + enuc
    for k in (0, 1):
        h_a, eri_a, e_core = freeze_core(h_mo, eri_mo, k)
        b = SectorBasis(h_a.shape[0], 2 - k, 2 - k)
        H = build_h_sector(h_a, eri_a, b)
        hf = 0
        for i in range(2 - k):
            hf |= (1 << (2 * i)) | (1 << (2 * i + 1))
        i = b.index[hf]
        assert abs(H[i, i] + e_core + enuc - e_rhf) < 1e-10, k


def test_dominant_block_projection_degenerate_pair():
    """A mixed degenerate pair spanning two momentum blocks must be
    detected and projected back to a symmetry-pure exact eigenvector."""
    from chaincompile.hubbard import hamiltonian
    from chaincompile.molecular import dominant_block_projection

    b = SectorBasis(6, 3, 3)
    H = hamiltonian(b, U=6.0)
    w, V = np.linalg.eigh(H)
    i = next(k for k in range(1, 20) if abs(w[k + 1] - w[k]) < 1e-9)
    vm = (V[:, i] + V[:, i + 1]) / np.sqrt(2.0)
    vp, blk, mixed = dominant_block_projection(vm, H)
    assert mixed
    assert abs(np.linalg.norm(vp) - 1.0) < 1e-12
    assert np.linalg.norm(H @ vp - w[i] * vp) < 1e-8   # still exact
    v0p, _, m0 = dominant_block_projection(V[:, 0], H)
    assert not m0 and np.array_equal(v0p, V[:, 0])

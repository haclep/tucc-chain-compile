import numpy as np
import pytest

from chaincompile.compile import compile_chain, prepare_state
from chaincompile.hubbard import fermi_sea_mask, hamiltonian
from chaincompile.sector import SectorBasis


def _gs(L, U):
    basis = SectorBasis(L=L, nup=L // 2, ndn=L // 2)
    H = hamiltonian(basis, U=U)
    assert np.allclose(H, H.T, atol=1e-12)
    evals, evecs = np.linalg.eigh(H)
    return basis, H, evals, evecs


def test_hamiltonian_conserves_momentum():
    basis, H, _, _ = _gs(4, 3.0)
    for j, m in enumerate(basis.masks):
        for i in np.nonzero(np.abs(H[:, j]) > 1e-12)[0]:
            assert basis.total_momentum(basis.masks[i]) == basis.total_momentum(m)


@pytest.mark.parametrize("L,U,mode", [(4, 8.0, "sd_routed"), (4, 8.0, "direct"),
                                      (6, 2.0, "sd_routed"), (6, 6.0, "sd_routed"),
                                      (6, 6.0, "direct")])
def test_compile_exact_and_ledger_theorem(L, U, mode):
    basis, H, evals, evecs = _gs(L, U)
    target = evecs[:, 0]
    res = compile_chain(target, basis, mode=mode)
    assert res.final_residual < 1e-10

    tgt = res.target
    # full reconstruction
    psi = prepare_state(res, basis)
    assert abs(abs(tgt @ psi) - 1.0) < 1e-9

    # ledger IS the truncation curve (three prefixes)
    for K in {1, max(1, res.length // 2), res.length}:
        psiK = prepare_state(res, basis, K)
        fid = abs(tgt @ psiK)
        assert abs(fid - res.ledger[K - 1].fid_after) < 1e-9

    # angle bound (CC-translatability)
    assert res.max_abs_theta() < np.pi / 2

    if mode == "sd_routed":
        assert all(sub.rank <= 2 for sub, _ in res.selected())


def test_excited_root_with_reref_pivot():
    basis, H, evals, evecs = _gs(6, 6.0)
    target = evecs[:, 1]
    res = compile_chain(target, basis, mode="sd_routed")
    assert res.final_residual < 1e-10
    psi = prepare_state(res, basis)
    assert abs(abs(res.target @ psi) - 1.0) < 1e-9


def test_open_shell_fermi_sea_flagged():
    _, deg = fermi_sea_mask(4, 2, 2)
    assert deg is True
    _, deg6 = fermi_sea_mask(6, 3, 3)
    assert deg6 is False


def test_endpoint_singlet_purity():
    """Singlet targets must compile to singlet endpoints in BOTH modes;
    interior prefixes are allowed (and measured) to spin-contaminate."""
    from chaincompile.diagnostics import prefix_s2_curve

    basis = SectorBasis(4, 2, 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=8.0))
    for mode in ("sd_routed", "direct"):
        res = compile_chain(evecs[:, 0], basis, mode=mode)
        curve = prefix_s2_curve(res, basis)
        assert abs(curve[-1][2]) < 1e-6, (mode, curve[-1])

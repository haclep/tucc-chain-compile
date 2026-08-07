"""sd_paired mode contracts: exactness, primitive rank<=2 letters,
bounded angles, ledger consistency, endpoint spin purity, ablated
routing (no forced overlap on L4), and letter-multiset determinism."""
import numpy as np

from chaincompile.compile import compile_chain, prepare_state
from chaincompile.hubbard import hamiltonian
from chaincompile.sector import SectorBasis


def _res():
    basis = SectorBasis(4, 2, 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=8.0))
    return basis, evecs[:, 0]


def test_paired_exact_and_bounded():
    basis, v = _res()
    res = compile_chain(v, basis, mode="sd_paired")
    assert res.final_residual < 1e-12
    assert all(sub.rank <= 2 for sub, _ in res.selected())
    assert res.max_abs_theta() < np.pi / 2
    psi = prepare_state(res, basis)
    assert abs(abs(float(res.target @ psi)) - res.ledger[-1].fid_after) < 1e-9
    assert res.solver_info["forced_overlap"] == 0


def test_paired_endpoint_singlet():
    basis, v = _res()
    res = compile_chain(v, basis, mode="sd_paired")
    psi = prepare_state(res, basis)
    S2 = basis.s2_matrix()
    assert abs(float(psi @ S2 @ psi)) < 1e-6


def test_paired_multiset_noise_stable():
    basis, v = _res()
    ref = compile_chain(v, basis, mode="sd_paired")
    rng = np.random.default_rng(5)
    vn = v + 1e-13 * rng.standard_normal(v.shape)
    vn /= np.linalg.norm(vn)
    r = compile_chain(vn, basis, mode="sd_paired")
    assert r.pivot_mask == ref.pivot_mask
    key = lambda res: sorted((s.holes, s.parts) for s, _ in res.selected())
    assert key(r) == key(ref)
    assert r.final_residual < 1e-12

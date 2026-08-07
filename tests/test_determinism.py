"""Platform-determinism regressions: the compiled chain must be invariant
under the perturbations that distinguish one machine's eigh output from
another's -- a global sign flip, and amplitude noise far above BLAS
rounding but far below the canonical tie tolerance."""
import numpy as np

from chaincompile.compile import compile_chain
from chaincompile.hubbard import hamiltonian
from chaincompile.sector import SectorBasis


def _structure(res):
    return [(s.holes, s.parts) for s, _ in res.selected()]


def _angles(res):
    return np.array([t for _, t in res.selected()])


def test_chain_invariant_under_global_sign():
    basis = SectorBasis(4, 2, 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=8.0))
    r1 = compile_chain(evecs[:, 0], basis, mode="sd_routed")
    r2 = compile_chain(-evecs[:, 0], basis, mode="sd_routed")
    assert r1.pivot_mask == r2.pivot_mask
    assert _structure(r1) == _structure(r2)
    assert np.allclose(_angles(r1), _angles(r2), atol=1e-10)


def test_chain_robust_to_eigensolver_noise():
    """1e-13 amplitude noise models cross-BLAS eigenvector differences
    (~1e-16) with two orders of margin. Guarantee scope (METHOD sec 13):
    every DISCRETE choice is canonical -- pivot and the exact multiset
    of letters are invariant, and the compile stays exact. The ORDER of
    growth letters is canonical only up to symmetry-equivalent
    Gauss-Newton basins: near a symmetric stall the continuous
    trajectory may land in either of two symmetry-related basins, which
    legitimately swaps symmetry-partner growth letters (first observed
    on a Windows/OpenBLAS run while Linux/OpenBLAS did not swap)."""
    basis = SectorBasis(4, 2, 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=8.0))
    v = evecs[:, 0]
    ref = compile_chain(v, basis, mode="sd_routed")
    for seed in (7, 11, 13):
        rng = np.random.default_rng(seed)
        vn = v + 1e-13 * rng.standard_normal(v.shape)
        vn /= np.linalg.norm(vn)
        r = compile_chain(vn, basis, mode="sd_routed")
        assert r.pivot_mask == ref.pivot_mask
        assert sorted(_structure(r)) == sorted(_structure(ref))
        assert len(_structure(r)) == len(_structure(ref))
        assert r.final_residual < 1e-12


def test_direct_mode_robust_to_noise():
    basis = SectorBasis(4, 2, 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=8.0))
    v = evecs[:, 0]
    ref = compile_chain(v, basis, mode="direct")
    rng = np.random.default_rng(3)
    vn = v + 1e-13 * rng.standard_normal(v.shape)
    vn /= np.linalg.norm(vn)
    r = compile_chain(vn, basis, mode="direct")
    assert r.pivot_mask == ref.pivot_mask
    assert _structure(r) == _structure(ref)


def test_degenerate_roots_symmetry_resolved():
    """The L6 U6 degenerate pair (roots 3/4) must come out of
    roots_table with pure integer K labels regardless of the arbitrary
    eigh basis inside the cluster."""
    from chaincompile.diagnostics import roots_table

    basis = SectorBasis(6, 3, 3)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=6.0))
    rows = roots_table(evals, evecs, basis, basis.s2_matrix(), nroots=6)
    assert abs(evals[3] - evals[4]) < 1e-9  # the cluster this test is about
    for row in rows:
        assert "," not in row["K"], row  # every root carries a pure K label

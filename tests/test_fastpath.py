"""Fast-path equivalence gates: the compiled and pure H-application
must match the dense builder to machine precision, and Davidson must
reproduce dense diagonalization."""
import numpy as np

from chaincompile.fastpath import HOperator, davidson
from chaincompile.molecular import (build_h_sector, hydrogen_integrals,
                                    mo_integrals, rhf)
from chaincompile.sector import SectorBasis


def _system(cent, basis_name, ndocc, nmo, damp=0.0):
    S, T, V, ERI, enuc = hydrogen_integrals(cent, basis_name)
    C, eps, e_el, conv = rhf(S, T + V, ERI, ndocc, damp=damp)
    h, e = mo_integrals(C, T + V, ERI)
    sb = SectorBasis(nmo, ndocc, ndocc)
    return sb, h, e


def test_matvec_matches_dense_both_paths():
    cent = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.4]])
    sb, h, e = _system(cent, "6-31g", 1, 4)
    Hd = build_h_sector(h, e, sb)
    op = HOperator(h, e, sb)
    v = np.random.default_rng(1).standard_normal(sb.dim)
    ref = Hd @ v
    assert float(np.max(np.abs(op.matvec(v) - ref))) < 1e-12
    assert float(np.max(np.abs(op.matvec(v, pure_python=True) - ref))) \
        < 1e-12
    assert float(np.max(np.abs(op.diagonal() - np.diag(Hd)))) < 1e-12


def test_davidson_matches_dense_h6():
    R = 1.9
    cent = np.array([[np.cos(2 * np.pi * k / 6),
                      np.sin(2 * np.pi * k / 6), 0.0]
                     for k in range(6)]) * (R / (2 * np.sin(np.pi / 6)))
    sb, h, e = _system(cent, "sto-3g", 3, 6, damp=0.3)
    Hd = build_h_sector(h, e, sb)
    op = HOperator(h, e, sb)
    w_ref = np.linalg.eigh(Hd)[0][:2]
    w, X, nmv = davidson(op, nroots=2, tol=1e-9)
    assert float(np.max(np.abs(w - w_ref))) < 1e-9
    for r in range(2):
        assert np.linalg.norm(op.matvec(X[:, r]) - w[r] * X[:, r]) < 1e-7


def test_sparse_matches_dense_and_davidson():
    from chaincompile.fastpath import SparseH

    cent = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.4]])
    sb, h, e = _system(cent, "6-31g", 1, 4)
    Hd = build_h_sector(h, e, sb)
    sp = SparseH(h, e, sb, chunk=7)   # force multi-chunk path
    v = np.random.default_rng(2).standard_normal(sb.dim)
    assert float(np.max(np.abs(sp.matvec(v) - Hd @ v))) < 1e-12
    assert float(np.max(np.abs(sp.diagonal() - np.diag(Hd)))) < 1e-12
    w, X, nmv = davidson(sp, nroots=2, tol=1e-10)
    w_ref = np.linalg.eigh(Hd)[0][:2]
    assert float(np.max(np.abs(w - w_ref))) < 1e-9


def test_resumable_solver_mirrors_compile_chain():
    """With no deadline and mirror_exact, the resumable loop must
    reproduce compile_chain's sd_routed result to machine precision."""
    import importlib.util
    import os
    spec = importlib.util.spec_from_file_location(
        "run_big_sd", os.path.join(os.path.dirname(__file__), "..",
                                   "examples", "run_big_sd.py"))
    big = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(big)

    from chaincompile.compile import _normalize_target, compile_chain
    from chaincompile.hubbard import hamiltonian

    basis = SectorBasis(4, 2, 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=8.0))
    ref = compile_chain(evecs[:, 0], basis, mode="sd_routed")
    ct, pivot_mask, p = _normalize_target(evecs[:, 0], basis, None)
    state = {"phase": "route", "support_tol": 1e-10}
    big.solve_resumable(ct, basis, pivot_mask, state, float("inf"),
                        mirror_exact=True, log=lambda *a, **k: None)
    assert pivot_mask == ref.pivot_mask
    word = [s for s, _, _ in state["seq"]]
    ref_word = [s for s, _ in ref.selected()]
    assert word == ref_word
    ref_th = np.array([t for _, t in ref.selected()])
    assert np.allclose(state["thetas"], ref_th, atol=1e-10)
    assert state["residual"] <= 1e-12

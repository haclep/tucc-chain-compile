import numpy as np

from chaincompile.compile import compile_chain, prepare_state
from chaincompile.hubbard import hamiltonian
from chaincompile.sector import SectorBasis
from chaincompile.translate import (
    build_T,
    cluster_analysis,
    exp_apply,
    sd_truncation_report,
)


def _setup(L=6, U=6.0):
    basis = SectorBasis(L=L, nup=L // 2, ndn=L // 2)
    H = hamiltonian(basis, U=U)
    evals, evecs = np.linalg.eigh(H)
    res = compile_chain(evecs[:, 0], basis, mode="sd_routed")
    psi = prepare_state(res, basis)
    return basis, H, evals, res, psi


def test_cluster_analysis_rebuild():
    basis, H, evals, res, psi = _setup()
    t_amps, T, maxrank, err = cluster_analysis(psi, basis, res.pivot_mask)
    assert err < 1e-10
    # explicit rebuild through build_T
    T2 = build_T(t_amps, basis, res.pivot_mask)
    p = basis.index[res.pivot_mask]
    v = exp_apply(T2, basis.basis_vector(res.pivot_mask), maxpow=maxrank + 1)
    ctil = psi / psi[p]
    assert np.linalg.norm(v - ctil) < 1e-10


def test_full_rank_energy_matches_exact():
    basis, H, evals, res, psi = _setup()
    rep = sd_truncation_report(psi, basis, res.pivot_mask, H)
    assert abs(rep["E_chain"] - evals[0]) < 1e-8
    # SD-truncated state is a genuine (distorted) approximation
    assert 0.0 < rep["fidelity_sd"] <= 1.0 + 1e-12
    assert rep["E_sd"] >= evals[0] - 1e-9  # variational

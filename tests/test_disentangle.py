"""Stage-1 certification tests: independent kernel, chain-JSON consumer,
and the secant-dressing law (exact on two-factor probes by theory)."""
import json
import math

import numpy as np

from chaincompile.compile import compile_chain, prepare_state
from chaincompile.dets import Substitution
from chaincompile.hubbard import hamiltonian
from chaincompile.sector import SectorBasis
from chaincompile.translate import cluster_analysis
from chaincompile import disentangle as dz


def test_two_factor_closed_forms():
    ta, tb = 0.31, 0.22
    # shared occupied 0: earlier letter dressed by sec(tb), later undressed
    st = dz.state_from_chain(
        [(Substitution((0,), (2,)), ta), (Substitution((0,), (3,)), tb)],
        (0, 1))
    psi0 = st[(0, 1)]
    sA = dz.apply_A(Substitution((0,), (2,)), (0, 1))[1]
    sB = dz.apply_A(Substitution((0,), (3,)), (0, 1))[1]
    assert abs(st[(1, 2)] / (sA * psi0) - math.tan(ta) / math.cos(tb)) < 1e-12
    assert abs(st[(1, 3)] / (sB * psi0) - math.tan(tb)) < 1e-12
    # shared virtual {4,5}: same secant dressing (the any-orbital topology)
    A, B = Substitution((0, 1), (4, 5)), Substitution((2, 3), (4, 5))
    st = dz.state_from_chain([(A, ta), (B, tb)], (0, 1, 2, 3))
    psi0 = st[(0, 1, 2, 3)]
    sA = dz.apply_A(A, (0, 1, 2, 3))[1]
    assert abs(st[(2, 3, 4, 5)] / (sA * psi0)
               - math.tan(ta) / math.cos(tb)) < 1e-12


def test_kernel_certifies_l4_chain():
    basis = SectorBasis(4, 2, 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=8.0))
    res = compile_chain(evecs[:, 0], basis, mode="sd_routed")
    pivot = tuple(i for i in range(16) if (res.pivot_mask >> i) & 1)
    v_vec = prepare_state(res, basis)
    v_ker = dz.state_dict_to_vector(
        dz.state_from_chain(res.selected(), pivot), basis)
    assert float(np.max(np.abs(v_vec - v_ker))) < 1e-12      # C1
    assert 1.0 - abs(float(evecs[:, 0] @ v_ker)) < 1e-12     # C2


def test_chain_json_loader_roundtrip(tmp_path):
    doc = {
        "schema": "chaincompile.chain.v0",
        "pivot_determinant": "|0u 0d 1u 1d>",
        "global_sign": 1,
        "steps": [
            {"step": 1, "holes": [2, 3], "parts": [8, 9], "theta": 0.25},
            {"step": 2, "holes": [0, 1], "parts": [4, 5], "theta": -0.5},
        ],
    }
    path = tmp_path / "chain.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    pivot, steps, meta = dz.load_chain_json(path)
    assert pivot == (0, 1, 2, 3)
    assert steps[0][0] == Substitution((2, 3), (8, 9))
    assert abs(steps[1][1] + 0.5) < 1e-15
    assert meta["global_sign"] == 1


def test_dressing_report_invariants():
    basis = SectorBasis(4, 2, 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=8.0))
    res = compile_chain(evecs[:, 0], basis, mode="sd_routed")
    pivot = tuple(i for i in range(16) if (res.pivot_mask >> i) & 1)
    t_amps, _, _, err = cluster_analysis(evecs[:, 0], basis, res.pivot_mask)
    assert err < 1e-10
    rows, summ = dz.secant_dressing_report(res.selected(), t_amps, pivot)
    # sd chains have rank<=2 letters only: T2 fully covered, T4 fully folded
    assert summ["coverage_by_rank"][2] > 0.999
    assert summ["coverage_by_rank"].get(4, 0.0) == 0.0
    assert summ["n_scored"] > 0
    assert all(("t_pred" in r and "t_pred_all" in r) for r in rows)

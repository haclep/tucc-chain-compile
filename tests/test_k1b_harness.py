"""K1b-T4 harness knobs on the L=4 Hubbard miniature (dim 36).

Checks (all against the certified mirror of `_compile_sd`):
  1. defaults unchanged: solve_resumable with no knobs still mirrors
     compile_chain (the existing test_fastpath guarantee, re-asserted);
  2. stop_after_greedy halts at phase 'joint' with nothing solved;
  3. a known-answer seed (the certified chain's grown letters and
     angles appended after the routed chain, routed angles from the
     certified chain) reaches the gate with at most one GN iteration;
  4. the harness's round-robin ordering never places identical letters
     adjacently.
"""
import importlib.util
import os

import numpy as np

from chaincompile.compile import _normalize_target, compile_chain
from chaincompile.dets import Substitution
from chaincompile.hubbard import hamiltonian
from chaincompile.sector import SectorBasis

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _target():
    basis = SectorBasis(4, 2, 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=8.0))
    ref = compile_chain(evecs[:, 0], basis, mode="sd_routed")
    ct, pivot_mask, _ = _normalize_target(evecs[:, 0], basis, None)
    return basis, ref, ct, pivot_mask


def test_defaults_still_mirror_compile_chain():
    big = _load("run_big_sd", os.path.join("examples", "run_big_sd.py"))
    basis, ref, ct, pivot_mask = _target()
    state = {"phase": "route", "support_tol": 1e-10}
    big.solve_resumable(ct, basis, pivot_mask, state, float("inf"),
                        mirror_exact=True, log=lambda *a, **k: None)
    assert [s for s, _, _ in state["seq"]] == [s for s, _ in ref.selected()]
    assert state["residual"] <= 1e-12


def test_stop_after_greedy_halts_at_joint():
    big = _load("run_big_sd", os.path.join("examples", "run_big_sd.py"))
    basis, ref, ct, pivot_mask = _target()
    state = {"phase": "route", "support_tol": 1e-10}
    done = big.solve_resumable(ct, basis, pivot_mask, state, float("inf"),
                               log=lambda *a, **k: None,
                               stop_after_greedy=True)
    assert done is False and state["phase"] == "joint"
    assert len(state["thetas"]) == len(state["seq"]) == state["routed"]
    assert "grown" not in state


def test_known_answer_seed_reaches_gate_immediately():
    big = _load("run_big_sd", os.path.join("examples", "run_big_sd.py"))
    basis, ref, ct, pivot_mask = _target()
    letters = [s for s, _ in ref.selected()]
    thetas = np.array([t for _, t in ref.selected()])
    state = {"phase": "route", "support_tol": 1e-10}
    big.solve_resumable(ct, basis, pivot_mask, state, float("inf"),
                        log=lambda *a, **k: None, stop_after_greedy=True)
    n_routed = len(state["seq"])
    assert [s for s, _, _ in state["seq"]] == letters[:n_routed]
    state["thetas"] = thetas[:n_routed].copy()
    for s, t in zip(letters[n_routed:], thetas[n_routed:]):
        state["seq"].append((Substitution(s.holes, s.parts), None, None))
    state["thetas"] = np.concatenate([state["thetas"], thetas[n_routed:]])
    big.solve_resumable(ct, basis, pivot_mask, state, float("inf"),
                        log=lambda *a, **k: None, plateau=0.01)
    assert state["phase"] == "noc"
    assert state["residual"] <= 1e-12
    assert state.get("grown", 0) == 0 and state.get("round", 0) == 0


def test_round_robin_never_adjacent():
    hz = _load("k1b_warmstart", "k1b_warmstart.py")
    letters = [((0,), (2,))] * 3 + [((1,), (3,))] * 2 + [((0, 1), (2, 3))]
    thetas = [0.1, 0.2, 0.3, -0.1, -0.2, 0.5]
    weights = [3, 3, 3, 2, 2, 1]
    out = hz._round_robin(letters, thetas, weights)
    assert len(out) == 6
    assert all(out[i][0] != out[i + 1][0] for i in range(len(out) - 1))
    assert out[0][0] == ((0,), (2,)) and out[1][0] == ((1,), (3,))

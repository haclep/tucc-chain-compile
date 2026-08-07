"""Constructive composer (translation stage i): operator-level exactness
vs an independent kernel (V1), and the pinned closed forms as EXACT
polynomial identities (V2) -- derived, not fitted."""
import numpy as np

from chaincompile.dets import Substitution
from chaincompile import disentangle as dz
from chaincompile import normalorder as NO
from chaincompile.normalorder import Poly


def _kernel_matrix(word, thetas, nso):
    dim = 1 << nso
    M = np.zeros((dim, dim))
    for mask in range(dim):
        occ = tuple(p for p in range(nso) if (mask >> p) & 1)
        state = {occ: 1.0}
        for sub, th in zip(word, thetas):
            state = dz.apply_factor(sub, th, state, tol=0.0)
        for d, amp in state.items():
            m2 = 0
            for q in d:
                m2 |= 1 << q
            M[m2, mask] += amp
    return M


def _v1(word, occ, nso, seed):
    th = np.random.default_rng(seed).uniform(-1.2, 1.2, size=len(word))
    U, sizes = NO.compose(word, frozenset(occ))
    dev = float(np.max(np.abs(NO.op_matrix(U, th, nso)
                              - _kernel_matrix(word, th, nso))))
    assert dev < 1e-12, (dev, sizes)
    return sizes


def test_v1_operator_exactness():
    _v1([Substitution((0,), (2,))], (0, 1), 4, 1)
    _v1([Substitution((0, 1), (4, 5))], (0, 1, 2, 3), 6, 2)
    _v1([Substitution((2,), (4,))], (0, 1), 6, 3)          # lateral
    _v1([Substitution((0,), (2,)), Substitution((0,), (3,))], (0, 1), 4, 4)
    _v1([Substitution((0, 1), (4, 5)), Substitution((2, 3), (4, 5))],
        (0, 1, 2, 3), 6, 5)
    _v1([Substitution((0,), (2,)), Substitution((2,), (4,))], (0, 1), 6, 6)
    _v1([Substitution((0,), (2,)), Substitution((0,), (3,)),
         Substitution((1,), (2,))], (0, 1), 4, 7)


def _sv(n, k):
    return Poly.var(n, "s", k)


def _cv(n, k):
    return Poly.var(n, "c", k)


def test_v2_closed_forms_exact():
    # shared-occupied pair: c0 = c1 c2, t(0->2) = s1, t(0->3) = c1 s2
    U, _ = NO.compose([Substitution((0,), (2,)),
                       Substitution((0,), (3,))], frozenset((0, 1)))
    c0, amps = NO.ref_amplitudes(U, frozenset((0, 1)))
    assert c0 == _cv(2, 0) * _cv(2, 1)
    assert amps[((0,), (2,))] == _sv(2, 0)
    assert amps[((0,), (3,))] == _cv(2, 0) * _sv(2, 1)

    # shared-virtual doubles: identical dressing topology
    U, _ = NO.compose([Substitution((0, 1), (4, 5)),
                       Substitution((2, 3), (4, 5))], frozenset((0, 1, 2, 3)))
    c0, amps = NO.ref_amplitudes(U, frozenset((0, 1, 2, 3)))
    assert c0 == _cv(2, 0) * _cv(2, 1)
    assert amps[((0, 1), (4, 5))] == _sv(2, 0)
    assert amps[((2, 3), (4, 5))] == _cv(2, 0) * _sv(2, 1)
    assert ((0, 1, 2, 3), (4, 5, 6, 7)) not in amps

    # disjoint doubles: quad coefficient s1 s2 exactly (connected T4 = 0),
    # and the SINGLE-factor amplitudes each keep the partner cosine --
    # the secant dressing is the ABSENCE of that cosine under sharing.
    U, _ = NO.compose([Substitution((0, 1), (4, 5)),
                       Substitution((2, 3), (6, 7))], frozenset((0, 1, 2, 3)))
    c0, amps = NO.ref_amplitudes(U, frozenset((0, 1, 2, 3)))
    assert c0 == _cv(2, 0) * _cv(2, 1)
    assert amps[((0, 1), (4, 5))] == _sv(2, 0) * _cv(2, 1)
    assert amps[((2, 3), (6, 7))] == _cv(2, 0) * _sv(2, 1)
    assert amps[((0, 1, 2, 3), (4, 5, 6, 7))] == _sv(2, 0) * _sv(2, 1)

    # routed cascade: c0 = c1 ONLY (factor 2 ref-inactive);
    # composite t(0->4) = s1 s2, i.e. tan(t1) sin(t2) after /c0.
    U, _ = NO.compose([Substitution((0,), (2,)),
                       Substitution((2,), (4,))], frozenset((0, 1)))
    c0, amps = NO.ref_amplitudes(U, frozenset((0, 1)))
    assert c0 == _cv(2, 0)
    assert amps[((0,), (2,))] == _sv(2, 0) * _cv(2, 1)
    assert amps[((0,), (4,))] == _sv(2, 0) * _sv(2, 1)


def test_ref_amplitudes_match_kernel():
    rng = np.random.default_rng(11)
    word = [Substitution((0,), (2,)), Substitution((0,), (3,)),
            Substitution((1,), (2,))]
    occ = (0, 1)
    U, _ = NO.compose(word, frozenset(occ))
    c0, amps = NO.ref_amplitudes(U, frozenset(occ))
    th = rng.uniform(-1.1, 1.1, size=3)
    state = {tuple(occ): 1.0}
    for sub, t in zip(word, th):
        state = dz.apply_factor(sub, float(t), state, tol=0.0)
    for (h, p), poly in amps.items():
        det, s = dz.apply_A(Substitution(h, p), tuple(occ))
        assert abs(poly.eval(th) - s * state.get(det, 0.0)) < 1e-12


def test_ann_pruning_exact_for_ref_projection():
    word = [Substitution((0,), (2,)), Substitution((0,), (3,)),
            Substitution((1,), (2,))]
    occ = frozenset((0, 1))
    U1, _ = NO.compose(word, occ, prune_ann=False)
    U2, _ = NO.compose(word, occ, prune_ann=True)
    assert NO.ref_amplitudes(U1, occ) == NO.ref_amplitudes(U2, occ)


def _chain(L, U_):
    from chaincompile.compile import compile_chain
    from chaincompile.hubbard import hamiltonian
    from chaincompile.sector import SectorBasis

    basis = SectorBasis(L, L // 2, L // 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=U_))
    res = compile_chain(evecs[:, 0], basis, mode="sd_routed")
    word = [s for s, _ in res.selected()]
    th = [t for _, t in res.selected()]
    occ = frozenset(p for p in range(2 * L) if (res.pivot_mask >> p) & 1)
    return word, th, occ


def _chain_state(word, th, occ):
    state = {tuple(sorted(occ)): 1.0}
    for sub, t in zip(word, th):
        state = dz.apply_factor(sub, float(t), state, tol=0.0)
    return state


def _acceptance(c0, amps, state, occ):
    ref = tuple(sorted(occ))
    dev = abs(c0 - state.get(ref, 0.0))
    for (h, p), w in amps.items():
        det, sg = dz.apply_A(Substitution(h, p), ref)
        dev = max(dev, abs(w - sg * state.get(det, 0.0)))
    return dev


def test_stage_ii_l4_chain_symbolic():
    word, th, occ = _chain(4, 8.0)
    U, sizes = NO.compose(word, occ, prune_ann=True)
    assert sizes[-1] == 10 and sizes[6:] == [10] * 7  # support saturation
    c0, amps = NO.ref_amplitudes(U, occ)
    state = _chain_state(word, th, occ)
    thv = np.array(th)
    dev = _acceptance(c0.eval(thv),
                      {k: p.eval(thv) for k, p in amps.items()}, state, occ)
    assert dev < 1e-12
    # the quad closed form is 9 exact pathway terms
    assert len(amps[((0, 1, 2, 3), (4, 5, 6, 7))].terms) == 9


def test_stage_ii_l6_chain_numeric():
    word, th, occ = _chain(6, 6.0)
    U, sizes = NO.compose_numeric(word, th, occ)
    c0, amps = NO.numeric_ref_amplitudes(U, occ)
    state = _chain_state(word, th, occ)
    assert _acceptance(c0, amps, state, occ) < 1e-12
    n_state = sum(1 for v in state.values() if abs(v) > 1e-12)
    assert len(amps) + 1 == n_state  # engine terms == state support


def test_batched_jacobian_equals_scalar():
    """The batched Jacobian build must reproduce the scalar per-letter
    build bitwise (guards the vectorization against drift)."""
    from chaincompile.compile import compile_chain
    from chaincompile.factors import apply_ucc_factor, apply_ucc_factor_cols
    from chaincompile.hubbard import hamiltonian
    from chaincompile.sector import SectorBasis

    basis = SectorBasis(4, 2, 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=8.0))
    res = compile_chain(evecs[:, 0], basis, mode="sd_routed")
    word = [s for s, _ in res.selected()]
    th = np.array([t for _, t in res.selected()])
    a = [basis.basis_vector(res.pivot_mask)]
    for sub, t in zip(word, th):
        a.append(apply_ucc_factor(a[-1], basis, sub, t))
    N = len(word)
    Jref = np.empty((basis.dim, N))
    for k in range(N):
        ii, jj, ss = basis.block_arrays(word[k])
        v = np.zeros(basis.dim)
        v[jj] = ss * a[k + 1][ii]
        v[ii] = -ss * a[k + 1][jj]
        for sub, t in zip(word[k + 1:], th[k + 1:]):
            v = apply_ucc_factor(v, basis, sub, t)
        Jref[:, k] = v
    Jb = np.zeros((basis.dim, N))
    for k in range(N):
        if k:
            Jb[:, :k] = apply_ucc_factor_cols(Jb[:, :k], basis, word[k],
                                              th[k])
        ii, jj, ss = basis.block_arrays(word[k])
        Jb[jj, k] = ss * a[k + 1][ii]
        Jb[ii, k] = -ss * a[k + 1][jj]
    assert float(np.max(np.abs(Jb - Jref))) == 0.0

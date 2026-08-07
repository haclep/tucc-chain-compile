import numpy as np

from chaincompile.dets import Substitution
from chaincompile.factors import apply_cc_triple, apply_ucc_factor, taylor_expm_apply
from chaincompile.sector import SectorBasis

RNG = np.random.default_rng(7)


def _random_state(dim):
    v = RNG.normal(size=dim)
    return v / np.linalg.norm(v)


def _subs(L):
    return [
        Substitution((0,), (2,)),                # single up
        Substitution((1,), (5,)),                # single dn
        Substitution((0, 1), (2, 3)),            # ud double
        Substitution((0, 2), (4, 2 * L - 2)),    # uu double
        Substitution((0, 1, 2, 3), (4, 5, 6, 7)),  # quad
    ]


def test_factor_matches_taylor_expm():
    basis = SectorBasis(L=4, nup=2, ndn=2)
    for sub in _subs(4):
        K = basis.generator_matrix(sub)
        for theta in (-1.2, -0.3, 0.45, 1.5):
            v = _random_state(basis.dim)
            fast = apply_ucc_factor(v, basis, sub, theta)
            ref = taylor_expm_apply(theta * K, v)
            assert np.allclose(fast, ref, atol=1e-12)
            # unitarity
            assert abs(np.linalg.norm(fast) - 1.0) < 1e-12


def test_disentangled_triple_equals_rotation():
    """Per-factor numeric witness of the Symmetry-2022 bridge:
    exp(theta(A-Adag)) = (I + tan A) diag (I - tan Adag), |theta|<pi/2."""
    basis = SectorBasis(L=4, nup=2, ndn=2)
    for sub in _subs(4):
        for theta in (-0.7, -0.2, 0.1, 0.6, 1.2):
            v = _random_state(basis.dim)
            a = apply_ucc_factor(v, basis, sub, theta)
            b = apply_cc_triple(v, basis, sub, theta)
            assert np.allclose(a, b, atol=1e-12)


def test_blocks_are_disjoint():
    from chaincompile.factors import iter_blocks

    basis = SectorBasis(L=4, nup=2, ndn=2)
    for sub in _subs(4):
        seen = set()
        for i, j, s in iter_blocks(basis, sub):
            assert i not in seen and j not in seen
            seen.update((i, j))
            assert s in (-1, 1)

import numpy as np

from chaincompile.dets import Substitution, apply_ops, bits, substitution_between
from chaincompile.sector import SectorBasis


def test_parity_hand_examples():
    # |0,1,2> mask=0b111 ; c_1 gives (-1)^1 |0,2>
    m, s = apply_ops(0b111, [("c", 1)])
    assert m == 0b101 and s == -1
    # cdag_1 on |0,2>
    m, s = apply_ops(0b101, [("cd", 1)])
    assert m == 0b111 and s == -1
    # Pauli
    m, s = apply_ops(0b101, [("cd", 0)])
    assert m is None and s == 0


def test_adjointness_dense():
    basis = SectorBasis(L=3, nup=2, ndn=1)
    subs = [
        Substitution((0,), (4,)),
        Substitution((0, 1), (4, 5)),
        Substitution((0, 2), (3, 5)),
    ]
    for sub in subs:
        A = basis.substitution_matrix(sub)
        Ad = basis.op_matrix(sub.apply_adag)
        assert np.allclose(Ad, A.T, atol=1e-14)
        # nilpotency of primitive substitutions
        assert np.allclose(A @ A, 0.0, atol=1e-14)


def test_cube_identity_p2_eq5():
    # (A + Adag)^3 = A + Adag  (P2 Eq. 5)
    basis = SectorBasis(L=3, nup=1, ndn=1)
    sub = Substitution((0, 1), (2, 3))
    A = basis.substitution_matrix(sub)
    X = A + A.T
    assert np.allclose(X @ X @ X, X, atol=1e-13)


def test_substitution_between_roundtrip():
    lower = 0b000111
    upper = 0b101010  # not a valid single sub necessarily; build a valid pair
    lower = 0b0000111  # so 0,1,2
    sub = Substitution((0, 2), (4, 6))
    up, s = sub.apply_a(lower)
    assert s in (-1, 1)
    back = substitution_between(lower, up)
    assert back == sub
    assert sorted(bits(lower)) == [0, 1, 2]

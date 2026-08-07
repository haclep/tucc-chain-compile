"""Exact application of factorized-UCC factors, real convention.

Generator: kappa = A - Adag (real antisymmetric), so

    exp(theta * kappa) = I + sin(theta) (A - Adag)
                           + (cos(theta) - 1) (A Adag + Adag A)

-- the real-rotation counterpart of P2 Eq. (6). A fixed substitution
partitions the sector into fixed points plus disjoint 2x2 blocks
(d_low, d_up) with A|d_low> = s |d_up>, s = +-1; inside each block

    [c_low']   [ cos t   -s sin t ] [c_low]
    [c_up '] = [ s sin t    cos t ] [c_up ]

`apply_cc_triple` applies instead the disentangled SL(2,C) product

    exp(theta kappa) = exp(tan(theta) A) * exp(-ln cos(theta) (A Adag - Adag A))
                        * exp(-tan(theta) Adag)

which is the per-factor content of the Symmetry-2022 CC<->UCC bridge
(UCC angle theta -> CC-side amplitude tan theta). Equality with the
rotation is asserted in tests to machine precision; |theta| < pi/2 is
required (the cos theta = 0 divergence = reference-annihilating angle).
"""
from __future__ import annotations

import numpy as np

from .dets import Substitution
from .sector import SectorBasis


def iter_blocks(basis: SectorBasis, sub: Substitution):
    """Yield (i_low, i_up, s) for every 2x2 block of `sub` inside the sector."""
    ii, jj, ss = basis.block_arrays(sub)
    for i, j, s in zip(ii, jj, ss):
        yield int(i), int(j), int(s)


def apply_ucc_factor(
    vec: np.ndarray, basis: SectorBasis, sub: Substitution, theta: float
) -> np.ndarray:
    """Return exp(theta (A - Adag)) @ vec, exactly, via block rotations."""
    c = vec.copy()
    ct, st = np.cos(theta), np.sin(theta)
    ii, jj, ss = basis.block_arrays(sub)
    lo, up = c[ii], c[jj]
    c[ii] = ct * lo - ss * st * up
    c[jj] = ss * st * lo + ct * up
    return c


def apply_ucc_factor_cols(
    M: np.ndarray, basis: SectorBasis, sub: Substitution, theta: float
) -> np.ndarray:
    """Column-batched exp(theta (A - Adag)) @ M -- identical block
    rotation applied to every column at once (Jacobian builds)."""
    out = M.copy()
    ct, st = np.cos(theta), np.sin(theta)
    ii, jj, ss = basis.block_arrays(sub)
    lo, up = M[ii], M[jj]
    out[ii] = ct * lo - (ss * st)[:, None] * up
    out[jj] = (ss * st)[:, None] * lo + ct * up
    return out


def apply_cc_triple(
    vec: np.ndarray, basis: SectorBasis, sub: Substitution, theta: float
) -> np.ndarray:
    """Apply the disentangled product (rightmost factor first):
    (I + tan A) . exp(-ln cos (AAdag - AdagA)) . (I - tan Adag).
    Valid for |theta| < pi/2. Numerically identical to apply_ucc_factor.
    """
    if abs(abs(theta) - np.pi / 2) < 1e-12 or abs(theta) > np.pi / 2:
        raise ValueError("disentangling requires |theta| < pi/2")
    t = np.tan(theta)
    ct = np.cos(theta)
    c = vec.copy()
    for i, j, s in iter_blocks(basis, sub):
        lo, up = c[i], c[j]
        lo1 = lo - t * s * up          # (I - tan Adag): Adag|up> = s|low>
        up1 = up
        lo2 = ct * lo1                 # diagonal factor: low * cos
        up2 = up1 / ct                 # diagonal factor: up  / cos
        up3 = up2 + t * s * lo2        # (I + tan A):     A|low> = s|up>
        c[i] = lo2
        c[j] = up3
    return c


def taylor_expm_apply(K: np.ndarray, v: np.ndarray, tol: float = 1e-15,
                      maxterms: int = 200) -> np.ndarray:
    """exp(K) @ v by plain Taylor series (numpy-only; fine at these norms).
    Used only in tests as an independent reference for the factor identity."""
    w = v.copy()
    term = v.copy()
    for k in range(1, maxterms):
        term = K @ term / k
        w = w + term
        if np.linalg.norm(term) < tol:
            break
    return w

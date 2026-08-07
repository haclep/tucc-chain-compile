"""Molecular layer for the H4 validation (numpy + stdlib only).

STO-3G hydrogen is s-Gaussians only, so every integral has a closed
form via the Boys function F0: overlap, kinetic, nuclear attraction,
and the ERI (chemists' notation). This module provides those integrals,
a plain closed-shell RHF, the MO transform, and a determinant-space
Hamiltonian builder over a chaincompile SectorBasis using the SAME
elementary-operator parity kernel as the rest of the stack -- so the
decisive internal identity <HF|H|HF> + E_nuc == E_RHF certifies the
whole integrals -> SCF -> transform -> H chain at once
(tests/test_h4.py).

Psi4 remains the production integral source per the roadmap; this
layer exists so the H4 validation is self-contained and pip-only.
Spin-orbital convention matches the rest of chaincompile: p = 2m + s
with s = 0 (up) / 1 (down) for spatial MO m.
"""
from __future__ import annotations

import math

import numpy as np

# Hydrogen s-only bases (scaling folded into the exponents).
# Each basis is a tuple of contracted shells; each shell a tuple of
# (exponent, coefficient) primitives.
H_BASES = {
    "sto-3g": ((( 3.42525091, 0.15432897),
                ( 0.62391373, 0.53532814),
                ( 0.16885540, 0.44463454)),),
    "6-31g": (((18.7311370, 0.03349460),
               ( 2.8253937, 0.23472695),
               ( 0.6401217, 0.81375733)),
              (( 0.1612778, 1.00000000),)),
}
_H_EXP = tuple(a for a, _ in H_BASES["sto-3g"][0])
_H_COEF = tuple(d for _, d in H_BASES["sto-3g"][0])


def _f0(x):
    if x < 1e-12:
        return 1.0 - x / 3.0
    return 0.5 * math.sqrt(math.pi / x) * math.erf(math.sqrt(x))


def hydrogen_integrals(atom_centers, basis="sto-3g"):
    """atom_centers: (n_atoms, 3) bohr; hydrogen atoms only, s-only
    basis from H_BASES. Returns (S, T, V, ERI, E_nuc) over the
    contracted AO basis (n_atoms * n_shells functions), ERI in
    chemists' notation (ij|kl)."""
    atom_centers = np.asarray(atom_centers, float)
    shells = H_BASES[basis]
    centers = []
    prim = []
    for R in atom_centers:
        for shell in shells:
            centers.append(R)
            prim.append([(a, d * (2.0 * a / math.pi) ** 0.75)
                         for a, d in shell])
    centers = np.asarray(centers, float)
    n = len(centers)

    def s_prim(a, A, b, B):
        p = a + b
        mu = a * b / p
        r2 = float(np.dot(A - B, A - B))
        return (math.pi / p) ** 1.5 * math.exp(-mu * r2)

    # contracted self-overlaps -> renormalize
    for i in range(n):
        s = sum(ca * cb * s_prim(a, centers[i], b, centers[i])
                for a, ca in prim[i] for b, cb in prim[i])
        prim[i] = [(a, c / math.sqrt(s)) for a, c in prim[i]]

    S = np.zeros((n, n))
    T = np.zeros((n, n))
    V = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            for a, ca in prim[i]:
                for b, cb in prim[j]:
                    p = a + b
                    mu = a * b / p
                    r2 = float(np.dot(centers[i] - centers[j],
                                      centers[i] - centers[j]))
                    sp = (math.pi / p) ** 1.5 * math.exp(-mu * r2)
                    S[i, j] += ca * cb * sp
                    T[i, j] += ca * cb * mu * (3.0 - 2.0 * mu * r2) * sp
                    P = (a * centers[i] + b * centers[j]) / p
                    for C in atom_centers:  # nuclei, Z = 1 for every H
                        pc2 = float(np.dot(P - C, P - C))
                        V[i, j] += ca * cb * (-2.0 * math.pi / p) * \
                            math.exp(-mu * r2) * _f0(p * pc2)
    ERI = np.zeros((n, n, n, n))
    for i in range(n):
        for j in range(n):
            for k in range(n):
                for l_ in range(n):
                    tot = 0.0
                    for a, ca in prim[i]:
                        for b, cb in prim[j]:
                            p = a + b
                            mu = a * b / p
                            rab2 = float(np.dot(centers[i] - centers[j],
                                                centers[i] - centers[j]))
                            P = (a * centers[i] + b * centers[j]) / p
                            for c, cc in prim[k]:
                                for d, cd in prim[l_]:
                                    q = c + d
                                    nu = c * d / q
                                    rcd2 = float(np.dot(
                                        centers[k] - centers[l_],
                                        centers[k] - centers[l_]))
                                    Q = (c * centers[k]
                                         + d * centers[l_]) / q
                                    rho = p * q / (p + q)
                                    pq2 = float(np.dot(P - Q, P - Q))
                                    tot += ca * cb * cc * cd * \
                                        2.0 * math.pi ** 2.5 / \
                                        (p * q * math.sqrt(p + q)) * \
                                        math.exp(-mu * rab2) * \
                                        math.exp(-nu * rcd2) * \
                                        _f0(rho * pq2)
                    ERI[i, j, k, l_] = tot
    e_nuc = 0.0
    na = len(atom_centers)
    for i in range(na):
        for j in range(i + 1, na):
            e_nuc += 1.0 / math.sqrt(
                float(np.dot(atom_centers[i] - atom_centers[j],
                             atom_centers[i] - atom_centers[j])))
    return S, T, V, ERI, e_nuc


def h4_integrals(centers):
    """Back-compatible wrapper: one STO-3G 1s per H atom."""
    return hydrogen_integrals(centers, "sto-3g")


def rhf(S, hcore, ERI, n_docc, max_iter=200, tol=1e-11, damp=0.0):
    """Plain closed-shell RHF. Returns (C, eps, E_elec, converged)."""
    w, U = np.linalg.eigh(S)
    X = U @ np.diag(w ** -0.5) @ U.T
    D = np.zeros_like(S)
    e_old = 0.0
    for it in range(max_iter):
        J = np.einsum("ls,mnls->mn", D, ERI)
        K = np.einsum("ls,mlns->mn", D, ERI)
        F = hcore + J - 0.5 * K
        e = 0.5 * float(np.sum(D * (hcore + F)))
        Fp = X.T @ F @ X
        eps, Cp = np.linalg.eigh(Fp)
        C = X @ Cp
        Dn = 2.0 * C[:, :n_docc] @ C[:, :n_docc].T
        D = (1 - damp) * Dn + damp * D
        if abs(e - e_old) < tol and it > 1:
            return C, eps, e, True
        e_old = e
    return C, eps, e_old, False


def mo_integrals(C, hcore, ERI):
    h_mo = C.T @ hcore @ C
    eri_mo = np.einsum("mnab,mi,nj,ak,bl->ijkl", ERI, C, C, C, C,
                       optimize=True)
    return h_mo, eri_mo


def _apply_string(ops, mask):
    """ops in MATH order (leftmost acts last); dets-consistent parity."""
    m, sign = mask, 1
    for p, dag in reversed(ops):
        occ = (m >> p) & 1
        if dag:
            if occ:
                return None
            s = -1 if (bin(m & ((1 << p) - 1)).count("1") & 1) else 1
            m |= 1 << p
        else:
            if not occ:
                return None
            s = -1 if (bin(m & ((1 << p) - 1)).count("1") & 1) else 1
            m &= ~(1 << p)
        sign *= s
    return m, sign


def build_h_sector(h_mo, eri_mo, basis):
    """Molecular Hamiltonian matrix over a SectorBasis (bitmask
    determinants, spin-orbital p = 2m + s), via elementary-operator
    strings -- sign conventions shared with the whole stack."""
    nmo = h_mo.shape[0]
    dim = basis.dim
    H = np.zeros((dim, dim))
    terms = []
    for m in range(nmo):
        for n_ in range(nmo):
            w = float(h_mo[m, n_])
            if w == 0.0:
                continue
            for s in (0, 1):
                terms.append((((2 * m + s, 1), (2 * n_ + s, 0)), w))
    for i in range(nmo):
        for j in range(nmo):
            for k in range(nmo):
                for l_ in range(nmo):
                    w = 0.5 * float(eri_mo[i, j, k, l_])
                    if w == 0.0:
                        continue
                    for s in (0, 1):
                        for t in (0, 1):
                            terms.append(
                                (((2 * i + s, 1), (2 * k + t, 1),
                                  (2 * l_ + t, 0), (2 * j + s, 0)), w))
    for col, mask in enumerate(basis.masks):
        for ops, w in terms:
            r = _apply_string(ops, mask)
            if r is not None:
                row = basis.index.get(r[0])
                if row is not None:
                    H[row, col] += r[1] * w
    return H


# ---------------------------------------------------------------------------
# integral-dump interface (the Psi4 parity adapter's file contract)
# ---------------------------------------------------------------------------
DUMP_SCHEMA = "tucc-psi4-dump-1"


def save_integral_dump(path, h_mo, eri_mo, e_nuc, e_scf, n_alpha, n_beta,
                       **meta):
    """Write the documented .npz integral dump.

    Contract (schema tucc-psi4-dump-1): spatial-orbital MO integrals,
    energy-ascending canonical RHF orbitals, ERI in CHEMISTS' notation
    (ij|kl), real orbitals, no frozen core. e_scf is the TOTAL RHF
    energy including nuclear repulsion -- it powers the certification
    identity <HF|H|HF> + Enuc = E_RHF on load. Optional metadata
    (basis, molecule, source, geometry_str, mo_energies) rides along.
    """
    np.savez(path, schema=DUMP_SCHEMA,
             h_mo=np.asarray(h_mo, float),
             eri_mo=np.asarray(eri_mo, float),
             e_nuc=float(e_nuc), e_scf=float(e_scf),
             n_alpha=int(n_alpha), n_beta=int(n_beta), **meta)


def load_integral_dump(path):
    """Load and validate a tucc-psi4-dump-1 file. Returns
    (h_mo, eri_mo, e_nuc, e_scf, n_alpha, n_beta, meta)."""
    d = np.load(path, allow_pickle=False)
    if str(d["schema"]) != DUMP_SCHEMA:
        raise ValueError(f"unknown dump schema {d['schema']!r}")
    h_mo = np.asarray(d["h_mo"], float)
    eri = np.asarray(d["eri_mo"], float)
    nmo = h_mo.shape[0]
    if h_mo.shape != (nmo, nmo) or eri.shape != (nmo,) * 4:
        raise ValueError("dump shape mismatch")
    if float(np.max(np.abs(h_mo - h_mo.T))) > 1e-9:
        raise ValueError("h_mo not symmetric")
    rng = np.random.default_rng(0)
    for _ in range(24):  # chemists' 8-fold symmetry, sampled
        i, j, k, l_ = rng.integers(0, nmo, 4)
        v = eri[i, j, k, l_]
        for w in (eri[j, i, k, l_], eri[i, j, l_, k], eri[k, l_, i, j]):
            if abs(v - w) > 1e-8:
                raise ValueError("eri_mo violates chemists' symmetry")
    meta = {k: d[k] for k in d.files
            if k not in ("schema", "h_mo", "eri_mo", "e_nuc", "e_scf",
                         "n_alpha", "n_beta")}
    return (h_mo, eri, float(d["e_nuc"]), float(d["e_scf"]),
            int(d["n_alpha"]), int(d["n_beta"]), meta)


def freeze_core(h_mo, eri_mo, n_core):
    """Fold the lowest n_core doubly occupied orbitals into an effective
    active-space problem (standard frozen-core construction, chemists'
    notation):

        E_core  = 2 sum_i h_ii + sum_ij [2 (ii|jj) - (ij|ji)]
        h_eff_pq = h_pq + sum_i [2 (pq|ii) - (pi|iq)]     (p, q active)
        eri_act  = (pq|rs) restricted to active indices

    with i, j over core orbitals. Total energies downstream are
    E_active_eigenvalue + E_core + E_nuc, and the certification
    identity extends exactly: <HF_active|H_active|HF_active> + E_core
    + E_nuc = E_RHF (tested)."""
    k = int(n_core)
    if k == 0:
        return h_mo, eri_mo, 0.0
    hc = h_mo[:k, :k]
    ec = eri_mo[:k, :k, :k, :k]
    e_core = (2.0 * float(np.einsum("ii->", hc))
              + 2.0 * float(np.einsum("iijj->", ec))
              - float(np.einsum("ijji->", ec)))
    h_eff = (h_mo[k:, k:]
             + 2.0 * np.einsum("pqii->pq", eri_mo[k:, k:, :k, :k])
             - np.einsum("piiq->pq", eri_mo[k:, :k, :k, k:]))
    return h_eff, eri_mo[k:, k:, k:, k:], e_core


def dominant_block_projection(v, H, thr=1e-10):
    """Dense diagonalization of a degenerate eigenpair returns an
    arbitrary mixture within the eigenspace -- which can span
    DISCONNECTED symmetry blocks of H (measured on stretched C2:
    support exactly 2x the single-block size). This projects onto the
    H-connected block of v's dominant determinant and renormalizes,
    recovering a symmetry-pure state that is still an exact
    eigenvector. Returns (v_projected, block_index_set, was_mixed)."""
    import collections
    j0 = int(np.argmax(np.abs(v)))
    adj = np.abs(H) > thr
    seen = {j0}
    dq = collections.deque(seen)
    while dq:
        i = dq.popleft()
        for j in np.nonzero(adj[i])[0]:
            j = int(j)
            if j not in seen:
                seen.add(j)
                dq.append(j)
    idx = np.fromiter(seen, int)
    mask = np.zeros(v.shape[0], bool)
    mask[idx] = True
    if float(np.linalg.norm(v[~mask])) < 1e-10:
        return v, seen, False
    vp = np.where(mask, v, 0.0)
    vp = vp / np.linalg.norm(vp)
    return vp, seen, True

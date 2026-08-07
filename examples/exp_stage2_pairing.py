"""Stage-2 EXPERIMENT: spin-flip-tied pair chains.

Hypothesis (docs/METHOD.md sections 12-13): the spin-flip operator
F (2m <-> 2m+1, with fermionic reordering signs) commutes with H and
grades spin multiplets by (-1)^S. A chain whose letters are either
F-self-conjugate or applied as adjacent (A, F(A)) pairs with TIED
angles (theta, sigma_A * theta, sigma_A the numerically measured sign in
F kappa_A F = sigma_A kappa_{F(A)}) keeps prefixes in the target's
F-sector at every unit boundary -- exactly when the partners commute
(disjoint support), to O(theta^2) otherwise -- excluding triplet
contamination structurally while keeping every letter a PRIMITIVE
rank<=2 substitution (the per-factor CC bridge survives).

This script does NOT touch the core solver: it reuses routing and the
factor machinery, builds tied units, solves them (greedy 1-D exact
trig-polynomial init + tied bounded Gauss-Newton + F-closed tangent
growth), and scores the result against the untied baseline on the
observables that matter: exactness, chain length, max|theta|, prefix
<S^2> peak, prefix <F>, and the fidelity curve.

Output: results/stage2_pairing.md. Runtime ~1-2 min.
"""
import math
import os
import sys
import time

import numpy as np

from chaincompile.compile import _route_sequence, _normalize_target, compile_chain
from chaincompile.dets import Substitution
from chaincompile.diagnostics import md_table, write_text, prefix_s2_curve
from chaincompile.factors import apply_ucc_factor
from chaincompile.hubbard import hamiltonian
from chaincompile.sector import SectorBasis

RES = os.path.join(os.path.dirname(__file__), "..", "results")
BOUND = math.pi / 2 - 0.02


def say(m):
    print(m, flush=True)


# -- spin-flip machinery ----------------------------------------------------
def spin_flip_matrix(basis, L):
    F = np.zeros((basis.dim, basis.dim))
    for i, m in enumerate(basis.masks):
        occ = [p for p in range(2 * L) if (m >> p) & 1]
        img = [p ^ 1 for p in occ]
        inv = sum(1 for a in range(len(img)) for b in range(a + 1, len(img))
                  if img[a] > img[b])
        m2 = 0
        for q in img:
            m2 |= 1 << q
        F[basis.index[m2], i] = (-1.0) ** inv
    return F


def fsub(sub):
    return Substitution(tuple(sorted(h ^ 1 for h in sub.holes)),
                        tuple(sorted(q ^ 1 for q in sub.parts)))


def kappa_vec(basis, sub, v):
    ii, jj, ss = basis.block_arrays(sub)
    out = np.zeros(basis.dim)
    out[jj] = ss * v[ii]   # blocks are disjoint: assignment is exact
    out[ii] = -ss * v[jj]
    return out


def sigma_of(basis, F, sub, _cache={}):
    key = (sub.holes, sub.parts)
    if key in _cache:
        return _cache[key]
    rng = np.random.default_rng(0)
    v = rng.standard_normal(basis.dim)
    lhs = F @ kappa_vec(basis, sub, F @ v)
    rhs = kappa_vec(basis, fsub(sub), v)
    s = float(lhs @ rhs) / float(rhs @ rhs)
    assert np.allclose(lhs, s * rhs, atol=1e-9)
    _cache[key] = round(s)
    return _cache[key]


# -- tied units -------------------------------------------------------------
def build_units(subs, basis, F):
    """[(letters, signs)] with letters primitive subs, signs the tied
    angle multipliers; pairs are (A, F(A)) with (+1, sigma_A)."""
    units, seen = [], set()
    for sub in subs:
        key = (sub.holes, sub.parts)
        if key in seen:
            continue
        seen.add(key)
        fs = fsub(sub)
        if fs == sub:
            units.append(([sub], [1.0]))
        else:
            seen.add((fs.holes, fs.parts))
            units.append(([sub, fs], [1.0, float(sigma_of(basis, F, sub))]))
    return units


def flatten(units, x):
    """(letters, thetas) for unit parameters x (tanh-bounded)."""
    th_u = BOUND * np.tanh(x)
    letters, thetas = [], []
    for (subs, sgns), t in zip(units, th_u):
        for sub, sg in zip(subs, sgns):
            letters.append(sub)
            thetas.append(sg * t)
    return letters, np.array(thetas)


def prep(units, x, basis, pivot_mask, start=None):
    v = basis.basis_vector(pivot_mask) if start is None else start.copy()
    letters, thetas = flatten(units, x)
    for sub, t in zip(letters, thetas):
        v = apply_ucc_factor(v, basis, sub, t)
    return v


# -- greedy init: exact 1-D overlap maximization per unit -------------------
_GRID = np.linspace(-BOUND, BOUND, 801)
_S, _C1 = np.sin(_GRID), 1.0 - np.cos(_GRID)


def unit_overlap_max(basis, ct, psi, unit):
    """max_theta <ct| U_unit(theta) |psi> on the grid, via the exact
    9-coefficient (3-coefficient for self) trig-polynomial expansion."""
    subs, sgns = unit
    ops = []
    for sub, sg in zip(subs, sgns):
        k1 = lambda v, sub=sub, sg=sg: sg * kappa_vec(basis, sub, v)
        k2 = lambda v, sub=sub: kappa_vec(basis, sub, kappa_vec(basis, sub, v))
        ops.append((k1, k2))
    vecs = {(): psi}
    for depth, (k1, k2) in enumerate(ops):
        new = {}
        for key, v in vecs.items():
            new[key + (0,)] = v
            new[key + (1,)] = k1(v)
            new[key + (2,)] = k2(v)
        vecs = new
    basisf = [np.ones_like(_GRID), _S, _C1]
    f = np.zeros_like(_GRID)
    for key, v in vecs.items():
        w = float(ct @ v)
        if w == 0.0:
            continue
        g = np.full_like(_GRID, w)
        for a in key:
            if a == 1:
                g = g * _S
            elif a == 2:
                g = g * _C1
        f += g
    i = int(np.argmax(f))
    return float(f[i]), float(_GRID[i])


def greedy_order_init(units, basis, pivot_mask, ct):
    psi = basis.basis_vector(pivot_mask)
    remaining = list(units)
    ordered, th0 = [], []
    while remaining:
        best = None
        for idx, u in enumerate(remaining):
            val, t = unit_overlap_max(basis, ct, psi, u)
            key = (u[0][0].holes, u[0][0].parts, abs(t), t)
            if best is None or val > best[0] + 1e-12 or (
                    val > best[0] - 1e-12 and key < best[1]):
                best = (val, key, idx, t)
        _, _, idx, t = best
        u = remaining.pop(idx)
        ordered.append(u)
        th0.append(math.atanh(max(-0.9999, min(0.9999, t / BOUND))))
        for sub, sg in zip(*u):
            psi = apply_ucc_factor(psi, basis, sub, sg * BOUND * math.tanh(th0[-1]))
    return ordered, np.array(th0)


# -- tied bounded Gauss-Newton ---------------------------------------------
def gauss_newton(units, x, basis, pivot_mask, ct, tol=1e-13, max_iter=300):
    lam = 1e-8
    x = x.copy()
    psi = prep(units, x, basis, pivot_mask)
    res = psi - ct
    rn = float(np.linalg.norm(res))
    nu = len(units)
    for _ in range(max_iter):
        if rn < tol:
            break
        letters, thetas = flatten(units, x)
        a = [basis.basis_vector(pivot_mask)]
        for sub, t in zip(letters, thetas):
            a.append(apply_ucc_factor(a[-1], basis, sub, t))
        # per-letter columns, then sum into unit columns with sgn weights
        J = np.zeros((basis.dim, nu))
        dth = BOUND * (1.0 - np.tanh(x) ** 2)
        pos = 0
        for ui, (subs, sgns) in enumerate(units):
            for sub, sg in zip(subs, sgns):
                v = sg * kappa_vec(basis, sub, a[pos + 1])
                for sub2, t2 in zip(letters[pos + 1:], thetas[pos + 1:]):
                    v = apply_ucc_factor(v, basis, sub2, t2)
                J[:, ui] += v
                pos += 1
            J[:, ui] *= dth[ui]
        JtJ, g = J.T @ J, J.T @ res
        for _ in range(60):
            try:
                delta = np.linalg.solve(JtJ + lam * np.eye(nu), -g)
            except np.linalg.LinAlgError:
                lam *= 10
                continue
            x_new = x + delta
            psi_new = prep(units, x_new, basis, pivot_mask)
            rn_new = float(np.linalg.norm(psi_new - ct))
            if rn_new < rn:
                x, psi, rn, res = x_new, psi_new, rn_new, psi_new - ct
                lam = max(lam / 3.0, 1e-14)
                break
            lam *= 10.0
        else:
            break
    return x, rn


# -- F-closed tangent growth ------------------------------------------------
def grow(units, x, basis, pivot_mask, ct, F, k_pure, rounds=10, budget_s=230.0):
    from chaincompile.dets import popcount, substitution_between

    t0 = time.time()
    x, rn = gauss_newton(units, x, basis, pivot_mask, ct, max_iter=120)
    say(f"  GN[init]: rn {rn:.2e}  units {len(units)}")
    for rd in range(rounds):
        if rn ** 2 < 1e-24 or time.time() - t0 > budget_s:
            break
        psi = prep(units, x, basis, pivot_mask)
        resv = psi - ct
        # saturated-unit splitting
        sat = [i for i, xi in enumerate(x)
               if abs(BOUND * math.tanh(xi)) >= 0.92 * BOUND]
        added = []
        for i in sat[:2]:
            added.append(units[i])
        # pair-aware first-order scoring over K-pure S/D edges
        order = np.argsort(-np.abs(resv))[:12]
        pool = {}
        for i in order:
            mi = basis.masks[int(i)]
            for j in range(basis.dim):
                mj = basis.masks[j]
                if mj == mi or popcount(mi & ~mj) > 2:
                    continue
                if k_pure and basis.total_momentum(mj) not in k_pure:
                    continue
                a_, b_ = (mi, mj) if mi < mj else (mj, mi)
                pool[(a_, b_)] = substitution_between(a_, b_)
        scored = []
        for (a_, b_), sub in pool.items():
            fs = fsub(sub)
            col = kappa_vec(basis, sub, psi)
            if fs != sub:
                col = col + sigma_of(basis, F, sub) * kappa_vec(basis, fs, psi)
            scored.append((abs(float(resv @ col)), (a_, b_), sub))
        scored.sort(key=lambda t: (-t[0], t[1]))
        for sc, _, sub in scored[: max(4, len(units) // 6)]:
            if sc < 1e-14:
                break
            added.extend(build_units([sub], basis, F))
        if not added:
            break
        units = units + added
        x = np.concatenate([x, np.zeros(len(added))])
        x, rn = gauss_newton(units, x, basis, pivot_mask, ct, max_iter=150)
        say(f"  GN[grow {rd+1}]: rn {rn:.2e}  units {len(units)}")
    return units, x, rn


# -- measurement ------------------------------------------------------------
def prefix_curves(units, x, basis, pivot_mask, ct, S2, F):
    letters, thetas = flatten(units, x)
    v = basis.basis_vector(pivot_mask)
    boundaries = set(np.cumsum([len(u[0]) for u in units]).tolist())
    rows, peak_all, peak_bnd = [], 0.0, 0.0
    minfid = 1.0
    for K, (sub, t) in enumerate(zip(letters, thetas), 1):
        v = apply_ucc_factor(v, basis, sub, t)
        s2 = float(v @ S2 @ v)
        fpar = float(v @ F @ v)
        fid = abs(float(ct @ v))
        minfid = min(minfid, fid)
        peak_all = max(peak_all, abs(s2))
        if K in boundaries:
            peak_bnd = max(peak_bnd, abs(s2))
        rows.append((K, fid, s2, fpar, K in boundaries))
    return rows, peak_all, peak_bnd, minfid, letters, thetas


def main():
    t0 = time.time()
    L, U = 6, 6.0
    basis = SectorBasis(L, 3, 3)
    H = hamiltonian(basis, U=U)
    evals, evecs = np.linalg.eigh(H)
    target = evecs[:, 0]
    S2 = basis.s2_matrix()
    F = spin_flip_matrix(basis, L)

    # baseline (untied canonical chain)
    base = compile_chain(target, basis, mode="sd_routed")
    bcurve = prefix_s2_curve(base, basis)
    bpeak = max(abs(s) for _, _, s in bcurve)
    bminfid = min(f for _, f, _ in bcurve)

    # tied experiment
    ct, pivot_mask, p = _normalize_target(target, basis, None)
    seq = _route_sequence(ct, basis, pivot_mask, 1e-10)
    ks = {basis.total_momentum(m) for m in basis.masks
          if abs(ct[basis.index[m]]) > 1e-10}
    k_pure = ks if len(ks) == 1 else None
    units = build_units([s for s, _, _ in seq], basis, F)
    say(f"routing: {len(seq)} letters -> {len(units)} tied units "
        f"({sum(1 for u in units if len(u[0]) == 1)} self-conjugate)")
    units, x0 = greedy_order_init(units, basis, pivot_mask, ct)
    units, x, rn = grow(units, x0, basis, pivot_mask, ct, F, k_pure)
    rows, peak_all, peak_bnd, minfid, letters, thetas = prefix_curves(
        units, x, basis, pivot_mask, ct, S2, F)
    fid_final = abs(float(ct @ prep(units, x, basis, pivot_mask)))
    say(f"tied solve: residual {max(0.0, 1 - fid_final**2):.2e}  letters "
        f"{len(letters)}  units {len(units)}  max|theta| "
        f"{float(np.max(np.abs(thetas))):.4f}  ({time.time()-t0:.1f} s)")
    say(f"prefix <S2> peak: tied {peak_all:.3f} (unit boundaries "
        f"{peak_bnd:.3f}) vs baseline {bpeak:.3f}")
    say(f"prefix min fidelity: tied {minfid:.3f} vs baseline {bminfid:.3f}")

    grid = [r for r in rows if r[0] % 10 == 0 or r[0] == len(rows)]
    tab = [{"K": K, "fid": f, "S2": s, "F_parity": fp,
            "unit_boundary": b} for K, f, s, fp, b in grid]
    verdict = (
        "SUPPORTED" if peak_bnd < 0.35 * bpeak else
        "PARTIAL" if peak_all < 0.75 * bpeak else "NOT SUPPORTED")
    write_text(os.path.join(RES, "stage2_pairing.md"),
        "# Stage-2 experiment -- spin-flip-tied pair chains\n\n"
        "Tied units: every letter primitive rank<=2 (CC bridge intact); "
        "non-self-conjugate letters applied as adjacent (A, F(A)) pairs "
        "with angles (theta, sigma_A theta). Prefixes at unit boundaries "
        "stay in the target F-sector exactly for commuting partners, to "
        "O(theta^2) for the overlapping class.\n\n"
        f"Baseline (canonical sd chain): {base.length} letters, prefix "
        f"<S2> peak {bpeak:.3f}, min prefix fidelity {bminfid:.3f}.\n\n"
        f"Tied chain: {len(letters)} letters in {len(units)} units, "
        f"residual {max(0.0, 1 - fid_final**2):.2e}, max|theta| "
        f"{float(np.max(np.abs(thetas))):.4f}. Prefix <S2> peak "
        f"{peak_all:.3f} overall, {peak_bnd:.3f} at unit boundaries; min "
        f"prefix fidelity {minfid:.3f}.\n\n"
        f"HYPOTHESIS {verdict}.\n\n" + md_table(tab, list(tab[0].keys()))
        + "\n")
    say(f"verdict: {verdict} -> results/stage2_pairing.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Stage-2 battery: the three measurements that close the sd_paired
engineering questions (run after exp_stage2_pairing.py).

  t1  CONVERGENCE: push the tied solve to the repo contract
      (residual 1 - fid^2 < 1e-12, i.e. rn < 1e-6) with growth rounds,
      long polishes, and jittered restarts; resumable across calls via a
      state pickle. Reports final length, max|theta|, and -- if a floor
      appears -- the rank of the tied Jacobian vs the F-sector sphere.
  t2  LEAKAGE DECOMPOSITION: spectral projectors of S^2 split every
      prefix state into S = 0/1/2/3 weights, for the tied chain (from
      t1's state) AND the untied baseline. Answers: is the residual
      contamination triplet (leakage) or quintet (allowed by the
      (-1)^S grading)?
  t3  ABLATION: post-routing repair replaces parents whose substitution
      falls in the overlapping-partner class (fsub(A) != A with shared
      support) by non-overlapping already-routed parents where possible,
      then re-runs the tied solve at the ORIGINAL budget for a matched
      comparison of the F-parity wobble and S^2 peak.

Usage: python -u examples/exp_stage2_battery.py {t1|t2|t3|report}
State: results/_stage2_state.pkl ; report: results/stage2_battery.md
"""
import math
import os
import pickle
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp_stage2_pairing as sp  # noqa: E402

from chaincompile.compile import _normalize_target, _route_sequence, \
    compile_chain  # noqa: E402
from chaincompile.dets import Substitution, popcount, \
    substitution_between  # noqa: E402
from chaincompile.diagnostics import md_table, write_text  # noqa: E402
from chaincompile.hubbard import hamiltonian  # noqa: E402
from chaincompile.sector import SectorBasis  # noqa: E402

RES = os.path.join(os.path.dirname(__file__), "..", "results")
STATE = os.path.join(RES, "_stage2_state.pkl")
L, U = 6, 6.0


def say(m):
    print(m, flush=True)


def setup():
    basis = SectorBasis(L, 3, 3)
    H = hamiltonian(basis, U=U)
    evals, evecs = np.linalg.eigh(H)
    target = evecs[:, 0]
    ct, pivot_mask, p = _normalize_target(target, basis, None)
    F = sp.spin_flip_matrix(basis, L)
    ks = {basis.total_momentum(m) for m in basis.masks
          if abs(ct[basis.index[m]]) > 1e-10}
    k_pure = ks if len(ks) == 1 else None
    return basis, ct, pivot_mask, F, k_pure, target


def gn_deadline(units, x, basis, pivot_mask, ct, deadline, tol=1e-13):
    """sp.gauss_newton with a hard wall-clock deadline per outer iteration."""
    lam = 1e-8
    x = x.copy()
    psi = sp.prep(units, x, basis, pivot_mask)
    res = psi - ct
    rn = float(np.linalg.norm(res))
    nu = len(units)
    while time.time() < deadline and rn >= tol:
        letters, thetas = sp.flatten(units, x)
        a = [basis.basis_vector(pivot_mask)]
        for sub, t in zip(letters, thetas):
            a.append(sp.apply_ucc_factor(a[-1], basis, sub, t))
        J = np.zeros((basis.dim, nu))
        dth = sp.BOUND * (1.0 - np.tanh(x) ** 2)
        pos = 0
        for ui, (subs, sgns) in enumerate(units):
            for sub, sg in zip(subs, sgns):
                v = sg * sp.kappa_vec(basis, sub, a[pos + 1])
                for sub2, t2 in zip(letters[pos + 1:], thetas[pos + 1:]):
                    v = sp.apply_ucc_factor(v, basis, sub2, t2)
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
            psi_new = sp.prep(units, x_new, basis, pivot_mask)
            rn_new = float(np.linalg.norm(psi_new - ct))
            if rn_new < rn:
                x, psi, rn, res = x_new, psi_new, rn_new, psi_new - ct
                lam = max(lam / 3.0, 1e-14)
                break
            lam *= 10.0
        else:
            break
    return x, rn


def units_to_ser(units):
    return [[(s.holes, s.parts, g) for s, g in zip(subs, sgns)]
            for subs, sgns in units]


def units_from_ser(ser):
    return [([Substitution(tuple(h), tuple(q)) for h, q, _ in u],
             [float(g) for _, _, g in u]) for u in ser]


def overlapping(sub):
    fs = sp.fsub(sub)
    return fs != sub and bool(set(sub.holes + sub.parts)
                              & set(fs.holes + fs.parts))


# ---------------------------------------------------------------- t1 ------
def t1():
    basis, ct, pivot_mask, F, k_pure, _ = setup()
    if os.path.exists(STATE):
        st = pickle.load(open(STATE, "rb"))
        units = units_from_ser(st["units"])
        x = np.array(st["x"])
        say(f"resume: {len(units)} units, rn {st['rn']:.2e}")
    else:
        seq = _route_sequence(ct, basis, pivot_mask, 1e-10)
        units = sp.build_units([s for s, _, _ in seq], basis, F)
        units, x = sp.greedy_order_init(units, basis, pivot_mask, ct)
        say(f"fresh: routing {len(seq)} letters -> {len(units)} units")
    t0 = time.time()
    hard = t0 + 235.0
    rng = np.random.default_rng(20260803)
    rn = None
    try:
        x, rn = gn_deadline(units, x, basis, pivot_mask, ct,
                            min(hard, time.time() + 50))
        say(f"  gn: rn {rn:.2e}  units {len(units)}")
        stall = 0
        while time.time() < hard - 15 and rn >= 1e-6:
            psi = sp.prep(units, x, basis, pivot_mask)
            resv = psi - ct
            added = []
            th_u = sp.BOUND * np.tanh(x)
            sat = [i for i, t in enumerate(th_u)
                   if abs(t) >= 0.92 * sp.BOUND]
            for i in sat[:3]:
                added.append(units[i])
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
            for key, sub in pool.items():
                fs = sp.fsub(sub)
                col = sp.kappa_vec(basis, sub, psi)
                if fs != sub:
                    col = col + sp.sigma_of(basis, F, sub) *                         sp.kappa_vec(basis, fs, psi)
                scored.append((abs(float(resv @ col)), key, sub))
            scored.sort(key=lambda t: (-t[0], t[1]))
            for sc, _, sub in scored[: max(4, len(units) // 6)]:
                if sc < 1e-14:
                    break
                added.extend(sp.build_units([sub], basis, F))
            rn_prev = rn
            if added:
                units = units + added
                x = np.concatenate([x, np.zeros(len(added))])
            x, rn = gn_deadline(units, x, basis, pivot_mask, ct,
                                min(hard, time.time() + 65))
            say(f"  grow: units {len(units)}  rn {rn:.2e}")
            stall = stall + 1 if rn > 0.97 * rn_prev else 0
            if stall >= 2 and time.time() < hard - 45:
                xj = x + rng.normal(scale=0.08, size=len(x))
                x3, rn3 = gn_deadline(units, xj, basis, pivot_mask, ct,
                                      min(hard, time.time() + 40))
                say(f"  jitter: rn {rn3:.2e}")
                if rn3 < rn:
                    x, rn = x3, rn3
                    stall = 0
    finally:
        if rn is not None:
            pickle.dump({"units": units_to_ser(units), "x": x.tolist(),
                         "rn": float(rn), "status": "checkpoint"},
                        open(STATE, "wb"))
    letters, thetas = sp.flatten(units, x)
    status = "CONVERGED" if rn < 1e-6 else "IN PROGRESS"
    extra = {}
    if rn >= 1e-6:
        # floor diagnostic: rank of the tied Jacobian at the stall
        a = [basis.basis_vector(pivot_mask)]
        for sub, t in zip(letters, thetas):
            a.append(sp.apply_ucc_factor(a[-1], basis, sub, t))
        J = np.zeros((basis.dim, len(units)))
        pos = 0
        for ui, (subs, sgns) in enumerate(units):
            for sub, sg in zip(subs, sgns):
                v = sg * sp.kappa_vec(basis, sub, a[pos + 1])
                for sub2, t2 in zip(letters[pos + 1:], thetas[pos + 1:]):
                    v = sp.apply_ucc_factor(v, basis, sub2, t2)
                J[:, ui] += v
                pos += 1
        extra["J_rank"] = int(np.linalg.matrix_rank(J, tol=1e-9))
        fdim = int(round(float(np.trace(
            (np.eye(basis.dim) - F) / 2.0))))  # dim of F = -1 sector
        extra["F_sector_dim"] = fdim
        say(f"  floor diagnostic: rank(J) {extra['J_rank']} vs F-sector "
            f"dim {fdim}")
    pickle.dump({"units": units_to_ser(units), "x": x.tolist(),
                 "rn": float(rn), "status": status, **extra},
                open(STATE, "wb"))
    say(f"t1 {status}: rn {rn:.2e} residual {rn*rn:.2e}  letters "
        f"{len(letters)}  units {len(units)}  max|theta| "
        f"{float(np.max(np.abs(thetas))):.4f}")
    return 0


# ---------------------------------------------------------------- t2 ------
def s_projectors(basis):
    S2 = basis.s2_matrix()
    w, V = np.linalg.eigh(S2)
    projs = {}
    for S, ev in ((0, 0.0), (1, 2.0), (2, 6.0), (3, 12.0)):
        cols = V[:, np.abs(w - ev) < 1e-6]
        projs[S] = cols @ cols.T
    return projs


def t2():
    basis, ct, pivot_mask, F, k_pure, target = setup()
    projs = s_projectors(basis)
    st = pickle.load(open(STATE, "rb"))
    units, x = units_from_ser(st["units"]), np.array(st["x"])
    letters, thetas = sp.flatten(units, x)

    def decompose(seq_letters, seq_thetas, label):
        v = basis.basis_vector(pivot_mask)
        rows, peak = [], (0.0, 0, None)
        for K, (sub, t) in enumerate(zip(seq_letters, seq_thetas), 1):
            v = sp.apply_ucc_factor(v, basis, sub, t)
            ws = {S: float(v @ (projs[S] @ v)) for S in projs}
            s2 = 2 * ws[1] + 6 * ws[2] + 12 * ws[3]
            if s2 > peak[0]:
                peak = (s2, K, ws)
            if K % 20 == 0 or K == len(seq_letters):
                rows.append({"K": K, "S2": s2, "w_S1": ws[1],
                             "w_S2": ws[2], "w_S3": ws[3]})
        s2p, Kp, wsp = peak
        say(f"{label}: peak <S2> {s2p:.3f} at K={Kp}: triplet w {wsp[1]:.4f}"
            f" quintet w {wsp[2]:.4f} septet w {wsp[3]:.4f}")
        say(f"  -> of the peak <S2>, triplet contributes "
            f"{2*wsp[1]/s2p:.1%}, quintet {6*wsp[2]/s2p:.1%}")
        return rows, peak

    tied_rows, tied_peak = decompose(letters, thetas, "tied chain")
    base = compile_chain(target, basis, mode="sd_routed")
    bl, bt = zip(*base.selected())
    base_rows, base_peak = decompose(list(bl), list(bt), "baseline chain")
    pickle.dump({"tied_rows": tied_rows, "tied_peak": tied_peak,
                 "base_rows": base_rows, "base_peak": base_peak},
                open(os.path.join(RES, "_stage2_t2.pkl"), "wb"))
    return 0


# ---------------------------------------------------------------- t3 ------
def t3():
    basis, ct, pivot_mask, F, k_pure, _ = setup()
    seq = _route_sequence(ct, basis, pivot_mask, 1e-10)
    rank_of = {m: basis.rank_between(m, pivot_mask) for m in basis.masks}
    routed = {pivot_mask}
    repaired, forced = 0, 0
    new_seq = []
    n_over_before = sum(1 for s, _, _ in seq if overlapping(s))
    for sub, child, parent in seq:
        if overlapping(sub):
            r = rank_of[child]
            best = None
            for cand in routed:
                rr = rank_of[cand]
                if rr not in (r - 1, r - 2):
                    continue
                if popcount(child & ~cand) > 2:
                    continue
                if k_pure and basis.total_momentum(cand) not in k_pure:
                    continue
                s2 = substitution_between(cand, child)
                if overlapping(s2):
                    continue
                key = (-abs(ct[basis.index[cand]]), cand)
                if best is None or key < best[0]:
                    best = (key, cand, s2)
            if best is not None:
                _, parent, sub = best
                repaired += 1
            else:
                forced += 1
        new_seq.append((sub, child, parent))
        routed.add(child)
    n_over_after = sum(1 for s, _, _ in new_seq if overlapping(s))
    say(f"repair: overlapping letters {n_over_before} -> {n_over_after} "
        f"({repaired} rerouted, {forced} forced)")

    units = sp.build_units([s for s, _, _ in new_seq], basis, F)
    units, x = sp.greedy_order_init(units, basis, pivot_mask, ct)
    units, x, rn = sp.grow(units, x, basis, pivot_mask, ct, F, k_pure,
                           rounds=10, budget_s=230.0)
    S2 = basis.s2_matrix()
    rows, peak_all, peak_bnd, minfid, letters, thetas = sp.prefix_curves(
        units, x, basis, pivot_mask, ct, S2, F)
    fmin = min(fp for _, _, _, fp, _ in rows)
    say(f"ablated tied solve: rn {rn:.2e}  letters {len(letters)}  "
        f"units {len(units)}  max|theta| "
        f"{float(np.max(np.abs(thetas))):.4f}")
    say(f"  S2 peak {peak_all:.3f} (boundaries {peak_bnd:.3f})  "
        f"min <F> along prefixes {fmin:+.4f}  minfid {minfid:.3f}")
    pickle.dump({"n_over": (n_over_before, n_over_after),
                 "repaired": repaired, "forced": forced, "rn": float(rn),
                 "letters": len(letters), "units": len(units),
                 "peak_all": peak_all, "peak_bnd": peak_bnd,
                 "min_F": fmin, "minfid": minfid},
                open(os.path.join(RES, "_stage2_t3.pkl"), "wb"))
    return 0


# ------------------------------------------------------------- report -----
def report():
    st = pickle.load(open(STATE, "rb"))
    t2d = pickle.load(open(os.path.join(RES, "_stage2_t2.pkl"), "rb"))
    t3d = pickle.load(open(os.path.join(RES, "_stage2_t3.pkl"), "rb"))
    s2p, Kp, wsp = t2d["tied_peak"]
    bs2p, bKp, bwsp = t2d["base_peak"]
    parts = [
        "# Stage-2 battery -- convergence, leakage decomposition, ablation\n",
        f"## T1 convergence\n\n{st['status']}: rn {st['rn']:.2e} "
        f"(residual {st['rn']**2:.2e}), "
        f"{sum(len(u) for u in st['units'])} letters in "
        f"{len(st['units'])} units."
        + (f" Floor diagnostic: rank(J) {st['J_rank']} vs F-sector "
           f"sphere dim {st['F_sector_dim'] - 1}." if "J_rank" in st
           else "") + "\n",
        f"## T2 leakage decomposition\n\n"
        f"Tied chain peak <S2> {s2p:.3f} at K={Kp}: triplet weight "
        f"{wsp[1]:.4f} ({2*wsp[1]/s2p:.1%} of <S2>), quintet weight "
        f"{wsp[2]:.4f} ({6*wsp[2]/s2p:.1%}). Baseline peak <S2> "
        f"{bs2p:.3f} at K={bKp}: triplet weight {bwsp[1]:.4f} "
        f"({2*bwsp[1]/bs2p:.1%}), quintet {bwsp[2]:.4f}.\n\n"
        "Tied-chain grid:\n\n"
        + md_table(t2d["tied_rows"], ["K", "S2", "w_S1", "w_S2", "w_S3"])
        + "\n",
        f"## T3 overlapping-class ablation\n\n"
        f"Post-routing repair: overlapping letters "
        f"{t3d['n_over'][0]} -> {t3d['n_over'][1]} ({t3d['repaired']} "
        f"rerouted, {t3d['forced']} forced). Matched-budget tied solve: "
        f"rn {t3d['rn']:.2e}, {t3d['letters']} letters / {t3d['units']} "
        f"units, S2 peak {t3d['peak_all']:.3f} (boundaries "
        f"{t3d['peak_bnd']:.3f}), min <F> {t3d['min_F']:+.4f}, min "
        f"prefix fidelity {t3d['minfid']:.3f}.\n",
    ]
    write_text(os.path.join(RES, "stage2_battery.md"), "\n".join(parts))
    say("report -> results/stage2_battery.md")
    return 0


if __name__ == "__main__":
    sys.exit({"t1": t1, "t2": t2, "t3": t3, "report": report}[sys.argv[1]]())

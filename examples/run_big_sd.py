"""Resumable sd-chain compiler for large supports (rung three, part two).

Compiles the sd_routed chain of a big state ACROSS RESTARTS: every
phase (eigensolve, routing, greedy, joint solve, growth rounds,
restarts, constructive translation) checkpoints its progress to a
pickle file, so one long calculation becomes many short invocations --
rerun the same command until it prints DONE. The solve loop is a
faithful mirror of the canonical `_compile_sd` (same routing, greedy,
growth scoring, restart seeds); `mirror_exact=True` (used by the test
suite) runs the phases un-sliced and must reproduce `compile_chain`
to machine precision.

Usage (repeat until DONE):
  python -u examples/run_big_sd.py dump.npz --n-core 2 --deadline 3000

State lives next to the dump as <stem>_bigsd.pkl; delete it to start
over. Requires numba (the [fast] extra) for the sparse eigensolve.
"""
import argparse
import math
import os
import pickle
import time

import numpy as np

from chaincompile.compile import (_canon_argmax, _canon_desc, _fold_pi,
                                  _gauss_newton, _normalize_target, _prep,
                                  _route_sequence)
from chaincompile.dets import Substitution, popcount, substitution_between
from chaincompile.diagnostics import write_text
from chaincompile.factors import apply_ucc_factor
from chaincompile.fastpath import SparseH, davidson, status
from chaincompile.molecular import freeze_core, load_integral_dump
from chaincompile.sector import SectorBasis
from chaincompile import disentangle as dz
from chaincompile import normalorder as NO

RES = os.path.join(os.path.dirname(__file__), "..", "results")
BOUND = math.pi / 2 - 0.02


def _csr_component(indptr, indices, data, seed, thr=1e-10):
    import collections
    seen = {int(seed)}
    dq = collections.deque(seen)
    while dq:
        i = dq.popleft()
        for k in range(indptr[i], indptr[i + 1]):
            if abs(data[k]) <= thr:
                continue
            j = int(indices[k])
            if j not in seen:
                seen.add(j)
                dq.append(j)
    return seen


def _greedy_init(ct, basis, pivot_mask, seq0):
    """Verbatim mirror of _compile_sd.greedy_order_init."""
    psi = basis.basis_vector(pivot_mask)
    remaining = list(seq0)
    ordered, th0 = [], []
    while remaining:
        A = float(ct @ psi)
        cands = []
        for idx, (sub, ch, pa) in enumerate(remaining):
            ii, jj, ss = basis.block_arrays(sub)
            B = float(ct[jj] @ (ss * psi[ii]) - ct[ii] @ (ss * psi[jj]))
            C = float(ct[ii] @ psi[ii] + ct[jj] @ psi[jj])
            th_s = math.atan2(B, C)
            for t in (th_s, BOUND, -BOUND):
                if abs(t) > BOUND + 1e-12:
                    continue
                val = (A - C) + B * math.sin(t) + C * math.cos(t)
                cands.append((val, (sub.holes, sub.parts, abs(t), t),
                              (idx, t)))
        idx, t = _canon_argmax(cands)
        entry = remaining.pop(idx)
        ordered.append(entry)
        th0.append(t)
        psi = apply_ucc_factor(psi, basis, entry[0], t)
    return ordered, np.array(th0)


def _grow_once(ct, basis, pivot_mask, seq, thetas, k_pure):
    """Verbatim mirror of one growth round of _compile_sd."""
    psi = _prep(thetas, seq, basis, pivot_mask)
    resv = psi - ct
    added = 0
    sat = [k for k, t in enumerate(thetas) if abs(t) >= 0.92 * BOUND]
    for k in sat[: max(2, len(seq) // 12)]:
        seq.append(seq[k])
        added += 1
    top = _canon_desc(
        [(abs(resv[i]), basis.masks[i], i)
         for i in range(basis.dim) if abs(resv[i]) > 1e-14])[:12]
    pool = {}
    for i in top:
        mi = basis.masks[i]
        for j in range(basis.dim):
            if j == i:
                continue
            mj = basis.masks[j]
            if k_pure and basis.total_momentum(mj) not in k_pure:
                continue
            if popcount(mi & ~mj) > 2:
                continue
            a, b = (mi, mj) if mi < mj else (mj, mi)
            pool[(a, b)] = substitution_between(a, b)
    scored = []
    for (a, b), sub in pool.items():
        ii, jj, ss = basis.block_arrays(sub)
        col = np.zeros(basis.dim)
        col[jj] = ss * psi[ii]
        col[ii] = -ss * psi[jj]
        scored.append((abs(float(resv @ col)), a, b, sub))
    scored = _canon_desc(
        [(sc, (a, b), (sc, a, b, sub)) for sc, a, b, sub in scored])
    for score, a, b, sub in scored[: max(4, len(seq) // 8)]:
        if score < 1e-14:
            break
        seq.append((sub, b, a))
        added += 1
    return added


def solve_resumable(ct, basis, pivot_mask, state, deadline_at,
                    fid_tol=1e-12, grow_rounds=28, mirror_exact=False,
                    log=print, save=lambda: None):
    """Advance the mirrored _compile_sd loop until done or deadline.
    `state` is a dict mutated in place; `save()` persists it at every
    phase transition. Returns True when converged."""
    def out_of_time():
        return (not mirror_exact) and time.time() > deadline_at

    if state["phase"] == "route":
        state["seq"] = _route_sequence(ct, basis, pivot_mask,
                                       state["support_tol"])
        k_t = {basis.total_momentum(basis.masks[i])
               for i in range(basis.dim)
               if abs(ct[i]) > state["support_tol"]}
        state["k_pure"] = k_t if len(k_t) == 1 else None
        state["routed"] = len(state["seq"])
        state["phase"] = "greedy"
        save()
        log(f"routed {len(state['seq'])} letters")
        if out_of_time():
            return False
    if state["phase"] == "greedy":
        if "g_rem" not in state:
            state["g_rem"] = list(state["seq"])
            state["g_ord"], state["g_th"] = [], []
            state["g_psi"] = basis.basis_vector(pivot_mask)
        rem, ordered = state["g_rem"], state["g_ord"]
        th0, psi = state["g_th"], state["g_psi"]
        step = 0
        while rem:
            A = float(ct @ psi)
            cands = []
            for idx, (sub, ch, pa) in enumerate(rem):
                ii, jj, ss = basis.block_arrays(sub)
                B = float(ct[jj] @ (ss * psi[ii])
                          - ct[ii] @ (ss * psi[jj]))
                C = float(ct[ii] @ psi[ii] + ct[jj] @ psi[jj])
                th_s = math.atan2(B, C)
                for t in (th_s, BOUND, -BOUND):
                    if abs(t) > BOUND + 1e-12:
                        continue
                    val = (A - C) + B * math.sin(t) + C * math.cos(t)
                    cands.append((val, (sub.holes, sub.parts,
                                        abs(t), t), (idx, t)))
            idx, t = _canon_argmax(cands)
            entry = rem.pop(idx)
            ordered.append(entry)
            th0.append(t)
            psi = apply_ucc_factor(psi, basis, entry[0], t)
            state["g_psi"] = psi
            step += 1
            if step % 50 == 0:
                save()
                log(f"greedy {len(ordered)}/{len(ordered)+len(rem)}")
                if out_of_time():
                    return False
        state["seq"] = ordered
        state["thetas"] = np.array(th0)
        for k in ("g_rem", "g_ord", "g_th", "g_psi"):
            state.pop(k, None)
        psi_g = _prep(state["thetas"], state["seq"], basis, pivot_mask)
        state["rn"] = float(np.linalg.norm(psi_g - ct))
        state["phase"] = "joint"
        state["iters_left"] = 300
        save()
        log(f"greedy done, |r| {state['rn']:.3e}")
        if out_of_time():
            return False
    while state["phase"] in ("joint", "grow_gn"):
        if not mirror_exact:
            est = state.get("slice_t")
            probe = est is None
            per = (est / 10.0) if est else 15.0
            budget = 2 if probe else 10
            if time.time() + 1.3 * per * budget > deadline_at:
                return False
            budget = min(state["iters_left"], budget)
        else:
            budget = state["iters_left"]
        t_sl = time.time()
        state["thetas"], state["rn"] = _gauss_newton(
            state["thetas"], state["seq"], basis, pivot_mask, ct,
            tol=1e-13, max_iter=budget, bound=BOUND)
        if not mirror_exact:
            state["slice_t"] = 10.0 * (time.time() - t_sl) / budget
        state["iters_left"] -= budget
        save()
        log(f"{state['phase']}: |r| {state['rn']:.3e} "
            f"(iters left {state['iters_left']}, len {len(state['seq'])})")
        if state["rn"] ** 2 < fid_tol:
            state["phase"] = "final"
            break
        if state["iters_left"] <= 0:
            if state["phase"] == "joint":
                state["phase"] = "grow"
                state["round"] = 0
            else:
                state["phase"] = "grow"
            break
        if out_of_time():
            return False
    while state["phase"] == "grow":
        if state["rn"] ** 2 < fid_tol or state["round"] >= grow_rounds:
            state["phase"] = "restarts"
            state.setdefault("tries", 0)
            state.setdefault("best", (state["thetas"].copy(),
                                      state["rn"]))
            break
        added = _grow_once(ct, basis, pivot_mask, state["seq"],
                           state["thetas"], state["k_pure"])
        if added == 0:
            state["phase"] = "restarts"
            state.setdefault("tries", 0)
            state.setdefault("best", (state["thetas"].copy(),
                                      state["rn"]))
            break
        state["thetas"] = np.concatenate(
            [state["thetas"], np.zeros(added)])
        state["grown"] = state.get("grown", 0) + added
        state["round"] += 1
        state["phase"] = "grow_gn"
        state["iters_left"] = 400
        save()
        log(f"grow round {state['round']}: +{added} letters "
            f"(len {len(state['seq'])})")
        if out_of_time():
            return False
        # fall back into the GN loop
        return solve_resumable(ct, basis, pivot_mask, state, deadline_at,
                               fid_tol, grow_rounds, mirror_exact, log)
    if state["phase"] == "restarts":
        rng = np.random.default_rng(20260803)
        rng.bit_generator.state = state.get(
            "rng_state", rng.bit_generator.state)
        best_th, best_rn = state["best"]
        while best_rn ** 2 > fid_tol and state["tries"] < 6:
            state["tries"] += 1
            jitter = rng.normal(scale=0.15 * (1 + state["tries"] / 3),
                                size=len(state["seq"]))
            th_try, rn_try = _gauss_newton(
                best_th + jitter, state["seq"], basis, pivot_mask, ct,
                tol=1e-13, max_iter=300, bound=BOUND)
            if rn_try < best_rn:
                best_th, best_rn = th_try, rn_try
            state["best"] = (best_th, best_rn)
            state["rng_state"] = rng.bit_generator.state
            save()
            log(f"restart {state['tries']}: best |r| {best_rn:.3e}")
            if out_of_time():
                return False
        state["thetas"], state["rn"] = best_th, best_rn
        state["phase"] = "final"
    if state["phase"] == "final":
        psi = _prep(state["thetas"], state["seq"], basis, pivot_mask)
        residual = float(max(0.0, 1.0 - abs(ct @ psi) ** 2))
        if residual > fid_tol:
            raise RuntimeError(
                f"solve stalled at residual {residual:.3e} "
                f"(len {len(state['seq'])}, grown "
                f"{state.get('grown', 0)}, restarts "
                f"{state.get('tries', 0)})")
        state["thetas"] = np.array(
            [_fold_pi(t) for t in state["thetas"]])
        state["residual"] = residual
        state["phase"] = "noc"
        state["noc_k"] = 0
        state["U"] = {((), ()): 1.0}
        state["sizes"] = []
    return state["phase"] == "noc"


def noc_resumable(state, occ, deadline_at, chunk=40, log=print):
    """Chunked mirror of normalorder.compose_numeric."""
    word = [s for s, _, _ in state["seq"]]
    th = state["thetas"]
    k = state["noc_k"]
    U = state["U"]
    while k < len(word):
        sub, t = word[k], float(th[k])
        s_, c_ = float(np.sin(t)), float(np.cos(t))
        A = NO._a_math_string(sub)
        Ad = tuple((p, 1 - d) for p, d in reversed(A))
        F = {((), ()): 1.0}
        for string, w in ((A, s_), (Ad, -s_),
                          (A + Ad, c_ - 1.0), (Ad + A, c_ - 1.0)):
            for mono, sg in NO.normal_order(string, occ).items():
                F[mono] = F.get(mono, 0.0) + w * sg
        out = {}
        for m1, w1 in F.items():
            s1 = NO._monomial_math_string(m1)
            for m2, w2 in U.items():
                for mono, sg in NO.normal_order(
                        s1 + NO._monomial_math_string(m2), occ).items():
                    if mono[1]:
                        continue
                    out[mono] = out.get(mono, 0.0) + w1 * w2 * sg
        U = {m: w for m, w in out.items() if abs(w) > 1e-15}
        k += 1
        state["U"], state["noc_k"], state["sizes"] = U, k, \
            state["sizes"] + [len(U)]
        if k % chunk == 0:
            state.get("_save", lambda: None)()
            log(f"noc: {k}/{len(word)} letters, |U| {len(U)}")
            if time.time() > deadline_at:
                return False
    state["phase"] = "done"
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--n-core", type=int, default=0)
    ap.add_argument("--deadline", type=float, default=3000,
                    help="seconds per invocation before checkpointing")
    ap.add_argument("--root", type=int, default=0,
                    help="Davidson root to compile (0 = ground; "
                    "nonzero suffixes checkpoint and report with _rootN)")
    ap.add_argument("--dense-init", action="store_true",
                    help="use dense eigh for the init roots instead of "
                    "seeded Davidson; mandatory at state-reordered "
                    "geometries where no seed touches the ground block")
    ap.add_argument("--state", default=None)
    a = ap.parse_args()
    status()
    import signal

    def _term(sig, frm):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _term)
    t_end = time.time() + a.deadline
    stem = os.path.splitext(os.path.basename(a.dump))[0]
    if a.root:
        stem = f"{stem}_root{a.root}"
    spath = a.state or os.path.join(
        os.path.dirname(os.path.abspath(a.dump)), f"{stem}_bigsd.pkl")

    h_mo, eri_mo, e_nuc, e_scf, na, nb, meta = load_integral_dump(a.dump)
    h_mo, eri_mo, e_core = freeze_core(h_mo, eri_mo, a.n_core)
    na -= a.n_core
    nb -= a.n_core
    nmo = h_mo.shape[0]
    basis = SectorBasis(nmo, na, nb)

    if os.path.exists(spath):
        with open(spath, "rb") as f:
            state = pickle.load(f)
        print(f"resuming phase '{state['phase']}' "
              f"(len {len(state.get('seq', []))})", flush=True)
        ct, pivot_mask = state["ct"], state["pivot_mask"]
    else:
        sp = SparseH(h_mo, eri_mo, basis)
        diag = sp.diagonal()
        # Seed policy: the HF determinant ALWAYS joins the lowest-
        # diagonal seeds. Davidson can never leave the H-disconnected
        # blocks its start vector touches, so the seeds must cover both
        # the HF block (equilibrium-type grounds) and the lowest-
        # diagonal blocks (stretched-type grounds).
        hf_mask = 0
        for m_ in range(na):
            hf_mask |= 1 << (2 * m_)
        for m_ in range(nb):
            hf_mask |= 1 << (2 * m_ + 1)
        masks_arr = np.asarray(basis.masks, dtype=np.int64)
        hits = np.nonzero(masks_arr == np.int64(hf_mask))[0]
        seeds = [int(hits[0])] if len(hits) else []
        if not seeds:
            print("WARNING: HF determinant not in sector basis; "
                  "seeding from diagonal only", flush=True)
        for j_ in np.argsort(diag)[:3]:
            if int(j_) not in seeds:
                seeds.append(int(j_))
        v0s = np.zeros((basis.dim, len(seeds)))
        for r_, s_ in enumerate(seeds):
            v0s[s_, r_] = 1.0
        if a.dense_init:
            Hd = np.zeros((basis.dim, basis.dim))
            for i_ in range(basis.dim):
                Hd[i_, sp.indices[sp.indptr[i_]:sp.indptr[i_ + 1]]] = \
                    sp.data[sp.indptr[i_]:sp.indptr[i_ + 1]]
            ww, XX = np.linalg.eigh(Hd)
            del Hd
            w, X, nmv = ww[:len(seeds)], XX[:, :len(seeds)], 0
        else:
            w, X, nmv = davidson(sp, nroots=len(seeds), tol=1e-10, v0=v0s)
        if not (0 <= a.root < X.shape[1]):
            raise SystemExit(f"--root {a.root} outside computed roots "
                             f"0..{X.shape[1]-1}")
        v0 = X[:, a.root]
        roots_abs = [float(x + e_nuc + e_core) for x in w]
        print(("dense-init eigh roots: " if a.dense_init
               else "davidson roots: ")
              + "  ".join(f"{x:.8f}" for x in roots_abs)
              + ("  (dense eigh; full spectrum computed)" if a.dense_init
                 else f"  ({nmv} matvecs; seeds = HF + {len(seeds)-1} "
                 f"lowest-diag)"), flush=True)
        # Purity of the SELECTED root, decided by leaked weight -- not
        # by a root gap. Walk at 1e-7 (above integral-noise couplings)
        # for the decision; walk at 1e-10 too, for the report.
        j0 = int(np.argmax(np.abs(v0)))
        comp_dec = _csr_component(sp.indptr, sp.indices, sp.data, j0,
                                  thr=1e-7)
        comp_rep = _csr_component(sp.indptr, sp.indices, sp.data, j0,
                                  thr=1e-10)
        mask = np.zeros(basis.dim, bool)
        mask[list(comp_dec)] = True
        leak = float(np.linalg.norm(v0[~mask]))
        projected, proj_res = False, None
        e0_abs = roots_abs[a.root]
        if leak > 1e-8:
            v0 = np.where(mask, v0, 0.0)
            v0 /= np.linalg.norm(v0)
            hv = sp.matvec(v0)
            e_act = float(v0 @ hv)
            proj_res = float(np.linalg.norm(hv - e_act * v0))
            projected = True
            e0_abs = e_act + e_nuc + e_core
            print(f"impure root (leak {leak:.3e}) projected onto "
                  f"dominant block ({len(comp_dec)} dets); eigen-"
                  f"residual after projection {proj_res:.3e}",
                  flush=True)
        support = int(np.count_nonzero(np.abs(v0) > 1e-10))
        hf_in_dom = bool(len(hits) and mask[int(hits[0])])
        print(f"target: support {support}, dominant block "
              f"{len(comp_dec)} (1e-7 walk) / {len(comp_rep)} "
              f"(1e-10 walk), HF in dominant block: {hf_in_dom}",
              flush=True)
        ct, pivot_mask, p = _normalize_target(v0, basis, None)
        state = {"phase": "route", "ct": ct, "pivot_mask": pivot_mask,
                 "support_tol": 1e-10, "e_shift": e_nuc + e_core,
                 "e0": e0_abs, "roots": roots_abs, "support": support,
                 "block_dec": len(comp_dec), "block_rep": len(comp_rep),
                 "projected": projected, "proj_res": proj_res,
                 "hf_in_dom": hf_in_dom}
        with open(spath, "wb") as f:
            pickle.dump(state, f)
        print("init checkpointed", flush=True)
    try:
        solved = solve_resumable(ct, basis, pivot_mask, state, t_end)
        if state["phase"] == "noc":
            occ = frozenset(q for q in range(2 * nmo)
                            if (pivot_mask >> q) & 1)
            noc_resumable(state, occ, t_end)
    finally:
        state.pop("_save", None)
        with open(spath, "wb") as f:
            pickle.dump(state, f)
        print(f"[state saved: phase '{state['phase']}']", flush=True)
    if state["phase"] != "done":
        print(f"CHECKPOINT phase '{state['phase']}' -- rerun the "
              f"same command to continue", flush=True)
        return
    # finished: acceptance + artifacts
    word = [s for s, _, _ in state["seq"]]
    th = state["thetas"]
    occ = frozenset(q for q in range(2 * nmo) if (pivot_mask >> q) & 1)
    c0, amps = NO.numeric_ref_amplitudes(state["U"], occ)
    ref = tuple(sorted(occ))
    st = {ref: 1.0}
    for sub, t in zip(word, th):
        st = dz.apply_factor(sub, float(t), st, tol=0.0)
    dev = abs(c0 - st.get(ref, 0.0))
    for (hh, pp), w_ in amps.items():
        det, sg = dz.apply_A(Substitution(hh, pp), ref)
        dev = max(dev, abs(w_ - sg * st.get(det, 0.0)))
    ranks = {}
    for sub in word:
        ranks[len(sub.holes)] = ranks.get(len(sub.holes), 0) + 1
    np.savez(os.path.join(os.path.dirname(spath), f"{stem}_chain.npz"),
             subs_h=np.array([s.holes for s in word], dtype=object),
             subs_p=np.array([s.parts for s in word], dtype=object),
             th=th, pivot=pivot_mask)
    routed = state.get("routed")
    warn = ""
    if routed is not None and state.get("grown", 0) >= routed:
        warn = (f"\nNOTE: growth ({state.get('grown', 0)}) >= "
                f"routing ({routed}) -- hard (strongly correlated) "
                f"target; see purity fields for multi-block status.\n")
    roots_s = ", ".join(f"{x:.8f}" for x in state.get("roots", [])) \
        or "n/a"
    pr = state.get("proj_res")
    diag_s = (
        f"Target diagnostics: roots [{roots_s}]; support "
        f"{state.get('support', 'n/a')}, dominant block "
        f"{state.get('block_dec', 'n/a')} (1e-7 walk) / "
        f"{state.get('block_rep', 'n/a')} (1e-10 walk), routed "
        f"{routed if routed is not None else 'n/a'}, projected "
        f"{state.get('projected', 'n/a')}"
        + (f" (eigen-residual {pr:.1e})" if pr is not None else "")
        + f", HF in dominant block "
        f"{state.get('hf_in_dom', 'n/a')}.\n")
    src_s = (
        f"Source: {meta.get('source', 'unknown')}; basis "
        f"{meta.get('basis', 'unknown')}; active nmo {nmo}; sector "
        f"({na},{nb}) dim {basis.dim}"
        + (f"; {a.n_core} core orbitals frozen, E_core = {e_core:.8f}"
           if a.n_core else "") + ".\n"
        f"Provenance: dump file {os.path.basename(a.dump)}; "
        f"invocation run_big_sd.py {os.path.basename(a.dump)} "
        f"--n-core {a.n_core}"
        + (f" --root {a.root}" if a.root else "")
        + (" --dense-init" if a.dense_init else "")
        + " (repeated to completion).\n\n")
    write_text(os.path.join(RES, f"bigsd_{stem}.md"),
        f"# Resumable sd chain -- {stem}\n\n"
        + src_s
        + f"E0 = {state['e0']:.8f}; chain length {len(word)}, ranks "
        f"{ranks}, max|theta| {float(np.max(np.abs(th))):.6f}, "
        f"residual {state['residual']:.1e}, grown "
        f"{state.get('grown', 0)}, restarts {state.get('tries', 0)}. "
        f"Constructive translation: {len(amps)+1} creator monomials, "
        f"acceptance {dev:.1e}, term-curve tail "
        f"{state['sizes'][-3:]}.\n\n"
        + diag_s + warn)
    print(f"DONE: len {len(word)} residual {state['residual']:.1e} "
          f"NOC acceptance {dev:.1e} -> results/bigsd_{stem}.md",
          flush=True)


if __name__ == "__main__":
    main()

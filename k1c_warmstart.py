#!/usr/bin/env python
"""k1c_warmstart.py -- K1c cost harness: race proposals in ROTATIONS.

A thin wrapper over the frozen K1b-T4 harness (k1b_warmstart.py, loaded
as a module so its rotation accounting, plateau rule, gate and report
are reused unchanged). Additions, all K1c protocol knobs:

  --pred-file PATH     read the proposal from any frozen file in the
                       harness's own format ({"preds": {seed: (word, th)}})
                       for ANY stem.
  --pred-source        file (default) | tangent | poolall | topk. With a live
                       source the proposal is computed at the actual
                       insertion state: the round-one pool from the TOP
                       largest-residual determinants, allocated in
                       proportion to the compiler's first-order fidelity
                       gradient (tangent), one copy each (poolall), or the
                       top-K distinct letters by gradient, one copy each
                       (topk), all at zero angle. No file, no parameters.
  --prejoint-iters N   cap on the pre-insertion joint solve (default 300;
                       the plateau rule still applies). Non-default values
                       are appended to the run tag.
  --scale N            tangent: total letters to propose (default: the
                       pool size); --scale-mult m: multiple of pool size.
  --top K              pool seeds (default k1c_pool.TOP).
  --insert post-joint  run the joint Gauss-Newton solve on the routed chain
                       BEFORE appending the proposal, then give the seeded
                       chain a fresh joint budget. The pre-insertion solve
                       is identical in every arm and recorded UNCHARGED
                       (rot_prep_uncharged in the summary). Live sources
                       require this insertion point.
  --gate X             certification gate on the squared residual norm
                       |r|^2 (default: the frozen harness's 1e-12, or the
                       K1_GATE environment variable). 1e-16 means the
                       rebuilt state matches the target to |r| < 1e-8,
                       which is well inside double precision; the
                       effective value is printed at start-up and every
                       module that holds a copy of the constant is set.

Everything else -- plateau 0.01, growth, restarts, the per-column 2x2
rotation count -- is the frozen harness's code. The
proposal construction itself (pool enumeration and scoring) is not
counted as rotations; it is O(pool x dim) vector work and is reported
in provenance.

Outputs go to k1c_runs/<tag>_{state.pkl,trace.jsonl,summary.json};
the chain .npz and the results/ report follow the frozen harness's
paths inside THIS checkout (never the campaign checkout).

Usage (H6, dense target):
    python k1c_warmstart.py k1_h6_ring_19 --arm cold --insert post-joint --target dense
    python k1c_warmstart.py k1_h6_ring_19 --arm pred --pred-source tangent --insert post-joint --target dense
    python k1c_warmstart.py k1_h6_ring_19 --arm pred --pred-source tangent --scale-mult 0.5 --pred-tag tangent_half --insert post-joint --target dense
    python k1c_warmstart.py k1_h6_ring_19 --arm pred --pred-file k1c_proposals/k1_h6_ring_19_model_s0.pkl --pred-tag model_s0 --insert post-joint --target dense
"""
import argparse
import hashlib
import importlib.util as iu
import inspect
import json
import os
import pickle
import sys
import time

import numpy as np

if os.name == "nt":
    # On Windows a just-written file can be held briefly by the antivirus
    # scanner or the search indexer, and os.replace then fails with
    # "Access is denied" (WinError 5). The frozen harness's save() calls
    # os.replace at every phase transition; retrying a few times with a
    # short pause is the standard remedy and changes nothing when the
    # rename succeeds first time.
    _os_replace = os.replace

    def _replace_retry(src, dst, *a, **k):
        for i in range(12):
            try:
                return _os_replace(src, dst, *a, **k)
            except PermissionError:
                time.sleep(0.25 * (i + 1))
        return _os_replace(src, dst, *a, **k)

    os.replace = _replace_retry

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "src"))


def _load(name, fn):
    spec = iu.spec_from_file_location(name, os.path.join(HERE, fn))
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kb = _load("k1b_warmstart", "k1b_warmstart.py")      # installs the counters
kp = _load("kp", "k1c_pool.py")                      # pool + TOP
p1 = kp.p1                                           # tangent_scores
from chaincompile import compile as _cc                  # noqa: E402
from chaincompile.compile import _gauss_newton, _prep   # noqa: E402


# ------------------------------------------------------------ gauge knobs
# Three conventions of the compiler are made settable at run time. None of
# them changes the certified state; each changes which factorization the
# compiler produces. No file under src/ is edited.
#
#   --pivot-rank N   use the N-th largest-amplitude determinant as the
#                    reference instead of the largest (requires
#                    --target dense; the checkpoint path carries its own
#                    pivot). Routing, greedy ordering and everything
#                    downstream key off the pivot, so this changes the
#                    whole chain, prefix included.
#   --support-tol X  amplitude threshold defining the support. Raising it
#                    routes fewer determinants and grows more; lowering it
#                    does the reverse.
#   --tie-seed S     replaces the canonical tie-break (smallest key) with a
#                    seeded hash of the key. It can only change the outcome
#                    where scores are equal within TIE_TOL, i.e. on genuine
#                    ties; any tie-break yields a valid factorization.

def _hkey(k, seed):
    return hashlib.blake2b(repr(k).encode(), digest_size=8,
                           key=str(seed).encode()).digest()


_argmax_frozen = _cc._canon_argmax
_desc_frozen = _cc._canon_desc
_route_frozen = _cc._route_sequence
_norm_frozen = _cc._normalize_target


def _canon_argmax(cands):
    s = CFG["tie_seed"]
    if not s:
        return _argmax_frozen(cands)
    return _argmax_frozen((sc, _hkey(k, s), pl) for sc, k, pl in cands)


def _canon_desc(cands):
    s = CFG["tie_seed"]
    if not s:
        return _desc_frozen(cands)
    return _desc_frozen([(sc, _hkey(k, s), pl) for sc, k, pl in cands])


def _route_sequence(c_t, basis, pivot_mask, support_tol):
    tol = CFG["support_tol"] if CFG["support_tol"] else support_tol
    return _route_frozen(c_t, basis, pivot_mask, tol)


def _normalize_target(target, basis, pivot_mask):
    r = int(CFG["pivot_rank"])
    if r and pivot_mask is None:
        c = np.asarray(target, float)
        order = np.argsort(-np.abs(c))
        pivot_mask = int(basis.masks[order[min(r, len(order) - 1)]])
    return _norm_frozen(target, basis, pivot_mask)


# ------------------------------------------------------------ fast Jacobian
# The frozen _gauss_newton builds the Jacobian one letter at a time and, at
# every letter, copies the whole dim x k block built so far
# (apply_ucc_factor_cols copies its input) although only the rows of that
# letter's 2x2 blocks change -- about a tenth of the rows on H8. The build
# below rotates those rows in place, with the same arithmetic in the same
# order, so the Jacobian is identical bit for bit and every member compiles
# to exactly the chain it would have compiled to, only sooner (4.9x on the
# H8 chain, 4,900 x 6,333, measured; the build is ~97% of an iteration).
# The harness's work counters (rot, gn_iters) are advanced exactly as the
# frozen build advances them. K1_FROZEN_JACOBIAN=1 restores the frozen build.
def _jacobian_inplace(a, seq, th, basis):
    N = len(seq)
    W = kb.WORK
    J = np.zeros((basis.dim, N))
    for k in range(N):
        ii, jj, ss = basis.block_arrays(seq[k][0])
        if k:
            W["rot"] += len(ii) * k
            if k == 1:
                W["gn_iters"] += 1
            ct, st = np.cos(th[k]), np.sin(th[k])
            lo, up = J[ii, :k], J[jj, :k]
            sst = (ss * st)[:, None]
            J[ii, :k] = ct * lo - sst * up
            J[jj, :k] = sst * lo + ct * up
        src = a[k + 1]
        J[jj, k] = ss * src[ii]
        J[ii, k] = -ss * src[jj]
    return J


def _gauss_newton_fast(thetas, seq, basis, pivot_mask, ct, tol, max_iter=200,
                       bound=None, start=None):
    """chaincompile.compile._gauss_newton with the in-place Jacobian build;
    everything else verbatim."""
    N = len(seq)
    lam = 1e-8
    if bound is None:
        to_th = lambda x: x                                    # noqa: E731
        dth_dx = lambda x: np.ones_like(x)                     # noqa: E731
        x = thetas.copy()
    else:
        to_th = lambda x: bound * np.tanh(x)                   # noqa: E731
        dth_dx = lambda x: bound * (1.0 - np.tanh(x) ** 2)     # noqa: E731
        x = np.arctanh(np.clip(thetas / bound, -0.9999, 0.9999))
    th = to_th(x)
    psi = _prep(th, seq, basis, pivot_mask, start=start)
    res = psi - ct
    rn = np.linalg.norm(res)
    for _ in range(max_iter):
        if rn < tol:
            break
        a = [basis.basis_vector(pivot_mask) if start is None else start.copy()]
        for (sub, _, _), t in zip(seq, th):
            a.append(_cc.apply_ucc_factor(a[-1], basis, sub, t))
        J = _jacobian_inplace(a, seq, th, basis)
        J = J * dth_dx(x)[None, :]
        JtJ = J.T @ J
        g = J.T @ res
        for _ in range(60):
            try:
                delta = np.linalg.solve(JtJ + lam * np.eye(N), -g)
            except np.linalg.LinAlgError:  # pragma: no cover
                lam *= 10
                continue
            x_new = x + delta
            th_new = to_th(x_new)
            psi_new = _prep(th_new, seq, basis, pivot_mask, start=start)
            rn_new = np.linalg.norm(psi_new - ct)
            if rn_new < rn:
                x, th = x_new, th_new
                psi, rn, res = psi_new, rn_new, psi_new - ct
                lam = max(lam / 3.0, 1e-14)
                break
            lam *= 10.0
        else:  # pragma: no cover
            break
    return th, rn


FAST_JACOBIAN = os.environ.get("K1_FROZEN_JACOBIAN", "") not in ("1", "true", "yes")


def _install_gauge():
    """Rebind in every namespace that resolved these names at import."""
    global _gauss_newton
    for mod in (_cc, kb.big, kb):
        for nm, fn in (("_canon_argmax", _canon_argmax),
                       ("_canon_desc", _canon_desc),
                       ("_route_sequence", _route_sequence),
                       ("_normalize_target", _normalize_target)):
            if hasattr(mod, nm):
                setattr(mod, nm, fn)
        if FAST_JACOBIAN and hasattr(mod, "_gauss_newton"):
            setattr(mod, "_gauss_newton", _gauss_newton_fast)
    if FAST_JACOBIAN:
        _gauss_newton = _gauss_newton_fast
    kb.load_target = _load_target


# ------------------------------------------------------------ cached target
# The frozen load_target diagonalizes the dump inside EVERY member and
# refuses dimensions above 6,000. For the corpus the target is computed
# once per stem and cached as data/<stem>_target.npz (the raw eigenvector;
# every member still applies its own pivot convention to it), dense up to
# DENSE_LIMIT and by sparse Lanczos on the package's SparseH above that.
# --target checkpoint is untouched.
DENSE_LIMIT = 20000
_load_target_frozen = kb.load_target


def _target_vector(stem, h, e, basis):
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    cache = os.path.join(HERE, "data", stem + "_target.npz")
    if os.path.exists(cache):
        try:
            z = np.load(cache)
            v0 = np.asarray(z["v0"], float)
            out = (v0, float(z["e0"]), str(z["how"]), float(z["gap"]))
        except Exception as ex:
            print("target cache %s unreadable (%s); recomputing"
                  % (os.path.basename(cache), ex.__class__.__name__), flush=True)
            os.remove(cache)
        else:
            if v0.size != basis.dim:
                raise RuntimeError("%s holds a vector of size %d, sector dim is %d"
                                   % (cache, v0.size, basis.dim))
            return out
    t0 = time.time()
    if basis.dim <= DENSE_LIMIT:
        H = kb.build_h_sector(h, e, basis)
        w, V = np.linalg.eigh(H)
        v0, e0, how = V[:, 0], float(w[0]), "dense eigh"
        gap = float(w[1] - w[0]) if len(w) > 1 else float("inf")
        del H, V
    else:
        from scipy.sparse.linalg import LinearOperator, eigsh
        from chaincompile.fastpath import SparseH
        sp = SparseH(h, e, basis)
        op = LinearOperator((basis.dim, basis.dim), matvec=sp.matvec,
                            dtype=float)
        w, V = eigsh(op, k=2, which="SA", tol=1e-12, maxiter=200000)
        o = np.argsort(w)
        v0, e0, how = V[:, o[0]], float(w[o[0]]), "sparse Lanczos (eigsh)"
        gap = float(w[o[1]] - w[o[0]])
        r = np.linalg.norm(sp.matvec(v0) - e0 * v0)
        how += " residual %.1e" % r
    v0 = v0 / np.linalg.norm(v0)
    tmp = cache + ".tmp.npz"
    np.savez(tmp, v0=v0, e0=e0, how=how, gap=gap, seconds=time.time() - t0)
    os.replace(tmp, cache)
    if gap < 1e-6:
        print("WARNING: %s has a degenerate ground state (gap %.1e); the "
              "target is one vector of that subspace" % (stem, gap), flush=True)
    return v0, e0, how, gap


def _load_target(stem, target_mode):
    if target_mode != "dense":
        return _load_target_frozen(stem, target_mode)
    dump = kb.kh._dumppath(stem)
    # dumps minted by k1c_corpus.py (recognized by their sidecar) hold the
    # active orbitals only; k1_harness's prefix table ("n2" -> 2 cores,
    # ...) must not apply to them
    minted = os.path.exists(os.path.join(HERE, "k1_corpus", stem + ".json"))
    n_core = 0 if minted else kb.kh._ncore(stem)
    h, e, e_nuc, e_scf, na, nb, meta = kb.load_integral_dump(dump)
    h, e, e_core = kb.freeze_core(h, e, n_core)
    basis = kb.SectorBasis(h.shape[0], na - n_core, nb - n_core)
    info = {"dump": os.path.basename(dump), "n_core": n_core,
            "e_shift": float(e_nuc + e_core), "dim": basis.dim,
            "nmo": int(h.shape[0]), "na": na - n_core, "nb": nb - n_core}
    v0, e0, how, gap = _target_vector(stem, h, e, basis)
    ct, pivot_mask, _ = kb._normalize_target(v0, basis, None)
    info.update({"target": "%s of the dump (root 0), cached" % how,
                 "support_tol": 1e-10, "e0": float(e0 + info["e_shift"]),
                 "gap": gap, "campaign_len": None})
    return ct, pivot_mask, basis, (h, e), info

RUNS = os.path.join(HERE, "k1c_runs")
CFG = {"insert": "greedy", "pred_file": None, "pred_tag": None,
       "pred_source": "file", "scale": None, "scale_mult": 1.0,
       "top": kp.TOP, "plateau": kb.PLATEAU_DEFAULT, "live": None,
       "prejoint_iters": 300, "pivot_rank": 0, "support_tol": None,
       "tie_seed": 0, "gate": None}


def allocate(scores, total):
    """Largest-remainder allocation of `total` copies proportional to
    scores (letters with zero score get nothing)."""
    scores = np.asarray(scores, float)
    out = np.zeros(len(scores), int)
    idx = np.where(scores > 0)[0]
    if total < 1 or len(idx) == 0:
        return out
    s = scores[idx] / scores[idx].sum() * total
    fl = np.floor(s).astype(int)
    rem = int(total - fl.sum())
    fl[np.argsort(-(s - fl))[:max(0, rem)]] += 1
    out[idx] = fl
    return out


# ------------------------------------------------------------ proposals
_build_seed_frozen = kb.build_seed


def _live_proposal():
    L = CFG["live"]
    if L is None:
        raise SystemExit("live proposal source needs --insert post-joint "
                         "(the insertion state was not captured)")
    psi = _prep(L["thetas"], L["seq"], L["basis"], L["pivot"])
    resv = psi - L["ct"]
    kp.TOP = int(CFG["top"])
    pool = kp.round_one_pool(L["basis"], resv)
    keys = sorted(pool)
    if CFG["pred_source"] == "poolall":
        counts = np.ones(len(keys), int)
        n_target = len(keys)
    elif CFG["pred_source"] == "topk":
        ts = p1.tangent_scores({"basis": L["basis"], "psi": psi,
                                "resv": resv}, keys)
        n_target = int(CFG["scale"]) if CFG["scale"] else \
            int(round(CFG["scale_mult"] * len(keys)))
        counts = np.zeros(len(keys), int)
        counts[np.argsort(-ts)[:max(1, n_target)]] = 1
    else:
        ts = p1.tangent_scores({"basis": L["basis"], "psi": psi,
                                "resv": resv}, keys)
        n_target = int(CFG["scale"]) if CFG["scale"] else \
            int(round(CFG["scale_mult"] * len(keys)))
        counts = allocate(ts, n_target)
    word = [k for k, c in zip(keys, counts) for _ in range(int(c))]
    th = [0.0] * len(word)
    cnt = kb.kh.counts(word)
    weights = [float(cnt[w]) for w in word]
    return word, th, weights, {"pool": len(keys), "top": int(CFG["top"]),
                               "scale_target": n_target,
                               "prejoint_iters": int(CFG["prejoint_iters"]),
                               "pivot_rank": int(CFG["pivot_rank"]),
                               "support_tol": CFG["support_tol"],
                               "tie_seed": int(CFG["tie_seed"]),
                               "rn_at_insertion": float(np.linalg.norm(resv))}


def build_seed(stem, arm, order, pred_seed, n_routed, routed_word):
    if arm == "pred" and CFG["pred_source"] in ("tangent", "poolall", "topk"):
        word, th, weights, info = _live_proposal()
        pairs = kb._round_robin(word, th, weights)
        if order == "shuffle":
            pairs = kb._shuffle(pairs)
        prov = {"arm": arm, "order": order, "source": CFG["pred_source"],
                "insert": CFG["insert"], "n": len(word),
                "n_distinct": len(set(word)), "theta": "zero"}
        prov.update(info)
        return pairs, None, prov
    if arm == "pred" and CFG["pred_file"]:
        with open(CFG["pred_file"], "rb") as fh:
            P = pickle.load(fh)
        word, th = P["preds"][pred_seed]
        word = [tuple(map(tuple, x)) for x in word]
        cnt = kb.kh.counts(word)
        weights = [cnt[L] + 1e-3 * abs(t) for L, t in zip(word, th)]
        pairs = kb._round_robin(word, th, weights)
        prov = {"arm": arm, "order": order,
                "source": os.path.basename(CFG["pred_file"]),
                "pred_seed": pred_seed, "config": P.get("config"),
                "insert": CFG["insert"], "n": len(word),
                "n_distinct": len(cnt)}
        if order == "shuffle":
            pairs = kb._shuffle(pairs)
        return pairs, None, prov
    pairs, routed_theta, prov = _build_seed_frozen(
        stem, arm, order, pred_seed, n_routed, routed_word)
    prov["insert"] = CFG["insert"]
    return pairs, routed_theta, prov


kb.build_seed = build_seed


# ------------------------------------------------------------ insertion
_solve_frozen = kb.big.solve_resumable


def solve_resumable(*args, **kw):
    """Post-joint insertion: after the frozen driver stops at the greedy
    state, run the joint phase exactly as the driver would (slices of
    10, plateau rule, 300-iteration budget), capture the state for live
    proposals, then hand it back at phase 'joint' with a fresh budget so
    the frozen run_arm appends the proposal and re-solves. Signature-
    agnostic: the driver recurses into this name positionally."""
    b = inspect.signature(_solve_frozen).bind(*args, **kw)
    b.apply_defaults()
    A = b.arguments
    ct, basis, pivot_mask, state = A["ct"], A["basis"], A["pivot_mask"], A["state"]
    log, save = A["log"], A["save"]
    stop = bool(A.get("stop_after_greedy", False))
    # A state file remembers the gate it was solved under. Resuming it at a
    # different gate would certify a chain at the wrong tolerance (a 1e-12
    # state resumed at phase 'noc' would pass straight to the summary), so
    # the mismatch is refused and the file named.
    want = float(CFG["gate"]) if CFG["gate"] is not None else float(kb.GATE)
    have = state.setdefault("k1c_gate", want)
    if abs(have - want) > 1e-3 * want:
        raise SystemExit(
            "this member's saved state was solved under gate %g; requested "
            "%g. Delete k1c_runs/<tag>_state.pkl (and the trace) to recompile "
            "it at the new gate." % (have, want))
    if CFG["gate"] is not None:
        # the certification gate is solve_resumable's fid_tol keyword (the
        # driver recurses into this wrapper positionally, so every level
        # of the recursion receives it here)
        A["fid_tol"] = float(CFG["gate"])
        args, kw = b.args, b.kwargs
    if not (CFG["insert"] == "post-joint" and stop):
        return _solve_gated(state, ct, basis, pivot_mask, args, kw)
    if state["phase"] in ("route", "greedy"):
        r = _solve_gated(state, ct, basis, pivot_mask, args, kw)
        if state["phase"] != "joint":
            return r
    if state["phase"] == "joint" and not state.get("k1c_prejoint_done"):
        plateau = CFG["plateau"]
        state["iters_left"] = min(int(state["iters_left"]),
                                  int(CFG["prejoint_iters"]))
        while True:
            budget = min(state["iters_left"], 10)
            if budget <= 0:
                break
            rn_before = state["rn"]
            state["thetas"], state["rn"] = _gauss_newton(
                state["thetas"], state["seq"], basis, pivot_mask, ct,
                tol=1e-13, max_iter=budget, bound=kb.big.BOUND)
            state["iters_left"] -= budget
            log("prejoint: |r| %.3e (iters left %d, len %d)"
                % (state["rn"], state["iters_left"], len(state["seq"])))
            if state["rn"] ** 2 < (CFG["gate"] if CFG["gate"] is not None
                                   else kb.GATE):
                break
            if plateau is not None and rn_before > 0 and \
                    (rn_before - state["rn"]) < plateau * rn_before:
                log("prejoint: plateau exit (slice gain %.2e < %s)"
                    % ((rn_before - state["rn"]) / rn_before, plateau))
                break
        state["k1c_prejoint_done"] = True
        state["rn_prejoint"] = float(state["rn"])
        state["phase"] = "joint"
        state["iters_left"] = 300
        save()
        log("post-joint insertion point: |r| %.3e after the uncharged joint "
            "solve; proposal appended next" % state["rn"])
    CFG["live"] = {"basis": basis, "pivot": pivot_mask, "ct": ct,
                   "thetas": np.asarray(state["thetas"], float),
                   "seq": list(state["seq"])}
    return False


def _stable_deficit(rn):
    """1 - |<ct|psi>|^2 from the residual norm rn = |psi - ct| of two unit
    vectors: exactly rn^2 - rn^4/4. Resolves far below the ~2e-16 floor of
    the direct formula."""
    r2 = float(rn) ** 2
    return max(0.0, r2 - 0.25 * r2 * r2)


def _solve_gated(state, ct, basis, pivot_mask, args, kw):
    """Run the frozen driver. Its 'final' phase re-derives the deficit with
    the direct formula 1 - |<ct|psi>|^2, which cannot resolve below ~2e-16
    and so, at a gate of 1e-16, rejects converged chains at random. When
    that happens (the loop itself already established rn^2 < fid_tol) the
    final transition is completed here exactly as the driver would have,
    with the deficit recorded from rn instead."""
    try:
        r = _solve_frozen(*args, **kw)
    except RuntimeError as ex:
        gate = CFG["gate"]
        if gate is None or "solve stalled" not in str(ex) or \
                state.get("phase") != "final" or \
                not (state["rn"] ** 2 < gate):
            raise
        state["thetas"] = np.array([kb.big._fold_pi(t) for t in state["thetas"]])
        state["residual"] = _stable_deficit(state["rn"])
        state["phase"] = "noc"
        state["noc_k"] = 0
        state["U"] = {((), ()): 1.0}
        state["sizes"] = []
        return True
    if state.get("phase") == "noc" and "residual" in state and \
            CFG["gate"] is not None:
        state["residual"] = _stable_deficit(state["rn"])
    return r


kb.big.solve_resumable = solve_resumable


# ------------------------------------------------------------ paths
def _paths(stem, arm, pred_seed, order):
    tag = "%s_%s" % (stem, arm)
    if arm == "pred":
        tag += "_%s" % (CFG["pred_tag"] or "s%d" % pred_seed)
    if order != kb._default_order(arm):
        tag += "_" + order
    if CFG["insert"] == "post-joint":
        tag += "_pj"
        if int(CFG["prejoint_iters"]) != 300:
            tag += str(int(CFG["prejoint_iters"]))
    if int(CFG["pivot_rank"]):
        tag += "_pv%d" % int(CFG["pivot_rank"])
    if CFG["support_tol"]:
        tag += "_st%g" % float(CFG["support_tol"])
    if int(CFG["tie_seed"]):
        tag += "_ts%d" % int(CFG["tie_seed"])
    os.makedirs(RUNS, exist_ok=True)
    return (tag, os.path.join(RUNS, tag + "_state.pkl"),
            os.path.join(RUNS, tag + "_trace.jsonl"),
            os.path.join(RUNS, tag + "_summary.json"))


kb._paths = _paths


# ------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stem")
    ap.add_argument("--arm", choices=kb.ARMS, default="cold")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--order", choices=("rank", "shuffle"), default=None)
    ap.add_argument("--plateau", default=str(kb.PLATEAU_DEFAULT))
    ap.add_argument("--deadline", type=float, default=14400)
    ap.add_argument("--target", choices=("checkpoint", "dense"),
                    default="dense")
    ap.add_argument("--insert", choices=("greedy", "post-joint"),
                    default="post-joint")
    ap.add_argument("--pred-file", default=None)
    ap.add_argument("--pred-source",
                    choices=("file", "tangent", "poolall", "topk"),
                    default="file")
    ap.add_argument("--pred-tag", default=None)
    ap.add_argument("--scale", type=int, default=None)
    ap.add_argument("--scale-mult", type=float, default=1.0)
    ap.add_argument("--top", type=int, default=kp.TOP)
    ap.add_argument("--prejoint-iters", type=int, default=300)
    ap.add_argument("--pivot-rank", type=int, default=0,
                    help="gauge: use the N-th largest-amplitude determinant "
                         "as the reference (needs --target dense)")
    ap.add_argument("--support-tol", type=float, default=None,
                    help="gauge: amplitude threshold defining the support")
    ap.add_argument("--tie-seed", type=int, default=0,
                    help="gauge: seeded tie-break instead of smallest-key")
    ap.add_argument("--translate", action="store_true")
    ap.add_argument("--prepare-target", action="store_true",
                    help="compute and cache the target for this stem, then exit")
    ap.add_argument("--gate", type=float,
                    default=float(os.environ["K1_GATE"]) if "K1_GATE" in os.environ else None,
                    help="certification gate on |r|^2 (default: harness value)")
    a = ap.parse_args()
    a.plateau = None if str(a.plateau).lower() == "none" else float(a.plateau)
    if a.order is None:
        a.order = kb._default_order(a.arm)
    if a.arm == "pred":
        if a.pred_source == "file" and not a.pred_file and a.stem != "h8_chain":
            raise SystemExit("--arm pred needs --pred-file (or --pred-source "
                             "tangent|poolall) for stems other than h8_chain")
        if a.pred_source != "file" and a.insert != "post-joint":
            raise SystemExit("--pred-source %s requires --insert post-joint"
                             % a.pred_source)
        if a.pred_source != "file" and not a.pred_tag:
            a.pred_tag = a.pred_source + "_live"
    CFG.update({"insert": a.insert, "pred_file": a.pred_file,
                "pred_tag": a.pred_tag, "pred_source": a.pred_source,
                "scale": a.scale, "scale_mult": a.scale_mult,
                "top": a.top, "plateau": a.plateau, "live": None,
                "prejoint_iters": a.prejoint_iters,
                "pivot_rank": a.pivot_rank, "support_tol": a.support_tol,
                "tie_seed": a.tie_seed})
    if a.pivot_rank and a.target != "dense":
        raise SystemExit("--pivot-rank requires --target dense")
    _install_gauge()
    if a.prepare_target:
        ct, pm, basis, _, info = _load_target(a.stem, "dense")
        print("target %s: dim %d, E0 %.10f, gap %.3e, pivot %d (%s)"
              % (a.stem, info["dim"], info["e0"], info["gap"], pm,
                 info["target"]), flush=True)
        return
    if a.gate is not None:
        _set_gate(a.gate)
    _refuse_stale_state(a)
    a.score = False
    kb.run_arm(a)
    _check_certificate(a)


def _refuse_stale_state(a):
    """A saved state carries the gate it was solved under (k1c_gate; absent
    on states from before this knob existed, which were solved at the
    harness default). Resuming one at a different gate would certify at
    the wrong tolerance, so the mismatch is refused here, before the
    harness loads it, whatever phase it is in."""
    want = float(CFG["gate"]) if CFG["gate"] is not None else float(kb.GATE)
    tag, spath, tpath, jpath = _paths(a.stem, a.arm, a.seed, a.order)
    if not os.path.exists(spath):
        return
    try:
        with open(spath, "rb") as fh:
            have = float(pickle.load(fh).get("k1c_gate", kb.GATE))
    except Exception as ex:
        # a checkpoint cut short by a preemption: start this member over
        print("saved state %s unreadable (%s); removed, starting the member over"
              % (os.path.basename(spath), ex.__class__.__name__), flush=True)
        for q in (spath, tpath):
            if os.path.exists(q):
                os.remove(q)
        return
    if abs(have - want) > 1e-3 * want:
        raise SystemExit(
            "saved state %s was solved under gate %g; requested %g. Delete it "
            "(and %s) to recompile this member at the new gate."
            % (os.path.basename(spath), have, want, os.path.basename(tpath)))


def _check_certificate(a):
    """After the harness returns: if it wrote a summary, its residual must
    satisfy the requested gate. The frozen harness gates its final re-check
    at kb.GATE (a guard, section _set_gate); this is the real check, on the
    residual recorded with the stable formula. A failing summary and its
    chain are removed so the gauge factory re-runs the member rather than
    counting it."""
    if CFG["gate"] is None:
        return
    tag, spath, tpath, jpath = _paths(a.stem, a.arm, a.seed, a.order)
    if not os.path.exists(jpath):
        return
    with open(jpath) as fh:
        s = json.load(fh)
    res = float(s.get("residual", float("inf")))
    if res <= float(CFG["gate"]):
        return
    chain = os.path.join(HERE, "k1b", tag + "_chain.npz")
    for p in (jpath, chain):
        if os.path.exists(p):
            os.remove(p)
    raise SystemExit("certificate residual %.3e is above the requested gate "
                     "%g; summary and chain removed (state kept at %s)"
                     % (res, CFG["gate"], os.path.basename(spath)))


def _set_gate(gate):
    """Certification gate on |r|^2 for this member. It reaches the driver
    as solve_resumable's fid_tol (see the wrapper) and the pre-insertion
    solve directly. The frozen harness's own re-check (k1b_warmstart.GATE,
    a direct 1 - |<ct|psi>|^2 that cannot resolve below ~2e-16) is left at
    its value as a gross-failure guard; it is only ever LOOSENED here, when
    a gate above it is requested. Nothing under src/ or in the frozen
    harness is edited."""
    gate = float(gate)
    if not (0.0 < gate < 1e-3):
        raise SystemExit("--gate %g is not a sensible squared residual" % gate)
    if gate < 1e-24:
        print("WARNING: gate %g is near the double-precision floor of the "
              "residual (~(sqrt(D)*sqrt(L)*1e-16)^2); expect members to stall"
              % gate, flush=True)
    CFG["gate"] = gate
    note = "gate: solver fid_tol 1e-12 -> %g" % gate
    if gate > kb.GATE:
        note += "; harness re-check %g -> %g" % (kb.GATE, gate)
        kb.GATE = gate
    else:
        note += "; harness re-check stays %g (direct formula, guard only)" % kb.GATE
    print(note, flush=True)


if __name__ == "__main__":
    main()

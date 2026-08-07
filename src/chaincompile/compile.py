"""Compile-from-target chain selector.

Two modes, one artifact format:

'direct'    Sequential Givens elimination against the running vector.
            Each step pairs the largest remaining determinant mu with the
            pivot via the rank-r substitution connecting them (r = mu's
            excitation rank) and zeroes it with a closed-form angle.
            Top-rank eliminations have no side blocks, pivot weight is
            monotone, and the ledger IS the truncation curve:
            fid(K) = pivot amplitude after K elimination steps. Short
            chains, high-rank generators (translation-hostile).

'sd_routed' Only singles/doubles generators; high-rank determinants are
            routed through intermediate determinants. Sequential greedy
            Givens provably CYCLES here (minimal counterexample: the
            4-site half-filled Hubbard ground state, where the quadruple
            amplitude is the sin^2 side effect of two doubles -- the
            coupling P2 Table 1 solves in closed form with its
            theta_4 = atan(gamma/alpha) - atan(tan^2 theta_3)). The
            angles of an SD-only chain satisfy COUPLED equations, so
            this mode is two-phase:
              1. routing: a deterministic factor sequence, one S/D
                 factor per support determinant, each connecting it to
                 a parent of lower rank (largest-|c| parent wins;
                 synthetic intermediates inserted when needed);
              2. solve: damped Gauss-Newton with target homotopy
                 (exact Jacobian) for all angles jointly, with
                 residual-driven growth if the word is too short.
            Exactness is asserted; the prefix-fidelity ledger is
            computed directly (not monotone in general).

Both modes emit the same CompileResult: prep-order factors, per-step
ledger with fid_after, angle flags for the CC-translation bounds
(|theta| <= pi/4 comfortable, |theta| < pi/2 required).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .dets import Substitution, popcount, substitution_between
from .factors import apply_ucc_factor, apply_ucc_factor_cols, iter_blocks
from .sector import SectorBasis

PRUNE = 1e-14


@dataclass
class LedgerRow:
    step: int
    sub: Substitution
    theta: float
    mu_mask: int          # determinant this factor is routed for / eliminates
    nu_mask: int          # partner (parent / pivot)
    rank_mu: int
    rank_nu: int
    c_mu: float           # target amplitude on mu
    c_nu: float           # target amplitude on nu
    fid_after: float      # |<target | psi_K>| for the K = step prefix
    flag: str = ""


@dataclass
class CompileResult:
    pivot_mask: int
    mode: str
    policy: str
    factors: list = field(default_factory=list)   # prep order: [(sub, theta)]
    ledger: list = field(default_factory=list)
    final_residual: float = 0.0                   # 1 - fid(full)^2
    global_sign: int = 1
    target: np.ndarray | None = None              # sign-fixed normalized target
    solver_info: dict = field(default_factory=dict)

    @property
    def length(self) -> int:
        return len(self.factors)

    def selected(self, K: int | None = None):
        K = self.length if K is None else K
        return self.factors[:K]

    def max_abs_theta(self, K: int | None = None) -> float:
        return max((abs(t) for _, t in self.selected(K)), default=0.0)

    def rank_counts(self, K: int | None = None) -> dict:
        out: dict = {}
        for sub, _ in self.selected(K):
            out[sub.rank] = out.get(sub.rank, 0) + 1
        return out


def prepare_state(res: CompileResult, basis: SectorBasis, K: int | None = None) -> np.ndarray:
    """State prepared by the first K prep-order factors applied to the pivot
    (factor 1 applied first)."""
    v = basis.basis_vector(res.pivot_mask)
    for sub, theta in res.selected(K):
        v = apply_ucc_factor(v, basis, sub, theta)
    return v


# ======================================================================
# shared helpers
# ======================================================================
def _normalize_target(target, basis, pivot_mask):
    c = np.array(target, dtype=float).copy()
    n = np.linalg.norm(c)
    if n == 0:
        raise ValueError("zero target")
    c /= n
    if pivot_mask is None:
        pivot_mask = _canon_argmax(
            (abs(c[i]), basis.masks[i], basis.masks[i])
            for i in range(basis.dim))
    p = basis.index[pivot_mask]
    if abs(c[p]) < 1e-12:
        raise ValueError("target has ~zero amplitude on the pivot determinant")
    if c[p] < 0:
        c = -c
    return c, pivot_mask, p


TIE_TOL = 1e-9  # relative: symmetry-tied scores differ only by BLAS noise


def _canon_argmax(cands):
    """cands: iterable of (score, key, payload). Payload of the canonical
    maximum: largest score, ties within a relative TIE_TOL broken by
    SMALLEST key -- so symmetry-degenerate choices (scores equal up to
    platform/BLAS rounding) resolve identically on every machine
    (METHOD.md section 13)."""
    bs = bk = bp = None
    for sc, k, pl in cands:
        if bs is None:
            bs, bk, bp = sc, k, pl
            continue
        scale = max(abs(sc), abs(bs), 1e-300)
        if sc > bs + TIE_TOL * scale:
            bs, bk, bp = sc, k, pl
        elif sc > bs - TIE_TOL * scale and k < bk:
            bs, bk, bp = max(sc, bs), k, pl
    return bp


def _canon_desc(cands):
    """cands: list of (score, key, payload). Payloads sorted by score
    descending, ties within relative TIE_TOL broken by ascending key
    (platform-canonical ordering; METHOD.md section 13)."""
    s0 = sorted(cands, key=lambda t: -t[0])
    out, i, n = [], 0, len(s0)
    while i < n:
        j = i + 1
        while j < n:
            scale = max(abs(s0[j - 1][0]), abs(s0[j][0]), 1e-300)
            if s0[j - 1][0] - s0[j][0] > TIE_TOL * scale:
                break
            j += 1
        out.extend(sorted(s0[i:j], key=lambda t: t[1]))
        i = j
    return [t[2] for t in out]


def _fold_pi(phi: float) -> float:
    """Fold to (-pi, pi] (exp(theta kappa) has period 2 pi)."""
    while phi > math.pi:
        phi -= 2 * math.pi
    while phi <= -math.pi:
        phi += 2 * math.pi
    return phi


def _angle_flag(theta: float) -> str:
    if abs(theta) >= math.pi / 2 - 1e-9:
        return "gt_pi2"          # tan-theta bridge invalid
    if abs(theta) > math.pi / 4:
        return "warn_gt_pi4"
    return ""


# ======================================================================
# direct mode: sequential Givens elimination (exact ledger theorem)
# ======================================================================
def _compile_direct(c, basis, pivot_mask, p, policy, fid_tol, max_steps):
    rank_of = [basis.rank_between(m, pivot_mask) for m in basis.masks]
    elim = []  # (sub, phi) elimination order
    rows = []
    steps_cap = max_steps or 20 * basis.dim
    for step in range(1, steps_cap + 1):
        residual = 1.0 - c[p] ** 2
        if residual < fid_tol:
            break
        # fidelity-derived support floor: amplitudes below this cannot
        # move the residual past fid_tol, so eliminating them only adds
        # noise-sensitive null steps (platform determinism, METHOD sec 13)
        floor = max(PRUNE, math.sqrt(fid_tol) / max(1, basis.dim))
        support = [i for i in range(basis.dim) if i != p and abs(c[i]) > floor]
        if policy == "amp_major":
            pool = support
        else:  # rank_major default
            rmax = max(rank_of[i] for i in support)
            pool = [i for i in support if rank_of[i] == rmax]
        mu_i = _canon_argmax((abs(c[i]), basis.masks[i], i) for i in pool)
        mu = basis.masks[mu_i]
        sub = substitution_between(pivot_mask, mu)  # pivot = lower, mu = upper
        _, s = sub.apply_a(pivot_mask)
        # zero the upper member: new c_up = s sin(phi) c_lo + cos(phi) c_up = 0
        phi = math.atan2(-c[mu_i], s * c[p])
        while phi > math.pi / 2:
            phi -= math.pi
        while phi <= -math.pi / 2:
            phi += math.pi
        c_mu0, c_p0 = c[mu_i], c[p]
        c = apply_ucc_factor(c, basis, sub, phi)
        if abs(c[mu_i]) > 1e-9:  # pragma: no cover
            raise AssertionError("direct elimination failed to zero target")
        c[np.abs(c) < PRUNE] = 0.0
        elim.append((sub, phi))
        rows.append(
            LedgerRow(
                step=step, sub=sub, theta=phi, mu_mask=mu, nu_mask=pivot_mask,
                rank_mu=rank_of[mu_i], rank_nu=0, c_mu=c_mu0, c_nu=c_p0,
                fid_after=float(abs(c[p])), flag=_angle_flag(phi),
            )
        )
    else:  # pragma: no cover
        raise RuntimeError(f"direct compile did not converge in {steps_cap} steps")

    gsign = 1 if c[p] > 0 else -1
    # prep order: eliminations reversed with negated angles; the ledger's
    # step-K prefix corresponds to prep factors [N-K+1 .. N] -- to keep the
    # unified "first K prep factors" truncation semantics, store prep order
    # as (elim_1 reversed): factors[j] = (sub_j, -phi_j) applied so that
    # factor 1 is elim step 1's inverse applied LAST... Instead we store
    # factors in the order that makes prefix K equal the theorem's psi_K:
    #   psi_K = exp(-phi_1 k_1) ... exp(-phi_K k_K) |pivot>
    # i.e. prep applies elim step K first. So factors[0] must be step K...
    # which depends on K. Resolution: store factors as the FULL prep order
    # [ (sub_N, -phi_N), ..., (sub_1, -phi_1) ] and OVERRIDE selection for
    # direct mode: the K-prefix is the LAST K of the elimination list,
    # applied in reverse. See _DirectResult.selected.
    return elim, rows, gsign, float(max(0.0, 1.0 - c[p] ** 2))


class _DirectResult(CompileResult):
    """Direct-mode result: prefix-K = first K eliminations (theorem form)."""

    def selected(self, K: int | None = None):
        K = len(self.solver_info["elim"]) if K is None else K
        steps = self.solver_info["elim"][:K]
        return [(sub, -phi) for sub, phi in reversed(steps)]

    @property
    def length(self) -> int:
        return len(self.solver_info["elim"])


# ======================================================================
# sd_routed mode: routing + joint angle solve
# ======================================================================
def _route_sequence(c_t, basis, pivot_mask, support_tol):
    """One S/D factor per routed determinant, parent of strictly lower rank.

    Parent choice: largest |c_target| among sector determinants within two
    electrons of the child at rank r-1 or r-2 (pivot competes as rank 0);
    synthetic intermediates (|c| ~ 0) are inserted and routed recursively
    when no populated parent is reachable. Returns list of
    (sub, child_mask, parent_mask) sorted stably by child rank.
    """
    p = basis.index[pivot_mask]
    rank_of = [basis.rank_between(m, pivot_mask) for m in basis.masks]
    idx_by_rank: dict = {}
    for i, m in enumerate(basis.masks):
        idx_by_rank.setdefault(rank_of[i], []).append(i)

    support = [
        i for i in range(basis.dim)
        if i != p and abs(c_t[i]) > support_tol
    ]
    support = _canon_desc(
        [(abs(c_t[i]), basis.masks[i], i) for i in support])
    support.sort(key=lambda i: rank_of[i])  # stable: canonical within rank

    ks = {basis.total_momentum(basis.masks[i]) for i in support}
    ks.add(basis.total_momentum(pivot_mask))
    k_pure = ks if len(ks) == 1 else None  # restrict routing to the K sector

    routed = {pivot_mask}
    seq: list = []

    def parent_candidates(mask, r):
        out = []
        for rr in (r - 2, r - 1):
            if rr < 0:
                continue
            for j in idx_by_rank.get(rr, []):
                nu = basis.masks[j]
                if k_pure and basis.total_momentum(nu) not in k_pure:
                    continue
                if popcount(mask & ~nu) <= 2:  # child differs by <= 2 electrons
                    out.append(j)
        return out

    def route(mask):
        if mask in routed:
            return
        i = basis.index[mask]
        r = rank_of[i]
        cands = parent_candidates(mask, r)
        if not cands:  # pragma: no cover - cannot happen for r >= 1
            raise RuntimeError(f"no S/D parent for {basis.det_label(mask)}")
        j = _canon_argmax(
            (abs(c_t[j]),
             (0 if basis.masks[j] == pivot_mask else 1, rank_of[j],
              basis.masks[j]),
             j)
            for j in cands)
        parent = basis.masks[j]
        route(parent)
        sub = substitution_between(parent, mask)
        assert sub.rank <= 2
        seq.append((sub, mask, parent))
        routed.add(mask)

    for i in support:
        route(basis.masks[i])
    seq.sort(key=lambda t: basis.rank_between(t[1], pivot_mask))  # stable
    return seq


def _prep(thetas, seq, basis, pivot_mask, K=None, start=None):
    v = basis.basis_vector(pivot_mask) if start is None else start.copy()
    K = len(seq) if K is None else K
    for (sub, _, _), th in zip(seq[:K], thetas[:K]):
        v = apply_ucc_factor(v, basis, sub, th)
    return v


def _gauss_newton(thetas, seq, basis, pivot_mask, ct, tol, max_iter=200,
                  bound=None, start=None):
    """Damped Gauss-Newton on F(theta) = prep(theta) - ct. Exact Jacobian:
    d psi / d theta_k = U_N ... U_{k+1} kappa_k U_k ... U_1 |pivot>.

    With `bound` set, solve in x with theta = bound * tanh(x): every angle
    is hard-constrained to (-bound, bound), which keeps each factor inside
    the tan-theta CC-translation window (|theta| < pi/2). Expressiveness
    lost to the bound is recovered by word growth, not larger angles.
    """
    N = len(seq)
    lam = 1e-8

    if bound is None:
        to_th = lambda x: x
        dth_dx = lambda x: np.ones_like(x)
        x = thetas.copy()
    else:
        to_th = lambda x: bound * np.tanh(x)
        dth_dx = lambda x: bound * (1.0 - np.tanh(x) ** 2)
        x = np.arctanh(np.clip(thetas / bound, -0.9999, 0.9999))

    th = to_th(x)
    psi = _prep(th, seq, basis, pivot_mask, start=start)
    res = psi - ct
    rn = np.linalg.norm(res)
    for _ in range(max_iter):
        if rn < tol:
            break
        # prefix states a_k = U_k ... U_1 |start>, a_0 = start (pivot default)
        a = [basis.basis_vector(pivot_mask) if start is None else start.copy()]
        for (sub, _, _), t in zip(seq, th):
            a.append(apply_ucc_factor(a[-1], basis, sub, t))
        # batched Jacobian: column k is kappa_k a_{k+1} propagated by the
        # remaining factors; propagation is applied to all existing
        # columns at once (same block rotations, matrix-valued).
        J = np.zeros((basis.dim, N))
        for k in range(N):
            if k:
                J[:, :k] = apply_ucc_factor_cols(J[:, :k], basis,
                                                 seq[k][0], th[k])
            src = a[k + 1]
            ii, jj, ss = basis.block_arrays(seq[k][0])
            J[jj, k] = ss * src[ii]
            J[ii, k] = -ss * src[jj]
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


def _compile_sd(c, basis, pivot_mask, p, fid_tol, support_tol, grow_rounds=28):
    ct = c
    seq = _route_sequence(ct, basis, pivot_mask, support_tol)
    thetas = np.zeros(len(seq))
    info = {"gn_stages": [], "grown": 0, "restarts": 0}
    k_t = {basis.total_momentum(basis.masks[i]) for i in range(basis.dim)
           if abs(ct[i]) > support_tol}
    k_pure = k_t if len(k_t) == 1 else None
    rng = np.random.default_rng(20260803)
    bound = math.pi / 2 - 0.02  # hard CC-bridge window per factor

    def greedy_order_init(seq0):
        """Order factors and initialize angles by exact 1-D overlap ascent.

        For one factor, <c_t| exp(theta kappa) |psi> = (A - C) + B sin(theta)
        + C cos(theta) with A = <c_t|psi>, B = <c_t|kappa psi>,
        C = <c_t|P_blocks psi>; the maximizer is theta* = atan2(B, C)
        (clamped to the angle bound). Each step appends the factor with the
        best achievable overlap, so the PREFIX fidelity of the
        initialization is monotone by construction -- the joint polish
        afterwards perturbs angles only slightly, keeping the truncation
        curve graded.
        """
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
                for t in (th_s, bound, -bound):
                    if abs(t) > bound + 1e-12:
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

    # Tangent-completion edge pool. The routed tree can generate a PROPER
    # subalgebra: at L=4 half filling the 9 downhill edges give a pivot
    # orbit of tangent dimension 8 in a 9-sphere (measured), so the target
    # is unreachable no matter the angles -- a residual floor that is an
    # invariant, not a local minimum. Cure: general K-conserving S/D edges
    # (lateral/same-rank allowed) scored by |<residual, kappa_e psi>|, the
    # first-order fidelity gain of appending that letter.
    def edge_pool(top_idx):
        pool = {}
        for i in top_idx:
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
        return pool

    # ------------------------------------------------------------------
    # Phase A: greedy anytime word (FROZEN). Its prefix fidelity is
    # monotone by construction -- this is what makes K-truncation of the
    # emitted chain a graded family of approximations.
    seq, thetas = greedy_order_init(seq)
    psi_g = _prep(thetas, seq, basis, pivot_mask)
    rn = float(np.linalg.norm(psi_g - ct))
    info["gn_stages"].append(("greedy", rn))

    # Phase B: joint bounded solve to exactness. Polish all angles from
    # the greedy init; if a residual floor remains, grow the word --
    # (i) split bound-saturated letters (frozen dtheta/dx) into duplicates,
    # (ii) append tangent-scored general S/D edges (first-order fidelity
    # gain |<residual, kappa_e psi>|), which also completes proper-
    # subalgebra orbits of the routed tree (see edge_pool note) -- and
    # re-solve. Jittered restarts are the last resort.
    thetas, rn = _gauss_newton(thetas, seq, basis, pivot_mask, ct,
                               tol=1e-13, max_iter=300, bound=bound)
    info["gn_stages"].append(("joint", float(rn)))

    for _ in range(grow_rounds):
        if rn ** 2 < fid_tol:
            break
        psi = _prep(thetas, seq, basis, pivot_mask)
        resv = psi - ct
        added = 0
        sat = [k for k, t in enumerate(thetas) if abs(t) >= 0.92 * bound]
        for k in sat[: max(2, len(seq) // 12)]:
            seq.append(seq[k])
            added += 1
        top = _canon_desc(
            [(abs(resv[i]), basis.masks[i], i)
             for i in range(basis.dim) if abs(resv[i]) > 1e-14])[:12]
        scored = []
        for (a, b), sub in edge_pool(top).items():
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
        if added == 0:  # pragma: no cover - no first-order direction left
            break
        thetas = np.concatenate([thetas, np.zeros(added)])
        info["grown"] += added
        thetas, rn = _gauss_newton(thetas, seq, basis, pivot_mask, ct,
                                   tol=1e-13, max_iter=400, bound=bound)
        info["gn_stages"].append(("grow", float(rn)))

    tries = 0
    best_th, best_rn = thetas.copy(), rn
    while best_rn ** 2 > fid_tol and tries < 6:
        tries += 1
        jitter = rng.normal(scale=0.15 * (1 + tries / 3), size=len(seq))
        th_try, rn_try = _gauss_newton(best_th + jitter, seq, basis,
                                       pivot_mask, ct, tol=1e-13,
                                       max_iter=300, bound=bound)
        if rn_try < best_rn:
            best_th, best_rn = th_try, rn_try
    info["restarts"] = tries
    thetas, rn = best_th, best_rn

    psi = _prep(thetas, seq, basis, pivot_mask)
    residual = float(max(0.0, 1.0 - abs(ct @ psi) ** 2))
    if residual > fid_tol:
        raise RuntimeError(
            f"sd_routed solve stalled at residual {residual:.3e} "
            f"(len {len(seq)}, grown {info['grown']}, "
            f"restarts {info['restarts']})"
        )
    thetas = np.array([_fold_pi(t) for t in thetas])
    return seq, thetas, info, residual


# ======================================================================
# ---------------------------------------------------------------------------
# mode = "sd_paired": spin-flip-tied chains (Stage-2 promotion)
# ---------------------------------------------------------------------------
def _spin_flip_matrix(basis):
    """F: global spin flip 2m <-> 2m+1 with fermionic reordering signs.
    F^2 = I, [H, F] = 0, and F grades spin multiplets by (-1)^S."""
    nso = max(m.bit_length() for m in basis.masks)
    nso += nso % 2
    F = np.zeros((basis.dim, basis.dim))
    for i, m in enumerate(basis.masks):
        occ = [q for q in range(nso) if (m >> q) & 1]
        img = [q ^ 1 for q in occ]
        inv = sum(1 for a in range(len(img)) for b in range(a + 1, len(img))
                  if img[a] > img[b])
        m2 = 0
        for q in img:
            m2 |= 1 << q
        F[basis.index[m2], i] = (-1.0) ** inv
    return F


def _fsub(sub):
    return Substitution(tuple(sorted(h ^ 1 for h in sub.holes)),
                        tuple(sorted(q ^ 1 for q in sub.parts)))


def _overlapping(sub):
    fs = _fsub(sub)
    return fs != sub and bool(set(sub.holes + sub.parts)
                              & set(fs.holes + fs.parts))


def _kvec(basis, sub, v):
    ii, jj, ss = basis.block_arrays(sub)
    out = np.zeros(basis.dim)
    out[jj] = ss * v[ii]
    out[ii] = -ss * v[jj]
    return out


def _sigma_of(basis, F, sub, _cache):
    key = (sub.holes, sub.parts)
    if key not in _cache:
        rng = np.random.default_rng(0)
        v = rng.standard_normal(basis.dim)
        rhs = _kvec(basis, _fsub(sub), v)
        s = float((F @ _kvec(basis, sub, F @ v)) @ rhs) / float(rhs @ rhs)
        _cache[key] = round(s)
    return _cache[key]


def _repair_routing(seq, basis, c_t, pivot_mask, k_pure):
    """T3 ablation as policy: reroute overlapping-partner letters through
    non-overlapping already-routed parents where possible (canonical)."""
    rank_of = {m: basis.rank_between(m, pivot_mask) for m in basis.masks}
    routed = {pivot_mask}
    out, forced = [], 0
    for sub, child, parent in seq:
        if _overlapping(sub):
            r = rank_of[child]
            cands = []
            for cand in routed:
                if rank_of[cand] not in (r - 1, r - 2):
                    continue
                if popcount(child & ~cand) > 2:
                    continue
                if k_pure and basis.total_momentum(cand) not in k_pure:
                    continue
                s2 = substitution_between(cand, child)
                if _overlapping(s2):
                    continue
                cands.append((abs(c_t[basis.index[cand]]), cand, (cand, s2)))
            pick = _canon_argmax(cands) if cands else None
            if pick is not None:
                parent, sub = pick
            else:
                forced += 1
        out.append((sub, child, parent))
        routed.add(child)
    return out, forced


def _mask_flip(m):
    out, q = 0, 0
    while m >> q:
        if (m >> q) & 1:
            out |= 1 << (q ^ 1)
        q += 1
    return out


def _build_units(metas, basis, F, sigma_cache):
    """metas: [(sub, child_mask, parent_mask)] -> tied units
    [([(sub, child, parent), ...], [signs])]; partners get F-image masks."""
    units, seen = [], set()
    for sub, ch, pa in metas:
        key = (sub.holes, sub.parts)
        if key in seen:
            continue
        seen.add(key)
        fs = _fsub(sub)
        if fs == sub:
            units.append(([(sub, ch, pa)], [1.0]))
        else:
            seen.add((fs.holes, fs.parts))
            units.append(([(sub, ch, pa),
                           (fs, _mask_flip(ch), _mask_flip(pa))],
                          [1.0, float(_sigma_of(basis, F, sub, sigma_cache))]))
    return units


def _flatten_units(units, x, bound):
    th_u = bound * np.tanh(x)
    letters, thetas = [], []
    for (metas, sgns), t in zip(units, th_u):
        for meta, sg in zip(metas, sgns):
            letters.append(meta)
            thetas.append(sg * t)
    return letters, np.array(thetas)


def _prep_units(units, x, basis, pivot_mask, bound):
    v = basis.basis_vector(pivot_mask)
    letters, thetas = _flatten_units(units, x, bound)
    for (sub, _, _), t in zip(letters, thetas):
        v = apply_ucc_factor(v, basis, sub, t)
    return v


def _gn_tied(units, x, basis, pivot_mask, ct, bound, tol=1e-13, max_iter=200):
    lam = 1e-8
    x = x.copy()
    psi = _prep_units(units, x, basis, pivot_mask, bound)
    res = psi - ct
    rn = float(np.linalg.norm(res))
    nu = len(units)
    for _ in range(max_iter):
        if rn < tol:
            break
        letters, thetas = _flatten_units(units, x, bound)
        a = [basis.basis_vector(pivot_mask)]
        for (sub, _, _), t in zip(letters, thetas):
            a.append(apply_ucc_factor(a[-1], basis, sub, t))
        L = len(letters)
        Jl = np.zeros((basis.dim, L))
        for k in range(L):
            if k:
                Jl[:, :k] = apply_ucc_factor_cols(Jl[:, :k], basis,
                                                  letters[k][0], thetas[k])
            src = a[k + 1]
            ii, jj, ss = basis.block_arrays(letters[k][0])
            Jl[jj, k] = ss * src[ii]
            Jl[ii, k] = -ss * src[jj]
        J = np.zeros((basis.dim, nu))
        dth = bound * (1.0 - np.tanh(x) ** 2)
        pos = 0
        for ui, (metas, sgns) in enumerate(units):
            for (sub, _, _), sg in zip(metas, sgns):
                J[:, ui] += sg * Jl[:, pos]
                pos += 1
            J[:, ui] *= dth[ui]
        JtJ, g = J.T @ J, J.T @ res
        for _ in range(60):
            try:
                delta = np.linalg.solve(JtJ + lam * np.eye(nu), -g)
            except np.linalg.LinAlgError:  # pragma: no cover
                lam *= 10
                continue
            x_new = x + delta
            psi_new = _prep_units(units, x_new, basis, pivot_mask, bound)
            rn_new = float(np.linalg.norm(psi_new - ct))
            if rn_new < rn:
                x, psi, rn, res = x_new, psi_new, rn_new, psi_new - ct
                lam = max(lam / 3.0, 1e-14)
                break
            lam *= 10.0
        else:  # pragma: no cover
            break
    return x, rn


def _compile_sd_paired(c, basis, pivot_mask, p, fid_tol, support_tol,
                       grow_rounds=40):
    """Spin-flip-tied SD chains: every letter a primitive rank<=2
    substitution (CC bridge intact); non-self-conjugate letters applied
    as adjacent (A, F(A)) pairs with tied angles (theta, sigma_A theta),
    keeping prefixes graded by (-1)^S. Routing is overlap-ablated (T3)
    and growth prefers non-overlapping edges. See METHOD.md section 14
    for the measured properties and costs.
    """
    ct = c  # _normalize_target already fixed the pivot-positive phase
    bound = math.pi / 2 - 0.02
    F = _spin_flip_matrix(basis)
    sig = {}
    k_t = {basis.total_momentum(m) for m in basis.masks
           if abs(ct[basis.index[m]]) > support_tol}
    k_pure = k_t if len(k_t) == 1 else None
    info = {"grown": 0, "forced_overlap": 0, "gn_stages": []}

    seq = _route_sequence(ct, basis, pivot_mask, support_tol)
    seq, forced = _repair_routing(seq, basis, ct, pivot_mask, k_pure)
    info["forced_overlap"] = forced
    units = _build_units(seq, basis, F, sig)

    # greedy anytime ordering + init over UNITS (exact 1-D trig scan)
    grid = np.linspace(-bound, bound, 801)
    gS, gC = np.sin(grid), 1.0 - np.cos(grid)

    def unit_max(psi, unit):
        metas, sgns = unit
        vecs = {(): psi}
        for (sub, _, _), sg in zip(metas, sgns):
            new = {}
            for key, v in vecs.items():
                new[key + (0,)] = v
                new[key + (1,)] = sg * _kvec(basis, sub, v)
                new[key + (2,)] = _kvec(basis, sub, _kvec(basis, sub, v))
            vecs = new
        f = np.zeros_like(grid)
        for key, v in vecs.items():
            w = float(ct @ v)
            if w == 0.0:
                continue
            g = np.full_like(grid, w)
            for a_ in key:
                if a_ == 1:
                    g = g * gS
                elif a_ == 2:
                    g = g * gC
            f += g
        i = int(np.argmax(f))
        return float(f[i]), float(grid[i])

    psi = basis.basis_vector(pivot_mask)
    remaining = list(units)
    ordered, x0 = [], []
    while remaining:
        cands = []
        for idx, u in enumerate(remaining):
            val, t = unit_max(psi, u)
            cands.append((val, (u[0][0][0].holes, u[0][0][0].parts,
                                abs(t), t), (idx, t)))
        idx, t = _canon_argmax(cands)
        u = remaining.pop(idx)
        ordered.append(u)
        x0.append(math.atanh(max(-0.9999, min(0.9999, t / bound))))
        for (sub, _, _), sg in zip(*u):
            psi = apply_ucc_factor(psi, basis, sub,
                                   sg * bound * math.tanh(x0[-1]))
    units = ordered
    x = np.array(x0)

    x, rn = _gn_tied(units, x, basis, pivot_mask, ct, bound, max_iter=150)
    info["gn_stages"].append(("greedy_init", float(rn)))
    for _ in range(grow_rounds):
        if rn ** 2 < fid_tol:
            break
        psi = _prep_units(units, x, basis, pivot_mask, bound)
        resv = psi - ct
        added = []
        th_u = bound * np.tanh(x)
        for i in [i for i, t in enumerate(th_u)
                  if abs(t) >= 0.92 * bound][:3]:
            added.append(units[i])
        top = _canon_desc([(abs(resv[i]), basis.masks[i], i)
                           for i in range(basis.dim)
                           if abs(resv[i]) > 1e-14])[:12]
        pool = {}
        for i in top:
            mi = basis.masks[i]
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
            fs = _fsub(sub)
            col = _kvec(basis, sub, psi)
            if fs != sub:
                col = col + _sigma_of(basis, F, sub, sig) * _kvec(basis, fs, psi)
            sc = abs(float(resv @ col))
            if _overlapping(sub):     # T3: prefer non-overlapping edges
                sc *= 1e-3
            scored.append((sc, key, sub))
        for sc, a_, b_, sub in _canon_desc(
                [(sc, key, (sc, key[0], key[1], sub))
                 for sc, key, sub in scored])[: max(4, len(units) // 6)]:
            if sc < 1e-14:
                break
            added.extend(_build_units([(sub, b_, a_)], basis, F, sig))
        if not added:  # pragma: no cover
            break
        units = units + added
        x = np.concatenate([x, np.zeros(len(added))])
        info["grown"] += len(added)
        x, rn = _gn_tied(units, x, basis, pivot_mask, ct, bound, max_iter=200)
        info["gn_stages"].append(("grow", float(rn)))
    if rn ** 2 > fid_tol:
        raise RuntimeError(
            f"sd_paired solve stalled at residual {rn**2:.3e} "
            f"(units {len(units)}, grown {info['grown']})")
    letters, thetas = _flatten_units(units, x, bound)
    info["units"] = len(units)
    psi = _prep_units(units, x, basis, pivot_mask, bound)
    residual = float(max(0.0, 1.0 - abs(ct @ psi) ** 2))
    return letters, thetas, info, residual


def compile_chain(
    target: np.ndarray,
    basis: SectorBasis,
    pivot_mask: int | None = None,
    mode: str = "sd_routed",
    policy: str = "rank_major",
    fid_tol: float = 1e-12,
    support_tol: float = 1e-12,
    max_steps: int | None = None,
) -> CompileResult:
    c, pivot_mask, p = _normalize_target(target, basis, pivot_mask)

    if mode == "direct":
        elim, rows, gsign, residual = _compile_direct(
            c.copy(), basis, pivot_mask, p, policy, fid_tol, max_steps
        )
        res = _DirectResult(
            pivot_mask=pivot_mask, mode=mode, policy=policy,
            factors=[(sub, -phi) for sub, phi in reversed(elim)],
            ledger=rows, final_residual=residual, global_sign=gsign,
            target=c, solver_info={"elim": elim},
        )
        return res

    if mode == "sd_routed":
        seq, thetas, info, residual = _compile_sd(
            c, basis, pivot_mask, p, fid_tol, support_tol
        )
        pol = "routed_joint_solve"
    elif mode == "sd_paired":
        seq, thetas, info, residual = _compile_sd_paired(
            c, basis, pivot_mask, p, fid_tol, support_tol
        )
        pol = "paired_tied_solve"
    else:
        raise ValueError(mode)
    factors = [(sub, float(t)) for (sub, _, _), t in zip(seq, thetas)]
    res = CompileResult(
        pivot_mask=pivot_mask, mode=mode, policy=pol,
        factors=factors, final_residual=residual, target=c,
        solver_info=info,
    )
    # prefix-fidelity ledger (single forward sweep)
    rank_of = [basis.rank_between(m, pivot_mask) for m in basis.masks]
    v = basis.basis_vector(pivot_mask)
    for k, ((sub, child, parent), th) in enumerate(zip(seq, thetas), start=1):
        v = apply_ucc_factor(v, basis, sub, th)
        res.ledger.append(
            LedgerRow(
                step=k, sub=sub, theta=float(th),
                mu_mask=child, nu_mask=parent,
                rank_mu=rank_of[basis.index[child]],
                rank_nu=rank_of[basis.index[parent]],
                c_mu=float(c[basis.index[child]]),
                c_nu=float(c[basis.index[parent]]),
                fid_after=float(abs(c @ v)),
                flag=_angle_flag(float(th)),
            )
        )
    res.global_sign = 1 if (c @ v) > 0 else -1
    return res

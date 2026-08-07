"""Stage-1 wiring: chain-JSON consumer, an independent determinant kernel,
and the secant-dressing certification against exact cluster amplitudes.

The kernel is ported from the upgradation project's symbolic engine
(Layer 4.3): a determinant is a sorted tuple of occupied spin-orbitals, a
state is {determinant: amplitude}, and parity is counted on tuples. That
makes it a second, fully independent implementation of the fermionic
algebra (chaincompile.dets counts parity on bitmasks). The composite
operator ordering is pinned to chaincompile.dets.Substitution -- A
annihilates holes in ascending order then creates parts in ascending
order; the adjoint is the exact reverse -- so states produced by the two
implementations are directly comparable with no convention factors.

Certification levels (docs/METHOD.md section 11):
  C1  kernel state == vector state for the same chain (signs, rotations)
  C2  chain-JSON round trip reproduces the eigenstate (fidelity 1)
  C3  the first-order operator-valued (secant-product) dressing law vs
      exact cluster amplitudes -- measuring where the law holds and where
      the folded terms begin.
"""
import json
import math
import re

from .dets import Substitution

_LABEL = re.compile(r"(\d+)([ud])")
_SWAP = {"c": "cd", "cd": "c"}


# ---------------------------------------------------------------------------
# chain JSON consumer
# ---------------------------------------------------------------------------
def parse_det_label(label: str) -> tuple:
    """'|0u 0d 1u 1d 5u 5d>' -> (0, 1, 2, 3, 10, 11)  (so = 2*orb + spin)."""
    sos = [2 * int(o) + (0 if s == "u" else 1) for o, s in _LABEL.findall(label)]
    if not sos:
        raise ValueError(f"no spin-orbital tokens in det label: {label!r}")
    return tuple(sorted(sos))


def load_chain_json(path):
    """Read a chaincompile.chain.v0 file into (pivot, steps, meta).

    steps is [(Substitution, theta)] in PREPARATION order (first listed is
    applied to the pivot first), exactly as the file's ordering note says.
    """
    with open(path, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    if d.get("schema") != "chaincompile.chain.v0":
        raise ValueError(f"not a chaincompile.chain.v0 file: {path}")
    steps = [
        (Substitution(tuple(sorted(st["holes"])), tuple(sorted(st["parts"]))),
         float(st["theta"]))
        for st in d["steps"]
    ]
    pivot = parse_det_label(d["pivot_determinant"])
    meta = {k: d.get(k) for k in
            ("note", "mode", "policy", "global_sign", "final_residual")}
    return pivot, steps, meta


# ---------------------------------------------------------------------------
# independent tuple-determinant kernel (ported from upgradation.symbolic)
# ---------------------------------------------------------------------------
def _create(p, occ):
    if p in occ:
        return None
    sign = -1 if (sum(1 for q in occ if q < p) & 1) else 1
    return tuple(sorted(occ + (p,))), sign


def _annihilate(p, occ):
    if p not in occ:
        return None
    sign = -1 if (sum(1 for q in occ if q < p) & 1) else 1
    return tuple(q for q in occ if q != p), sign


def _apply_ops(occ, ops):
    sign = 1
    for kind, p in ops:
        r = _create(p, occ) if kind == "cd" else _annihilate(p, occ)
        if r is None:
            return None
        occ, s = r
        sign *= s
    return occ, sign


def _a_ops(sub: Substitution):
    return [("c", i) for i in sub.holes] + [("cd", a) for a in sub.parts]


def apply_A(sub: Substitution, occ):
    """A|det>: annihilate holes ascending, create parts ascending
    (mirrors Substitution.a_ops)."""
    return _apply_ops(occ, _a_ops(sub))


def apply_Adag(sub: Substitution, occ):
    """A^dag|det>: the exact adjoint (mirrors Substitution.adag_ops)."""
    return _apply_ops(occ, [(_SWAP[k], p) for k, p in reversed(_a_ops(sub))])


def apply_generator(sub: Substitution, state: dict) -> dict:
    """kappa = A - A^dag applied to a {det: amp} state."""
    out = {}
    for occ, amp in state.items():
        r = apply_A(sub, occ)
        if r is not None:
            d, s = r
            out[d] = out.get(d, 0.0) + s * amp
        r = apply_Adag(sub, occ)
        if r is not None:
            d, s = r
            out[d] = out.get(d, 0.0) - s * amp
    return out


def apply_factor(sub: Substitution, theta: float, state: dict,
                 tol: float = 1e-15) -> dict:
    """exp(theta kappa) state, exactly: I + sin(theta) kappa
    + (1 - cos(theta)) kappa^2 (kappa^3 = -kappa at every rank)."""
    g = apply_generator(sub, state)
    g2 = apply_generator(sub, g)
    s, c = math.sin(theta), 1.0 - math.cos(theta)
    out = dict(state)
    for k, v in g.items():
        out[k] = out.get(k, 0.0) + s * v
    for k, v in g2.items():
        out[k] = out.get(k, 0.0) + c * v
    return {k: v for k, v in out.items() if abs(v) > tol}


def state_from_chain(steps, pivot: tuple, tol: float = 1e-15) -> dict:
    """Prepare the chain state in the tuple-determinant representation."""
    state = {tuple(pivot): 1.0}
    for sub, th in steps:
        state = apply_factor(sub, th, state, tol=tol)
    return state


def state_dict_to_vector(state: dict, basis):
    """Map a {det-tuple: amp} state onto a SectorBasis coefficient vector."""
    import numpy as np

    v = np.zeros(basis.dim)
    for occ, amp in state.items():
        mask = 0
        for p in occ:
            mask |= 1 << p
        j = basis.index.get(mask)
        if j is None:
            raise ValueError(f"kernel produced out-of-sector determinant {occ}")
        v[j] = amp
    return v


# ---------------------------------------------------------------------------
# C3: the first-order operator-valued (secant-product) dressing law
# ---------------------------------------------------------------------------
def secant_dressing_report(steps, t_amps, pivot: tuple, floor: float = 1e-8):
    """Compare exact cluster amplitudes against the secant-product law.

    Law under test (upgradation.symbolic, measured on two-factor probes;
    Freericks Symmetry 2022 eqs. 38/46/51): the amplitude contributed by
    chain letter k on its own substitution is tan(theta_k) dressed by
    sec(theta_j) for every LATER letter j sharing ANY spin-orbital
    (occupied or virtual) with it. Letters whose substitution does not act
    on the pivot ("routed" letters) have no pivot-relative amplitude to
    compare -- they, together with composite-rank amplitudes, constitute
    the folded structure the first-order law does not address.

    Returns (rows, summary).
    """
    pivot_mask = 0
    for p in pivot:
        pivot_mask |= 1 << p

    def orbset(s):
        return set(s.holes) | set(s.parts)

    exact_all = {key: t for tn in t_amps.values() for key, t in tn.items()}

    order, letters = [], {}
    for k, (sub, th) in enumerate(steps):
        key = (sub.holes, sub.parts)
        if key not in letters:
            letters[key] = []
            order.append((key, sub))
        letters[key].append(k)

    n = len(steps)
    rows = []
    for key, sub in order:
        anchored = sub.is_lower(pivot_mask)
        pred = pred_all = bare = 0.0
        for k in letters[key]:
            th_k = steps[k][1]
            dress = dress_all = 1.0
            for j in range(n):
                if j == k or not (orbset(steps[j][0]) & orbset(sub)):
                    continue
                dress_all /= math.cos(steps[j][1])
                if j > k:
                    dress /= math.cos(steps[j][1])
            pred += math.tan(th_k) * dress
            pred_all += math.tan(th_k) * dress_all
            bare += math.tan(th_k)
        exact = exact_all.get(key, 0.0)
        row = {
            "sub": Substitution(*key).label(), "rank": sub.rank,
            "n_letters": len(letters[key]), "anchored": anchored,
            "t_exact": exact, "t_bare": bare, "t_pred": pred,
            "t_pred_all": pred_all,
        }
        if anchored and abs(exact) > floor:
            row["relerr_pred"] = abs(pred / exact - 1.0)
            row["relerr_all"] = abs(pred_all / exact - 1.0)
            row["relerr_bare"] = abs(bare / exact - 1.0)
        rows.append(row)

    scored = [r for r in rows if "relerr_pred" in r]
    chain_keys = set(letters)

    def _med(xs):
        xs = sorted(xs)
        m = len(xs)
        return 0.0 if m == 0 else (
            xs[m // 2] if m % 2 else 0.5 * (xs[m // 2 - 1] + xs[m // 2]))

    coverage = {}
    for r, tn in sorted(t_amps.items()):
        den = sum(t * t for t in tn.values())
        num = sum(t * t for key, t in tn.items() if key in chain_keys)
        coverage[r] = (num / den) if den > 0 else 1.0
    folded = sorted(
        ((r, key, t) for r, tn in t_amps.items() for key, t in tn.items()
         if key not in chain_keys),
        key=lambda x: -abs(x[2]))

    summary = {
        "n_letters": n,
        "n_distinct": len(rows),
        "n_anchored": sum(1 for r in rows if r["anchored"]),
        "n_scored": len(scored),
        "median_relerr_pred": _med([r["relerr_pred"] for r in scored]),
        "median_relerr_all": _med([r["relerr_all"] for r in scored]),
        "median_relerr_bare": _med([r["relerr_bare"] for r in scored]),
        "max_relerr_pred": max((r["relerr_pred"] for r in scored), default=0.0),
        "coverage_by_rank": coverage,
        "top_folded": [(r, Substitution(*key).label(), t)
                       for r, key, t in folded[:5]],
    }
    return rows, summary

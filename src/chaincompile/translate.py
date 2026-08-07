"""Numeric CC-side translation diagnostics.

Two distinct things are validated here (docs/METHOD.md, section 5):

1. Per-factor bridge (operator level): each UCC factor equals the
   disentangled SL(2,C) triple with CC-side amplitude tan(theta)
   (Symmetry 2022, Eqs. 15/19/38) -- verified in factors.apply_cc_triple
   + tests. The full normal-ordered, operator-valued reordering of a
   whole chain (Hadamard-lemma pass) is a roadmap item, NOT done here.

2. State-equivalent CC amplitudes (this module): for the state a chain
   prepares, extract the unique intermediate-normalized cluster operator
   T = T1 + T2 + ... with  exp(T)|pivot> = |psi>/c_pivot  (cluster
   analysis, exact rank recursion; T is nilpotent-graded so exp is a
   finite polynomial). Truncating T at singles+doubles and rebuilding
   exp(T1+T2)|pivot> gives the honest "translated with reported
   distortion" numbers for a rank-capped CC handoff.
"""
from __future__ import annotations

import json
from datetime import date

import numpy as np

from .dets import bits, substitution_between
from .sector import SectorBasis


def _pivot_sub(pivot: int, mask: int):
    return substitution_between(pivot, mask)


def exp_apply(T: np.ndarray, v: np.ndarray, maxpow: int, tol: float = 1e-16) -> np.ndarray:
    w = v.copy()
    term = v.copy()
    for k in range(1, maxpow + 1):
        term = T @ term / k
        w = w + term
        if np.linalg.norm(term) < tol:
            break
    return w


def cluster_analysis(psi: np.ndarray, basis: SectorBasis, pivot_mask: int):
    """Return (t_amps, T_matrix, maxrank).

    t_amps: {rank: {sub_label_tuple: t_value}} with sub = (holes, parts)
    relative to the pivot; sign convention: t is defined so that the
    operator sum_mu t_mu A_mu (A_mu the primitive substitution operator,
    signs from dets.py) reproduces the state via exp(T)|pivot>.
    """
    p = basis.index[pivot_mask]
    if abs(psi[p]) < 1e-12:
        raise ValueError("pivot weight ~ 0; cluster analysis undefined")
    ctil = psi / psi[p]
    rank_of = [basis.rank_between(m, pivot_mask) for m in basis.masks]
    maxrank = max(
        (rank_of[i] for i in range(basis.dim) if abs(ctil[i]) > 1e-13), default=0
    )
    T = np.zeros((basis.dim, basis.dim))
    t_amps: dict = {}
    for n in range(1, maxrank + 1):
        d = exp_apply(T, basis.basis_vector(pivot_mask), maxpow=maxrank)
        tn: dict = {}
        for i, m in enumerate(basis.masks):
            if rank_of[i] != n:
                continue
            resid = ctil[i] - d[i]
            if abs(resid) < 1e-14 and abs(ctil[i]) < 1e-14:
                continue
            sub = _pivot_sub(pivot_mask, m)
            up, s = sub.apply_a(pivot_mask)
            assert up == m
            t = resid / s
            if abs(t) < 1e-14:
                continue
            tn[(sub.holes, sub.parts)] = float(t)
            T += t * basis.substitution_matrix(sub)
        if tn:
            t_amps[n] = tn
    # verify
    rebuilt = exp_apply(T, basis.basis_vector(pivot_mask), maxpow=maxrank)
    err = float(np.linalg.norm(rebuilt - ctil))
    return t_amps, T, maxrank, err


def build_T(t_amps: dict, basis: SectorBasis, pivot_mask: int, ranks=None) -> np.ndarray:
    T = np.zeros((basis.dim, basis.dim))
    for n, tn in t_amps.items():
        if ranks is not None and n not in ranks:
            continue
        for (holes, parts), t in tn.items():
            from .dets import Substitution

            T += t * basis.substitution_matrix(Substitution(holes, parts))
    return T


def rank_table(t_amps: dict):
    rows = []
    for n in sorted(t_amps):
        vals = np.array(list(t_amps[n].values()))
        rows.append(
            {
                "rank": n,
                "n_amps": len(vals),
                "norm2": float(np.linalg.norm(vals)),
                "max_abs_t": float(np.max(np.abs(vals))),
            }
        )
    return rows


def sd_truncation_report(
    psi: np.ndarray, basis: SectorBasis, pivot_mask: int, H: np.ndarray
):
    """Distortion of the SD-rank-capped CC-side state vs the chain state."""
    t_amps, T_full, maxrank, rebuild_err = cluster_analysis(psi, basis, pivot_mask)
    out = {"rebuild_err": rebuild_err, "maxrank": maxrank, "ranks": rank_table(t_amps)}
    e_chain = float(psi @ H @ psi / (psi @ psi))
    out["E_chain"] = e_chain
    T_sd = build_T(t_amps, basis, pivot_mask, ranks={1, 2})
    v = exp_apply(T_sd, basis.basis_vector(pivot_mask), maxpow=max(2 * maxrank, 4))
    v = v / np.linalg.norm(v)
    out["fidelity_sd"] = float(abs(v @ (psi / np.linalg.norm(psi))))
    out["E_sd"] = float(v @ H @ v)
    out["t_amps"] = t_amps
    return out


# ----------------------------------------------------------------------
def _decode_so(p: int):
    return {"so": int(p), "orbital": int(p // 2), "spin": "u" if p % 2 == 0 else "d"}


def export_amps_json(
    path,
    t_amps: dict,
    pivot_mask: int,
    basis: SectorBasis,
    energy: float,
    meta: dict | None = None,
):
    """Emit state-equivalent CC amplitudes as JSON.

    Schema is self-describing, NOT yet the Procopius translation-suite
    `amps:<file.json>` schema -- adapt keys when wiring into the audit
    engine (see README, Integration notes).
    """
    payload = {
        "schema": "chaincompile.amps.v0",
        "generated": str(date.today()),
        "note": (
            "state-equivalent CC amplitudes from cluster analysis of a "
            "compiled factorized-UCC chain state; intermediate "
            "normalization on the pivot determinant"
        ),
        "pivot_determinant": [_decode_so(p) for p in bits(pivot_mask)],
        "energy": float(energy),
        "amplitudes": [
            {
                "rank": n,
                "holes": [_decode_so(h) for h in holes],
                "parts": [_decode_so(a) for a in parts],
                "t": t,
            }
            for n, tn in sorted(t_amps.items())
            for (holes, parts), t in sorted(tn.items())
        ],
    }
    if meta:
        payload["meta"] = meta
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return path

"""Diagnostics tables (markdown + CSV), ASCII-safe, utf-8 files.

Console output stays ASCII (Windows-console-safe); files are written
with explicit encoding="utf-8".
"""
from __future__ import annotations

import csv

import numpy as np


def fmt(x, nd=6):
    if isinstance(x, float):
        if x == 0:
            return "0"
        if abs(x) < 1e-4 or abs(x) >= 1e6:
            return f"{x:.3e}"
        return f"{x:.{nd}f}"
    return str(x)


def md_table(rows: list[dict], cols: list[str]) -> str:
    head = "| " + " | ".join(cols) + " |"
    sep = "|" + "|".join(["---"] * len(cols)) + "|"
    body = ["| " + " | ".join(fmt(r.get(c, "")) for c in cols) + " |" for r in rows]
    return "\n".join([head, sep] + body) + "\n"


def write_csv(path, rows: list[dict], cols: list[str]):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def write_text(path, text: str):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# ----------------------------------------------------------------------
def resolve_degenerate_roots(evals, evecs, basis, nroots, tol=1e-8):
    """Within each degenerate eigenvalue cluster, rotate to the
    simultaneous eigenbasis of total momentum K and then S^2, and fix
    each column sign by its canonical dominant amplitude. Degenerate
    multiplets then carry pure, platform-stable (K, S^2) labels
    (ADR-003; docs/METHOD.md section 13)."""
    V = np.array(evecs[:, :nroots], dtype=float, copy=True)
    kdiag = np.array([basis.total_momentum(m) for m in basis.masks], float)
    S2 = basis.s2_matrix()
    i = 0
    while i < nroots:
        j = i + 1
        # extend to the FULL degenerate cluster, even past nroots, so a
        # truncated listing never shows an unresolved mixture
        while j < len(evals) and evals[j] - evals[i] < tol:
            j += 1
        if j - i > 1:
            P = np.array(evecs[:, i:j], dtype=float, copy=True)
            w, Q = np.linalg.eigh(P.T @ (kdiag[:, None] * P))
            P = P @ Q
            a = 0
            while a < j - i:
                b = a + 1
                while b < j - i and w[b] - w[a] < 1e-6:
                    b += 1
                if b - a > 1:
                    _, Q2 = np.linalg.eigh(P[:, a:b].T @ S2 @ P[:, a:b])
                    P[:, a:b] = P[:, a:b] @ Q2
                a = b
            keep = min(j, nroots) - i
            V[:, i:i + keep] = P[:, :keep]
        i = j
    for r in range(V.shape[1]):
        v = V[:, r]
        amax = float(np.max(np.abs(v)))
        dom = min(basis.masks[k] for k in range(basis.dim)
                  if abs(v[k]) >= (1.0 - 1e-9) * amax)
        if v[basis.index[dom]] < 0:
            V[:, r] = -v
    return V


def roots_table(evals, evecs, basis, S2, nroots=8):
    """Per-root E, total momentum K, <S^2>, dominant determinant + weight.
    Multi-root, spin-labeled listings per the ADR-003 reference protocol.
    Degenerate clusters are symmetry-resolved and sign-canonicalized so
    the table is platform-stable."""
    rows = []
    V = resolve_degenerate_roots(evals, evecs, basis, min(nroots, len(evals)))
    for r in range(V.shape[1]):
        v = V[:, r]
        amax = float(np.max(np.abs(v)))
        dom = min(basis.masks[k] for k in range(basis.dim)
                  if abs(v[k]) >= (1.0 - 1e-9) * amax)
        i = basis.index[dom]
        ks = {basis.total_momentum(basis.masks[j]) for j in range(basis.dim)
              if abs(v[j]) > 1e-8}
        rows.append(
            {
                "root": r,
                "E": float(evals[r]),
                "K": ",".join(str(k) for k in sorted(ks)),
                "S2": float(v @ S2 @ v),
                "dominant_det": basis.det_label(basis.masks[i]),
                "dominant_weight": float(v[i] ** 2),
            }
        )
    return rows


def ledger_rows(res, basis):
    rows = []
    for r in res.ledger:
        rows.append(
            {
                "step": r.step,
                "factor": r.sub.label(basis.L),
                "rank_gen": r.sub.rank,
                "theta": r.theta,
                "tan_theta": float(np.tan(r.theta)),
                "mu": basis.det_label(r.mu_mask),
                "rank_mu": r.rank_mu,
                "nu": basis.det_label(r.nu_mask),
                "rank_nu": r.rank_nu,
                "abs_c_mu": abs(r.c_mu),
                "abs_c_nu": abs(r.c_nu),
                "fid_after": r.fid_after,
                "flag": r.flag,
            }
        )
    return rows


def prefix_s2_curve(res, basis):
    """(K, fid_after, <S2>) along the preparation prefixes of a compile
    result (either mode). The endpoint of a singlet-target chain must be
    a singlet; the interior measurably is NOT spin-pure in either mode --
    see docs/METHOD.md section 12."""
    from .factors import apply_ucc_factor

    S2 = basis.s2_matrix()
    v = basis.basis_vector(res.pivot_mask)
    out = []
    for K, (sub, th) in enumerate(res.selected(), 1):
        v = apply_ucc_factor(v, basis, sub, th)
        out.append((K, res.ledger[K - 1].fid_after, float(v @ S2 @ v)))
    return out

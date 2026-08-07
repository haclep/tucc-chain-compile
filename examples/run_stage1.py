"""Stage-1 certification driver.

Consumes the COMMITTED chain JSONs under results/ (plus an in-process
L4 U8 compile), and for each chain runs the three certification levels:

  C1  the independent tuple-determinant kernel (ported from the
      upgradation symbolic engine, operator ordering pinned to
      chaincompile.dets) reproduces the vector-machinery state,
  C2  the chain JSON round-trips to the eigenstate (fidelity 1),
  C3  the first-order operator-valued (secant-product) dressing law is
      scored against exact cluster amplitudes -- measuring where the
      first-order law holds and where the folded terms begin.

Outputs: results/stage1_certification.md, results/stage1_dressing_*.csv.
Run AFTER examples/run_hubbard.py (it reads the chain JSONs written there).
"""
import glob
import math
import os
import re
import sys
import time

import numpy as np

from chaincompile.compile import compile_chain
from chaincompile.diagnostics import md_table, write_csv, write_text
from chaincompile.factors import apply_ucc_factor
from chaincompile.hubbard import hamiltonian
from chaincompile.sector import SectorBasis
from chaincompile.translate import cluster_analysis
from chaincompile import disentangle as dz

RES = os.path.join(os.path.dirname(__file__), "..", "results")


def say(msg):
    print(msg, flush=True)


def infer_sector(pivot, steps):
    top = max([max(p) for p in (pivot,)] +
              [max(s.holes + s.parts) for s, _ in steps])
    L = top // 2 + 1
    nup = sum(1 for p in pivot if p % 2 == 0)
    ndn = len(pivot) - nup
    return L, nup, ndn


def certify(tag, pivot, steps, meta, basis, target):
    pivot_mask = 0
    for p in pivot:
        pivot_mask |= 1 << p

    # C1: independent kernel vs vector machinery, same chain
    v = basis.basis_vector(pivot_mask)
    for sub, th in steps:
        v = apply_ucc_factor(v, basis, sub, th)
    state = dz.state_from_chain(steps, pivot)
    v_ker = dz.state_dict_to_vector(state, basis)
    c1 = float(np.max(np.abs(v - v_ker)))

    # C2: chain reproduces the eigenstate
    c2 = 1.0 - abs(float(target @ v_ker))

    # C3: secant-dressing law vs exact cluster amplitudes
    t_amps, _, maxrank, err = cluster_analysis(target, basis, pivot_mask)
    rows, summ = dz.secant_dressing_report(steps, t_amps, pivot)

    say(f"  {tag}: C1 {c1:.2e}  C2 {c2:.2e}  cluster rebuild {err:.1e}  "
        f"letters {summ['n_letters']} (anchored {summ['n_anchored']})")
    say(f"    dressing relerr median: later-sec {summ['median_relerr_pred']:.3f}"
        f"  all-sec {summ['median_relerr_all']:.3f}"
        f"  bare-tan {summ['median_relerr_bare']:.3f}")
    cov = ", ".join(f"T{r}: {v:.3f}" for r, v in
                    sorted(summ["coverage_by_rank"].items()))
    say(f"    chain coverage of ||T_r||^2: {cov}")
    return c1, c2, err, rows, summ


def section(tag, c1, c2, err, rows, summ, n_show):
    cols = ["sub", "rank", "n_letters", "anchored",
            "t_exact", "t_pred", "t_pred_all", "t_bare"]
    shown = sorted(rows, key=lambda r: -abs(r["t_exact"]))[:n_show]
    cov = ", ".join(f"T{r}: {v:.4f}" for r, v in
                    sorted(summ["coverage_by_rank"].items()))
    folded = "; ".join(f"rank {r} {lab} t={t:+.4f}"
                       for r, lab, t in summ["top_folded"]) or "(none)"
    return (
        f"## {tag}\n\n"
        f"C1 kernel-vs-vector max deviation: {c1:.2e}. "
        f"C2 eigenstate infidelity: {c2:.2e}. "
        f"Cluster-analysis rebuild error: {err:.1e}.\n\n"
        f"Letters: {summ['n_letters']} ({summ['n_distinct']} distinct, "
        f"{summ['n_anchored']} pivot-anchored, {summ['n_scored']} scored). "
        f"Median relative error of the dressing law on anchored amplitudes: "
        f"later-secants {summ['median_relerr_pred']:.3f}, "
        f"all-secants {summ['median_relerr_all']:.3f}, "
        f"bare tan(theta) {summ['median_relerr_bare']:.3f}.\n\n"
        f"Chain coverage of ||T_r||^2 by letter substitutions: {cov}. "
        f"Largest folded (composite) amplitudes: {folded}.\n\n"
        + md_table(shown, cols) + "\n"
    )


def main():
    t0 = time.time()
    say("Stage-1 certification: kernel, JSON round trip, dressing law")
    parts = [
        "# Stage-1 certification -- operator-kernel and dressing law\n\n"
        "C1: an independent tuple-determinant kernel (ported from the "
        "upgradation symbolic engine; composite operator ordering pinned to "
        "chaincompile.dets) must reproduce the vector-machinery chain state. "
        "C2: the committed chain JSON must round-trip to the eigenstate. "
        "C3: the first-order operator-valued dressing law -- each letter's "
        "amplitude tan(theta_k) dressed by sec(theta_j) over sharing letters "
        "(Freericks Symmetry 2022 eqs. 38/46/51; measured exactly on "
        "two-factor probes in tests) -- scored against exact cluster "
        "amplitudes. Deviations and un-covered ranks quantify the folded "
        "structure a first-order operator-valued form does not carry.\n"
    ]

    # committed chains
    for path in sorted(glob.glob(os.path.join(RES, "chain_*.json"))):
        tag = re.sub(r"^chain_|\.json$", "", os.path.basename(path))
        pivot, steps, meta = dz.load_chain_json(path)
        L, nup, ndn = infer_sector(pivot, steps)
        m = re.search(r"U(\d+(?:\.\d+)?)", tag)
        U = float(m.group(1)) if m else 0.0
        basis = SectorBasis(L, nup, ndn)
        evals, evecs = np.linalg.eigh(hamiltonian(basis, U=U))
        c1, c2, err, rows, summ = certify(
            tag, pivot, steps, meta, basis, evecs[:, 0])
        write_csv(os.path.join(RES, f"stage1_dressing_{tag}.csv"), rows,
                  list(rows[0].keys()))
        parts.append(section(tag, c1, c2, err, rows, summ, n_show=10))

    # in-process L4 U8 (no committed chain JSON; the P2 lattice)
    basis = SectorBasis(4, 2, 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=8.0))
    res = compile_chain(evecs[:, 0], basis, mode="sd_routed")
    pivot = tuple(i for i in range(16) if (res.pivot_mask >> i) & 1)
    c1, c2, err, rows, summ = certify(
        "L4_U8_gs_sd (in-process)", pivot, res.selected(), {}, basis,
        evecs[:, 0])
    write_csv(os.path.join(RES, "stage1_dressing_L4_U8_gs_sd.csv"), rows,
              list(rows[0].keys()))
    parts.append(section("L4_U8_gs_sd (in-process)", c1, c2, err, rows, summ,
                         n_show=len(rows)))

    write_text(os.path.join(RES, "stage1_certification.md"),
               "\n".join(parts))
    say(f"done in {time.time() - t0:.1f} s -> results/stage1_certification.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

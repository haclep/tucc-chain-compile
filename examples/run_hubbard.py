"""End-to-end worked validation of the compile-from-target selector.

Systems (momentum-space Hubbard ring, t = 1):
  A. L=6, half filling, U=2 and U=6  -- closed-shell Fermi-sea reference
     (primary validation: compile GS, truncate at each K, translate,
      tabulate angle + rank diagnostics; excited-root demo at U=6).
  B. L=4, half filling, U=8          -- the P2 lattice; DEGENERATE Fermi
     sea, so the pivot is taken from the target root (re-referencing
     demo); direct mode exhibits the quadruple factor of P2 Table 1,
     sd_routed replaces it with a doubles route.

Run:  python -u examples/run_hubbard.py     (writes results/)
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np

from chaincompile import __version__
from chaincompile.compile import compile_chain, prepare_state
from chaincompile.diagnostics import (
    fmt,
    ledger_rows,
    md_table,
    roots_table,
    write_csv,
    write_text,
)
from chaincompile.hubbard import fermi_sea_mask, hamiltonian
from chaincompile.sector import SectorBasis
from chaincompile.translate import export_amps_json, sd_truncation_report

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
RES.mkdir(exist_ok=True)

K_GRID = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256]


def say(msg=""):
    print(msg, flush=True)


def ref_energy(H, basis, pivot_mask):
    p = basis.index[pivot_mask]
    return float(H[p, p])


def truncation_rows(res, basis, H, e_exact):
    tgt = res.target
    e_ref = ref_energy(H, basis, res.pivot_mask)
    ks = sorted({k for k in K_GRID if k < res.length} | {res.length})
    rows = []
    max_ledger_dev = 0.0
    for K in ks:
        psi = prepare_state(res, basis, K)
        fid = float(abs(tgt @ psi))
        led = float(res.ledger[K - 1].fid_after)
        max_ledger_dev = max(max_ledger_dev, abs(fid - led))
        e = float(psi @ H @ psi)
        rc = res.rank_counts(K)
        rows.append(
            {
                "K": K,
                "fidelity": fid,
                "infidelity": 1.0 - fid,
                "dE_mt": (e - e_exact) * 1e3,
                "pct_corr": 100.0 * (e - e_ref) / (e_exact - e_ref),
                "max_abs_theta": res.max_abs_theta(K),
                "n_singles": rc.get(1, 0),
                "n_doubles": rc.get(2, 0),
                "n_higher": sum(v for r, v in rc.items() if r > 2),
            }
        )
    return rows, max_ledger_dev


def chain_json(path, res, basis, note):
    steps = [
        {
            "step": i + 1,
            "factor": sub.label(basis.L),
            "holes": list(sub.holes),
            "parts": list(sub.parts),
            "rank": sub.rank,
            "theta": th,
            "tan_theta": float(np.tan(th)),
        }
        for i, (sub, th) in enumerate(res.selected())
    ]
    payload = {
        "schema": "chaincompile.chain.v0",
        "generated": str(date.today()),
        "note": note,
        "ordering": (
            "preparation order: the FIRST listed factor is applied to the "
            "pivot first; truncation at K keeps the first K factors. "
            "Ordering is part of the ansatz (T-7)."
        ),
        "pivot_determinant": basis.det_label(res.pivot_mask),
        "mode": res.mode,
        "policy": res.policy,
        "global_sign": res.global_sign,
        "final_residual": res.final_residual,
        "steps": steps,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def run_L6(U, do_translate, do_excited, summary):
    tag = f"L6_U{U:g}"
    say(f"== L=6 half filling, U={U:g} " + "=" * 30)
    basis = SectorBasis(6, 3, 3)
    H = hamiltonian(basis, U=U)
    evals, evecs = np.linalg.eigh(H)
    S2 = basis.s2_matrix()
    roots = roots_table(evals, evecs, basis, S2, nroots=8)
    write_text(
        RES / f"roots_{tag}.md",
        f"# Roots, momentum-space Hubbard {tag} (t=1)\n\n"
        + md_table(roots, ["root", "E", "K", "S2", "dominant_det", "dominant_weight"]),
    )
    say(f"sector dim {basis.dim}; E0 = {evals[0]:.9f} t; roots table written")

    fs, deg = fermi_sea_mask(6, 3, 3)
    assert not deg
    gs = evecs[:, 0]
    p_idx = int(np.argmax(np.abs(gs)))
    assert basis.masks[p_idx] == fs, "GS dominant det should be the Fermi sea here"

    results = {}
    for mode in ("sd_routed", "direct"):
        t0 = time.time()
        res = compile_chain(gs, basis, pivot_mask=fs, mode=mode)
        dt = time.time() - t0
        say(
            f"  compile[{mode:9s}]: length {res.length:4d}  "
            f"max|theta| {res.max_abs_theta():.4f}  "
            f"ranks {res.rank_counts()}  residual {res.final_residual:.2e}  "
            f"({dt:.2f} s)"
        )
        results[mode] = res

    res = results["sd_routed"]
    lrows = ledger_rows(res, basis)
    write_csv(RES / f"ledger_{tag}_gs_sd.csv", lrows, list(lrows[0].keys()))
    write_text(
        RES / f"ledger_{tag}_gs_sd.md",
        f"# Compile ledger (first 20 of {res.length} steps), {tag} GS, sd_routed\n\n"
        + md_table(lrows[:20], ["step", "factor", "rank_gen", "theta", "tan_theta",
                                "rank_mu", "rank_nu", "abs_c_mu", "abs_c_nu",
                                "fid_after", "flag"])
        + f"\nFull ledger: ledger_{tag}_gs_sd.csv\n",
    )

    trows, dev = truncation_rows(res, basis, H, evals[0])
    cols = ["K", "fidelity", "dE_mt", "pct_corr", "max_abs_theta",
            "n_singles", "n_doubles"]
    write_text(
        RES / f"truncation_{tag}_gs_sd.md",
        f"# K-truncation, {tag} GS, sd_routed (dE in 1e-3 t)\n\n"
        + md_table(trows, cols)
        + f"\nledger-vs-reconstruction max deviation: {dev:.2e}. "
        "fid_after(K) equals the K-prefix fidelity by construction; for "
        "jointly-solved SD words this curve is NOT monotone (ordering is "
        "part of the ansatz; see docs/METHOD.md). Use mode=direct for the "
        "anytime-graded chain.\n",
    )
    write_csv(RES / f"truncation_{tag}_gs_sd.csv", trows, list(trows[0].keys()))

    dres = results["direct"]
    trows_d, dev_d = truncation_rows(dres, basis, H, evals[0])
    write_text(
        RES / f"truncation_{tag}_gs_direct.md",
        f"# K-truncation, {tag} GS, direct (dE in 1e-3 t)\n\n"
        + md_table(trows_d, cols + ["n_higher"])
        + f"\nledger-vs-reconstruction max deviation: {dev_d:.2e}. "
        "Monotone by the elimination theorem: fid(K) = pivot amplitude "
        "after K elimination steps (no side blocks at the top rank).\n",
    )
    write_csv(RES / f"truncation_{tag}_gs_direct.csv", trows_d,
              list(trows_d[0].keys()))
    say(f"  truncation tables written (sd dev {dev:.2e}, direct dev {dev_d:.2e})")

    summary.append(
        {
            "system": tag + " GS",
            "pivot": basis.det_label(fs),
            "len_sd": res.length,
            "len_direct": dres.length,
            "max_theta_sd": res.max_abs_theta(),
            "max_theta_direct": dres.max_abs_theta(),
            "direct_ranks": str(dres.rank_counts()),
            "fid": 1.0 - res.final_residual,
        }
    )

    chain_json(RES / f"chain_{tag}_gs_sd.json", res, basis,
               f"compiled GS chain, momentum-space Hubbard {tag}")

    if do_translate:
        say("  translating (cluster analysis + SD-rank cap) ...")
        psi = prepare_state(res, basis)
        rep = sd_truncation_report(psi, basis, res.pivot_mask, H)
        lines = [f"# Translation diagnostics, {tag} GS (chain state)\n"]
        lines.append(
            f"cluster-analysis rebuild error: {rep['rebuild_err']:.2e} "
            f"(max excitation rank {rep['maxrank']})\n"
        )
        lines.append(md_table(rep["ranks"], ["rank", "n_amps", "norm2", "max_abs_t"]))
        e0 = evals[0]
        lines.append(
            "\nSD-rank-capped rebuild exp(T1+T2)|pivot> "
            "(the 'translated with reported distortion' numbers):\n\n"
        )
        lines.append(
            md_table(
                [
                    {
                        "state": "chain (exact)",
                        "fidelity_vs_target": 1.0 - res.final_residual,
                        "E": rep["E_chain"],
                        "dE_mt": (rep["E_chain"] - e0) * 1e3,
                    },
                    {
                        "state": "exp(T1+T2)|pivot>",
                        "fidelity_vs_target": rep["fidelity_sd"],
                        "E": rep["E_sd"],
                        "dE_mt": (rep["E_sd"] - e0) * 1e3,
                    },
                ],
                ["state", "fidelity_vs_target", "E", "dE_mt"],
            )
        )
        write_text(RES / f"translate_{tag}_gs.md", "".join(lines))
        export_amps_json(
            RES / f"amps_{tag}_gs.json",
            rep["t_amps"],
            res.pivot_mask,
            basis,
            energy=rep["E_chain"],
            meta={"system": tag, "root": 0, "chaincompile": __version__},
        )
        say(
            f"  translation: rebuild err {rep['rebuild_err']:.1e}; "
            f"SD-cap fidelity {rep['fidelity_sd']:.6f}, "
            f"dE {1e3 * (rep['E_sd'] - e0):.3f} mt; amps JSON written"
        )
        summary[-1]["sd_cap_fidelity"] = rep["fidelity_sd"]
        summary[-1]["sd_cap_dE_mt"] = 1e3 * (rep["E_sd"] - e0)

    if do_excited:
        r_ex = next(
            (r for r in range(1, 8) if roots[r]["S2"] < 0.1), 1
        )
        say(f"  excited-root demo: root {r_ex} "
            f"(E={roots[r_ex]['E']:.6f}, S2={roots[r_ex]['S2']:.3f}, "
            f"K={roots[r_ex]['K']})")
        tgt = evecs[:, r_ex]
        rese = compile_chain(tgt, basis, mode="sd_routed")  # pivot = argmax (re-reference)
        psie = prepare_state(rese, basis)
        fid = abs(rese.target @ psie)
        nflag = sum(1 for r in rese.ledger if r.flag)
        trows_e, dev_e = truncation_rows(rese, basis, H, roots[r_ex]["E"])
        write_text(
            RES / f"excited_{tag}_root{r_ex}_sd.md",
            f"# Excited root {r_ex}, {tag}, sd_routed, re-referenced pivot\n\n"
            f"pivot: {basis.det_label(rese.pivot_mask)} "
            f"(weight {max(np.abs(rese.target))**2:.4f}); "
            f"length {rese.length}; max|theta| {rese.max_abs_theta():.4f}; "
            f"flags {nflag}; final fidelity {fid:.12f}; "
            f"ledger-vs-reconstruction dev {dev_e:.2e}\n\n"
            + md_table(trows_e, cols),
        )
        say(
            f"    length {rese.length}, pivot {basis.det_label(rese.pivot_mask)}, "
            f"max|theta| {rese.max_abs_theta():.4f}, flags {nflag}, fidelity {fid:.10f}"
        )
        summary.append(
            {
                "system": f"{tag} root {r_ex} (S2={roots[r_ex]['S2']:.2f})",
                "pivot": basis.det_label(rese.pivot_mask),
                "len_sd": rese.length,
                "len_direct": "-",
                "max_theta_sd": rese.max_abs_theta(),
                "max_theta_direct": "-",
                "direct_ranks": "-",
                "fid": fid,
            }
        )


def run_L4(summary):
    tag = "L4_U8"
    say(f"== L=4 half filling, U=8 (P2 lattice; degenerate Fermi sea) " + "=" * 5)
    basis = SectorBasis(4, 2, 2)
    H = hamiltonian(basis, U=8.0)
    evals, evecs = np.linalg.eigh(H)
    S2 = basis.s2_matrix()
    roots = roots_table(evals, evecs, basis, S2, nroots=6)
    write_text(
        RES / f"roots_{tag}.md",
        f"# Roots, momentum-space Hubbard {tag} (t=1)\n\n"
        + md_table(roots, ["root", "E", "K", "S2", "dominant_det", "dominant_weight"]),
    )
    _, deg = fermi_sea_mask(4, 2, 2)
    say(f"sector dim {basis.dim}; degenerate Fermi sea: {deg} -> pivot from target root")
    gs = evecs[:, 0]
    out = {}
    for mode in ("sd_routed", "direct"):
        res = compile_chain(gs, basis, mode=mode)
        psi = prepare_state(res, basis)
        fid = abs(res.target @ psi)
        say(
            f"  compile[{mode:9s}]: pivot {basis.det_label(res.pivot_mask)}  "
            f"length {res.length:3d}  ranks {res.rank_counts()}  "
            f"max|theta| {res.max_abs_theta():.4f}  fidelity {fid:.12f}"
        )
        out[mode] = res
    rd = out["direct"].rank_counts()
    say(
        "  P2 tie-in: direct mode uses "
        f"{rd.get(4, 0)} quadruple factor(s) (Table 1's quad rotation); "
        "sd_routed replaces them with a doubles route."
    )
    pres = compile_chain(gs, basis, mode="sd_paired")
    say(f"  compile[sd_paired]: length {pres.length:4d}  "
        f"units {pres.solver_info['units']}  forced "
        f"{pres.solver_info['forced_overlap']}  max|theta| "
        f"{pres.max_abs_theta():.4f}  residual {pres.final_residual:.2e}")
    summary.append(
        {
            "system": tag + " GS",
            "pivot": basis.det_label(out["sd_routed"].pivot_mask),
            "len_sd": out["sd_routed"].length,
            "len_direct": out["direct"].length,
            "max_theta_sd": out["sd_routed"].max_abs_theta(),
            "max_theta_direct": out["direct"].max_abs_theta(),
            "direct_ranks": str(rd),
            "fid": 1.0 - out["sd_routed"].final_residual,
        }
    )


def main():
    t0 = time.time()
    say(f"chaincompile {__version__} worked validation  ({date.today()})")
    say(f"results -> {RES}")
    summary: list = []
    run_L6(2.0, do_translate=False, do_excited=False, summary=summary)
    run_L6(6.0, do_translate=True, do_excited=True, summary=summary)
    run_L4(summary)
    write_text(
        RES / "summary.md",
        "# chaincompile worked validation -- summary\n\n"
        f"generated {date.today()}, chaincompile {__version__}; "
        "momentum-space Hubbard ring, t=1; all compiles exact "
        "(residual < 1e-12) by construction.\n\n"
        + md_table(
            summary,
            ["system", "pivot", "len_sd", "len_direct", "max_theta_sd",
             "max_theta_direct", "direct_ranks", "sd_cap_fidelity",
             "sd_cap_dE_mt", "fid"],
        ),
    )
    say(f"\nsummary.md written; total {time.time() - t0:.1f} s")


if __name__ == "__main__":
    sys.exit(main())

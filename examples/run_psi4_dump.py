"""Ingest a tucc-psi4-dump-1 file end to end (Seneca side):
load -> certification identity -> FCI roots with S^2 labels (ADR-003)
-> sd_routed compile -> constructive translation ->
results/psi4_<name>.md.

Usage: python -u examples/run_psi4_dump.py path/to/dump.npz
       [--nroots 4] [--max-dim 4000]
"""
import argparse
import os

import numpy as np

from chaincompile.compile import compile_chain
from chaincompile.dets import Substitution
from chaincompile.diagnostics import md_table, write_text
from chaincompile.molecular import build_h_sector, load_integral_dump
from chaincompile.sector import SectorBasis
from chaincompile import disentangle as dz
from chaincompile import normalorder as NO

RES = os.path.join(os.path.dirname(__file__), "..", "results")


def hf_mask(na, nb):
    m = 0
    for i in range(na):
        m |= 1 << (2 * i)
    for i in range(nb):
        m |= 1 << (2 * i + 1)
    return m


def canonical_dominant(sb, v, tol=1e-9):
    a = np.abs(v)
    mx = float(np.max(a))
    mask = min(sb.masks[i] for i in range(sb.dim) if a[i] > mx - tol)
    return sb.det_label(mask), float(v[sb.index[mask]] ** 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--nroots", type=int, default=4)
    ap.add_argument("--max-dim", type=int, default=4000)
    ap.add_argument("--mode", default="sd_routed",
                    choices=["sd_routed", "sd_paired", "direct"])
    ap.add_argument("--n-core", type=int, default=0,
                    help="freeze this many lowest doubly occupied "
                         "orbitals (active-space calculation)")
    a = ap.parse_args()
    h_mo, eri_mo, e_shift, e_scf, na, nb, meta = load_integral_dump(a.dump)
    from chaincompile.molecular import freeze_core
    h_mo, eri_mo, e_core = freeze_core(h_mo, eri_mo, a.n_core)
    na -= a.n_core
    nb -= a.n_core
    e_shift = e_shift + e_core
    nmo = h_mo.shape[0]
    sb = SectorBasis(nmo, na, nb)
    name = str(meta.get("molecule", "custom"))
    if name == "custom":   # legacy dumps predate stem-naming
        name = os.path.splitext(os.path.basename(a.dump))[0]
    core_note = (f", {a.n_core} core frozen (E_core {e_core:+.6f})"
                 if a.n_core else "")
    print(f"{name}: active nmo {nmo}, sector ({na},{nb}), dim {sb.dim}"
          f"{core_note}", flush=True)
    if sb.dim > a.max_dim:
        raise SystemExit(f"sector dim {sb.dim} exceeds --max-dim "
                         f"{a.max_dim}; dense FCI not attempted")
    H = build_h_sector(h_mo, eri_mo, sb)
    hf = hf_mask(na, nb)
    ident = abs(H[sb.index[hf], sb.index[hf]] + e_shift - e_scf)
    print(f"certification identity |<HF|H|HF>+Enuc - E_SCF(dump)| = "
          f"{ident:.2e}", flush=True)
    # symmetry-block check: is the support the full H-connected block?
    import collections
    adj = np.abs(H) > 1e-10
    seen = {sb.index[hf]}
    dq = collections.deque(seen)
    while dq:
        i = dq.popleft()
        for j in np.nonzero(adj[i])[0]:
            j = int(j)
            if j not in seen:
                seen.add(j)
                dq.append(j)
    block = len(seen)
    w, Vv = np.linalg.eigh(H)
    v0 = Vv[:, 0]
    floor = np.sqrt(1e-12) / sb.dim
    sup1 = int(np.sum(np.abs(v0) > floor))
    # the ground state may live in a DIFFERENT block than HF (state
    # reordering; measured at stretched C2) -- walk from its own
    # dominant determinant as well
    from chaincompile.molecular import dominant_block_projection
    v0, seen2, mixed = dominant_block_projection(v0, H)
    block_gs = len(seen2)
    if mixed:
        sup1 = int(np.sum(np.abs(v0) > floor))
        print("degenerate ground pair mixed by the eigensolver -- "
              "projected onto the dominant determinant's block "
              f"(support now {sup1})", flush=True)
    print(f"symmetry blocks: HF-connected {block}, ground-state-"
          f"connected {block_gs} of {sb.dim}; ground support {sup1}"
          + ("" if sb.index[hf] in seen2 else
             "  [ground state NOT in the HF block]"), flush=True)
    S2 = sb.s2_matrix()
    rows = []
    for r in range(min(a.nroots, sb.dim)):
        v = Vv[:, r]
        lab, wgt = canonical_dominant(sb, v)
        rows.append({"root": r, "E_tot": w[r] + e_shift,
                     "S2": float(v @ S2 @ v), "dominant": lab,
                     "weight": wgt})
    from chaincompile.factors import apply_ucc_factor
    res = compile_chain(v0, sb, mode=a.mode)
    word = [s for s, _ in res.selected()]
    th = [t for _, t in res.selected()]
    # prefix <S^2> peak (spin grading readout; sd modes)
    s2_peak = None
    if a.mode != "direct":
        v = sb.basis_vector(res.pivot_mask)
        s2_peak = 0.0
        for sub, t in zip(word, th):
            v = apply_ucc_factor(v, sb, sub, float(t))
            s2_peak = max(s2_peak, abs(float(v @ S2 @ v)))
    extra = ""
    if a.mode == "sd_paired":
        extra = (f"  units {res.solver_info.get('units')}  forced "
                 f"{res.solver_info.get('forced_overlap')}")
    if a.mode == "direct":
        dev, namps = None, None
        print(f"direct len {res.length} residual "
              f"{res.final_residual:.1e}; translation skipped "
              f"(rank-cost law, METHOD sec 18)", flush=True)
    else:
        occ = frozenset(p for p in range(2 * nmo)
                        if (res.pivot_mask >> p) & 1)
        U, sizes = NO.compose_numeric(word, th, occ)
        c0, amps = NO.numeric_ref_amplitudes(U, occ)
        namps = len(amps) + 1
        ref = tuple(sorted(occ))
        state = {ref: 1.0}
        for sub, t in zip(word, th):
            state = dz.apply_factor(sub, float(t), state, tol=0.0)
        dev = abs(c0 - state.get(ref, 0.0))
        for (h, p), w_ in amps.items():
            det, sg = dz.apply_A(Substitution(h, p), ref)
            dev = max(dev, abs(w_ - sg * state.get(det, 0.0)))
        print(f"{a.mode} len {res.length} residual "
              f"{res.final_residual:.1e}; NOC acceptance {dev:.1e}; "
              f"prefix <S2> peak {s2_peak:.3f}{extra}", flush=True)
    lines = [
        f"# Psi4-dump ingestion -- {name}\n",
        f"Source: {meta.get('source', 'unknown')}; basis "
        f"{meta.get('basis', 'unknown')}; active nmo {nmo}; sector "
        f"({na},{nb}) dim {sb.dim}"
        + (f"; {a.n_core} core orbitals frozen, E_core = {e_core:.8f}"
           if a.n_core else "") + ".\n",
        f"Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = {ident:.2e}. "
        f"E_SCF = {e_scf:.8f}; E_FCI = {w[0]+e_shift:.8f}; Ecorr = "
        f"{w[0]+e_shift-e_scf:.8f}.\n",
        md_table(rows, ["root", "E_tot", "S2", "dominant", "weight"]),
        f"\nSymmetry blocks: HF-connected {block}, ground-state-"
        f"connected {block_gs} of {sb.dim}; ground support {sup1}"
        + ("" if sb.index[hf] in seen2 else
           " -- ground state NOT in the HF block (state reordering)")
        + (" Degenerate pair projected onto the dominant block."
           if mixed else "") + ".\n",
        f"\n{a.mode}: length {res.length}, ranks {res.rank_counts()}, "
        f"max|theta| {res.max_abs_theta():.6f}, residual "
        f"{res.final_residual:.1e}."
        + ("" if s2_peak is None else
           f" Prefix <S2> peak {s2_peak:.4f}.{extra}")
        + ("" if dev is None else
           f" Constructive translation: {namps} creator monomials, "
           f"acceptance {dev:.1e}.") + "\n",
    ]
    suffix = "" if a.mode == "sd_routed" else f"_{a.mode}"
    if a.n_core:
        suffix += f"_nc{a.n_core}"
    out = os.path.join(RES, f"psi4_{name}{suffix}.md")
    write_text(out, "\n".join(lines))
    print(f"-> results/psi4_{name}.md")


if __name__ == "__main__":
    main()

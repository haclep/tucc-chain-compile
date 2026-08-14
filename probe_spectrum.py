"""probe_spectrum.py -- read-only dense spectrum reference.

The first half of examples/run_psi4_dump.py (load -> certification
identity -> exact dense diagonalization -> roots with S^2 labels ->
two-anchor block walk with degenerate projection) with NO compile
stage, for systems whose dense compile is unaffordable but whose
exact low spectrum is needed as the census reference for a sparse
run. Prints to console; writes nothing.

Every physics line is a verbatim recomposition of the corresponding
run_psi4_dump.py lines, so its output is directly comparable to the
ingestion reports.

Usage (repo root, Seneca env):
  python -u probe_spectrum.py h8_chain.npz --nroots 6
  python -u probe_spectrum.py somedump.npz --n-core 2 --nroots 6
"""
import argparse
import collections

import numpy as np

from chaincompile.diagnostics import md_table
from chaincompile.molecular import (build_h_sector,
                                    dominant_block_projection,
                                    freeze_core, load_integral_dump)
from chaincompile.sector import SectorBasis


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
    ap.add_argument("--nroots", type=int, default=6)
    ap.add_argument("--max-dim", type=int, default=5000)
    ap.add_argument("--n-core", type=int, default=0)
    a = ap.parse_args()

    h_mo, eri_mo, e_shift, e_scf, na, nb, meta = load_integral_dump(a.dump)
    h_mo, eri_mo, e_core = freeze_core(h_mo, eri_mo, a.n_core)
    na -= a.n_core
    nb -= a.n_core
    e_shift = e_shift + e_core
    nmo = h_mo.shape[0]
    sb = SectorBasis(nmo, na, nb)
    core_note = (f", {a.n_core} core frozen (E_core {e_core:+.6f})"
                 if a.n_core else "")
    print(f"{a.dump}: active nmo {nmo}, sector ({na},{nb}), "
          f"dim {sb.dim}{core_note}", flush=True)
    if sb.dim > a.max_dim:
        raise SystemExit(f"sector dim {sb.dim} exceeds --max-dim "
                         f"{a.max_dim}; dense diagonalization not "
                         f"attempted")
    H = build_h_sector(h_mo, eri_mo, sb)
    hf = hf_mask(na, nb)
    ident = abs(H[sb.index[hf], sb.index[hf]] + e_shift - e_scf)
    print(f"certification identity |<HF|H|HF>+Enuc - E_SCF(dump)| = "
          f"{ident:.2e}", flush=True)

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
    v0, seen2, mixed = dominant_block_projection(v0, H)
    if mixed:
        sup1 = int(np.sum(np.abs(v0) > floor))
        print("degenerate ground pair mixed by the eigensolver -- "
              "projected onto the dominant determinant's block "
              f"(support now {sup1})", flush=True)
    print(f"symmetry blocks: HF-connected {block}, ground-state-"
          f"connected {len(seen2)} of {sb.dim}; ground support {sup1}"
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
    print()
    print(md_table(rows, ["root", "E_tot", "S2", "dominant", "weight"]))
    print("\nread-only: nothing was written.")


if __name__ == "__main__":
    main()

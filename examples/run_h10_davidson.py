"""The dense-impossible demonstration: H10 ring, sector (5,5),
dim 63,504 -- the dense matrix would be 32 GB and is never built.
Sparse construction once, then Davidson. Requires numba (the [fast]
extra); several minutes total, dominated by the one-time sparse build.
-> results/h10_davidson.md (deterministic content; timings console-only)
"""
import os
import time

import numpy as np

from chaincompile.diagnostics import write_text
from chaincompile.fastpath import SparseH, davidson
from chaincompile.molecular import hydrogen_integrals, mo_integrals, rhf
from chaincompile.sector import SectorBasis

RES = os.path.join(os.path.dirname(__file__), "..", "results")


def main():
    import argparse
    from chaincompile.fastpath import status
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-slow", action="store_true",
                    help="run even without numba (hours-tier)")
    a = ap.parse_args()
    if not status() and not a.allow_slow:
        raise SystemExit(
            "Refusing the dense-impossible demo without numba: the "
            "pure-Python build takes ~2+ hours (measured). Install "
            "numba (pip install numba) or pass --allow-slow.")
    t0 = time.time()
    R = 1.8
    cent = np.array([[np.cos(2 * np.pi * k / 10),
                      np.sin(2 * np.pi * k / 10), 0.0]
                     for k in range(10)]) * (R / (2 * np.sin(np.pi / 10)))
    S, T, V, ERI, enuc = hydrogen_integrals(cent, "sto-3g")
    C, eps, e_el, conv = rhf(S, T + V, ERI, 5, damp=0.3)
    h, e = mo_integrals(C, T + V, ERI)
    e_rhf = e_el + enuc
    print(f"integrals+RHF {time.time()-t0:.0f}s conv {conv}", flush=True)
    basis = SectorBasis(10, 5, 5)
    t0 = time.time()
    sp = SparseH(h, e, basis, chunk=2048)
    print(f"sparse build {time.time()-t0:.0f}s nnz {sp.nnz}", flush=True)
    t0 = time.time()
    w, X, nmv = davidson(sp, nroots=1, tol=1e-9)
    res = float(np.linalg.norm(sp.matvec(X[:, 0]) - w[0] * X[:, 0]))
    print(f"davidson {time.time()-t0:.0f}s: E {w[0]+enuc:.6f} "
          f"({nmv} matvecs, residual {res:.1e})", flush=True)
    floor = np.sqrt(1e-12) / basis.dim
    sup = int(np.sum(np.abs(X[:, 0]) > floor))
    write_text(os.path.join(RES, "h10_davidson.md"),
        "# H10 ring -- the first dense-impossible exact ground state\n\n"
        f"Sector (5,5), dim {basis.dim}; the dense matrix would be "
        f"{basis.dim**2*8/1e9:.0f} GB and is never built. Sparse H: "
        f"{sp.nnz} stored couplings ({sp.nnz*16/1e6:.0f} MB). "
        f"E_RHF = {e_rhf:.6f}; E_FCI = {w[0]+enuc:.6f}; Ecorr = "
        f"{w[0]+enuc-e_rhf:.6f}; Davidson converged in {nmv} matvecs "
        f"to residual {res:.1e}. Ground-state support {sup} of "
        f"{basis.dim}. Gates: sparse matvec vs the dense builder < "
        f"1e-12 (tests), and a one-shot term-walk cross-check at this "
        f"dimension agreed to 2e-14 (METHOD sec 22).\n")
    print("-> results/h10_davidson.md")


if __name__ == "__main__":
    main()

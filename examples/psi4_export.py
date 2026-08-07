"""Psi4 -> tucc integral exporter. RUN THIS IN YOUR `upgradation` CONDA
ENVIRONMENT (it imports psi4; it deliberately imports nothing from
chaincompile, so the two environments never mix).

Writes the tucc-psi4-dump-1 schema consumed by
chaincompile.molecular.load_integral_dump and examples/run_psi4_dump.py:
spatial-orbital MO integrals from a canonical RHF (energy-ascending,
symmetry c1), ERI in CHEMISTS' notation (ij|kl), total SCF energy for
the certification identity, no frozen core.

NOTE: written against the stable psi4 MintsHelper API but untested in
this repository's numpy-only environment -- your first run certifies
it, and the loader-side identity <HF|H|HF> + Enuc = E_RHF is the
tripwire: ANY convention mismatch (notation, ordering, units) fails it
loudly.

Examples (PowerShell, upgradation env):
  python psi4_export.py --system h4_rect --basis 6-31g --out h4_631g_psi4.npz
  python psi4_export.py --system h2_14 --basis cc-pvdz --out h2_ccpvdz.npz
  python psi4_export.py --system lih_30 --basis sto-3g --out lih_sto3g.npz
  python psi4_export.py --geom "H 0 0 0; H 0 0 1.4" --basis 6-31g --out custom.npz
"""
import argparse

import numpy as np

PRESETS = {
    "h2_14": [("H", 0, 0, 0), ("H", 0, 0, 1.4)],
    "h4_rect": [("H", 0, 0, 0), ("H", 2.0, 0, 0),
                ("H", 0, 2.5, 0), ("H", 2.0, 2.5, 0)],
    "h4_nearsq": [("H", 0, 0, 0), ("H", 2.0, 0, 0),
                  ("H", 0, 2.05, 0), ("H", 2.0, 2.05, 0)],
    "h6_ring": None,  # built below (side 1.9 bohr)
    "lih_30": [("Li", 0, 0, 0), ("H", 0, 0, 3.0)],
}


def h6_ring(side=1.9):
    import math
    r = side / (2 * math.sin(math.pi / 6))
    return [("H", r * math.cos(2 * math.pi * k / 6),
             r * math.sin(2 * math.pi * k / 6), 0.0) for k in range(6)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", choices=sorted(PRESETS))
    ap.add_argument("--geom", help="'Elem x y z; Elem x y z; ...' in bohr")
    ap.add_argument("--basis", default="sto-3g")
    ap.add_argument("--charge", type=int, default=0)
    ap.add_argument("--mult", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if a.system:
        atoms = h6_ring() if a.system == "h6_ring" else PRESETS[a.system]
        name = a.system
    elif a.geom:
        atoms = [(t[0], *map(float, t[1:4])) for t in
                 (x.split() for x in a.geom.split(";"))]
        import os
        name = os.path.splitext(os.path.basename(a.out))[0]
    else:
        ap.error("--system or --geom required")

    import psi4
    psi4.core.set_output_file("psi4_export.out", False)
    lines = "\n".join(f"{e} {x:.10f} {y:.10f} {z:.10f}"
                      for e, x, y, z in atoms)
    mol = psi4.geometry(
        f"{a.charge} {a.mult}\n{lines}\nunits bohr\nsymmetry c1\n")
    psi4.set_options({"basis": a.basis, "scf_type": "pk",
                      "reference": "rhf", "e_convergence": 1e-11,
                      "d_convergence": 1e-10})
    e_scf, wfn = psi4.energy("scf", return_wfn=True)
    mints = psi4.core.MintsHelper(wfn.basisset())
    T = np.asarray(mints.ao_kinetic())
    V = np.asarray(mints.ao_potential())
    ERI = np.asarray(mints.ao_eri())          # chemists' (uv|ls)
    C = np.asarray(wfn.Ca())
    h_mo = C.T @ (T + V) @ C
    eri_mo = np.einsum("abcd,ap,bq,cr,ds->pqrs", ERI, C, C, C, C,
                       optimize=True)
    extra = {}
    try:  # optional orbital labels: <Lz^2> per MO (sigma 0, pi 1)
        Lmats = mints.ao_angular_momentum()
        Az = np.asarray(Lmats[2])          # Lz = i * Az (Az real antisym)
        Amo = C.T @ Az @ C
        extra["lz2_mo_diag"] = -np.diag(Amo @ Amo)
    except Exception as ex:                 # informational only
        print(f"(lz2 labels skipped: {ex})")
    np.savez(a.out, schema="tucc-psi4-dump-1", **extra,
             h_mo=h_mo, eri_mo=eri_mo,
             e_nuc=float(mol.nuclear_repulsion_energy()),
             e_scf=float(e_scf),
             n_alpha=int(wfn.nalpha()), n_beta=int(wfn.nbeta()),
             mo_energies=np.asarray(wfn.epsilon_a()),
             basis=a.basis, molecule=name,
             source=f"psi4 {psi4.__version__}", geometry_str=lines)
    print(f"wrote {a.out}: nmo {h_mo.shape[0]}, e_scf {e_scf:.10f}, "
          f"n_alpha/beta {wfn.nalpha()}/{wfn.nbeta()}")


if __name__ == "__main__":
    main()

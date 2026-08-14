"""Seneca-side hydrogen-system dump minter (no conda required).

Writes tucc-psi4-dump-1 files for H_N chains and rings from the
self-contained s-only closed-form integrals (chaincompile.molecular),
so hydrogen systems flow through the same stamped ingestion path as
every Psi4 molecule. The loader-side certification identity
    |<HF|H|HF> + Enuc - E_SCF(dump)| ~ 1e-13
is the validator: any schema or convention error in this writer
fails C0 loudly at the first ingestion.

The schema (12 keys) matches psi4_export.py and the enumerated
on-disk dumps exactly. Source is stamped "tucc s-only closed forms"
so reports distinguish internal from Psi4 integrals; molecule is
stamped with the out-file stem so reports are born properly named.

RHF at stretched geometries can refuse to converge: a dump is only
written when RHF reports convergence (no silent degradation); raise
--damp and retry on failure. Existing dumps are never overwritten
without --force.

Usage (repo root, Seneca env):
  python -u examples/make_h_dumps.py --list
  python -u examples/make_h_dumps.py h6_ring_19
  python -u examples/make_h_dumps.py --set h6_scan
  python -u examples/make_h_dumps.py --set h8_pair
  python -u examples/make_h_dumps.py h6_chain_36 --damp 0.6 --force
"""
import argparse
import math
import os

import numpy as np

BASIS = "sto-3g"
SOURCE = "tucc s-only closed forms"


def chain(n, s):
    """n hydrogens on the z axis, nearest-neighbor spacing s (bohr)."""
    return np.array([[0.0, 0.0, s * k] for k in range(n)], dtype=float)


def ring(n, s):
    """n hydrogens on a circle with nearest-neighbor spacing s (bohr)."""
    r = s / (2.0 * math.sin(math.pi / n))
    return np.array([[r * math.cos(2.0 * math.pi * k / n),
                      r * math.sin(2.0 * math.pi * k / n), 0.0]
                     for k in range(n)], dtype=float)


def spec(n, topo, s, damp):
    build = chain if topo == "chain" else ring
    return {"n": n, "topo": topo, "s": s, "damp": damp,
            "cent": build(n, s)}


GRID6 = (1.4, 1.8, 1.9, 2.4, 3.0, 3.6)
SYSTEMS = {}
for _s in GRID6:
    _tag = f"{_s:.1f}".replace(".", "")
    _damp = 0.3 if _s < 2.4 else 0.5
    SYSTEMS[f"h6_chain_{_tag}"] = spec(6, "chain", _s, _damp)
    SYSTEMS[f"h6_ring_{_tag}"] = spec(6, "ring", _s, _damp)
SYSTEMS["h8_chain"] = spec(8, "chain", 1.9, 0.3)
SYSTEMS["h8_ring"] = spec(8, "ring", 1.9, 0.4)

SETS = {
    "h6_scan": sorted(k for k in SYSTEMS if k.startswith("h6_")),
    "h8_pair": ["h8_chain", "h8_ring"],
    "all": sorted(SYSTEMS),
}


def geometry_lines(cent):
    return "\n".join(f"H {x:.10f} {y:.10f} {z:.10f}" for x, y, z in cent)


def build_payload(name, cent, ndocc, e_nuc, e_scf, eps, h_mo, eri_mo):
    """The exact 12-key tucc-psi4-dump-1 payload (order-independent)."""
    return {
        "schema": "tucc-psi4-dump-1",
        "h_mo": h_mo,
        "eri_mo": eri_mo,
        "e_nuc": float(e_nuc),
        "e_scf": float(e_scf),
        "n_alpha": int(ndocc),
        "n_beta": int(ndocc),
        "mo_energies": np.asarray(eps),
        "basis": BASIS,
        "molecule": name,
        "source": SOURCE,
        "geometry_str": geometry_lines(cent),
    }


def make_one(name, sp, damp_override, force):
    from chaincompile.molecular import hydrogen_integrals, mo_integrals, rhf
    out = f"{name}.npz"
    if os.path.exists(out) and not force:
        print(f"{name}: {out} exists -- skipped (use --force to rewrite)")
        return "skipped"
    damp = sp["damp"] if damp_override is None else damp_override
    cent = sp["cent"]
    ndocc = sp["n"] // 2
    S, T, V, ERI, e_nuc = hydrogen_integrals(cent, BASIS)
    C, eps, e_el, conv = rhf(S, T + V, ERI, ndocc, damp=damp)
    if not conv:
        print(f"{name}: RHF NOT CONVERGED (damp {damp}) -- dump NOT "
              f"written; retry with a larger --damp")
        return "failed"
    h_mo, eri_mo = mo_integrals(C, T + V, ERI)
    e_scf = e_el + e_nuc
    np.savez(out, **build_payload(name, cent, ndocc, e_nuc, e_scf,
                                  eps, h_mo, eri_mo))
    print(f"wrote {out}: nmo {h_mo.shape[0]}, e_scf {e_scf:.10f}, "
          f"n_alpha/beta {ndocc}/{ndocc}, damp {damp}, "
          f"{sp['topo']} spacing {sp['s']:.1f} bohr")
    return "written"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stems", nargs="*",
                    help="system stems to write (see --list)")
    ap.add_argument("--set", dest="setname", choices=sorted(SETS),
                    help="write a named set of systems")
    ap.add_argument("--damp", type=float, default=None,
                    help="override the per-system RHF damping")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing dump")
    ap.add_argument("--list", action="store_true",
                    help="list available systems and sets, then exit")
    a = ap.parse_args()
    if a.list:
        for k in sorted(SYSTEMS):
            sp = SYSTEMS[k]
            print(f"  {k:14s} H{sp['n']} {sp['topo']:5s} "
                  f"spacing {sp['s']:.1f} bohr  damp {sp['damp']}")
        for k in sorted(SETS):
            print(f"  --set {k}: {len(SETS[k])} systems")
        return
    names = list(a.stems)
    if a.setname:
        names += SETS[a.setname]
    if not names:
        ap.error("no systems selected (give stems, --set, or --list)")
    seen, order = set(), []
    for n in names:
        if n not in SYSTEMS:
            ap.error(f"unknown system {n!r} (see --list)")
        if n not in seen:
            seen.add(n)
            order.append(n)
    tally = {"written": 0, "skipped": 0, "failed": 0}
    for n in order:
        tally[make_one(n, SYSTEMS[n], a.damp, a.force)] += 1
    print(f"done: {tally['written']} written, {tally['skipped']} "
          f"skipped, {tally['failed']} failed")
    if tally["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

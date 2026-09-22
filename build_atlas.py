#!/usr/bin/env python
"""build_atlas.py -- generate the Seneca corpus specification.

Emits atlas.json: every system the foundry should produce, with active space,
spin sector, geometry sweep, computed sector dimension, the phase it belongs
to, and the RECIPE k1c_corpus.py follows to build its Hamiltonian dump
(geometry builder, orbital-space selection, file stem). Dimensions are
computed here, never transcribed.

A "system" is one (molecule, geometry, active space, spin sector). Each
system yields ~20 certified derivations from the gauge factory's quick plan.

Conventions shared with k1c_corpus.py
  * geometries are in Angstrom, except the hydrogen models, whose spacing
    grid is in BOHR so that their stems match the existing K1 corpus
    (k1_h6_ring_19 = H6 ring, 1.9 bohr). Their dumps still carry the
    geometry in Angstrom with an explicit units key.
  * a ring's parameter is the nearest-neighbour distance. For H6 this
    equals the ring radius, which is the convention of the sample pack's
    H6 ring; for other ring sizes the two differ.
  * selection "full"   : every orbital of the basis is active (RHF orbitals)
    selection "energy" : CASSCF; starting space = the mean-field orbitals
                         around the Fermi level (frozen core below)
    selection "avas"   : CASSCF; starting space chosen by projection onto
                         the listed atomic orbitals, count-matched to the
                         requested (n_electrons, n_orbitals)
"""
import json
from math import comb
from collections import defaultdict

# Equilibrium bond lengths in Angstrom. VERIFY against NIST CCCBDB before
# production; these are working values good to ~0.02 A.
RE = {
    "H2": 0.741, "LiH": 1.596, "BeH2": 1.334, "BH": 1.232, "HF": 0.917,
    "N2": 1.098, "C2": 1.243, "O2": 1.208, "F2": 1.412, "CO": 1.128,
    "BN": 1.281, "BeO": 1.331, "LiF": 1.564,
    "ScH": 1.775, "TiH": 1.781, "VH": 1.719, "CrH": 1.655,
    "MnH": 1.731, "FeH": 1.589, "CoH": 1.514, "NiH": 1.454, "CuH": 1.463,
    "Cr2": 1.679, "Mo2": 1.940,
    "TiO": 1.620, "VO": 1.589, "CrO": 1.615,
    "H2O": 0.958, "NH3": 1.012, "CH4": 1.087, "O3": 1.278,
}

# Scan multipliers of Re. Dense near equilibrium, out to full dissociation.
SCAN = [0.85, 0.95, 1.00, 1.10, 1.25, 1.45, 1.70, 2.00, 2.50, 3.20]
# Cr2/Mo2: extra points across the 2.5-3.0 A shoulder, in absolute Angstrom.
CR2_ABS = [1.40, 1.55, 1.68, 1.80, 2.00, 2.20, 2.40, 2.60, 2.80, 3.00,
           3.30, 3.80, 4.50]
# Hydrogen models: BOHR grid, a 12-point subset of the K1 corpus grid
# (1.2-3.6 bohr step 0.1). 1.9 is the sample-pack point.
H_BOHR = [1.2, 1.4, 1.6, 1.8, 1.9, 2.0, 2.2, 2.4, 2.6, 2.8, 3.2, 3.6]


def sector(nelec, mult):
    """(n_alpha, n_beta) from electron count and spin multiplicity."""
    unpaired = mult - 1
    nb = (nelec - unpaired) // 2
    return nelec - nb, nb


def dim(norb, nelec, mult):
    na, nb = sector(nelec, mult)
    return comb(norb, na) * comb(norb, nb)


SYSTEMS = []


def add(label, formula, kind, nelec, norb, mult, basis, phase, why,
        scan=None, absolute=None, atoms=None, geometry="diatomic",
        selection="energy", avas=None, units="angstrom", equilibrium=None):
    na, nb = sector(nelec, mult)
    d = dim(norb, nelec, mult)
    if absolute is not None:
        geoms = list(absolute)
    elif scan is not None:
        geoms = [round(RE[formula] * m, 3) for m in scan]
    else:
        geoms = [RE[formula]]
    if phase == 0:                      # 0 = "assign me by dimension"
        phase = 1 if d <= 20000 else (3 if d <= 120000 else 4)
    if equilibrium is None:
        equilibrium = RE.get(formula)
    SYSTEMS.append({
        "label": label, "formula": formula, "kind": kind,
        "active_space": {"n_electrons": nelec, "n_orbitals": norb,
                         "multiplicity": mult, "n_alpha": na, "n_beta": nb},
        "sector_dimension": d, "basis": basis, "phase": phase,
        "geometries": geoms, "geometry_units": units,
        "n_geometries": len(geoms),
        "equilibrium": equilibrium,
        "recipe": {"geometry": geometry, "selection": selection,
                   "avas_labels": avas or []},
        "rationale": why,
        "atoms": atoms or formula,
    })


# ===================================================================
# PHASE 1  --  D <= 20,000.  Runs today, no new capability required.
# ===================================================================

# --- main-group dissociation atlas: the correlation-growth curriculum
mg = [
    ("h2",   "H2",   2,  2, 1, "the floor: exactly solvable by hand, D=4"),
    ("lih",  "LiH",  4,  6, 1, "continuity with the existing sample pack"),
    ("hf",   "HF",   8,  8, 1, "polar single bond, ionic dissociation"),
    ("lif",  "LiF",  8,  8, 1, "avoided crossing: ionic/covalent curve cross"),
    ("beo",  "BeO",  8,  8, 1, "polar double bond, low-lying excited states"),
    ("bn",   "BN",   8,  8, 1, "near-degenerate ground state, notoriously hard"),
    ("co",   "CO",  10,  8, 1, "triple bond, closed shell, industrially central"),
    ("n2",   "N2",  10,  8, 1, "the standard multireference benchmark"),
    ("c2",   "C2",   8,  8, 1, "contested bond order; multiple bonds at once"),
    ("f2",   "F2",  14, 10, 1, "weak bond; 2 virtuals added because full valence is nearly closed"),
]
for lab, f, ne, no, mult, why in mg:
    add(lab, f, "main-group diatomic", ne, no, mult, "cc-pVDZ", 0, why,
        scan=SCAN)

add("o2-triplet", "O2", "main-group diatomic", 12, 8, 3, "cc-pVDZ", 0,
    "open-shell ground state: exercises Sz != 0 in the compiler", scan=SCAN)

# --- polyatomic stretches
add("h2o-sym", "H2O", "polyatomic", 8, 6, 1, "cc-pVDZ", 0,
    "symmetric O-H stretch; double dissociation in a bent molecule",
    scan=SCAN, geometry="h2o-sym",
    atoms="H2O, HOH angle fixed 104.5 deg, both O-H scanned together")
add("nh3-sym", "NH3", "polyatomic", 8, 7, 1, "cc-pVDZ", 0,
    "triple N-H dissociation",
    scan=SCAN, geometry="nh3-sym",
    atoms="NH3, C3v, HNH angle fixed 106.7 deg, all three N-H scanned together")
add("ch4-sym", "CH4", "polyatomic", 8, 8, 1, "cc-pVDZ", 0,
    "quadruple C-H dissociation, the saturated-carbon reference",
    scan=SCAN, geometry="ch4-sym",
    atoms="CH4, Td, all four C-H scanned together")

# --- hydrogen ladder: continuity with existing work, clean size scaling.
# STO-3G and a BOHR grid, so that H4/H6 stems coincide with the K1 corpus
# already on disk (those dumps are reused, not regenerated).
for n, lab in [(4, "h4"), (6, "h6"), (8, "h8")]:
    for geom in ["chain", "ring"]:
        add("%s-%s" % (lab, geom), "H%d" % n, "hydrogen model", n, n, 1,
            "STO-3G", 0,
            "size ladder at fixed chemistry; %s already in the sample" % geom,
            absolute=H_BOHR, units="bohr", selection="full",
            geometry="h-" + geom, equilibrium=None,
            atoms="%d H atoms, uniform nearest-neighbour spacing, %s" % (n, geom))

# --- FIRST-ROW TRANSITION-METAL HYDRIDES
# Where 3d correlation enters the corpus, at trivial cost. Active space is
# metal 3d(5) + 4s(1) + 4p(3) + H 1s(1) = 10 orbitals throughout; the 4p
# keep the high-spin sectors non-trivial (MnH in 7 orbitals has D = 7).
tmh = [
    ("sch", "ScH",  4, 1, "3d^1: the simplest 3d bond"),
    ("tih", "TiH",  5, 4, "3d^2, 4-Phi ground state"),
    ("vh",  "VH",   6, 5, "3d^3, high spin"),
    ("crh", "CrH",  7, 6, "3d^5 4s^1: the Cr atom's own configuration"),
    ("mnh", "MnH",  8, 7, "3d^5 4s^2, maximal high spin"),
    ("feh", "FeH",  9, 4, "3d^6, near-degenerate low-lying states"),
    ("coh", "CoH", 10, 3, "3d^7"),
    ("nih", "NiH", 11, 2, "3d^8, approaching closed d shell"),
]
for lab, f, ne, mult, why in tmh:
    M = f[:-1]
    add(lab, f, "transition-metal hydride", ne, 10, mult, "def2-SVP", 0,
        "3d physics before Cr2. Space = 3d(5) + 4s + 4p(3) + H1s. " + why,
        scan=SCAN[:8], selection="avas",
        avas=["%s 3d" % M, "%s 4s" % M, "%s 4p" % M, "H 1s"])

# --- ozone: the classic main-group multireference pathology
add("o3", "O3", "polyatomic", 12, 9, 1, "cc-pVDZ", 0,
    "singlet ozone: strong biradical character at a closed-shell geometry",
    absolute=[1.20, 1.24, 1.278, 1.32, 1.40, 1.55, 1.75, 2.00],
    geometry="o3-sym",
    atoms="O3, C2v, OOO angle fixed 116.8 deg, both O-O scanned together")

# --- Cr2 AND Mo2 SUB-SPACES: the endgame enters the corpus now.
# Molecular axis is z: sigma = dz^2, pi = dxz, dyz, delta = dxy, dx2-y2.
CR_SP = ["Cr 3dz^2", "Cr 3dxz", "Cr 3dyz"]
MO_SP = ["Mo 4dz^2", "Mo 4dxz", "Mo 4dyz"]
add("cr2-cas66", "Cr2", "target sub-space", 6, 6, 1, "def2-SVP", 0,
    "Cr2 3d-sigma + 3d-pi only, 3d-delta frozen. Same molecule and geometry "
    "sweep as the CAS(12,12) target, at a dimension already proven.",
    absolute=CR2_ABS, selection="avas", avas=CR_SP)
add("cr2-cas88", "Cr2", "target sub-space", 8, 8, 1, "def2-SVP", 0,
    "Cr2 3d-sigma + 3d-pi + 4s-sigma. Second rung of the Cr2 ladder.",
    absolute=CR2_ABS, selection="avas", avas=CR_SP + ["Cr 4s"])
add("mo2-cas66", "Mo2", "target sub-space", 6, 6, 1, "def2-SVP", 0,
    "4d analogue of Cr2, sextuply bonded and less pathological: the "
    "dress rehearsal that fails cheaply.",
    scan=SCAN, selection="avas", avas=MO_SP)
add("mo2-cas88", "Mo2", "target sub-space", 8, 8, 1, "def2-SVP", 0,
    "Mo2 second rung.",
    scan=SCAN, selection="avas", avas=MO_SP + ["Mo 5s"])

# ===================================================================
# PHASE 3  --  D ~ 63,504.  Needs a high-memory instance (~10 GB J).
# ===================================================================
add("h10-chain", "H10", "hydrogen model", 10, 10, 1, "STO-3G", 0,
    "top of the hydrogen ladder; direct 13x scaling test vs h8",
    absolute=H_BOHR, units="bohr", selection="full", geometry="h-chain",
    equilibrium=None, atoms="10 H atoms, uniform spacing, chain")
add("h10-ring", "H10", "hydrogen model", 10, 10, 1, "STO-3G", 0,
    "ring counterpart",
    absolute=H_BOHR, units="bohr", selection="full", geometry="h-ring",
    equilibrium=None,
    atoms="10 H atoms, uniform nearest-neighbour spacing, ring")
add("cr2-cas1010", "Cr2", "target sub-space", 10, 10, 1, "def2-TZVP", 0,
    "Cr2 full 3d manifold, 4s excluded. Third rung; the last step before "
    "the target space.", absolute=CR2_ABS, selection="avas", avas=["Cr 3d"])
add("mo2-cas1010", "Mo2", "target sub-space", 10, 10, 1, "def2-TZVP", 0,
    "Mo2 third rung.", scan=SCAN, selection="avas", avas=["Mo 4d"])
for lab, f, ne, mult, why in [
        ("tio", "TiO", 10, 1, "3d metal oxide, closed-shell singlet"),
        ("vo",  "VO",  11, 4, "3d metal oxide, quartet"),
        ("cro", "CrO", 12, 5, "3d metal oxide, quintet; Cr in a second bonding motif")]:
    M = f[:-1]
    add(lab, f, "transition-metal oxide", ne, 10, mult, "def2-TZVP", 0,
        "3d physics at rung-2 size. Space = 3d(5) + 4s + O 2s + O 2p(3). " + why,
        scan=SCAN[:8], selection="avas",
        avas=["%s 3d" % M, "%s 4s" % M, "O 2s", "O 2p"])

# ===================================================================
# PHASE 4  --  D = 853,776.  Requires Jacobian-free Gauss-Newton.
# ===================================================================
add("mo2-cas1212", "Mo2", "target", 12, 12, 1, "def2-TZVP", 4,
    "Full 4d+5s valence. Run BEFORE Cr2: same dimension, same bonding "
    "pattern, less pathological.",
    scan=SCAN, selection="avas", avas=["Mo 4d", "Mo 5s"])
add("cr2-cas1212", "Cr2", "target", 12, 12, 1, "def2-TZVP", 4,
    "THE TARGET. Full 3d+4s valence, sextuple bond, 13 geometries spanning "
    "equilibrium (1.68 A), the shoulder (2.4-3.0 A), and dissociation.",
    absolute=CR2_ABS, selection="avas", avas=["Cr 3d", "Cr 4s"])

# ===================================================================
# summary
# ===================================================================
out = {
    "corpus": "seneca-atlas-v1",
    "author": "Dr. Luogen Xu, Seneca Labs",
    "note": "Each system yields ~20 certified derivations (gauge quick plan). "
            "Flagship systems use the wide plan (~120).",
    "conventions": {
        "geometry_units": "angstrom unless the system says bohr (hydrogen "
                          "models, to match K1 corpus stems)",
        "ring_parameter": "nearest-neighbour distance",
        "stems": "hydrogen models: k1_h<n>_<chain|ring>_<spacing in tenths "
                 "of a bohr>; all others: <label with - as _>_r<distance in "
                 "angstrom, 3 decimals, '.' as 'p'>",
        "dump_energies": "e_nuc is the CONSTANT part of the energy in the "
                         "orbital space: nuclear repulsion plus the frozen "
                         "core, if any. e_scf is the energy of the reference "
                         "determinant (lowest orbitals) in that space.",
    },
    "held_out": {
        "policy": "cr2-cas1212 is the size-transfer test. Train on the "
                  "Cr2 (6,6), (8,8) and (10,10) ladder; evaluate on (12,12), "
                  "which never enters training.",
        "systems": ["cr2-cas1212"],
    },
    "systems": SYSTEMS,
}
with open("atlas.json", "w") as fh:
    json.dump(out, fh, indent=1)

# ---- report
byphase = defaultdict(lambda: {"sys": 0, "geo": 0, "maxd": 0, "mols": set()})
for s in SYSTEMS:
    b = byphase[s["phase"]]
    b["sys"] += 1
    b["geo"] += s["n_geometries"]
    b["maxd"] = max(b["maxd"], s["sector_dimension"])
    b["mols"].add(s["formula"])

print("=" * 74)
print("SENECA ATLAS v1")
print("=" * 74)
print("%-7s %7s %10s %8s %10s %12s" %
      ("phase", "specs", "systems", "molec", "max dim", "records@20"))
tot = 0
for ph in sorted(byphase):
    b = byphase[ph]
    tot += b["geo"] * 20
    print("%-7d %7d %10d %8d %10d %12d"
          % (ph, b["sys"], b["geo"], len(b["mols"]), b["maxd"], b["geo"] * 20))
print("%-7s %7d %10d %8s %10s %12d"
      % ("total", len(SYSTEMS), sum(b["geo"] for b in byphase.values()),
         "", "", tot))

print("\nPHASE 1 BREAKDOWN (runs today)")
k = defaultdict(lambda: [0, 0])
for s in SYSTEMS:
    if s["phase"] == 1:
        k[s["kind"]][0] += 1
        k[s["kind"]][1] += s["n_geometries"]
for kind in sorted(k):
    print("  %-28s %3d specs  %4d systems" % (kind, k[kind][0], k[kind][1]))

p1 = sum(s["n_geometries"] for s in SYSTEMS if s["phase"] == 1)
print("\nPHASE 1 COST at ~18 core-hours per system (H6-scale, 20 derivations):")
print("  %d systems x 18 = %d core-hours" % (p1, p1 * 18))
print("  spot @ $0.0125/vCPU-hr  ->  $%.0f" % (p1 * 18 * 0.0125))
print("  one 60-vCPU spot VM     ->  %.1f days wall" % (p1 * 18 / 56 / 24))

print("\nOPEN-SHELL SYSTEMS (Sz != 0 -- new regime for the compiler):")
for s in SYSTEMS:
    if s["active_space"]["multiplicity"] > 1:
        a = s["active_space"]
        print("  %-14s mult %d  sector (%d,%d)  dim %d"
              % (s["label"], a["multiplicity"], a["n_alpha"], a["n_beta"],
                 s["sector_dimension"]))

print("\nTHE Cr2 LADDER (same molecule, same geometries, growing space):")
for s in SYSTEMS:
    if s["formula"] == "Cr2":
        a = s["active_space"]
        print("  %-14s CAS(%d,%2d)  dim %7d  phase %d  %d geometries"
              % (s["label"], a["n_electrons"], a["n_orbitals"],
                 s["sector_dimension"], s["phase"], s["n_geometries"]))

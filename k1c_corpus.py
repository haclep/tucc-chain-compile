#!/usr/bin/env python
"""k1c_corpus.py -- mint Hamiltonian dumps for every system in atlas.json.

Reads the atlas, builds each geometry, runs the mean field and (where the
recipe says so) a CASSCF in the requested active space, and writes
k1_corpus/<stem>.npz in the format the compiler's load_dump reads:

    h_mo           (n, n)        one-electron integrals in the orbital basis,
                                 frozen core folded in
    eri_mo         (n, n, n, n)  two-electron integrals, chemist notation (pq|rs)
    e_nuc          float         the CONSTANT part of the total energy in this
                                 space: nuclear repulsion + frozen-core energy
    e_scf          float         total energy of the reference determinant
                                 (lowest n_alpha alpha / n_beta beta orbitals)
    n_alpha, n_beta              the sector
    basis, molecule, geometry_str, geometry_units ("angstrom")

plus provenance keys (method, orbital_space, e_mean_field, e_casscf,
natural_occupations, ...). A JSON sidecar with the same provenance sits next
to each dump; k1_corpus/index.json accumulates one entry per finished stem;
k1_corpus/failures.log records anything that did not converge.

Orbital basis inside the active space: NATURAL ORBITALS of the CASSCF state,
sorted by occupation, largest first, so that "the lowest orbitals" are the
most occupied ones and the reference determinant is the natural leading
configuration. Hydrogen models (recipe "full") keep RHF canonical orbitals,
exactly as the existing K1 corpus does.

Every dump is checked before it is written: the FCI energy recomputed from
h_mo / eri_mo / e_nuc must reproduce the CASSCF energy, the sector dimension
must match the atlas, and the two lowest sector roots are recorded so that a
degenerate or spin-reordered ground state is visible in the sidecar.

Usage
    python k1c_corpus.py atlas.json                    # everything, phase 1 first
    python k1c_corpus.py atlas.json --phase 1          # one phase only
    python k1c_corpus.py atlas.json --only h2 lih      # some labels
    python k1c_corpus.py atlas.json --dry-run          # list the stems, do nothing
    python k1c_corpus.py atlas.json -j 8 --threads 2   # 8 systems at a time
    python k1c_corpus.py atlas.json --report           # table of what exists

Existing dumps are never overwritten; rerunning finishes what is missing.
Geometries within a system run in order of distance from equilibrium, each
CASSCF warm-started from the previous one, so the orbital space is continuous
along the scan.
"""
import argparse
import json
import os
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import comb, sin, cos, pi, sqrt, radians


def _threads_from_argv():
    """--threads must take effect before numpy loads its BLAS, so it is read
    here, ahead of the imports. Running more BLAS threads than cores makes
    parallel jobs many times slower, not faster."""
    for i, a in enumerate(sys.argv):
        if a == "--threads" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if a.startswith("--threads="):
            return a.split("=", 1)[1]
    return "1"


for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, _threads_from_argv())

import numpy as np  # noqa: E402

BOHR = 0.52917721092          # angstrom per bohr
OUT = "k1_corpus"
DUMP_SCHEMA = "tucc-psi4-dump-1"   # the tag chaincompile.molecular.load_integral_dump checks

# ------------------------------------------------------------------ stems

def stem_of(system, g):
    """File stem for one (system, geometry). Hydrogen models use the K1
    corpus scheme so that dumps already on disk are reused."""
    r = system["recipe"]["geometry"]
    if r in ("h-chain", "h-ring"):
        n = int(system["formula"][1:])
        tenths = int(round(g * 10))
        if abs(g * 10 - tenths) > 1e-9:
            raise ValueError("hydrogen spacing %r is not a tenth of a bohr" % g)
        return "k1_h%d_%s_%d" % (n, r[2:], tenths)
    return "%s_r%s" % (system["label"].replace("-", "_"),
                       ("%.3f" % g).replace(".", "p"))


# -------------------------------------------------------------- geometries

def split_formula(f):
    """'LiH' -> ['Li', 'H'];  'Cr2' -> ['Cr', 'Cr'];  'CO' -> ['C', 'O']."""
    import re
    out = []
    for sym, cnt in re.findall(r"([A-Z][a-z]?)(\d*)", f):
        out += [sym] * (int(cnt) if cnt else 1)
    return out


def build_geometry(system, g):
    """List of (symbol, x, y, z) in ANGSTROM for scan parameter g."""
    kind = system["recipe"]["geometry"]
    if system.get("geometry_units", "angstrom") == "bohr":
        g = g * BOHR
    if kind == "diatomic":
        a, b = split_formula(system["formula"])
        return [(a, 0.0, 0.0, 0.0), (b, 0.0, 0.0, g)]
    if kind == "h-chain":
        n = int(system["formula"][1:])
        return [("H", 0.0, 0.0, g * k) for k in range(n)]
    if kind == "h-ring":
        n = int(system["formula"][1:])
        R = g / (2.0 * sin(pi / n))          # nearest-neighbour distance g
        return [("H", R * cos(2 * pi * k / n), R * sin(2 * pi * k / n), 0.0)
                for k in range(n)]
    if kind == "h2o-sym":
        th = radians(104.5) / 2
        return [("O", 0.0, 0.0, 0.0),
                ("H", g * sin(th), 0.0, g * cos(th)),
                ("H", -g * sin(th), 0.0, g * cos(th))]
    if kind == "o3-sym":
        th = radians(116.8) / 2
        return [("O", 0.0, 0.0, 0.0),
                ("O", g * sin(th), 0.0, g * cos(th)),
                ("O", -g * sin(th), 0.0, g * cos(th))]
    if kind == "nh3-sym":
        alpha = radians(106.7)                 # HNH angle
        rho = 2 * g * sin(alpha / 2) / sqrt(3)  # circumradius of the H3 triangle
        h = sqrt(g * g - rho * rho)
        return [("N", 0.0, 0.0, 0.0)] + [
            ("H", rho * cos(2 * pi * k / 3), rho * sin(2 * pi * k / 3), -h)
            for k in range(3)]
    if kind == "ch4-sym":
        c = g / sqrt(3)
        return [("C", 0.0, 0.0, 0.0), ("H", c, c, c), ("H", c, -c, -c),
                ("H", -c, c, -c), ("H", -c, -c, c)]
    raise ValueError("unknown geometry kind %r" % kind)


def geometry_str(atoms):
    return "\n".join("%s %.10f %.10f %.10f" % a for a in atoms)


# ------------------------------------------------------------- selection

def _regex_label(lab):
    """pyscf matches AO labels as regular expressions; '3dz^2' must have its
    caret escaped or it matches nothing."""
    return lab.replace("^", r"\^")


def avas_projector(mf, labels, ref_basis):
    """Projection weights of the mean-field orbitals onto the listed atomic
    orbitals of a reference basis (the AVAS construction). Returns the
    matrix C^T P C over ALL orbitals of mf."""
    import scipy.linalg
    from pyscf import gto
    mol = mf.mol
    pmol = mol.copy()
    pmol.atom = mol._atom
    pmol.unit = "B"
    pmol.symmetry = False
    pmol.basis = ref_basis
    if ref_basis != "minao":
        pmol.ecp = mol.ecp
    pmol.build(False, False)
    bas = pmol.search_ao_label([_regex_label(lab) for lab in labels])
    if len(bas) == 0:
        raise ValueError("no reference AOs match %r in %s" % (labels, ref_basis))
    s2 = pmol.intor_symmetric("int1e_ovlp")[bas][:, bas]
    s21 = gto.intor_cross("int1e_ovlp", pmol, mol)[bas]
    s21 = s21 @ mf.mo_coeff
    return s21.T @ scipy.linalg.solve(s2, s21, assume_a="pos"), len(bas)


def labels_in_minao(mol, labels):
    """True if every label matches something in the minao reference basis."""
    from pyscf import gto
    pmol = mol.copy()
    pmol.atom = mol._atom
    pmol.unit = "B"
    pmol.symmetry = False
    pmol.basis = "minao"
    try:
        pmol.build(False, False)
    except Exception:
        return False
    return all(len(pmol.search_ao_label([_regex_label(lab)])) > 0 for lab in labels)


def select_space(mf, system, log):
    """Return (mo, ncore, ncas, note): orbitals ordered core | active | virtual
    for the requested active space, before CASSCF optimization."""
    a = system["active_space"]
    norb, nelec, mult = a["n_orbitals"], a["n_electrons"], a["multiplicity"]
    sel = system["recipe"]["selection"]
    mo, occ = mf.mo_coeff, mf.mo_occ
    nsingly = mult - 1
    if int(round(mf.mol.spin)) != nsingly:
        raise ValueError("mean-field spin %d != multiplicity-1 = %d"
                         % (mf.mol.spin, nsingly))
    if sel == "full":
        if mo.shape[1] != norb:
            raise ValueError("full-space recipe but basis has %d orbitals, "
                             "atlas says %d" % (mo.shape[1], norb))
        return mo, 0, norb, "full space, RHF canonical orbitals"

    docc = np.where(occ > 1.5)[0]
    socc = np.where((occ > 0.5) & (occ < 1.5))[0]
    virt = np.where(occ < 0.5)[0]
    if len(socc) != nsingly:
        raise ValueError("mean field has %d singly occupied orbitals, expected %d"
                         % (len(socc), nsingly))
    ndocc_act = (nelec - nsingly) // 2
    nvir_act = norb - ndocc_act - nsingly
    if (nelec - nsingly) % 2 or ndocc_act < 0 or nvir_act < 0 \
            or ndocc_act > len(docc) or nvir_act > len(virt):
        raise ValueError("active space (%d,%d) mult %d is inconsistent with the "
                         "mean field (%d docc, %d socc, %d virt)"
                         % (nelec, norb, mult, len(docc), len(socc), len(virt)))
    ncore = len(docc) - ndocc_act

    if sel == "energy":
        # by orbital energy: highest docc, all socc, lowest virt
        core_idx = docc[:ncore]
        act_idx = np.concatenate([docc[ncore:], socc, virt[:nvir_act]])
        rest_idx = virt[nvir_act:]
        new = np.hstack([mo[:, core_idx], mo[:, act_idx], mo[:, rest_idx]])
        return new, ncore, norb, "energy-ordered mean-field orbitals"

    if sel == "avas":
        labels = system["recipe"]["avas_labels"]
        ref = "minao" if labels_in_minao(mf.mol, labels) else mf.mol.basis
        W, nref = avas_projector(mf, labels, ref)
        if nref != norb:
            log("  note: %d reference AOs for %d active orbitals" % (nref, norb))
        # occupied block
        wd, ud = np.linalg.eigh(W[np.ix_(docc, docc)])
        od = np.argsort(-wd)
        mo_d = mo[:, docc] @ ud
        act_d, core_d = mo_d[:, od[:ndocc_act]], mo_d[:, od[ndocc_act:]]
        wv, uv = np.linalg.eigh(W[np.ix_(virt, virt)])
        ov = np.argsort(-wv)
        mo_v = mo[:, virt] @ uv
        act_v, rest_v = mo_v[:, ov[:nvir_act]], mo_v[:, ov[nvir_act:]]
        chosen = list(wd[od[:ndocc_act]]) + list(wv[ov[:nvir_act]])
        rejected = list(wd[od[ndocc_act:]]) + list(wv[ov[nvir_act:]])
        lo = min(chosen) if chosen else 1.0
        hi = max(rejected) if rejected else 0.0
        note = ("AVAS on %s (ref %s): weakest chosen %.3f, strongest rejected %.3f"
                % (" ".join(labels), ref, lo, hi))
        if lo < 0.5 or hi > 0.5:
            note += "  [WEAK SEPARATION]"
        new = np.hstack([core_d, act_d, mo[:, socc], act_v, rest_v])
        return new, ncore, norb, note
    raise ValueError("unknown selection %r" % sel)


# ---------------------------------------------------------------- energy

def reference_energy(h, eri, na, nb, econst):
    """Total energy of the determinant with alpha in orbitals 0..na-1 and
    beta in 0..nb-1, from the active-space integrals."""
    A, B = range(na), range(nb)
    e = sum(h[i, i] for i in A) + sum(h[i, i] for i in B)
    e += 0.5 * sum(eri[i, i, j, j] - eri[i, j, j, i] for i in A for j in A)
    e += 0.5 * sum(eri[i, i, j, j] - eri[i, j, j, i] for i in B for j in B)
    e += sum(eri[i, i, j, j] for i in A for j in B)
    return float(e + econst)


def orbital_energies(h, eri, na, nb):
    """Diagonal of the Fock operator of the reference determinant (alpha in
    0..na-1, beta in 0..nb-1): eps_p = h_pp + sum_j [(pp|jj) - delta_spin (pj|jp)]
    over occupied spin-orbitals j. Equals the canonical RHF orbital energies
    for a closed-shell full-space dump; a labelled diagnostic otherwise."""
    n = h.shape[0]
    eps = np.zeros(n)
    for p in range(n):
        v = h[p, p]
        for j in range(na):
            v += eri[p, p, j, j] - 0.5 * eri[p, j, j, p]
        for j in range(nb):
            v += eri[p, p, j, j] - 0.5 * eri[p, j, j, p]
        eps[p] = v
    return eps


def sector_check(h, eri, n, na, nb, econst, want_mult):
    """FCI in the sector from the dump integrals: two lowest roots, spin of
    the ground state, weight of the reference determinant."""
    from pyscf import fci
    solver = fci.direct_spin1.FCI()
    solver.conv_tol = 1e-12
    solver.max_cycle = 500
    nroots = 2 if comb(n, na) * comb(n, nb) > 1 else 1
    es, cs = solver.kernel(h, eri, n, (na, nb), nroots=nroots, ecore=econst)
    es = np.atleast_1d(es)
    cs = cs if nroots > 1 else [cs]
    ss, mult = fci.spin_op.spin_square(cs[0], n, (na, nb))
    w0 = float(cs[0][0, 0] ** 2)
    return {"e_fci": float(es[0]),
            "e_fci_root2": float(es[1]) if nroots > 1 else None,
            "gap_root2": float(es[1] - es[0]) if nroots > 1 else None,
            "ground_state_S2": float(ss),
            "ground_state_multiplicity": float(mult),
            "requested_multiplicity": want_mult,
            "reference_weight": w0}


def sidecar_for_existing(system, g, stem, path):
    """Sidecar for a dump that was not minted here: the same checks, the
    provenance taken from the file itself."""
    z = np.load(path, allow_pickle=True)
    h = np.asarray(z["h_mo"], float)
    eri = np.asarray(z["eri_mo"], float)
    na, nb = int(z["n_alpha"]), int(z["n_beta"])
    norb = h.shape[0]
    a = system["active_space"]
    if (norb, na, nb) != (a["n_orbitals"], a["n_alpha"], a["n_beta"]):
        raise RuntimeError("dump is (%d orbitals, %d, %d), atlas says (%d, %d, %d)"
                           % (norb, na, nb, a["n_orbitals"], a["n_alpha"], a["n_beta"]))
    econst = float(z["e_nuc"])
    e_scf = float(z["e_scf"])
    D = comb(norb, na) * comb(norb, nb)
    e_ref = reference_energy(h, eri, na, nb, econst)
    chk = sector_check(h, eri, norb, na, nb, econst, a["multiplicity"])
    degenerate = chk["gap_root2"] is not None and chk["gap_root2"] < 1e-6
    return {
        "stem": stem, "label": system["label"], "formula": system["formula"],
        "kind": system["kind"], "phase": system["phase"],
        "geometry": g, "geometry_units": system.get("geometry_units", "angstrom"),
        "basis": str(z["basis"]) if "basis" in z.files else system["basis"],
        "method": str(z["method"]) if "method" in z.files else "pre-existing dump",
        "selection_note": "dump found on disk; not minted by k1c_corpus.py",
        "n_orbitals": norb, "n_electrons": na + nb, "n_alpha": na, "n_beta": nb,
        "multiplicity": a["multiplicity"], "sector_dimension": D,
        "e_mean_field": e_scf, "mean_field_converged": True,
        "e_casscf": None, "casscf_converged": None, "warm_started": None,
        "e_constant": econst, "e_nuclear_repulsion": econst,
        "e_reference_determinant": e_ref,
        "reference_energy_matches_e_scf": bool(abs(e_ref - e_scf) < 1e-8),
        "natural_occupations": None,
        "sector_ground_state": chk, "degenerate_ground_state": bool(degenerate),
        "seconds": 0.0, "pyscf_version": __import__("pyscf").__version__,
    }


# ------------------------------------------------------------ one system

def run_system(system, out_dir, threads, do_check, verbose):
    """Mint every geometry of one atlas system. Returns a list of index
    entries (one per geometry) and a list of failure strings."""
    from pyscf import gto, scf, mcscf, ao2mo, lib
    lib.num_threads(threads)
    a = system["active_space"]
    norb, nelec, mult = a["n_orbitals"], a["n_electrons"], a["multiplicity"]
    na, nb = a["n_alpha"], a["n_beta"]
    label = system["label"]
    entries, failures = [], []
    lines = []

    def log(s):
        lines.append(s)
        if verbose:
            print("[%s] %s" % (label, s), flush=True)

    geoms = list(system["geometries"])
    # order: from equilibrium outward (larger first, then smaller)
    eq = system.get("equilibrium")
    if eq is None:
        eq = sorted(geoms)[len(geoms) // 2]
    up = sorted([g for g in geoms if g >= eq])
    down = sorted([g for g in geoms if g < eq], reverse=True)
    order = up + down
    prev = {"mo": None, "mol": None}      # warm start along the scan

    for i, g in enumerate(order):
        stem = stem_of(system, g)
        path = os.path.join(out_dir, stem + ".npz")
        if os.path.exists(path):
            side = os.path.join(out_dir, stem + ".json")
            if os.path.exists(side):
                log("%s exists, skipped" % stem)
                entries.append({"stem": stem, "label": label, "geometry": g,
                                "status": "exists"})
            else:
                # a dump minted elsewhere (the K1 corpus): check it the same
                # way and give it a sidecar so it enters the index
                try:
                    meta = sidecar_for_existing(system, g, stem, path)
                    with open(side, "w") as fh:
                        json.dump(meta, fh, indent=1)
                    chk = meta["sector_ground_state"]
                    log("%s pre-existing, checked: E_exact %.8f  w0 %.3f"
                        % (stem, chk["e_fci"], chk["reference_weight"]))
                    entries.append(dict(meta, status="done"))
                except Exception as ex:
                    failures.append("%s (pre-existing): %s" % (stem, ex))
                    log("FAILED %s (pre-existing): %s" % (stem, ex))
            continue
        t0 = time.time()
        try:
            atoms = build_geometry(system, g)
            heavy = any(gto.charge(s) > 36 for s, *_ in atoms)
            mol = gto.M(atom=[(s, (x, y, z)) for s, x, y, z in atoms],
                        basis=system["basis"],
                        ecp=system["basis"] if heavy else None,
                        spin=mult - 1, charge=0, unit="Angstrom",
                        symmetry=False, verbose=0)
            mf = scf.RHF(mol) if mult == 1 else scf.ROHF(mol)
            mf.conv_tol = 1e-10
            mf.max_cycle = 200
            e_mf = mf.kernel()
            if not mf.converged:
                mf = mf.newton()
                e_mf = mf.kernel()
            mf_conv = bool(mf.converged)
            if not mf_conv:
                log("  %s: mean field NOT converged (%.8f); continuing" % (stem, e_mf))

            sel = system["recipe"]["selection"]
            if sel == "full":
                mo, ncore, ncas, note = select_space(mf, system, log)
                h = mo.T @ mf.get_hcore() @ mo
                eri = ao2mo.restore(1, ao2mo.full(mol, mo), norb)
                econst = float(mol.energy_nuc())
                e_cas, cas_conv, noons = None, None, None
                method = "RHF, full orbital space"
                warm = None
            else:
                if prev["mo"] is not None:
                    mc = mcscf.CASSCF(mf, norb, (na, nb))
                    mo = mcscf.project_init_guess(mc, prev["mo"], prev["mol"])
                    ncore = mc.ncore
                    note = "warm start from previous geometry"
                    warm = True
                else:
                    mo, ncore, ncas, note = select_space(mf, system, log)
                    warm = False
                mc = mcscf.CASSCF(mf, norb, (na, nb))
                mc.ncore = ncore
                S = (mult - 1) / 2.0
                mc.fix_spin_(ss=S * (S + 1))
                mc.conv_tol = 1e-10
                mc.conv_tol_grad = 1e-6
                mc.max_cycle_macro = 150
                mc.fcisolver.conv_tol = 1e-12
                mc.fcisolver.max_cycle = 500
                mc.natorb = False
                mc.canonicalization = False
                e_cas = mc.kernel(mo)[0]
                if not mc.converged:
                    mc.max_stepsize = 0.02
                    mc.max_cycle_macro = 300
                    e_cas = mc.kernel(mc.mo_coeff)[0]
                cas_conv = bool(mc.converged)
                if not cas_conv:
                    log("  %s: CASSCF NOT converged (%.8f)" % (stem, e_cas))
                # natural orbitals of the active space, most occupied first
                dm1 = mc.fcisolver.make_rdm1(mc.ci, norb, (na, nb))
                w, U = np.linalg.eigh(dm1)
                o = np.argsort(-w)
                noons = w[o]
                mo_all = mc.mo_coeff.copy()
                mo_all[:, ncore:ncore + norb] = mc.mo_coeff[:, ncore:ncore + norb] @ U[:, o]
                h, econst = mc.get_h1eff(mo_all)
                eri = ao2mo.restore(1, mc.get_h2eff(mo_all), norb)
                econst = float(econst)
                prev["mo"], prev["mol"] = mo_all, mol
                method = "CASSCF(%d,%d) natural orbitals, %d frozen core" \
                    % (nelec, norb, ncore)
            h = np.ascontiguousarray(h, dtype=float)
            eri = np.ascontiguousarray(eri, dtype=float)

            # --- checks
            D = comb(norb, na) * comb(norb, nb)
            if D != system["sector_dimension"]:
                raise RuntimeError("sector dimension %d != atlas %d"
                                   % (D, system["sector_dimension"]))
            if np.abs(h - h.T).max() > 1e-10:
                raise RuntimeError("h_mo not symmetric")
            e_ref = reference_energy(h, eri, na, nb, econst)
            chk = sector_check(h, eri, norb, na, nb, econst, mult)
            if e_cas is not None and abs(chk["e_fci"] - e_cas) > 1e-6:
                if chk["ground_state_multiplicity"] - mult > 0.5 or \
                        chk["ground_state_multiplicity"] - mult < -0.5:
                    log("  %s: sector ground state has multiplicity %.2f, requested "
                        "%d (E_sector %.8f vs E_CASSCF %.8f)"
                        % (stem, chk["ground_state_multiplicity"], mult,
                           chk["e_fci"], e_cas))
                else:
                    raise RuntimeError("FCI from dump %.10f != CASSCF %.10f"
                                       % (chk["e_fci"], e_cas))
            if chk["e_fci"] > e_ref + 1e-9:
                raise RuntimeError("FCI energy above the reference determinant")
            degenerate = chk["gap_root2"] is not None and chk["gap_root2"] < 1e-6

            meta = {
                "stem": stem, "label": label, "formula": system["formula"],
                "kind": system["kind"], "phase": system["phase"],
                "geometry": g, "geometry_units": system.get("geometry_units", "angstrom"),
                "basis": system["basis"], "method": method, "selection_note": note,
                "n_orbitals": norb, "n_electrons": nelec, "n_alpha": na, "n_beta": nb,
                "multiplicity": mult, "sector_dimension": D,
                "e_mean_field": float(e_mf), "mean_field_converged": mf_conv,
                "e_casscf": None if e_cas is None else float(e_cas),
                "casscf_converged": cas_conv, "warm_started": warm,
                "e_constant": econst, "e_nuclear_repulsion": float(mol.energy_nuc()),
                "e_reference_determinant": e_ref,
                "natural_occupations": None if noons is None else [float(x) for x in noons],
                "sector_ground_state": chk, "degenerate_ground_state": bool(degenerate),
                "seconds": round(time.time() - t0, 1),
                "pyscf_version": __import__("pyscf").__version__,
            }
            eps = orbital_energies(h, eri, na, nb)
            np.savez(path,
                     schema=DUMP_SCHEMA,
                     h_mo=h, eri_mo=eri, e_nuc=econst, e_scf=e_ref,
                     n_alpha=na, n_beta=nb, mo_energy=eps,
                     nmo=norb, n_elec=nelec, program="pyscf",
                     created=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                     basis=system["basis"], molecule=system["formula"],
                     geometry_str=geometry_str(atoms), geometry_units="angstrom",
                     n_orbitals=norb, n_electrons=nelec, multiplicity=mult,
                     method=method, orbital_space=method,
                     e_mean_field=float(e_mf),
                     e_casscf=np.nan if e_cas is None else float(e_cas),
                     e_fci=chk["e_fci"],
                     e_nuclear_repulsion=float(mol.energy_nuc()),
                     natural_occupations=np.array([] if noons is None else noons),
                     atlas_label=label, stem=stem)
            with open(os.path.join(out_dir, stem + ".json"), "w") as fh:
                json.dump(meta, fh, indent=1)
            flag = ""
            if not (mf_conv and (cas_conv is None or cas_conv)):
                flag += " [NOT CONVERGED]"
                failures.append("%s: mean field %s, casscf %s" % (stem, mf_conv, cas_conv))
            if degenerate:
                flag += " [DEGENERATE GROUND STATE gap %.1e]" % chk["gap_root2"]
            if abs(chk["ground_state_multiplicity"] - mult) > 0.5:
                flag += " [SECTOR GROUND STATE mult %.1f]" % chk["ground_state_multiplicity"]
            log("%s  D=%d  E_ref %.8f  E_exact %.8f  Ecorr %.5f  w0 %.3f  %.0fs%s"
                % (stem, D, e_ref, chk["e_fci"], chk["e_fci"] - e_ref,
                   chk["reference_weight"], time.time() - t0, flag))
            entries.append(dict(meta, status="done"))
        except Exception as ex:
            msg = "%s: %s" % (stem, ex)
            failures.append(msg)
            log("FAILED " + msg)
            if verbose:
                traceback.print_exc()
            entries.append({"stem": stem, "label": label, "geometry": g,
                            "status": "failed", "error": str(ex)})
            prev = {"mo": None, "mol": None}
    return label, entries, failures, lines


# ------------------------------------------------------------------ main

def load_index(out_dir):
    """The index is rebuilt from the per-dump sidecars, so a run that was
    killed half-way loses nothing: every finished geometry is on disk."""
    import glob
    idx = {}
    for p in sorted(glob.glob(os.path.join(out_dir, "*.json"))):
        if os.path.basename(p) == "index.json":
            continue
        try:
            with open(p) as fh:
                e = json.load(fh)
        except Exception:
            continue
        if "stem" in e and os.path.exists(os.path.join(out_dir, e["stem"] + ".npz")):
            e.setdefault("status", "done")
            idx[e["stem"]] = e
    return idx


def save_index(out_dir, idx):
    p = os.path.join(out_dir, "index.json")
    tmp = p + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(idx, fh, indent=1)
    os.replace(tmp, p)


def report(out_dir):
    idx = load_index(out_dir)
    if not idx:
        print("no index at %s" % out_dir)
        return
    print("%-26s %-12s %8s %7s %12s %8s %6s %s"
          % ("stem", "label", "geom", "dim", "E_exact", "Ecorr", "w0", "flags"))
    for stem in sorted(idx):
        e = idx[stem]
        if e.get("status") != "done":
            print("%-26s %-12s %8s %s" % (stem, e.get("label"), e.get("geometry"),
                                         e.get("status")))
            continue
        chk = e["sector_ground_state"]
        flags = []
        if not e["mean_field_converged"]:
            flags.append("mf!")
        if e["casscf_converged"] is False:
            flags.append("cas!")
        if e["degenerate_ground_state"]:
            flags.append("degenerate")
        if abs(chk["ground_state_multiplicity"] - e["multiplicity"]) > 0.5:
            flags.append("mult%.0f" % chk["ground_state_multiplicity"])
        print("%-26s %-12s %8.3f %7d %12.6f %8.4f %6.3f %s"
              % (stem, e["label"], e["geometry"], e["sector_dimension"],
                 chk["e_fci"], chk["e_fci"] - e["e_reference_determinant"],
                 chk["reference_weight"], " ".join(flags)))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("atlas")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--phase", type=int, nargs="*", default=None)
    ap.add_argument("--only", nargs="*", default=None, help="atlas labels")
    ap.add_argument("-j", "--jobs", type=int, default=1)
    ap.add_argument("--threads", type=int, default=1, help="OpenMP threads per job")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="(checks always run; kept for compatibility)")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--max-geometries", type=int, default=None,
                    help="only the N geometries nearest equilibrium (calibration)")
    ap.add_argument("-q", "--quiet", action="store_true")
    a = ap.parse_args()

    if a.report:
        report(a.out)
        return
    with open(a.atlas) as fh:
        atlas = json.load(fh)
    systems = atlas["systems"]
    if a.phase:
        systems = [s for s in systems if s["phase"] in a.phase]
    if a.only:
        want = set(a.only)
        systems = [s for s in systems if s["label"] in want]
        missing = want - {s["label"] for s in systems}
        if missing:
            raise SystemExit("unknown labels: %s" % ", ".join(sorted(missing)))
    systems.sort(key=lambda s: (s["phase"], s["sector_dimension"]))
    if a.max_geometries:
        for s in systems:
            eq = s.get("equilibrium")
            if eq is None:
                eq = sorted(s["geometries"])[len(s["geometries"]) // 2]
            s["geometries"] = sorted(s["geometries"], key=lambda g: abs(g - eq))[:a.max_geometries]

    os.makedirs(a.out, exist_ok=True)
    idx = load_index(a.out)
    todo = []
    for s in systems:
        stems = [stem_of(s, g) for g in s["geometries"]]
        have = sum(os.path.exists(os.path.join(a.out, st + ".npz")) for st in stems)
        checked = sum(os.path.exists(os.path.join(a.out, st + ".npz")) and
                      os.path.exists(os.path.join(a.out, st + ".json")) for st in stems)
        complete = have == len(stems) and checked == len(stems)
        print("%-14s phase %d  D=%-7d %2d geometries, %2d on disk%s"
              % (s["label"], s["phase"], s["sector_dimension"], len(stems), have,
                 "  (complete)" if complete else
                 ("  (%d unchecked)" % (have - checked) if have > checked else "")))
        if a.dry_run:
            for st in stems:
                print("     ", st)
        if not complete:
            todo.append(s)
    if a.dry_run:
        print("\n%d system(s) would run" % len(todo))
        return
    if not todo:
        print("nothing to do")
        return

    t0 = time.time()
    fails = []
    verbose = not a.quiet and a.jobs == 1
    if a.jobs == 1:
        results = (run_system(s, a.out, a.threads, a.check, verbose) for s in todo)
        for label, entries, failures, lines in results:
            for e in entries:
                if e["status"] != "exists":
                    idx[e["stem"]] = e
            save_index(a.out, idx)
            fails += failures
    else:
        with ProcessPoolExecutor(max_workers=a.jobs) as ex:
            futs = {ex.submit(run_system, s, a.out, a.threads, a.check, False): s
                    for s in todo}
            for f in as_completed(futs):
                label, entries, failures, lines = f.result()
                for e in entries:
                    if e["status"] != "exists":
                        idx[e["stem"]] = e
                save_index(a.out, idx)
                fails += failures
                print("\n".join("[%s] %s" % (label, ln) for ln in lines), flush=True)
    if fails:
        with open(os.path.join(a.out, "failures.log"), "a") as fh:
            fh.write("\n".join(fails) + "\n")
    done = sum(1 for e in idx.values() if e.get("status") == "done")
    print("\n%d dump(s) on disk in %s; %d problem(s) this run; %.0f s"
          % (done, a.out, len(fails), time.time() - t0))
    if fails:
        print("problems (also in failures.log):")
        for f in fails:
            print("  " + f)


if __name__ == "__main__":
    main()

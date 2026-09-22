#!/usr/bin/env python
"""verify.py -- independent verification of a Seneca sample record.

Requires numpy and nothing else. Reads a record's .json and .npz, applies
the recorded sequence of rotations to the recorded reference determinant,
and reports three independent checks:

  1. FIDELITY      1 - |<exact | rebuilt>|^2 against the exact eigenvector
                   shipped in the record.
  2. ENERGY        <rebuilt|H|rebuilt> - E_exact, with H rebuilt from the
                   one- and two-electron integrals in the record. This is
                   independent of check 1: it uses the Hamiltonian, not the
                   eigenvector.
  3. EIGENSTATE    || (H - E) psi || , which is zero only for an exact
                   eigenstate and needs no reference answer at all.

Checks 2 and 3 run with --energy (they build the full sector Hamiltonian,
which takes a few seconds per record at dimension 4,900). A self-diagnostic
is printed alongside them: the residual of the exact eigenvector under the
same Hamiltonian, which is zero only if the assembly is right, so a large
value there indicts this script rather than the record. Energies are
TOTAL energies: nuclear repulsion (energy_nuclear) is added to H.

A rotation with holes (i,j) and particles (a,b) and angle t acts as
exp(t (A - A^dag)) with A = a^dag_a a^dag_b a_j a_i, which on each pair of
determinants it connects is a 2x2 Givens rotation of angle t.

    python verify.py records/<system>/<record_id>.json
    python verify.py records/<system>/          # every record in a directory

Author: Dr. Luogen Xu, Seneca Labs
"""
import glob
import json
import os
import sys

import numpy as np


def popcount(x):
    return bin(x).count("1")


def apply_op(mask, holes, parts):
    """Annihilate holes (ascending), then create particles (ascending).
    Returns (new_mask, sign) or None if the operation annihilates."""
    sign = 1
    for q in holes:
        if not (mask >> q) & 1:
            return None
        sign *= (-1) ** popcount(mask & ((1 << q) - 1))
        mask ^= 1 << q
    for q in parts:
        if (mask >> q) & 1:
            return None
        sign *= (-1) ** popcount(mask & ((1 << q) - 1))
        mask |= 1 << q
    return mask, sign


def build_basis(dets):
    return {int(m): i for i, m in enumerate(dets)}


def apply_rotation(psi, dets, index, holes, parts, theta):
    """One factor, as disjoint 2x2 Givens rotations on the pairs it links."""
    c, s = np.cos(theta), np.sin(theta)
    out = psi.copy()
    done = set()
    for i, m in enumerate(dets):
        if i in done:
            continue
        r = apply_op(int(m), holes, parts)
        if r is None:
            continue
        m2, sg = r
        j = index.get(m2)
        if j is None or j in done:
            continue
        a, b = psi[i], psi[j]
        out[i] = c * a - sg * s * b
        out[j] = c * b + sg * s * a
        done.add(i)
        done.add(j)
    return out


def hamiltonian(h_mo, eri_mo, dets, index, e_nuc):
    """Sector Hamiltonian from the integrals in the record. Chemist
    notation (pq|rs) = eri_mo[p,q,r,s]; spin-orbital p has spatial p//2
    and spin p % 2."""
    n = len(dets)
    nso = 2 * h_mo.shape[0]
    H = np.zeros((n, n))
    sp, sg_ = (lambda p: p // 2), (lambda p: p % 2)
    for j, mj in enumerate(dets):
        mj = int(mj)
        H[j, j] += e_nuc
        occ = [q for q in range(nso) if (mj >> q) & 1]
        for p in occ:
            H[j, j] += h_mo[sp(p), sp(p)]
        for x in range(len(occ)):
            for y in range(x + 1, len(occ)):
                p, q = occ[x], occ[y]
                H[j, j] += eri_mo[sp(p), sp(p), sp(q), sp(q)]
                if sg_(p) == sg_(q):
                    H[j, j] -= eri_mo[sp(p), sp(q), sp(q), sp(p)]
        # single excitations
        for p in range(nso):
            for q in range(nso):
                if p == q or sg_(p) != sg_(q):
                    continue
                r = apply_op(mj, [q], [p])
                if r is None:
                    continue
                m2, sgn = r
                i = index.get(m2)
                if i is None:
                    continue
                v = h_mo[sp(p), sp(q)]
                for o in occ:
                    if o == q:
                        continue
                    v += eri_mo[sp(p), sp(q), sp(o), sp(o)]
                    if sg_(p) == sg_(o):
                        v -= eri_mo[sp(p), sp(o), sp(o), sp(q)]
                H[i, j] += sgn * v
        # double excitations
        for a in range(nso):
            for b in range(a + 1, nso):
                for i_ in range(nso):
                    for j_ in range(i_ + 1, nso):
                        if a in (i_, j_) or b in (i_, j_):
                            continue      # a spectator: that is a single or the diagonal, counted above
                        r = apply_op(mj, [i_, j_], [b, a])   # a+_a a+_b a_j a_i
                        if r is None:
                            continue
                        m2, sgn = r
                        k = index.get(m2)
                        if k is None:
                            continue
                        v = 0.0
                        if sg_(a) == sg_(i_) and sg_(b) == sg_(j_):
                            v += eri_mo[sp(a), sp(i_), sp(b), sp(j_)]
                        if sg_(a) == sg_(j_) and sg_(b) == sg_(i_):
                            v -= eri_mo[sp(a), sp(j_), sp(b), sp(i_)]
                        H[k, j] += sgn * v
    return 0.5 * (H + H.T)


def verify(json_path, full=False):
    rec = json.load(open(json_path))
    z = np.load(json_path[:-5] + ".npz", allow_pickle=False)
    dets = z["determinants"]
    index = build_basis(dets)
    pivot = int(z["reference_determinant"])
    psi = np.zeros(len(dets))
    psi[index[pivot]] = 1.0
    hh, pp, ang = z["seq_holes"], z["seq_parts"], z["seq_angle"]
    for k in range(len(ang)):
        holes = [int(q) for q in hh[k] if q >= 0]
        parts = [int(q) for q in pp[k] if q >= 0]
        psi = apply_rotation(psi, dets, index, holes, parts, float(ang[k]))
    exact = z["exact_vector"]
    # 1 - |<exact|psi>|^2, computed from the difference of the unit vectors
    # (overlap = 1 - d^2/2 exactly, so the deficit is d^2 - d^4/4). The
    # direct formula 1 - ov**2 cannot resolve anything below ~2e-16.
    u = psi / np.linalg.norm(psi)
    v = exact / np.linalg.norm(exact)
    if u @ v < 0:
        v = -v
    d2 = float(np.sum((u - v) ** 2))
    deficit = max(0.0, d2 - 0.25 * d2 * d2)
    out = {"record": rec["record_id"], "length": len(ang),
           "fidelity_deficit": deficit,
           "reported_fidelity_deficit": rec["fidelity_deficit"]}
    if full:
        H = hamiltonian(z["h_mo"], z["eri_mo"], dets, index,
                        float(rec["energy_nuclear"]))
        n = psi / np.linalg.norm(psi)
        e = float(n @ (H @ n))
        out["energy"] = e
        out["energy_error"] = e - rec["energy_exact"]
        out["schrodinger_residual"] = float(np.linalg.norm(H @ n - e * n))
        # self-diagnostic: the same Hamiltonian applied to the exact vector
        x = exact / np.linalg.norm(exact)
        ex = float(x @ (H @ x))
        out["assembly_check"] = float(np.linalg.norm(H @ x - ex * x))
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    full = "--energy" in sys.argv
    target = [a for a in sys.argv[1:] if not a.startswith("--")][0]
    paths = ([target] if target.endswith(".json")
             else sorted(glob.glob(os.path.join(target, "*.json"))))
    if not paths:
        raise SystemExit("no records found at %s" % target)
    hdr = ("%-26s %6s %16s" % ("record", "len", "fidelity deficit"))
    if full:
        hdr += "%16s%16s%16s" % ("energy error", "|(H-E)psi|",
                                 "assembly check")
    print(hdr)
    worst = 0.0
    for p in paths:
        r = verify(p, full=full)
        worst = max(worst, r["fidelity_deficit"])
        line = "%-26s %6d %16.3e" % (r["record"][:26], r["length"],
                                      r["fidelity_deficit"])
        if full:
            line += "%16.3e%16.3e%16.3e" % (r["energy_error"],
                                            r["schrodinger_residual"],
                                            r["assembly_check"])
        print(line)
    print("\n%d records verified; largest fidelity deficit %.3e"
          % (len(paths), worst))
    if full:
        print("assembly check is the residual of the EXACT vector under this "
              "script's Hamiltonian;\nif it is not near zero the Hamiltonian "
              "assembly is at fault, not the record.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""build_pack.py -- assemble the Seneca sample pack.

Reads raw compiler output and emits a sanitized, self-contained record
tree. Nothing is copied verbatim: every field that ships is named
explicitly in the whitelists below, so a field is included only if it was
chosen, never by omission.

WHAT IS DELIBERATELY NOT EMITTED
Any field describing how a derivation was produced. The raw reports and
summaries carry a great deal of that, and a reader can reconstruct the
architecture from field names alone. The exclusion list is enforced twice:
by building records from scratch rather than filtering, and by a final
scan that aborts the build if a forbidden token appears anywhere in the
emitted tree.

Output
    seneca-sample-v1/
      MANIFEST.json          every record, its family, hardness scalars
      SCHEMA.md              field by field
      verify.py              numpy only, no Seneca import
      records/<system>/<id>.json   metadata, labels, amplitudes
      records/<system>/<id>.npz    integrals, exact vector, the sequence
      families/<system>.json membership plus pairwise statistics
      report/                written separately

Usage
    python build_pack.py --system k1_h6_ring_19 --sector 6 3 3 \
        --chains "k1b/k1_h6_ring_19_*_chain.npz" --dump k1_corpus/k1_h6_ring_19.npz
    python build_pack.py --config pack.json
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import os
import shutil
import sys
from collections import Counter
from itertools import combinations

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "src"))

OUT = os.path.join(HERE, "seneca-sample-v1")

# --------------------------------------------------------------------------
# Whitelists. A field ships only if it is named here.
# --------------------------------------------------------------------------
RECORD_JSON_FIELDS = [
    "record_id", "system", "family_id", "formula", "geometry",
    "basis", "n_orbitals", "n_electrons", "n_alpha", "n_beta",
    "sector_dimension", "reference_determinant",
    "energy_exact", "energy_nuclear", "energy_reference",
    "energy_correlation", "sequence_length", "rank_counts",
    "fidelity_deficit", "energy_error", "circuit_depth",
    "hardness", "labels", "cc_amplitudes", "cc_status",
]
NPZ_FIELDS = ["h_mo", "eri_mo", "e_nuc", "exact_vector", "determinants",
              "reference_determinant", "seq_holes", "seq_parts", "seq_angle",
              "rdm1", "natural_occupations"]

# Tokens that must not appear anywhere in the emitted tree. Checked at the
# end; the build aborts if one is found.
FORBIDDEN = [
    "topk", "tangent", "poolall", "post-joint", "prejoint", "pivot_rank",
    "tie_seed", "plateau", "scale_target", "rn_at_insertion", "warmstart",
    "warm_start", "k1b", "k1c", "arm", "routed", "greedy", "grow", "growth",
    "oracle", "pool", "proposal", "seed_provenance", "harness", "invocation",
    "chaincompile", "gauge", "cold_pj", "_pv", "_ts", "compiler", "rotation",
    "gate", "certif",
]
# ...with these exempt, since they are ordinary words the schema needs.
FORBIDDEN_EXEMPT = {"certif": ["certified derivation", "certificate"]}

CC_MAX_T = 35.0          # translation screen: t = tan(max|theta|)
CC_ACCEPT = 1e-10        # rebuild residual a translation must meet
SUPPORT_TOL = 1e-10


# ==========================================================================
# Physics helpers (no Seneca imports beyond the determinant algebra)
# ==========================================================================
def load_dump(path):
    d = np.load(path, allow_pickle=True)
    return {"h_mo": np.asarray(d["h_mo"], float),
            "eri_mo": np.asarray(d["eri_mo"], float),
            "e_nuc": float(d["e_nuc"]), "e_scf": float(d["e_scf"]),
            "n_alpha": int(d["n_alpha"]), "n_beta": int(d["n_beta"]),
            "basis": str(d["basis"]) if "basis" in d else "",
            "molecule": str(d["molecule"]) if "molecule" in d else "",
            "geometry": str(d["geometry_str"]) if "geometry_str" in d else ""}


def fidelity_deficit(psi, exact):
    """1 - |<exact|psi>|^2 for real vectors, computed from the DIFFERENCE of
    the normalized vectors so that it resolves below 1e-16. With u, v unit
    vectors and d = |u - v| (sign of v chosen so <u|v> >= 0), the overlap is
    1 - d^2/2 exactly, hence 1 - overlap^2 = d^2 - d^4/4. The direct
    formula 1 - ov**2 loses everything below ~2e-16 to rounding; this one
    is limited only by the rounding in the vectors themselves."""
    u = np.asarray(psi, float) / np.linalg.norm(psi)
    v = np.asarray(exact, float) / np.linalg.norm(exact)
    if u @ v < 0:
        v = -v
    d2 = float(np.sum((u - v) ** 2))
    return max(0.0, d2 - 0.25 * d2 * d2)


def load_sequence(path):
    d = np.load(path, allow_pickle=True)
    holes = [tuple(int(q) for q in h) for h in d["subs_h"]]
    parts = [tuple(int(q) for q in p) for p in d["subs_p"]]
    return holes, parts, [float(t) for t in d["th"]], int(d["pivot"])


def sector_hamiltonian(dump, basis):
    from chaincompile.molecular import build_h_sector
    return build_h_sector(dump["h_mo"], dump["eri_mo"], basis)


def exact_state(dump, basis):
    """Exact eigenvector and energy in the sector."""
    from chaincompile.molecular import build_h_sector
    H = build_h_sector(dump["h_mo"], dump["eri_mo"], basis)
    w, V = np.linalg.eigh(H)
    return np.asarray(V[:, 0], float), float(w[0])


def apply_sequence(holes, parts, angles, basis, pivot):
    from chaincompile.factors import apply_ucc_factor
    from chaincompile.dets import Substitution
    psi = basis.basis_vector(pivot)
    for h, p, t in zip(holes, parts, angles):
        psi = apply_ucc_factor(psi, basis, Substitution(h, p), t)
    return psi


def depth(holes, parts):
    last, d = {}, 0
    for h, p in zip(holes, parts):
        S = tuple(h) + tuple(p)
        layer = 1 + max((last.get(q, 0) for q in S), default=0)
        for q in S:
            last[q] = layer
        d = max(d, layer)
    return d


def rdm1_and_noons(psi, basis):
    """Spin-summed one-body density matrix and its natural occupations."""
    n_so = 2 * basis.L
    nmo = basis.L
    rdm = np.zeros((nmo, nmo))
    masks, idx = basis.masks, basis.index
    for j, m in enumerate(masks):
        cj = psi[j]
        if abs(cj) < 1e-14:
            continue
        for p in range(n_so):
            if not (m >> p) & 1:
                continue
            for q in range(n_so):
                if p % 2 != q % 2:
                    continue
                if q != p and (m >> q) & 1:
                    continue
                m1 = m ^ (1 << p)
                sg = (-1) ** bin(m & ((1 << p) - 1)).count("1")
                if q == p:
                    # a_p^dag a_p: the two signs are the same and cancel,
                    # leaving the occupation weight |c|^2
                    m2, sg2 = m, sg
                else:
                    sg2 = (-1) ** bin(m1 & ((1 << q) - 1)).count("1")
                    m2 = m1 | (1 << q)
                i = idx.get(m2)
                if i is not None:
                    rdm[q // 2, p // 2] += psi[i] * cj * sg * sg2
    rdm = 0.5 * (rdm + rdm.T)
    noons = np.sort(np.linalg.eigvalsh(rdm))[::-1]
    return rdm, noons


def hardness(psi, basis, pivot, noons, e_total, e_scf, angles):
    """State- and derivation-level diagnostics.

    e_total and e_scf must both be TOTAL energies (nuclear repulsion
    included); the eigenvalue of the electronic Hamiltonian is not on the
    same footing as a self-consistent-field total energy, and differencing
    them without the constant returns the nuclear repulsion rather than the
    correlation energy.

    reference_weight is a property of THIS derivation's reference, not of
    the state: a derivation built from a different reference reports a
    different value. The other diagnostics here are state properties.
    """
    ip = basis.index[pivot]
    w_ref = float(psi[ip] ** 2 / (psi @ psi))
    dev = float(max(min(n, 2.0 - n) / 2.0 for n in noons)) if len(noons) else 0.0
    supp = int(np.sum(np.abs(psi) > SUPPORT_TOL))
    mx = float(max(abs(t) for t in angles)) if angles else 0.0
    return {
        "reference_weight": w_ref,
        "max_natural_occupation_deviation": dev,
        "correlation_energy": float(e_total - e_scf),
        "support_fraction": supp / basis.dim,
        "support_size": supp,
        "max_angle": mx,
        "max_cc_amplitude_bound": float(math.tan(mx)) if mx < math.pi / 2 else None,
    }


# ==========================================================================
# Family statistics
# ==========================================================================
def content_f1(a, b):
    ca, cb = Counter(a), Counter(b)
    inter = sum((ca & cb).values())
    if not inter:
        return 0.0, 0.0, 0.0
    p, r = inter / sum(ca.values()), inter / sum(cb.values())
    return p, r, 2 * p * r / (p + r)


def canonicalize(seq):
    """Normal form under reordering of index-disjoint (commuting) factors."""
    out, masks = [], []
    for L in seq:
        mx = 0
        for q in L[0] + L[1]:
            mx |= 1 << q
        i = len(out) - 1
        while i >= 0 and (masks[i] & mx) == 0:
            i -= 1
        p = i + 1
        while p < len(out) and out[p] < L:
            p += 1
        out.insert(p, L)
        masks.insert(p, mx)
    return out


def first_positions(seq):
    pos = {}
    for i, L in enumerate(seq):
        if L not in pos:
            pos[L] = i / max(1, len(seq) - 1)
    return pos


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return None
    return float(np.corrcoef(np.argsort(np.argsort(x)),
                             np.argsort(np.argsort(y)))[0, 1])


def family_stats(members):
    """members: {record_id: {"seq": [...], "reference": int}}"""
    ids = sorted(members)
    groups = {}
    for i in ids:
        groups.setdefault(members[i]["reference"], []).append(i)
    pairs, f1s = [], []
    for a, b in combinations(ids, 2):
        sa, sb = members[a]["seq"], members[b]["seq"]
        p, r, f = content_f1(sa, sb)
        pa, pb = first_positions(sa), first_positions(sb)
        shared = sorted(set(sa) & set(sb))
        o_raw = spearman([pa[k] for k in shared], [pb[k] for k in shared]) \
            if len(shared) >= 3 else None
        ca, cb = canonicalize(sa), canonicalize(sb)
        pca, pcb = first_positions(ca), first_positions(cb)
        o_can = spearman([pca[k] for k in shared], [pcb[k] for k in shared]) \
            if len(shared) >= 3 else None
        pairs.append({"a": a, "b": b, "precision": p, "recall": r,
                      "content_f1": f, "order_agreement": o_raw,
                      "order_agreement_canonical": o_can,
                      "same_reference": members[a]["reference"]
                      == members[b]["reference"]})
        f1s.append(f)
    # Invariant core of the LARGEST reference group: the rotations present
    # in every member of it. Reported for one group because a rotation
    # cannot be common across derivations built from different references.
    core = None
    if groups:
        ms = max(groups.values(), key=len)
        c = Counter(members[ms[0]]["seq"])
        for m in ms[1:]:
            c &= Counter(members[m]["seq"])
        core = {"reference_group_size": len(ms),
                "shared_by_all_letters": sum(c.values()),
                "shared_by_all_distinct": len(c)}
    f1s = np.array(f1s) if f1s else np.array([0.0])
    return {"n_members": len(ids), "n_pairs": len(pairs),
            "n_reference_groups": len(groups),
            "content_f1_mean": float(f1s.mean()),
            "content_f1_min": float(f1s.min()),
            "content_f1_max": float(f1s.max()),
            "invariant_core": core, "pairs": pairs}


# ==========================================================================
# Emission
# ==========================================================================
def record_id(system, holes, parts, angles, pivot):
    h = hashlib.blake2b(repr((system, holes, parts,
                              [round(a, 15) for a in angles], pivot)).encode(),
                        digest_size=6).hexdigest()
    return "%s-%s" % (system.replace("_", "-"), h)


def build_system(name, label, dump_path, chain_glob, L, na, nb, args):
    from chaincompile.sector import SectorBasis
    from k1c_fcc import translate_chain
    dump = load_dump(dump_path)
    basis = SectorBasis(L, na, nb)
    psi_exact, e_elec = exact_state(dump, basis)
    Hmat = sector_hamiltonian(dump, basis)
    # Put the exact energy on the same (total) footing as the dump's
    # self-consistent-field energy, so the two are directly comparable and
    # so energy_correlation is the correlation energy rather than the
    # nuclear repulsion.
    e_exact = float(e_elec + dump["e_nuc"])
    rdm, noons = rdm1_and_noons(psi_exact, basis)
    paths = sorted(glob.glob(chain_glob))
    if not paths:
        raise SystemExit("no sequences matched %s" % chain_glob)
    print("%s: %d candidate sequences, sector dim %d" % (label, len(paths),
                                                         basis.dim))
    rec_dir = os.path.join(OUT, "records", label)
    os.makedirs(rec_dir, exist_ok=True)
    members, entries, seen = {}, [], set()
    for p in paths:
        holes, parts, angles, pivot = load_sequence(p)
        seq = list(zip(holes, parts))
        key = hashlib.blake2b(repr((seq, [round(a, 15) for a in angles],
                                    pivot)).encode(), digest_size=8).digest()
        if key in seen:
            continue
        seen.add(key)
        psi = apply_sequence(holes, parts, angles, basis, pivot)
        R = fidelity_deficit(psi, psi_exact)
        if R > args.max_deficit:
            print("  skipped (deficit %.1e)" % R)
            continue
        rid = record_id(label, holes, parts, angles, pivot)
        hard = hardness(psi_exact, basis, pivot, noons, e_exact,
                        dump["e_scf"], angles)
        # --- CC translation behind the screen -----------------------------
        cc, cc_status = None, {}
        t_bound = hard["max_cc_amplitude_bound"]
        if t_bound is None:
            cc_status = {"included": False,
                         "reason": "largest rotation angle at the domain bound"}
        elif t_bound > args.max_t:
            cc_status = {"included": False, "amplitude_bound": t_bound,
                         "reason": "amplitude bound above the screen threshold"}
        else:
            try:
                tr = translate_chain(seq, angles, basis, pivot, decompose=False)
                alg, T = tr["alg"], tr["T"]
                res = float(tr["residual_rebuild"])
                if res > args.accept:
                    cc_status = {"included": False, "acceptance": res,
                                 "reason": "acceptance residual above threshold"}
                else:
                    cc = [{"holes": list(alg.sub_of(m)[0].holes),
                           "particles": list(alg.sub_of(m)[0].parts),
                           "rank": alg.rank_of(m),
                           "amplitude": c / alg.sub_of(m)[1]}
                          for m, c in sorted(T.items(),
                                             key=lambda kv: -abs(kv[1]))]
                    cc_status = {"included": True, "acceptance": res,
                                 "n_amplitudes": len(cc),
                                 "max_rank": int(tr["maxrank"]),
                                 "largest_amplitude": float(tr["max_amplitude"])}
            except Exception as e:
                cc_status = {"included": False, "reason": str(e)[:120]}
        ranks = Counter(len(h) for h in holes)
        rec = {
            "record_id": rid, "system": label, "family_id": label,
            "formula": dump["molecule"] or name,
            "geometry": dump["geometry"], "basis": dump["basis"],
            "n_orbitals": int(L), "n_electrons": int(na + nb),
            "n_alpha": int(na), "n_beta": int(nb),
            "sector_dimension": int(basis.dim),
            "reference_determinant": int(pivot),
            "energy_exact": e_exact, "energy_nuclear": dump["e_nuc"],
            "energy_reference": dump["e_scf"],
            "energy_correlation": float(e_exact - dump["e_scf"]),
            "sequence_length": len(seq),
            "rank_counts": {str(k): int(v) for k, v in sorted(ranks.items())},
            "fidelity_deficit": R,
            "energy_error": float((psi @ (Hmat @ psi)) / (psi @ psi)
                                  + dump["e_nuc"] - e_exact),
            "circuit_depth": depth(holes, parts),
            "hardness": hard,
            "labels": {"natural_occupations": [float(x) for x in noons]},
            "cc_amplitudes": cc, "cc_status": cc_status,
        }
        rec = {k: rec[k] for k in RECORD_JSON_FIELDS}
        with open(os.path.join(rec_dir, rid + ".json"), "w") as fh:
            json.dump(rec, fh, indent=1)
        np.savez_compressed(
            os.path.join(rec_dir, rid + ".npz"),
            h_mo=dump["h_mo"], eri_mo=dump["eri_mo"],
            e_nuc=np.array(dump["e_nuc"]), exact_vector=psi_exact,
            determinants=np.array(basis.masks, dtype=np.int64),
            reference_determinant=np.array(pivot, dtype=np.int64),
            seq_holes=np.array([list(h) + [-1] * (2 - len(h))
                                for h in holes], dtype=np.int16),
            seq_parts=np.array([list(p) + [-1] * (2 - len(p))
                                for p in parts], dtype=np.int16),
            seq_angle=np.array(angles, dtype=np.float64),
            rdm1=rdm, natural_occupations=noons)
        members[rid] = {"seq": seq, "reference": int(pivot)}
        entries.append({"record_id": rid, "system": label, "family_id": label,
                        "sequence_length": len(seq),
                        "fidelity_deficit": R,
                        "reference_determinant": int(pivot),
                        "cc_included": bool(cc), "hardness": hard})
        print("  %s len %4d deficit %.1e  t<=%s  cc %s"
              % (rid, len(seq), R,
                 "%.1f" % t_bound if t_bound else "inf",
                 "yes" if cc else "no (%s)" % cc_status.get("reason", "")[:34]))
    os.makedirs(os.path.join(OUT, "families"), exist_ok=True)
    fam = family_stats(members)
    fam["system"] = label
    with open(os.path.join(OUT, "families", label + ".json"), "w") as fh:
        json.dump(fam, fh, indent=1)
    print("  family: %d members, %d pairs, content F1 mean %.3f "
          "(min %.3f max %.3f), %d reference groups"
          % (fam["n_members"], fam["n_pairs"], fam["content_f1_mean"],
             fam["content_f1_min"], fam["content_f1_max"],
             fam["n_reference_groups"]))
    return entries, fam


# ==========================================================================
# Leak scan
# ==========================================================================
def leak_scan(root):
    bad = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if not f.endswith((".json", ".md", ".py", ".txt")):
                continue
            p = os.path.join(dirpath, f)
            txt = open(p, encoding="utf-8", errors="replace").read().lower()
            for tok in FORBIDDEN:
                if tok in txt:
                    ok = False
                    for ex in FORBIDDEN_EXEMPT.get(tok, []):
                        if txt.count(tok) <= txt.count(ex):
                            ok = True
                    if not ok:
                        bad.append((os.path.relpath(p, root), tok))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", action="append", default=[],
                    metavar="NAME:LABEL:DUMP:GLOB:L:NA:NB",
                    help="colon-separated system spec; repeatable")
    ap.add_argument("--config", default=None, help="JSON list of specs")
    ap.add_argument("--max-deficit", type=float, default=1e-11)
    ap.add_argument("--max-t", type=float, default=CC_MAX_T)
    ap.add_argument("--accept", type=float, default=CC_ACCEPT)
    ap.add_argument("--clean", action="store_true")
    a = ap.parse_args()
    specs = []
    if a.config:
        specs = json.load(open(a.config))
    for s in a.system:
        p = s.split(":")
        specs.append({"name": p[0], "label": p[1], "dump": p[2], "glob": p[3],
                      "L": int(p[4]), "na": int(p[5]), "nb": int(p[6])})
    if not specs:
        raise SystemExit("give --system or --config")
    if a.clean and os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)
    all_entries, fams = [], {}
    for s in specs:
        e, f = build_system(s["name"], s["label"], s["dump"], s["glob"],
                            s["L"], s["na"], s["nb"], a)
        all_entries += e
        fams[s["label"]] = {k: f[k] for k in
                            ("n_members", "n_pairs", "content_f1_mean",
                             "content_f1_min", "content_f1_max",
                             "n_reference_groups")}
    manifest = {"pack": "seneca-sample-v1",
                "author": "Dr. Luogen Xu, Seneca Labs",
                "n_records": len(all_entries),
                "systems": sorted(fams),
                "families": fams, "records": all_entries,
                "screens": {"fidelity_deficit_max": a.max_deficit,
                            "cc_amplitude_bound_max": a.max_t,
                            "cc_acceptance_max": a.accept}}
    with open(os.path.join(OUT, "MANIFEST.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)
    print("\n%d records across %d systems -> %s"
          % (len(all_entries), len(fams), OUT))
    bad = leak_scan(OUT)
    if bad:
        print("\nLEAK SCAN FAILED -- these files contain excluded tokens:")
        for p, t in bad[:20]:
            print("   %-50s '%s'" % (p, t))
        raise SystemExit(1)
    print("leak scan clean (%d excluded tokens checked)" % len(FORBIDDEN))


if __name__ == "__main__":
    main()

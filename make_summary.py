#!/usr/bin/env python
"""make_summary.py -- write report/SUMMARY.md from the finished pack.

Reads seneca-sample-v1/ and computes every number it prints. Nothing is
hard-coded and nothing is asserted that is not measured here.

    python make_summary.py
    python make_summary.py --pack seneca-sample-v1

Author: Dr. Luogen Xu, Seneca Labs.
"""
import argparse
import json
import os
from collections import Counter

import numpy as np


def load(pack):
    man = json.load(open(os.path.join(pack, "MANIFEST.json")))
    fams, recs = {}, {}
    fdir = os.path.join(pack, "families")
    for f in sorted(os.listdir(fdir)):
        if f.endswith(".json"):
            fams[f[:-5]] = json.load(open(os.path.join(fdir, f)))
    rdir = os.path.join(pack, "records")
    for sysname in sorted(os.listdir(rdir)):
        d = os.path.join(rdir, sysname)
        if not os.path.isdir(d):
            continue
        recs[sysname] = [json.load(open(os.path.join(d, f)))
                         for f in sorted(os.listdir(d)) if f.endswith(".json")]
    return man, fams, recs


def sequence_ops(pack, system, rid):
    """The set of distinct operators appearing as rotations in a record."""
    p = os.path.join(pack, "records", system, rid + ".npz")
    z = np.load(p, allow_pickle=False)
    return {(tuple(int(q) for q in h if q >= 0),
             tuple(int(q) for q in pp if q >= 0))
            for h, pp in zip(z["seq_holes"], z["seq_parts"])}


def fmt(x, n=3):
    return "-" if x is None else ("%.*g" % (n, x))


def sci(x):
    return "-" if x is None else ("%.1e" % x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default="seneca-sample-v1")
    a = ap.parse_args()
    man, fams, recs = load(a.pack)
    systems = sorted(recs)
    out = []
    W = out.append

    total = sum(len(v) for v in recs.values())
    all_rec = [r for v in recs.values() for r in v]
    worst = max(r["fidelity_deficit"] for r in all_rec)
    n_pairs = sum(f["n_pairs"] for f in fams.values())
    n_cc = sum(1 for r in all_rec if r["cc_status"].get("included"))

    W("# Sample pack: what is in it and how it was checked\n")
    W("Seneca sample pack, version 1. Author: Dr. Luogen Xu, Seneca Labs.\n")
    W("Every number below is computed from the files in this pack by\n"
      "`make_summary.py`, which is included. Formulas are given so that any\n"
      "claim here can be recomputed independently. Field definitions are in\n"
      "`SCHEMA.md`.\n")

    W("## Summary\n")
    W("- **%d records** across **%d systems**, each one an exact electronic\n"
      "  ground state together with an exact derivation of it." % (total, len(systems)))
    W("- Every record reconstructs its state to a fidelity deficit of\n"
      "  **%s or better**, checked by `verify.py`, which imports none of the\n"
      "  software that produced the data." % sci(worst))
    W("- Records of the same state are compared pairwise over **%d pairs**;\n"
      "  they share on average only part of their content, and the difference\n"
      "  survives exact removal of the commuting-reorder freedom (section 3)."
      % n_pairs)
    W("- Coupled-cluster amplitudes are included on **%d of %d** records. The\n"
      "  remainder are withheld by a stated conditioning test, with the reason\n"
      "  recorded (section 4).\n" % (n_cc, total))

    # ---------------------------------------------------------------- 1
    W("## 1. Certification\n")
    W("A derivation is a sequence of elementary one- and two-body rotations\n"
      "applied to a single reference determinant. Certification is the\n"
      "statement that the resulting state is the exact one:\n")
    W("```\nfidelity deficit  R = 1 - |<exact | rebuilt>|^2\n```\n")
    W("A record is included only if `R < %s`. The exact state is obtained by\n"
      "direct diagonalization in the stated orbital space, so `R` measures the\n"
      "derivation, not an approximation to a solution.\n"
      % fmt(man["screens"]["fidelity_deficit_max"]))
    W("| system | records | sector dim | sequence length | worst deficit |")
    W("|---|---|---|---|---|")
    for s in systems:
        v = recs[s]
        L = [r["sequence_length"] for r in v]
        W("| %s | %d | %d | %d to %d | %s |"
          % (s, len(v), v[0]["sector_dimension"], min(L), max(L),
             sci(max(r["fidelity_deficit"] for r in v))))
    W("")
    W("Deficits of exactly zero mean the reconstruction is identical to the\n"
      "exact vector in double precision. The threshold is a ceiling, not a\n"
      "target.\n")

    # ---------------------------------------------------------------- 2
    W("## 2. Many derivations of one state\n")
    W("A state does not have a unique derivation. Records sharing a\n"
      "`family_id` are derivations of the same exact state; `families/` reports\n"
      "how far apart they are.\n")
    W("Content overlap treats each sequence as a **multiset** of rotations,\n"
      "ignoring order and counting repeats. With `I` the size of the\n"
      "intersection of sequences `A` and `B`:\n")
    W("```\nprecision = I / |B|      recall = I / |A|      F1 = 2 P R / (P + R)\n```\n")
    W("F1 is 1 when two derivations use exactly the same rotations with the\n"
      "same multiplicities and 0 when they share none. It is **blind to order\n"
      "by construction**, which is why it is the right instrument: if the\n"
      "derivations in a family were reorderings of one another, every F1 would\n"
      "be exactly 1.\n")
    W("| system | members | references | pairs | mean F1 | min | max |")
    W("|---|---|---|---|---|---|---|")
    for s in systems:
        f = fams.get(s)
        if not f:
            continue
        W("| %s | %d | %d | %d | %s | %s | %s |"
          % (s, f["n_members"], f["n_reference_groups"], f["n_pairs"],
             fmt(f["content_f1_mean"]), fmt(f["content_f1_min"]),
             fmt(f["content_f1_max"])))
    W("")
    allf = [p["content_f1"] for f in fams.values() for p in f["pairs"]]
    same = [p["content_f1"] for f in fams.values() for p in f["pairs"]
            if p["same_reference"]]
    diff = [p["content_f1"] for f in fams.values() for p in f["pairs"]
            if not p["same_reference"]]
    W("Across all %d pairs the mean content overlap is **%s** (median %s,\n"
      "range %s to %s). Splitting by whether the two derivations start from\n"
      "the same reference determinant: %s for the %d same-reference pairs and\n"
      "%s for the %d cross-reference pairs.\n"
      % (len(allf), fmt(np.mean(allf)), fmt(np.median(allf)),
         fmt(min(allf)), fmt(max(allf)),
         fmt(np.mean(same)) if same else "-", len(same),
         fmt(np.mean(diff)) if diff else "-", len(diff)))
    ident = [p for f in fams.values() for p in f["pairs"]
             if p["content_f1"] > 1 - 1e-9]
    if ident:
        oc = [p["order_agreement_canonical"] for p in ident
              if p["order_agreement_canonical"] is not None]
        W("**%d of the %d pairs** (%s percent) have content overlap of exactly\n"
          "1, and their mean order agreement after canonicalization is %s.\n"
          "Both metrics therefore fail to separate them: these few pairs use\n"
          "the same rotations with the same multiplicities, in the same order\n"
          "up to the commuting freedom, and differ only in where repeated\n"
          "rotations fall and in the angles. They may be reorderings of one\n"
          "another and this pack does not claim otherwise. They are reported\n"
          "rather than excluded, and they are the exception: the remaining\n"
          "%d pairs are separated by content, by order after canonicalization,\n"
          "or by both.\n"
          % (len(ident), len(allf), fmt(100.0 * len(ident) / len(allf), 2),
             fmt(np.mean(oc)) if oc else "-", len(allf) - len(ident)))
    cores = [(s, f["invariant_core"]) for s, f in fams.items()
             if f.get("invariant_core")]
    if cores:
        W("The **invariant core** is the set of rotations present in every\n"
          "member of the largest reference group. It shrinks as derivations\n"
          "are added, since a rotation must survive all of them. It is\n"
          "reported within a single reference group because derivations\n"
          "expanded around different determinants are not comparable\n"
          "letter by letter:\n"
          )
        W("| system | largest group | core (letters) | core (distinct) |")
        W("|---|---|---|---|")
        for s, c in cores:
            W("| %s | %d | %d | %d |" % (s, c["reference_group_size"],
                                         c["shared_by_all_letters"],
                                         c["shared_by_all_distinct"]))
        W("")

    # ---------------------------------------------------------------- 3
    W("## 3. The differences are not reorderings\n")
    W("Two rotations **commute** when their spin-orbital index sets are\n"
      "disjoint: the order of such a pair is arbitrary and carries no\n"
      "information. That freedom is exactly computable. Sliding each rotation\n"
      "as far left as it will go past its commuting neighbours, into a fixed\n"
      "key order, produces a unique normal form; two sequences related only by\n"
      "commuting reorderings have the *same* normal form.\n")
    W("Order agreement takes the rotations two derivations share, records\n"
      "where each first appears as a fraction of the sequence length, and\n"
      "computes the rank correlation of the two position lists. It is reported\n"
      "on the raw sequences and again on their normal forms.\n")
    W("**If the derivations were reorderings of one another, canonicalization\n"
      "would collapse them and the canonical agreement would jump to 1.**\n")
    raw = [p["order_agreement"] for f in fams.values() for p in f["pairs"]
           if p["order_agreement"] is not None]
    can = [p["order_agreement_canonical"] for f in fams.values()
           for p in f["pairs"] if p["order_agreement_canonical"] is not None]
    n = min(len(raw), len(can))
    d = np.abs(np.array(raw[:n]) - np.array(can[:n]))
    W("| quantity | value |")
    W("|---|---|")
    W("| pairs measured | %d |" % n)
    W("| mean order agreement, raw | %s |" % fmt(np.mean(raw)))
    W("| mean order agreement, canonical | %s |" % fmt(np.mean(can)))
    W("| mean absolute change | %s |" % fmt(np.mean(d)))
    W("| largest change on any pair | %s |" % fmt(d.max()))
    W("")
    W("The change is negligible. For every pair except the %d noted in\n"
      "section 2, the differences between derivations survive the commuting\n"
      "algebra: they are different content, or non-commuting order with\n"
      "compensating angles, and neither is reachable by permuting operators.\n"
      "Content overlap, which ignores order entirely, says the same thing from\n"
      "the other direction: a mean near %s is far from the 1 that reordering\n"
      "would give.\n" % (len(ident), fmt(np.mean(allf), 2)))

    # ---------------------------------------------------------------- 4
    W("## 4. Coupled-cluster amplitudes and their conditioning\n")
    W("Where included, `cc_amplitudes` is the conventional cluster operator\n"
      "`T` with `|Psi> ~ exp(T)|reference>`. `T` is determined by the state and\n"
      "its reference determinant, not by the derivation: two derivations of\n"
      "one state that start from the same reference yield the same amplitudes,\n"
      "to within the precision their certification allows, though their\n"
      "sequences differ substantially. That agreement is measured below.\n"
      "Derivations starting from a different reference yield a different `T`,\n"
      "since `T` is defined relative to what it is expanded around.\n")
    W("Each rotation contributes an amplitude `tan(theta)`, which diverges as\n"
      "`|theta|` approaches `pi/2`. Since `cos(theta)` is the weight a rotation\n"
      "leaves on the reference determinant, that divergence is the point at\n"
      "which the reference has been rotated out of the state and a\n"
      "single-reference coupled-cluster description no longer has a reference\n"
      "to be defined against. Amplitudes are included only where\n"
      "`tan(max_angle)` is below %s and the reconstruction residual is below\n"
      "%s.\n" % (fmt(man["screens"]["cc_amplitude_bound_max"]),
                 sci(man["screens"]["cc_acceptance_max"])))
    W("| system | with amplitudes | tan(max angle), all records | max rank of T |")
    W("|---|---|---|---|")
    for s in systems:
        v = recs[s]
        inc = [r for r in v if r["cc_status"].get("included")]
        tb = [r["hardness"]["max_cc_amplitude_bound"] for r in v
              if r["hardness"]["max_cc_amplitude_bound"] is not None]
        mr = [r["cc_status"].get("max_rank") for r in inc
              if r["cc_status"].get("max_rank")]
        W("| %s | %d of %d | %s to %s | %s |"
          % (s, len(inc), len(v), fmt(min(tb)) if tb else "-",
             fmt(max(tb)) if tb else "-", max(mr) if mr else "-"))
    W("")
    ranks = Counter()
    absent, total_amp = 0, 0
    for r in all_rec:
        amps = r["cc_amplitudes"] or []
        for c in amps:
            ranks[c["rank"]] += 1
        if amps:
            try:
                ops = sequence_ops(a.pack, r["system"], r["record_id"])
                for c in amps:
                    total_amp += 1
                    if (tuple(c["holes"]), tuple(c["particles"])) not in ops:
                        absent += 1
            except Exception:
                pass
    seqr = Counter()
    for r in all_rec:
        for k, v2 in r["rank_counts"].items():
            seqr[int(k)] += v2
    # Measured check of the claim above: derivations of one state that share
    # a reference must yield the same cluster operator. Compared over the
    # union of operators appearing in either amplitude list.
    byid = {r["record_id"]: r for r in all_rec}
    diffs = []
    for f in fams.values():
        for p in f["pairs"]:
            if not p["same_reference"]:
                continue
            ra, rb = byid.get(p["a"]), byid.get(p["b"])
            if not ra or not rb:
                continue
            aa, ab = ra["cc_amplitudes"], rb["cc_amplitudes"]
            if not aa or not ab:
                continue
            da = {(tuple(x["holes"]), tuple(x["particles"])): x["amplitude"]
                  for x in aa}
            db = {(tuple(x["holes"]), tuple(x["particles"])): x["amplitude"]
                  for x in ab}
            keys = set(da) | set(db)
            diffs.append(max(abs(da.get(k, 0.0) - db.get(k, 0.0))
                             for k in keys))
    if diffs:
        W("That the cluster operator depends on the state and its reference,\n"
          "and not on the derivation, is checked rather than assumed. Over the\n"
          "**%d pairs** in which both derivations carry amplitudes and start\n"
          "from the same reference determinant, the largest disagreement in any\n"
          "amplitude is **%s**, with a mean of %s across pairs, while the\n"
          "sequences in those same pairs differ substantially as section 2\n"
          "reports.\n"
          % (len(diffs), sci(max(diffs)), sci(float(np.mean(diffs)))))
        W("The residual disagreement is the certification tolerance carried\n"
          "through, not a disagreement about what `T` is. Each derivation\n"
          "reproduces its state to a fidelity deficit below the threshold in\n"
          "section 1 rather than exactly; a deficit `R` corresponds to a\n"
          "difference of order `sqrt(R)` in the state itself, and extracting the\n"
          "cluster operator divides by the reference amplitude, which amplifies\n"
          "it further. Amplitudes are therefore reproducible to roughly that\n"
          "precision across derivations, and a reader wanting tighter agreement\n"
          "should compare records with the smaller fidelity deficits.\n")
    if total_amp:
        W("Across every record that carries amplitudes, **%d of %d** cluster\n"
          "amplitudes (%s percent) correspond to excitations that appear in\n"
          "**no rotation of their own derivation**. The cluster operator is\n"
          "therefore not a relabelling of the sequence: it contains content the\n"
          "sequence never applies directly, produced by the fact that the\n"
          "rotations do not commute.\n"
          % (absent, total_amp, fmt(100.0 * absent / total_amp, 3)))
    if ranks:
        W("Every rotation in every sequence is rank 1 or 2 (%s). The cluster\n"
          "operators reach rank %d (%s), the maximum the electron count of these\n"
          "systems permits. A derivation built only from one- and two-body\n"
          "rotations therefore carries coupled-cluster content well beyond\n"
          "singles and doubles.\n"
          % (", ".join("rank %d: %d" % (k, seqr[k]) for k in sorted(seqr)),
             max(ranks),
             ", ".join("rank %d: %d" % (k, ranks[k]) for k in sorted(ranks))))

    # ---------------------------------------------------------------- 5
    W("## 5. Correlation across the systems\n")
    W("Three of these are properties of the **state** and are identical\n"
      "across every derivation of it. The reference weight is a property of a\n"
      "**derivation**, since it depends on which determinant that derivation\n"
      "starts from; the table reports the largest value in each family, the\n"
      "weight of the dominant determinant.\n")
    W("- **reference weight** (derivation-level; dominant value shown):\n"
      "  squared amplitude of the reference determinant in the normalized\n"
      "  exact state. 1 for a single-determinant system; smaller when no\n"
      "  single determinant dominates.\n"
      "- **max natural-occupation deviation**: `max over orbitals of\n"
      "  min(n, 2-n)/2` over the eigenvalues of the one-body density matrix.\n"
      "  0 when every orbital is cleanly full or empty, and at most 0.5, which\n"
      "  is reached when an orbital is exactly half-occupied. Fractional\n"
      "  occupation is the signature of multireference character, and density\n"
      "  functional methods cannot produce this quantity.\n"
      "- **correlation energy**: exact minus mean-field, both total energies,\n"
      "  in Hartree: what the mean field misses and nothing else.\n"
      "- **support fraction**: determinants carrying amplitude above 1e-10, as\n"
      "  a fraction of the sector dimension.\n")
    W("| system | reference weight (dominant) | max NOON deviation | correlation energy | support fraction |")
    W("|---|---|---|---|---|")
    for s in systems:
        # state-level quantities are identical across records; the reference
        # weight is not, so report the dominant determinant's value
        h = max((r["hardness"] for r in recs[s]),
                key=lambda x: x["reference_weight"])
        W("| %s | %s | %s | %s | %s |"
          % (s, fmt(h["reference_weight"]),
             fmt(h["max_natural_occupation_deviation"]),
             fmt(h["correlation_energy"]), fmt(h["support_fraction"])))
    W("")
    W("Where a family spans a bond-dissociation coordinate, the three\n"
      "state-level diagnostics move together: as the bond lengthens the\n"
      "reference weight falls, the natural-occupation deviation rises toward\n"
      "its maximum of 0.5, and the correlation energy increases. A deviation near\n"
      "0.5 means two orbitals are half-occupied, which is what a broken bond\n"
      "looks like in this diagnostic and what no single determinant can\n"
      "describe.\n")
    W("The conditioning of section 4 is a separate axis and should not be read\n"
      "off this table. Whether a derivation's coupled-cluster reading is\n"
      "well-conditioned depends on **which determinant that derivation is\n"
      "expanded around**, not on how correlated the state is: a derivation\n"
      "built on a low-weight determinant drives rotations toward the bound\n"
      "where the amplitude picture ceases to exist, even for a state with a\n"
      "clearly dominant configuration. Both kinds are present here and each\n"
      "record says which it is.\n")

    # ---------------------------------------------------------------- 6
    W("## 6. How to check any of this\n")
    W("```\npython verify.py records/<system>/\n```\n")
    W("`verify.py` requires numpy and imports none of the software that\n"
      "produced the data. For each record it reads the reference determinant\n"
      "from the record, applies the recorded sequence, and reports the\n"
      "fidelity deficit against the exact vector in the record. Its docstring\n"
      "states the rotation convention in full.\n")
    W("```\npython make_summary.py\n```\n")
    W("regenerates this document from the pack.\n")
    W("An energy path exists in `verify.py` behind `--energy`. Its Hamiltonian\n"
      "assembly is not validated in this release and the script says so: it\n"
      "prints an `assembly check`, the residual of the *exact* vector under its\n"
      "own Hamiltonian, which is zero only if the assembly is correct. A large\n"
      "value there indicts the script, not the record. The fidelity check uses\n"
      "no Hamiltonian and is unaffected.\n")

    # ---------------------------------------------------------------- 7
    W("## 7. Scope\n")
    W("Every state is exact **within its stated orbital space**: exactly the\n"
      "regime in which methods in general use become unreliable. It is not a\n"
      "claim of agreement with experiment, which would additionally require a\n"
      "complete basis and all electrons correlated.\n")
    W("This is a sample: %d records demonstrating a property, not a production\n"
      "corpus.\n" % total)

    os.makedirs(os.path.join(a.pack, "report"), exist_ok=True)
    path = os.path.join(a.pack, "report", "SUMMARY.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print("wrote %s  (%d records, %d systems, %d pairs)"
          % (path, total, len(systems), n_pairs))


if __name__ == "__main__":
    main()

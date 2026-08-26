#!/usr/bin/env python
"""k1_freeze_splits.py -- census + frozen splits for the K1 test.

Reads k1_corpus/labels/*.pkl, writes:
  k1_corpus/census.md   -- aggregate corpus statistics
  k1_corpus/splits.json -- frozen split definitions (pre-registration
                           commit b01d01d recorded inside)
Split filters per protocol Sec. 10: systems with mixed == True are
excluded from all TRAINING folds (kept as tagged challenge items).
"""
import glob
import json
import os
import pickle
import time

LAB = os.path.join("k1_corpus", "labels")
labs = {}
for p in sorted(glob.glob(os.path.join(LAB, "*.pkl"))) + \
         sorted(glob.glob(os.path.join("k1_corpus", "labels_tierB", "*.pkl"))):
    with open(p, "rb") as fh:
        d = pickle.load(fh)
    labs[d["name"]] = d

fams = {}
for name, d in labs.items():
    if not name.startswith("k1_"):
        continue
    fam = "_".join(name.split("_")[1:3])          # h4_chain etc.
    fams.setdefault(fam, []).append(name)
# Tier-B scan families (splits v2, pre-training amendment, 2026-08-26)
fams["lih"] = ["lih_sto3g", "lih_45", "lih_60", "lih_75", "lih_90"]
fams["c2_singlet"] = ["c2_2348", "c2_26", "c2_28_root2", "c2_30_root2"]
fams["h2o_fc_series"] = ["h2o_sto3g_fc", "h2o_15re", "h2o_20re"]
fams["n2_series"] = ["n2_2074", "n2_3111", "n2_4148"]
fams = {k: [n for n in v if n in labs] for k, v in fams.items()}

lines = ["# K1 Tier-A corpus census -- %s" % time.strftime("%Y-%m-%d"),
         "", "systems %d; preregistration b01d01d" % len(labs), ""]
for fam in sorted(fams):
    names = sorted(fams[fam])
    L = [len(labs[n]["word"]) for n in names]
    S = [len(labs[n]["support"]) for n in names]
    M = [labs[n]["n_monomials"] for n in names]
    mix = sum(1 for n in names if labs[n]["mixed"])
    over = sum(1 for n in names if labs[n]["n_monomials"] > len(labs[n]["support"]))
    sup_pinned = len(set(tuple(labs[n]["support"]) for n in names)) == 1
    lines.append("%-9s n=%2d  len %3d-%3d  support %s  mono>sup on %d  "
                 "mixed %d  support-SET pinned: %s"
                 % (fam, len(names), min(L), max(L),
                    ("%d (const)" % S[0]) if len(set(S)) == 1
                    else "%d-%d" % (min(S), max(S)),
                    over, mix, sup_pinned))
lines.append("")
lines.append("residual max over corpus: %.1e" %
             max(labs[n]["residual"] for n in labs))
open(os.path.join("k1_corpus", "census.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

spac = sorted(set(n.split("_")[-1] for n in labs))
splits = {
  "preregistration_commit": "b01d01d",
  "splits_revision": "v2: +lih, +c2_singlet, +h2o_fc_series, +n2_series Split-A families (pre-training, 2026-08-26)",
  "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
  "train_filter": "exclude mixed==True from all training folds",
  "gauge_note": ("k1_corpus dumps are the sole canonical inputs; "
                 "degenerate-shell gauge is pinned by platform AND "
                 "SCF damping path (recorded per system)"),
  "split_A_interpolation": {
      fam: [{"held_out": n,
             "train": [m for m in sorted(fams[fam])
                       if m != n and not labs[m]["mixed"]]}
            for n in sorted(fams[fam])]
      for fam in sorted(fams)},
  "split_C_cross_size": {
      "train": [n for n in sorted(labs) if not labs[n]["mixed"]],
      "test_tierB": ["h8_chain  (data/h8_chain_bigsd.pkl + "
                     "data/h8_chain_chain.npz; label extraction pending)"]},
  "split_D_cross_topology": {
      "train": [n for n in sorted(labs) if "_chain_" in n
                and not labs[n]["mixed"]],
      "test": [n for n in sorted(labs) if "_ring_" in n]},
  "split_B_transition_tierB": {
      "train": ["c2_2348 singlet", "c2_26 singlet", "c2_28 singlet"],
      "test": ["c2_30 singlet (root 2)"],
      "status": "labels to be extracted from archived chains+dumps"},
  "split_E_cross_molecule_tierB": {
      "train": "TierA + LiH scan + H2O series + N2 series",
      "test": "C2 equilibrium singlet",
      "status": "PENDING: h2o/n2 dumps not yet in container"},
}
with open(os.path.join("k1_corpus", "splits.json"), "w") as fh:
    json.dump(splits, fh, indent=1)
print("\nsplits.json written (A: %d families x LOGO; C train %d; D train %d/test %d)"
      % (len(fams), len(splits["split_C_cross_size"]["train"]),
         len(splits["split_D_cross_topology"]["train"]),
         len(splits["split_D_cross_topology"]["test"])))

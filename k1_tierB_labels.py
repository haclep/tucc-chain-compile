#!/usr/bin/env python
"""k1_tierB_labels.py -- Tier-B labels from archived chains + checkpoints.

Writes k1_corpus/labels_tierB/<stem>.pkl in the Tier-A label schema.
Sources: <stem>_chain.npz (word, thetas, pivot) + data/<stem>_bigsd.pkl
(ct, e0, roots, residual). Support recomputed from ct at the standard
floor. s2_root0 recorded as None for chain-derived entries (all are
nondegenerate singlet grounds by campaign record). LiH systems are
compiled fresh from their dumps via the Tier-A path.
"""
import os
import pickle
import time

import numpy as np

from chaincompile.sector import SectorBasis
from chaincompile import normalorder as NO
from chaincompile.dets import Substitution

OUT = os.path.join("k1_corpus", "labels_tierB")
os.makedirs(OUT, exist_ok=True)

# stem -> (L, na, nb) for basis reconstruction from campaign record
SECTOR = {
    "h2o_sto3g_full": (7, 5, 5), "h2o_sto3g_fc": (6, 4, 4),
    "h2o_15re": (6, 4, 4), "h2o_20re": (6, 4, 4),
    "n2_2074": (8, 5, 5), "n2_3111": (8, 5, 5), "n2_4148": (8, 5, 5),
    "h8_chain": (8, 4, 4),
}


def label_from_artifacts(stem):
    t0 = time.time()
    ck = pickle.load(open(os.path.join("data", stem + "_bigsd.pkl"), "rb"))
    d = np.load(stem + "_chain.npz", allow_pickle=True)
    L, na, nb = SECTOR[stem]
    sb = SectorBasis(L, na, nb)
    ct = np.asarray(ck["ct"], float)
    assert ct.size == sb.dim, (stem, ct.size, sb.dim)
    floor = np.sqrt(1e-12) / sb.dim
    supp = sorted(int(m) for m, k in zip(sb.masks, np.abs(ct) > floor) if k)
    word = [(tuple(h), tuple(p)) for h, p in zip(d["subs_h"], d["subs_p"])]
    th = [float(x) for x in np.asarray(d["th"], float).ravel()]
    import re
    rep = os.path.join("results", "bigsd_%s.md" % stem)
    n_mono, msrc = None, "unavailable"
    if os.path.exists(rep):
        m = re.search(r"(\d+) creator monomials", open(rep).read())
        if m:
            n_mono, msrc = int(m.group(1)), "committed report"
    lab = {"name": stem, "dim": sb.dim,
           "roots": [float(x) for x in ck.get("roots", [ck["e0"]])[:4]],
           "s2_root0": None, "mixed": False,
           "e_scf": None, "e_fci": float(ck["e0"]),
           "support": supp, "pivot": int(d["pivot"]),
           "word": word, "th": th,
           "residual": float(ck["residual"]),
           "n_monomials": n_mono,
           "source": "chain+checkpoint; monomials: %s" % msrc}
    print("  %-16s dim %4d len %4d mono %4d sup %4d  (%.0f s)"
          % (stem, sb.dim, len(word), lab["n_monomials"], len(supp),
             time.time() - t0))
    return lab


def main():
    print("tierB from chains+checkpoints:")
    for stem in SECTOR:
        outp = os.path.join(OUT, stem + ".pkl")
        if os.path.exists(outp):
            continue
        if not os.path.exists(stem + "_chain.npz"):
            print("  %-16s SKIP: chain file absent" % stem)
            continue
        lab = label_from_artifacts(stem)
        with open(outp, "wb") as fh:
            pickle.dump(lab, fh)
    print("tierB LiH from dumps (fresh compile):")
    import importlib.util as iu
    spec = iu.spec_from_file_location("kc", "k1_corpus_compile.py")
    kc = iu.module_from_spec(spec)
    spec.loader.exec_module(kc)
    for stem in ("lih_sto3g", "lih_45", "lih_60", "lih_75", "lih_90"):
        outp = os.path.join(OUT, stem + ".pkl")
        if os.path.exists(outp) or not os.path.exists(stem + ".npz"):
            continue
        lab = kc.compile_one(stem + ".npz")
        lab["source"] = "dump+fresh-compile"
        with open(outp, "wb") as fh:
            pickle.dump(lab, fh)
        print("  %-16s dim %4d len %4d mono %4d sup %4d"
              % (lab["name"], lab["dim"], len(lab["word"]),
                 lab["n_monomials"], len(lab["support"])))
    print("done.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""k1_c2_labels.py -- Split-B labels: the C2 singlet family.

Four systems: equilibrium (2.348), 2.6, 2.8, 3.0 bohr -- the diabatic
singlet tracked across the crossing (root 0 / 0 / 2 / 2). Chains from
archived artifacts; supports from independent eigenvectors; monomial
counts and residuals from the committed reports (source recorded).
Writes k1_corpus/labels_tierB/<name>.pkl.
"""
import os
import pickle

import numpy as np

from chaincompile.molecular import load_integral_dump, build_h_sector, freeze_core
from chaincompile.sector import SectorBasis

OUT = os.path.join("k1_corpus", "labels_tierB")
os.makedirs(OUT, exist_ok=True)
sb = SectorBasis(8, 4, 4)
FLOOR = np.sqrt(1e-12) / sb.dim

# name -> (chain path, singlet root index, mono from report, resid from report)
SYS = {
    "c2_2348":      (os.path.join("data", "c2_2348_chain.npz"), None, 1220, 6.4e-15),
    "c2_26":        ("c2_26_chain.npz",        0, 1109, 0.0),
    "c2_28_root2":  ("c2_28_root2_chain.npz",  2, 1252, 3.4e-13),
    "c2_30_root2":  ("c2_30_root2_chain.npz",  2, 660,  0.0),
}


def vec_for(name, root):
    if name == "c2_2348":
        ck = pickle.load(open(os.path.join("data", "c2_2348_bigsd.pkl"), "rb"))
        return np.asarray(ck["ct"], float), [float(x) for x in ck["roots"][:4]], float(ck["e0"])
    stem = name.split("_root")[0]
    ref = "/tmp/c2scan_ref.npz"
    if os.path.exists(ref) and stem in ("c2_26", "c2_28"):
        r = np.load(ref)
        V, w, sh = r[stem + "_V"], r[stem + "_w"], float(r[stem + "_shift"][0])
    else:
        h, e, e_nuc, e_scf, na, nb, meta = load_integral_dump(stem + ".npz")
        h, e, e_core = freeze_core(h, e, 2)
        w, V = np.linalg.eigh(build_h_sector(h, e, sb))
        sh = e_nuc + e_core
    roots = [float(x + sh) for x in w[:4]]
    return V[:, root], roots, roots[root]


for name, (cpath, root, mono, resid) in SYS.items():
    outp = os.path.join(OUT, name + ".pkl")
    if os.path.exists(outp):
        continue
    d = np.load(cpath, allow_pickle=True)
    v, roots, e = vec_for(name, root)
    supp = sorted(int(m) for m, k in zip(sb.masks, np.abs(v) > FLOOR) if k)
    word = [(tuple(h), tuple(p)) for h, p in zip(d["subs_h"], d["subs_p"])]
    th = [float(x) for x in np.asarray(d["th"], float).ravel()]
    lab = {"name": name, "dim": sb.dim, "roots": roots, "s2_root0": None,
           "mixed": False, "e_scf": None, "e_fci": e,
           "support": supp, "pivot": int(d["pivot"]),
           "word": word, "th": th, "residual": resid,
           "n_monomials": mono,
           "source": "chain artifact + independent eigenvector; "
                     "monomials+residual: committed report"}
    with open(outp, "wb") as fh:
        pickle.dump(lab, fh)
    print("  %-12s len %4d sup %4d mono %4d E %.8f"
          % (name, len(word), len(supp), mono, e))
print("done.")

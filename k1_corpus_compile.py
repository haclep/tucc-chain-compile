#!/usr/bin/env python
"""k1_corpus_compile.py -- labels for the K1 Tier-A corpus.

For every dump in k1_corpus/, computes and caches to
k1_corpus/labels/<name>.pkl:
  roots (first 4, with S2 of root 0), mixed/projected tags,
  support set, sd_routed chain (letters + thetas), residual,
  creator-monomial count, E_FCI.
Self-scheduling: --budget N compiles pending systems until ~N seconds
are spent, then exits listing what remains. Deterministic order
(sorted names); rerun to continue. Read-only w.r.t. the dumps.
"""
import glob
import os
import pickle
import sys
import time

import numpy as np

from chaincompile.compile import compile_chain
from chaincompile.molecular import (build_h_sector, load_integral_dump,
                                    freeze_core, dominant_block_projection)
from chaincompile.sector import SectorBasis
from chaincompile import normalorder as NO

LAB = os.path.join("k1_corpus", "labels")
os.makedirs(LAB, exist_ok=True)


def compile_one(path):
    name = os.path.splitext(os.path.basename(path))[0]
    h, e, e_shift, e_scf, na, nb, meta = load_integral_dump(path)
    h, e, e_core = freeze_core(h, e, 0)
    sb = SectorBasis(h.shape[0], na, nb)
    H = build_h_sector(h, e, sb)
    w, V = np.linalg.eigh(H)
    S2 = sb.s2_matrix()
    s2_0 = float(V[:, 0] @ (S2 @ V[:, 0]))
    v0, seen2, mixed = dominant_block_projection(V[:, 0], H)
    floor = np.sqrt(1e-12) / sb.dim
    supp = sorted(int(m) for m, k in zip(sb.masks, np.abs(v0) > floor) if k)
    res = compile_chain(v0, sb, mode="sd_routed")
    word = [(tuple(s.holes), tuple(s.parts)) for s, _ in res.selected()]
    th = [float(t) for _, t in res.selected()]
    occ = frozenset(p for p in range(2 * h.shape[0])
                    if (res.pivot_mask >> p) & 1)
    subs = [s for s, _ in res.selected()]
    U, sizes = NO.compose_numeric(subs, th, occ)
    c0, amps = NO.numeric_ref_amplitudes(U, occ)
    return {"name": name, "dim": sb.dim,
            "roots": [float(x + e_shift) for x in w[:4]],
            "s2_root0": s2_0, "mixed": bool(mixed),
            "e_scf": float(e_scf), "e_fci": float(w[0] + e_shift),
            "support": supp, "pivot": int(res.pivot_mask),
            "word": word, "th": th,
            "residual": float(res.final_residual),
            "n_monomials": len(amps) + 1}


def main():
    budget = 220.0
    for i, a in enumerate(sys.argv):
        if a == "--budget":
            budget = float(sys.argv[i + 1])
    t0 = time.time()
    dumps = sorted(glob.glob(os.path.join("k1_corpus", "*.npz")))
    pending = [d for d in dumps if not os.path.exists(
        os.path.join(LAB, os.path.splitext(os.path.basename(d))[0] + ".pkl"))]
    print("k1_corpus_compile: %d total, %d pending, budget %.0f s"
          % (len(dumps), len(pending), budget))
    done = 0
    for d in pending:
        if time.time() - t0 > budget:
            break
        lab = compile_one(d)
        with open(os.path.join(LAB, lab["name"] + ".pkl"), "wb") as fh:
            pickle.dump(lab, fh)
        print("  %-18s dim %4d len %4d resid %.1e mono %4d sup %4d "
              "s2 %.3f%s" % (lab["name"], lab["dim"], len(lab["word"]),
                             lab["residual"], lab["n_monomials"],
                             len(lab["support"]), lab["s2_root0"],
                             "  MIXED" if lab["mixed"] else ""))
        done += 1
    left = len(pending) - done
    print("compiled %d this pass; %d remain%s"
          % (done, left, "" if left == 0 else " -- rerun to continue"))


if __name__ == "__main__":
    main()

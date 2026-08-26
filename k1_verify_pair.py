#!/usr/bin/env python
"""k1_verify_pair.py -- platform-pair verification of the K1 freeze (v2).

v2 (2026-08-26): the pass criterion is the INVARIANT, not the gauge.
Discrete quantities (letters, order, support, pivot, monomial count)
must be exactly equal across platforms. Angles are compared by
CROSS-REPLAY: the fresh theta and the committed theta are each applied
through the (identical) letter sequence, and the two resulting states
must agree to deficit <= 1e-11. Pointwise max|dtheta| is reported as a
DIAGNOSTIC of the theta-redundancy manifold (overparameterized chains
admit a manifold of equivalent angle vectors; platforms park at
different points on it), never as a pass/fail quantity.

Run from the repo root, Seneca environment:  python -u k1_verify_pair.py
"""
import os
import pickle
import sys

import numpy as np

import importlib.util as iu
spec = iu.spec_from_file_location("kc", "k1_corpus_compile.py")
kc = iu.module_from_spec(spec)
spec.loader.exec_module(kc)

from chaincompile.dets import Substitution
from chaincompile import disentangle as dz

SYSTEMS = ["k1_h6_chain_14", "k1_h6_ring_19", "k1_h6_ring_30",
           "k1_h4_ring_20", "k1_h4_chain_24", "lih_60"]


def labpath(name):
    for sub in ("labels", "labels_tierB"):
        p = os.path.join("k1_corpus", sub, name + ".pkl")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def replay(word, th, pivot):
    occ = tuple(sorted(q for q in range(64) if (pivot >> q) & 1))
    st = {occ: 1.0}
    for (hh, pp), t in zip(word, th):
        st = dz.apply_factor(Substitution(hh, pp), float(t), st, tol=0.0)
    nrm = sum(v * v for v in st.values()) ** 0.5
    return {k: v / nrm for k, v in st.items()}


def overlap(a, b):
    return abs(sum(v * b.get(k, 0.0) for k, v in a.items()))


def main():
    names = sys.argv[1:] or SYSTEMS
    allok = True
    for name in names:
        ref = pickle.load(open(labpath(name), "rb"))
        fresh = kc.compile_one(os.path.join("k1_corpus", name + ".npz"))
        word_ok = fresh["word"] == ref["word"]
        disc = (word_ok and fresh["support"] == ref["support"]
                and fresh["pivot"] == ref["pivot"]
                and fresh["n_monomials"] == ref["n_monomials"])
        dth = (max(abs(a - b) for a, b in zip(fresh["th"], ref["th"]))
               if word_ok and fresh["th"] else float("inf"))
        if disc:
            pf = replay(fresh["word"], fresh["th"], fresh["pivot"])
            pc = replay(ref["word"], ref["th"], ref["pivot"])
            deficit = abs(1.0 - overlap(pf, pc) ** 2)
        else:
            deficit = float("inf")
        ok = disc and deficit <= 1e-11
        allok &= ok
        print("  %-16s discrete %s  max|dtheta| %.1e (diagnostic)  "
              "cross-replay deficit %.1e  -> %s"
              % (name, "==" if disc else "DIFF", dth, deficit,
                 "MATCH" if ok else "MISMATCH"))
    print("VERDICT: %s" % ("PLATFORM PAIR PASSED -- training may begin"
                           if allok else "MISMATCH -- do not train; "
                           "paste this output back"))


if __name__ == "__main__":
    main()

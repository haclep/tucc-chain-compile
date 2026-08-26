#!/usr/bin/env python
"""k1_verify_pair.py -- platform-pair verification of the K1 freeze.

Recompiles six named systems from the committed k1_corpus dumps and
diffs them against the committed labels. Discrete quantities (letters,
order, support, pivot, monomial count) must be EXACTLY equal across
platforms; angles are compared at 1e-9 (libm last-bit tolerance, per
the campaign's platform-pair measurements). Writes nothing under
k1_corpus; recompiles go to a throwaway scratch in memory.

Run from the repo root, Seneca environment:  python -u k1_verify_pair.py
Optional: pass system names to restrict the set.
"""
import os
import pickle
import sys

import numpy as np

import importlib.util as iu
spec = iu.spec_from_file_location("kc", "k1_corpus_compile.py")
kc = iu.module_from_spec(spec)
spec.loader.exec_module(kc)

SYSTEMS = ["k1_h6_chain_14", "k1_h6_ring_19", "k1_h6_ring_30",
           "k1_h4_ring_20", "k1_h4_chain_24", "lih_60"]


def labpath(name):
    for sub in ("labels", "labels_tierB"):
        p = os.path.join("k1_corpus", sub, name + ".pkl")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def main():
    names = sys.argv[1:] or SYSTEMS
    allok = True
    for name in names:
        ref = pickle.load(open(labpath(name), "rb"))
        fresh = kc.compile_one(os.path.join("k1_corpus", name + ".npz"))
        word_ok = fresh["word"] == ref["word"]
        sup_ok = fresh["support"] == ref["support"]
        piv_ok = fresh["pivot"] == ref["pivot"]
        mono_ok = fresh["n_monomials"] == ref["n_monomials"]
        dth = (max(abs(a - b) for a, b in zip(fresh["th"], ref["th"]))
               if word_ok and fresh["th"] else float("inf"))
        ok = word_ok and sup_ok and piv_ok and mono_ok and dth < 1e-9
        allok &= ok
        print("  %-16s word %s  support %s  pivot %s  mono %s  "
              "max|dtheta| %.1e  -> %s"
              % (name, "==" if word_ok else "DIFF",
                 "==" if sup_ok else "DIFF", "==" if piv_ok else "DIFF",
                 "==" if mono_ok else "DIFF", dth,
                 "MATCH" if ok else "MISMATCH"))
    print("VERDICT: %s" % ("PLATFORM PAIR PASSED -- training may begin"
                           if allok else "MISMATCH -- do not train; "
                           "paste this output back"))


if __name__ == "__main__":
    main()

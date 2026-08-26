#!/usr/bin/env python
"""k1_corpus_mint.py -- Tier-A corpus for the K1 pre-registration
(docs/k1_learnability_preregistration.md, frozen at b01d01d).

Mints H4 and H6, chain and ring, spacings 1.2..3.6 bohr step 0.1
(25 points): up to 100 dumps under k1_corpus/. These container-minted
dumps ARE the canonical corpus gauge: for degenerate-shell systems
(rings, near-square H4) the archived file pins the MO gauge per the
MO-gauge law, so all training and evaluation must run from exactly
these files. Failures to converge are RECORDED, not retried with
altered physics; a failed point is simply absent, by name, from the
frozen splits.
"""
import importlib.util as iu
import os
import sys

import numpy as np

spec = iu.spec_from_file_location("mh", os.path.join("examples", "make_h_dumps.py"))
mh = iu.module_from_spec(spec)
spec.loader.exec_module(mh)

OUT = "k1_corpus"
os.makedirs(OUT, exist_ok=True)
SPACINGS = [round(1.2 + 0.1 * k, 1) for k in range(25)]

ok, fail = [], []
for n in (4, 6):
    for topo in ("chain", "ring"):
        for s in SPACINGS:
            name = "k1_h%d_%s_%02d" % (n, topo, round(s * 10))
            out = os.path.join(OUT, name + ".npz")
            if os.path.exists(out):
                ok.append(name)
                continue
            cent = mh.chain(n, s) if topo == "chain" else mh.ring(n, s)
            wrote = False
            why = "no attempt"
            cwd = os.getcwd()
            for damp in (0.3, 0.5, 0.7, 0.85):
                sp_ = mh.spec(n, topo, s, damp)
                try:
                    os.chdir(OUT)
                    try:
                        r = mh.make_one(name, sp_, damp, False)
                    finally:
                        os.chdir(cwd)
                    if r in ("written", "skipped") and os.path.exists(out):
                        wrote = True
                        break
                    why = "RHF not converged through damp %.2f" % damp
                except Exception as exc:
                    os.chdir(cwd)
                    why = repr(exc)[:80]
                    break
            if wrote:
                ok.append(name)
            else:
                fail.append((name, why))
print("minted/present %d; failed %d" % (len(ok), len(fail)))
for name, why in fail:
    print("  FAIL %s : %s" % (name, why))

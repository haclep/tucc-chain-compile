#!/usr/bin/env python
"""k1c_phase1.py -- K1c step 1b: the compiler's own state at proposal time.

In the K1b-T4 harness every arm runs phase 1 (routing + greedy ordering)
identically, then the proposal is appended. Everything phase 1 knows is
therefore available to a proposer for free and is identical across
arms. This module reproduces phase 1 with the driver's own functions
(chaincompile._route_sequence, run_big_sd._greedy_init, _prep),
verifies that the routed+greedy prefix equals the label's, and derives
the features a proposer should have but the frozen model did not:

  per routed letter : greedy-init angle theta0 (the saturation-split
                      rule duplicates letters whose |theta| reaches
                      0.92*BOUND), number of routed occurrences, first
                      position.
  per universe letter: the compiler's first-order fidelity gain
                      |<residual, kappa_e psi>| at the greedy state --
                      exactly the score growth round one uses to choose
                      new letters -- and support connectivity (how many
                      support determinants the letter maps into support
                      versus into fill-in).

Decomposition (2026-09-08, this repo): on h8_chain 52% of the grown
multiset mass is copies of routed letters and 48% is new tangent edges,
none of them pivot-referenced. The two halves are different prediction
problems and each has its own compiler-native feature here.

Results are cached to k1c_cache/<name>.pkl (phase-1 state is
deterministic; the cache is a convenience). Nothing here writes to k1b/
or touches the campaign checkout.

Usage:
    python k1c_phase1.py k1_h6_chain_19 h8_chain     # verify + cache
    python k1c_phase1.py --all-h6                    # cache the H6 set
"""
import argparse
import importlib.util as iu
import math
import os
import pickle
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "src"))

from chaincompile.compile import (_normalize_target, _prep,          # noqa: E402
                                  _route_sequence)
from chaincompile.dets import Substitution                          # noqa: E402
from chaincompile.molecular import (build_h_sector, freeze_core,    # noqa: E402
                                    load_integral_dump,
                                    dominant_block_projection)
from chaincompile.sector import SectorBasis                         # noqa: E402


def _load(name, fn):
    spec = iu.spec_from_file_location(name, os.path.join(HERE, fn))
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kh = _load("kh", "k1_harness.py")
ku = _load("ku", "k1c_universe.py")
big = _load("run_big_sd", os.path.join("examples", "run_big_sd.py"))
BOUND = big.BOUND
CACHE = os.path.join(HERE, "k1c_cache")


# ------------------------------------------------------------ target
def load_target(name):
    """Target vector, pivot, basis -- checkpoint if one exists (the
    campaign's exact target, as the harness uses), else dense eigh with
    the corpus compiler's dominant-block projection."""
    nc = kh._ncore(name)
    dump = kh._dumppath(name)
    h, e, e_nuc, e_scf, na, nb, meta = load_integral_dump(dump)
    h, e, e_core = freeze_core(h, e, nc)
    basis = SectorBasis(h.shape[0], na - nc, nb - nc)
    stem = kh._dumpstem(name)
    ck = os.path.join(HERE, "data", stem + "_bigsd.pkl")
    if os.path.exists(ck):
        with open(ck, "rb") as fh:
            C = pickle.load(fh)
        ct, pivot = np.asarray(C["ct"], float), int(C["pivot_mask"])
        assert ct.size == basis.dim, (ct.size, basis.dim)
        return ct, pivot, basis, float(C.get("support_tol", 1e-10)), "checkpoint"
    if basis.dim > 8000:
        raise SystemExit("dense target refused at dim %d" % basis.dim)
    H = build_h_sector(h, e, basis)
    w, V = np.linalg.eigh(H)
    v0, _, _ = dominant_block_projection(V[:, 0], H)
    ct, pivot, _ = _normalize_target(v0, basis, None)
    return ct, pivot, basis, 1e-12, "dense"


# ------------------------------------------------------------ phase 1
def phase1(name, verify=True):
    """Route + greedy-order exactly as the harness; return the state at
    proposal time plus label bookkeeping."""
    lab = pickle.load(open(kh._labpath(name), "rb"))
    ct, pivot, basis, support_tol, src = load_target(name)
    seq0 = _route_sequence(ct, basis, pivot, support_tol)
    seq, th0 = big._greedy_init(ct, basis, pivot, seq0)
    psi = _prep(th0, seq, basis, pivot)
    resv = psi - ct
    rn = float(np.linalg.norm(resv))
    routed_word = [(tuple(s.holes), tuple(s.parts)) for s, _, _ in seq]
    word = [tuple(map(tuple, x)) for x in lab["word"]]
    n_routed = len(lab["support"]) - 1
    ok = (routed_word == word[:n_routed])
    if verify and not ok:
        # fall back: compare as multisets, report first mismatch
        i = next((k for k in range(min(len(routed_word), n_routed))
                  if routed_word[k] != word[k]), None)
        raise SystemExit("%s: phase-1 prefix does not match the label "
                         "(len %d vs %d, first mismatch at %s) -- target "
                         "source %s" % (name, len(routed_word), n_routed,
                                        i, src))
    supp = {int(basis.masks[i]) for i in range(basis.dim)
            if abs(ct[i]) > support_tol}
    return {"name": name, "ct": ct, "pivot": pivot, "basis": basis,
            "seq": seq, "theta0": np.asarray(th0, float), "psi": psi,
            "resv": resv, "rn": rn, "routed_word": routed_word,
            "n_routed": n_routed, "grown": word[n_routed:],
            "support": supp, "target_src": src, "prefix_ok": ok}


# ------------------------------------------------------------ features
def tangent_scores(P, universe):
    """|<resv, kappa_e psi>| for every letter of the universe at the
    greedy state: the compiler's own first-order fidelity gain."""
    basis, psi, resv = P["basis"], P["psi"], P["resv"]
    out = np.zeros(len(universe))
    for n, (hh, pp) in enumerate(universe):
        sub = Substitution(tuple(hh), tuple(pp))
        ii, jj, ss = basis.block_arrays(sub)
        if len(ii) == 0:
            continue
        out[n] = abs(float(resv[jj] @ (ss * psi[ii])
                           - resv[ii] @ (ss * psi[jj])))
    return out


def support_connectivity(P, universe):
    """Per letter: number of support determinants it maps INTO support,
    and number it maps OUT of support (fill-in)."""
    supp = P["support"]
    masks = list(supp)
    n_in = np.zeros(len(universe), int)
    n_out = np.zeros(len(universe), int)
    for n, (hh, pp) in enumerate(universe):
        hm = sum(1 << q for q in hh)
        pm = sum(1 << q for q in pp)
        for m in masks:
            if (m & hm) == hm and (m & pm) == 0:
                m2 = (m ^ hm) | pm
                if m2 in supp:
                    n_in[n] += 1
                else:
                    n_out[n] += 1
    return n_in, n_out


def routed_stats(P):
    """Per distinct routed letter: occurrences, |theta0| sum/max/mean,
    saturated count, normalized first position."""
    stats = {}
    L = len(P["seq"])
    for pos, (key, t) in enumerate(zip(P["routed_word"], P["theta0"])):
        d = stats.setdefault(key, {"n": 0, "abs_sum": 0.0, "abs_max": 0.0,
                                   "n_sat": 0, "first": pos / max(1, L)})
        d["n"] += 1
        d["abs_sum"] += abs(t)
        d["abs_max"] = max(d["abs_max"], abs(t))
        d["n_sat"] += int(abs(t) >= 0.92 * BOUND)
    for d in stats.values():
        d["abs_mean"] = d["abs_sum"] / d["n"]
    return stats


def compute(name, verify=True, force=False):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name + ".pkl")
    if os.path.exists(path) and not force:
        with open(path, "rb") as fh:
            return pickle.load(fh)
    P = phase1(name, verify=verify)
    S = ku.load_system(name)
    uni = ku.full_universe(S["n_so"])
    ts = tangent_scores(P, uni)
    n_in, n_out = support_connectivity(P, uni)
    out = {"name": name, "universe": uni, "tangent": ts,
           "supp_in": n_in, "supp_out": n_out, "rn": P["rn"],
           "theta0": P["theta0"], "routed_word": P["routed_word"],
           "routed": routed_stats(P), "n_routed": P["n_routed"],
           "grown": P["grown"], "target_src": P["target_src"],
           "n_support": len(P["support"]), "bound": BOUND}
    with open(path, "wb") as fh:
        pickle.dump(out, fh)
    return out


def report(F):
    grown = F["grown"]
    cnt = kh.counts(grown)
    rset = set(F["routed_word"])
    copies = sum(c for k, c in cnt.items() if k in rset)
    new = len(grown) - copies
    uni = F["universe"]
    idx = {k: i for i, k in enumerate(uni)}
    newkeys = [k for k in cnt if k not in rset]
    ts = F["tangent"]
    # where do the new letters sit in the tangent ranking?
    order = np.argsort(-ts)
    rankof = np.empty(len(uni), int)
    rankof[order] = np.arange(len(uni))
    ranks = sorted(rankof[idx[k]] for k in newkeys)
    n_new_d = len(newkeys)
    topn_hit = sum(1 for r in ranks if r < n_new_d)
    sat = [k for k, d in F["routed"].items() if d["n_sat"] > 0]
    sat_copied = sum(1 for k in sat if cnt.get(k, 0) > 0)
    copied = [k for k in cnt if k in rset]
    copied_sat = sum(1 for k in copied if F["routed"][k]["n_sat"] > 0)
    print("%-16s target %s | |r| greedy %.3e | routed %d (%d distinct) | "
          "grown %d: copies %d (%.0f%%) new %d (%d distinct)"
          % (F["name"], F["target_src"], F["rn"], F["n_routed"],
             len(rset), len(grown), copies, 100.0 * copies / max(1, len(grown)),
             new, n_new_d))
    print("   tangent ranking at greedy state: of the %d distinct new "
          "letters, %d are in the top-%d (%.0f%%); median rank %d of %d"
          % (n_new_d, topn_hit, n_new_d,
             100.0 * topn_hit / max(1, n_new_d),
             int(np.median(ranks)) if ranks else -1, len(uni)))
    print("   saturation at greedy: %d routed letters saturated; %d of them "
          "got copies; of %d copied letters %d were saturated at greedy"
          % (len(sat), sat_copied, len(copied), copied_sat))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--all-h6", action="store_true")
    ap.add_argument("--all-h4", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-verify", action="store_true")
    a = ap.parse_args()
    labs = kh.load_labels()
    names = list(a.names)
    if a.all_h4:
        names += sorted(n for n in labs if n.startswith("k1_h4")
                        and not labs[n].get("mixed", False))
    if a.all_h6:
        names += sorted(n for n in labs if n.startswith("k1_h6")
                        and not labs[n].get("mixed", False))
    for n in names:
        F = compute(n, verify=not a.no_verify, force=a.force)
        report(F)


if __name__ == "__main__":
    main()

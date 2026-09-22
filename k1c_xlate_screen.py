#!/usr/bin/env python
"""k1c_xlate_screen.py -- translation-safety screen for certified chains.

The UCC->CC disentangling identity (Freericks, Symmetry 14, 494 (2022),
Eq. 15) sets the CC-side amplitude to t = tan(theta) and a Cartan factor
to -ln(cos theta) for every UCC factor. Both diverge as |theta| -> pi/2.
The divergence is not an artifact: the factorization is a Gauss
decomposition of SL(2,C), which does not cover the whole group, and
cos(theta) is precisely the weight the factor leaves on the reference
determinant. |theta| = pi/2 is the point at which the reference is
rotated out of the state entirely, and single-reference CC has nothing
left to be a theory of. The paper restricts to -pi/2 < theta < pi/2 and
notes that amplitudes are "usually not larger than pi/4" (t < 1), which
is the weakly correlated assumption our regime violates by design.

This script does NOT translate. It screens: for every banked chain it
reports max|theta|, the CC-side amplitude t = tan(max|theta|), and the
reference weight cos(max|theta|), and bands each member against the
calibration points on record. Translation is then attempted only on
eligible members, and shipped only if the translator's own acceptance
number meets the floor -- max|theta| is the cheap pre-screen, acceptance
is the gate, because products of tangents compound across a chain and
the largest single angle does not by itself decide safety.

Bands (thresholds are conventions, set here, changeable):
  usual      t < 1        the paper's weakly correlated range
  routine    1 <= t < 10
  verified   10 <= t < 35 at or below the C2 flagship (t = 34.4,
                          acceptance 2.6e-16) and LiH R=9.0 (t = 25)
  untested   35 <= t < 50 past every verified point; translate and
                          judge on acceptance alone
  ceiling    t >= 50      at or past the documented ~50 ceiling; do not
                          ship a translation without an acceptance number

Usage:
    python k1c_xlate_screen.py
    python k1c_xlate_screen.py --stem h8_chain
    python k1c_xlate_screen.py --max-t 35        # eligibility cut
Writes k1c_runs/xlate_screen.json (the manifest the packer reads).
"""
import argparse
import glob
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "k1c_runs")
RESULTS = os.path.join(HERE, "results")
BANDS = [(1.0, "usual"), (10.0, "routine"), (35.0, "verified"),
         (50.0, "untested"), (float("inf"), "ceiling")]
CAL = {"C2 2.348 flagship": 34.4, "LiH R=9.0": 25.0}


def band(t):
    for hi, name in BANDS:
        if t < hi:
            return name
    return "ceiling"


def amp(theta):
    """CC-side amplitude and reference weight for the largest factor."""
    c = math.cos(theta)
    return (math.tan(theta) if abs(c) > 1e-15 else float("inf")), c


def from_summaries():
    out = []
    for p in sorted(glob.glob(os.path.join(RUNS, "*_summary.json"))) + \
            sorted(glob.glob(os.path.join(HERE, "k1b", "*_summary.json"))):
        try:
            s = json.load(open(p))
        except Exception:
            continue
        if "max_abs_theta" not in s:
            continue
        tag = os.path.basename(p)[:-len("_summary.json")]
        stem = s.get("stem", "")
        out.append({"stem": stem, "member": tag[len(stem) + 1:] or tag,
                    "theta": float(s["max_abs_theta"]),
                    "len": s.get("final_len"), "R": s.get("residual"),
                    "src": os.path.relpath(p, HERE)})
    return out


def from_reports():
    """Reports carry max|theta| for runs whose summary is not on disk."""
    pat = re.compile(r"max\|theta\|\s*([0-9.]+)")
    lenpat = re.compile(r"final chain (\d+) letters")
    out = []
    for p in sorted(glob.glob(os.path.join(RESULTS, "*.md"))):
        txt = open(p, encoding="utf-8", errors="replace").read()
        m = pat.search(txt)
        if not m:
            continue
        name = os.path.basename(p)[:-3]
        L = lenpat.search(txt)
        out.append({"stem": "", "member": name, "theta": float(m.group(1)),
                    "len": int(L.group(1)) if L else None, "R": None,
                    "src": os.path.relpath(p, HERE)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stem", default=None)
    ap.add_argument("--max-t", type=float, default=35.0,
                    help="eligibility cut on t = tan(max|theta|)")
    ap.add_argument("--reports", action="store_true",
                    help="also scan results/*.md for runs without summaries")
    a = ap.parse_args()
    rows = from_summaries() + (from_reports() if a.reports else [])
    seen, uniq = set(), []
    for r in rows:
        k = (r["stem"], r["member"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    if a.stem:
        uniq = [r for r in uniq if r["stem"] == a.stem or
                a.stem in r["member"]]
    if not uniq:
        raise SystemExit("no chains with max|theta| found")
    for r in uniq:
        r["t"], r["c0"] = amp(r["theta"])
        r["band"] = band(r["t"])
        r["eligible"] = r["t"] < a.max_t
    uniq.sort(key=lambda r: (r["stem"], -r["t"]))
    print("%-14s %-30s %8s %10s %9s %-9s %s"
          % ("stem", "member", "max|th|", "t=tan", "cos", "band", "elig"))
    for r in uniq:
        print("%-14s %-30s %8.4f %10.2f %9.5f %-9s %s"
              % (r["stem"][:14], r["member"][:30], r["theta"], r["t"],
                 r["c0"], r["band"], "yes" if r["eligible"] else "NO"))
    ts = [r["t"] for r in uniq]
    n_ok = sum(r["eligible"] for r in uniq)
    print("\n%d chains | t from %.2f to %.2f (spread x%.0f) | %d eligible "
          "at t < %g, %d held"
          % (len(uniq), min(ts), max(ts), max(ts) / max(min(ts), 1e-9),
             n_ok, a.max_t, len(uniq) - n_ok))
    print("calibration on record: " + ", ".join("%s t=%.1f" % (k, v)
                                                for k, v in CAL.items()))
    by_stem = {}
    for r in uniq:
        by_stem.setdefault(r["stem"], []).append(r["t"])
    multi = {k: v for k, v in by_stem.items() if len(v) > 1 and k}
    if multi:
        print("\nper-state spread of the largest CC amplitude across "
              "certified derivations of the SAME wavefunction:")
        for k, v in sorted(multi.items()):
            print("  %-14s %2d chains | t %.2f to %.2f (x%.0f)"
                  % (k, len(v), min(v), max(v), max(v) / max(min(v), 1e-9)))
    os.makedirs(RUNS, exist_ok=True)
    with open(os.path.join(RUNS, "xlate_screen.json"), "w") as fh:
        json.dump({"max_t": a.max_t, "bands": [b[1] for b in BANDS],
                   "calibration": CAL, "members": uniq}, fh, indent=1)
    print("\nmanifest -> k1c_runs/xlate_screen.json")


if __name__ == "__main__":
    main()

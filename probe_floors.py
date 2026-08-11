#!/usr/bin/env python
"""probe_floors.py -- read-only closure check (METHOD open item).

Counts, at amplitude floors 1e-8 / 1e-10 / 1e-12 / 1e-14, how many
stored weights exceed each floor, for two objects in the flagship
checkpoint data/c2_2348_bigsd.pkl:

  [4] 'ct'  the stored target eigenvector -- CALIBRATION. Must
      reproduce the already-recorded [1108, 1108, 1108, 1258].
      A four-fold MATCH certifies the script reads the storage
      correctly; only then does step [5] mean anything.
  [5] 'U'   the translated monomial weights -- THE CHECK. The
      pre-registered prediction is about [1108, 1108, ~1108, ~1219].

Convention (matches the recorded target probe): a weight is counted
at floor f when |w| > f, strictly. The band table below each count
shows where the sub-resolution entries actually live.

This script opens files for READING ONLY and writes nothing. It is a
probe in the probe_checkpoint.py tradition: run it, paste the output,
do not commit it.
"""
import os
import pickle
import sys

import numpy as np

PKL = os.path.join("data", "c2_2348_bigsd.pkl")
NPZ = os.path.join("data", "c2_2348_chain.npz")
FLOORS = (1e-8, 1e-10, 1e-12, 1e-14)
BANDS = ((1e-8, None), (1e-10, 1e-8), (1e-12, 1e-10),
         (1e-14, 1e-12), (0.0, 1e-14))


def fail(msg):
    print("STOP:", msg)
    sys.exit(1)


def describe(name, v):
    """One anatomy line per object: what it is, before any counting."""
    if isinstance(v, np.ndarray):
        print("    %-10s ndarray shape=%s dtype=%s" % (name, v.shape, v.dtype))
    elif isinstance(v, dict):
        ks = list(v.keys())
        print("    %-10s dict len=%d sample_keys=%s" % (name, len(v), ks[:3]))
    elif isinstance(v, (list, tuple)):
        print("    %-10s %s len=%d" % (name, type(v).__name__, len(v)))
    else:
        print("    %-10s %s = %s" % (name, type(v).__name__, repr(v)[:60]))


def as_weights(obj):
    """Pull one flat array of |weights| out of obj, defensively.

    Returns (weights, note) on success or (None, note) on failure --
    in the failure case the anatomy printed above tells us what the
    object really is, and the probe gets finalized against that.
    """
    scalar_types = (int, float, complex, np.floating, np.complexfloating)
    if isinstance(obj, np.ndarray):
        if obj.dtype.kind in "fc":
            if obj.ndim == 1:
                return np.abs(obj.ravel()), "1-d float array"
            if obj.ndim == 2 and 2 in obj.shape:
                cols = obj if obj.shape[1] == 2 else obj.T
                a = np.abs(cols[:, 0]).max()
                b = np.abs(cols[:, 1]).max()
                pick = cols[:, 1] if b <= a else cols[:, 0]
                return (np.abs(np.asarray(pick).ravel()),
                        "2-column array; smaller-magnitude column taken as weights")
            return np.abs(obj.ravel()), "float array (flattened)"
        return None, "array dtype %s is not float/complex" % obj.dtype
    if isinstance(obj, dict):
        vals = list(obj.values())
        if vals and all(isinstance(v, scalar_types) for v in vals[:50]):
            try:
                w = np.abs(np.asarray(vals, dtype=complex)).astype(float)
                return w, "dict values (scalar weights)"
            except Exception:
                pass
        floats = {k: v for k, v in obj.items()
                  if isinstance(v, np.ndarray) and v.dtype.kind in "fc"}
        if len(floats) == 1:
            k = next(iter(floats))
            return np.abs(floats[k].ravel()), "float array under dict key %r" % k
        for cand in ("w", "weights", "vals", "values", "c", "coef", "coeff"):
            if cand in floats:
                return (np.abs(floats[cand].ravel()),
                        "float array under dict key %r" % cand)
        return None, ("dict without an unambiguous float-weight member "
                      "(float-array keys: %s)" % list(floats))
    if isinstance(obj, (list, tuple)):
        if obj and all(isinstance(v, scalar_types) for v in obj[:50]):
            try:
                w = np.abs(np.asarray(obj, dtype=complex)).astype(float)
                return w, "sequence of scalar weights"
            except Exception:
                pass
        floats = [v for v in obj
                  if isinstance(v, np.ndarray) and v.dtype.kind in "fc"]
        if len(floats) == 1:
            return (np.abs(floats[0].ravel()),
                    "float array inside a %s" % type(obj).__name__)
        return None, "sequence without a single float array"
    return None, "unhandled type %s" % type(obj).__name__


def floor_counts(w):
    return [int(np.count_nonzero(w > f)) for f in FLOORS]


def band_table(w):
    rows = []
    for lo, hi in BANDS:
        if hi is None:
            n = int(np.count_nonzero(w > lo))
            lab = "(> %.0e)" % lo
        else:
            n = int(np.count_nonzero((w > lo) & (w <= hi)))
            lab = "(%.0e, %.0e]" % (lo, hi)
        rows.append((lab, n))
    return rows


def print_bands(w):
    for lab, n in band_table(w):
        print("      band %-22s %5d" % (lab, n))


def main():
    print("probe_floors: read-only closure check (writes nothing)")
    print("convention: a weight is counted at floor f when |w| > f (strict)")

    if not os.path.exists(PKL):
        fail("checkpoint not found at %s -- run from the repo root" % PKL)
    with open(PKL, "rb") as fh:
        ck = pickle.load(fh)
    if not isinstance(ck, dict):
        fail("checkpoint is %s, expected dict" % type(ck).__name__)
    print("[1] loaded %s  (%d keys)" % (PKL, len(ck)))

    print("[2] anchors from the checkpoint")
    for k in ("e0", "residual", "support", "grown", "routed",
              "projected", "hf_in_dom", "phase", "round"):
        if k in ck:
            describe(k, ck[k])
    if "roots" in ck:
        try:
            r = np.asarray(ck["roots"], dtype=float).ravel()
            print("    roots      " + "  ".join("%.8f" % x for x in r[:6]))
        except Exception:
            describe("roots", ck["roots"])
    if "noc_k" in ck:
        try:
            t = [int(x) for x in np.asarray(ck["noc_k"]).ravel()]
            print("    noc_k tail %s" % t[-3:])
        except Exception:
            describe("noc_k", ck["noc_k"])

    print("[3] anatomy of the two objects of interest")
    for k in ("U", "ct"):
        if k in ck:
            describe(k, ck[k])
        else:
            print("    %-10s MISSING" % k)

    print("[4] calibration: floor counts on 'ct' (stored target)")
    calibrated = False
    if "ct" in ck:
        w, note = as_weights(ck["ct"])
        if w is None:
            print("    could not read weights from ct: %s" % note)
            print("    calibration skipped -- paste this output back")
        else:
            print("    reading: %s, %d entries, max|w|=%.6f"
                  % (note, w.size, w.max()))
            got = floor_counts(w)
            exp = [1108, 1108, 1108, 1258]
            calibrated = (got == exp)
            for f, g, e in zip(FLOORS, got, exp):
                tag = "MATCH" if g == e else "MISMATCH"
                print("    floor %.0e : %5d   (recorded %5d)  %s"
                      % (f, g, e, tag))
            print_bands(w)
    else:
        print("    no 'ct' key -- calibration skipped")

    print("[5] the check: floor counts on 'U' (translated monomial weights)")
    if "U" not in ck:
        fail("no 'U' key in checkpoint")
    w, note = as_weights(ck["U"])
    if w is None:
        print("    could not read weights from U: %s" % note)
        print("    paste this whole output back; the probe will be")
        print("    finalized against the anatomy printed in [3].")
        sys.exit(0)
    nz = w[w > 0]
    print("    reading: %s, %d entries, max|w|=%.6f, min nonzero=%.3e"
          % (note, w.size, w.max(), nz.min() if nz.size else 0.0))
    got = floor_counts(w)
    pred = ("1108", "1108", "~1108", "~1219")
    for f, g, p in zip(FLOORS, got, pred):
        print("    floor %.0e : %5d   (pre-registered prediction %s)"
              % (f, g, p))
    print_bands(w)
    if not calibrated:
        print("    NOTE: calibration in [4] did not certify -- treat [5]")
        print("    as provisional until the reading is confirmed.")

    print("[6] chain-file anchors (%s)" % NPZ)
    if os.path.exists(NPZ):
        d = np.load(NPZ)
        if "th" in d.files:
            th = np.asarray(d["th"], dtype=float).ravel()
            print("    chain length %d (expect 3202), max|theta| %.6f "
                  "(expect 1.541729)" % (th.size, np.abs(th).max()))
        else:
            print("    fields: %s" % sorted(d.files))
    else:
        print("    not found -- skipped")

    print("done. read-only: nothing was written.")


if __name__ == "__main__":
    main()

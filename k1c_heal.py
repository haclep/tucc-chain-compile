#!/usr/bin/env python
"""k1c_heal.py -- remove files cut short by a machine stop, so the foundry
re-does exactly those pieces and nothing else.

A Spot preemption stops the machine with whatever was mid-write left
truncated on disk. Every artefact the foundry reads back is checked here:

    k1b/<member>_chain.npz          unreadable -> chain + its summary removed
                                    (the member re-runs)
    k1c_runs/<member>_summary.json  unreadable -> summary + chain removed
    k1c_runs/<member>_state.pkl     unreadable -> state + trace removed
                                    (the member starts over)
    k1c_runs/gauge_<stem>.json      unreadable -> removed (family re-reported)
    data/<stem>_target.npz          unreadable -> removed (recomputed)
    k1_corpus/<stem>.npz            unreadable -> dump + sidecar removed
                                    (the point is re-minted)
    k1_corpus/<stem>.json           unreadable -> sidecar removed
                                    (the dump is re-checked)

Run it before every launch; run_foundry.sh does. Reading every chain and
dump takes a minute or two on a full phase.

    python k1c_heal.py            # act
    python k1c_heal.py --dry-run  # only report
"""
import glob
import json
import os
import pickle
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DRY = "--dry-run" in sys.argv
removed = []


def rm(p, why):
    if os.path.exists(p):
        removed.append((p, why))
        if not DRY:
            os.remove(p)


def npz_ok(p, keys):
    try:
        z = np.load(p, allow_pickle=True)
        for k in keys:
            np.asarray(z[k])
        return True
    except Exception:
        return False


def json_ok(p):
    try:
        with open(p) as fh:
            json.load(fh)
        return True
    except Exception:
        return False


class _Stub:
    """Stands in for any class the checkpoint refers to (the compiler's
    Substitution, numpy internals): the stream's structure is what is
    being checked, not its contents."""
    def __init__(self, *a, **k):
        pass

    def __setstate__(self, state):
        pass


class _Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
        try:
            return super().find_class(module, name)
        except Exception:
            return _Stub


def pkl_ok(p):
    try:
        with open(p, "rb") as fh:
            _Unpickler(fh).load()
        return True
    except (EOFError, pickle.UnpicklingError, ValueError, IndexError,
            AttributeError, TypeError):
        return False
    except Exception:
        return True          # unreadable for another reason: leave it alone


def partner_summary(chain):
    tag = os.path.basename(chain)[:-len("_chain.npz")]
    return os.path.join(HERE, "k1c_runs", tag + "_summary.json")


def partner_chain(summary):
    tag = os.path.basename(summary)[:-len("_summary.json")]
    return os.path.join(HERE, "k1b", tag + "_chain.npz")


n = 0
for p in glob.glob(os.path.join(HERE, "k1b", "*_chain.npz")):
    n += 1
    if not npz_ok(p, ("subs_h", "subs_p", "th", "pivot")):
        rm(p, "truncated chain")
        rm(partner_summary(p), "summary of a truncated chain")
for p in glob.glob(os.path.join(HERE, "k1c_runs", "*_summary.json")):
    n += 1
    if not json_ok(p):
        rm(p, "truncated summary")
        rm(partner_chain(p), "chain of a truncated summary")
for p in glob.glob(os.path.join(HERE, "k1c_runs", "*_state.pkl")):
    n += 1
    if not pkl_ok(p):
        rm(p, "truncated checkpoint")
        rm(p[:-len("_state.pkl")] + "_trace.jsonl", "trace of a truncated checkpoint")
for p in glob.glob(os.path.join(HERE, "k1c_runs", "gauge_*.json")):
    n += 1
    if not json_ok(p):
        rm(p, "truncated family report")
for p in glob.glob(os.path.join(HERE, "data", "*_target.npz")):
    n += 1
    if not npz_ok(p, ("v0", "e0")):
        rm(p, "truncated target cache")
for p in glob.glob(os.path.join(HERE, "k1_corpus", "*.npz")):
    n += 1
    if not npz_ok(p, ("h_mo", "eri_mo", "e_nuc", "e_scf")):
        rm(p, "truncated dump")
        rm(p[:-4] + ".json", "sidecar of a truncated dump")
for p in glob.glob(os.path.join(HERE, "k1_corpus", "*.json")):
    if os.path.basename(p) == "index.json":
        continue
    n += 1
    if not json_ok(p):
        rm(p, "truncated sidecar")
# leftovers of atomic writes that never completed
for p in glob.glob(os.path.join(HERE, "**", "*.tmp*"), recursive=True):
    rm(p, "unfinished temporary file")

for p, why in removed:
    print("%s  %s: %s" % ("would remove" if DRY else "removed", os.path.relpath(p, HERE), why))
print("heal: %d file(s) checked, %d %s" % (n, len(removed), "would be removed" if DRY else "removed"))

#!/usr/bin/env python
"""k1c_gauge.py -- the gauge-orbit factory.

Produces many CERTIFIED factorizations of ONE exact state by varying
compiler conventions. Every member reaches the same gate (squared
residual < 1e-12 by default, or --gate / K1_GATE) against the same
target, so membership in the family is proven rather than assumed. No compiler file is edited: the conventions
are run-time overrides in k1c_warmstart.py.

Axes varied (each a legitimate convention, none changes the state):

  pivot        which determinant is the reference. Routing, greedy
               ordering and everything downstream key off it, so this
               changes the whole chain including the routed prefix.
               The deepest axis available without touching the basis.
  support_tol  the amplitude threshold defining the support: fewer
               routed letters and more grown, or the reverse.
  tie_seed     the tie-break among candidates whose scores are equal
               within TIE_TOL. Only fires on genuine ties, which are
               common on symmetric systems and rare otherwise.
  warm start   which letters are proposed at the post-joint state and
               how many (pred-source, scale-mult, top) -- the axis the
               H6 sweep already showed produces distinct chains.
  prefix       how long the pre-insertion joint solve runs.
  plateau      the growth-round exit threshold.

Each member is a subprocess, so a failure costs one member and leaves no
state behind. Members already on disk are skipped, so the factory is
resumable.

Usage:
    python k1c_gauge.py k1_h6_ring_19 --plan quick        # ~24 members
    python k1c_gauge.py k1_h6_ring_19 --plan wide -j 6    # ~120 members
    python k1c_gauge.py --raced --plan quick -j 6
    python k1c_gauge.py k1_h6_ring_19 --report            # analyse only
    python k1c_gauge.py k1_h6_ring_19 --plan wide --dry-run
    python k1c_gauge.py --corpus k1_corpus --phase 1 --plan quick -j 56 --gate 1e-16
        # every dump k1c_corpus.py has minted for phase 1, smallest first;
        # finished systems (a gauge_<stem>.json report) are skipped
"""
import argparse
import glob
import hashlib
import itertools
import json
import os
import subprocess
import sys
import time
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "k1c_runs")
CHAINS = os.path.join(HERE, "k1b")
GATE = float(os.environ["K1_GATE"]) if "K1_GATE" in os.environ else None
RACED = ["k1_h6_chain_14", "k1_h6_chain_19", "k1_h6_chain_22",
         "k1_h6_chain_26", "k1_h6_chain_30", "k1_h6_chain_34",
         "k1_h6_ring_14", "k1_h6_ring_19", "k1_h6_ring_22",
         "k1_h6_ring_26", "k1_h6_ring_30", "k1_h6_ring_34"]


# ------------------------------------------------------------ the plans
def settings(plan):
    """Each setting is a dict of overrides. 'warm' picks the proposal;
    None means cold (no proposal), which is a legitimate member too."""
    warm = [("topk", 0.25), ("topk", 0.5), ("tangent", 0.25), None]
    if plan == "quick":
        piv = [0, 1, 2, 3, 5, 8]
        tol = [None]
        ties = [0]
        pre = [300]
        plat = [0.01]
    elif plan == "wide":
        piv = [0, 1, 2, 3, 4, 5, 6, 8, 10, 13, 17, 21]
        tol = [None, 1e-9, 1e-11]
        ties = [0, 7, 13]
        pre = [300, 10]
        plat = [0.01]
    elif plan == "deep":
        piv = list(range(0, 40))
        tol = [None, 1e-9, 1e-10, 1e-11]
        ties = [0, 3, 7, 13, 29]
        pre = [300, 40, 10]
        plat = [0.01, 0.02, 0.005]
    else:
        raise SystemExit("unknown plan " + plan)
    out = []
    for p, t, s, pr, pl, w in itertools.product(piv, tol, ties, pre, plat,
                                                warm):
        # keep the grid from exploding: vary one non-pivot axis at a time
        n_off = sum([t is not None, s != 0, pr != 300, pl != 0.01])
        if n_off > 1:
            continue
        out.append({"pivot_rank": p, "support_tol": t, "tie_seed": s,
                    "prejoint": pr, "plateau": pl, "warm": w})
    return out


def tag_of(st):
    w = st["warm"]
    t = "gauge"
    if w is None:
        t += "_cold"
    else:
        t += "_%s%g" % (w[0], w[1])
    if st["prejoint"] != 300:
        t += "_p%d" % st["prejoint"]
    if st["plateau"] != 0.01:
        t += "_pl%g" % st["plateau"]
    return t


def command(stem, st, deadline):
    w = st["warm"]
    cmd = [sys.executable, os.path.join(HERE, "k1c_warmstart.py"), stem,
           "--insert", "post-joint", "--target", "dense",
           "--deadline", str(deadline),
           "--prejoint-iters", str(st["prejoint"]),
           "--plateau", str(st["plateau"]),
           "--pivot-rank", str(st["pivot_rank"]),
           "--tie-seed", str(st["tie_seed"])]
    if st["support_tol"]:
        cmd += ["--support-tol", repr(st["support_tol"])]
    if GATE is not None:
        cmd += ["--gate", repr(GATE)]
    if w is None:
        cmd += ["--arm", "cold"]
    else:
        cmd += ["--arm", "pred", "--pred-source", w[0],
                "--scale-mult", str(w[1]), "--pred-tag", tag_of(st)[6:]]
    return cmd


def summary_path(stem, st):
    """Mirror k1c_warmstart._paths so finished members are skipped."""
    t = tag_of(st)
    arm = "cold" if st["warm"] is None else "pred_" + t[6:]
    name = "%s_%s_pj" % (stem, arm)
    if st["prejoint"] != 300:
        name += str(st["prejoint"])
    if st["pivot_rank"]:
        name += "_pv%d" % st["pivot_rank"]
    if st["support_tol"]:
        name += "_st%g" % st["support_tol"]
    if st["tie_seed"]:
        name += "_ts%d" % st["tie_seed"]
    return os.path.join(RUNS, name + "_summary.json")


# ------------------------------------------------------------ running
def last_trace_line(stem, st):
    """Phase and message of the member's last trace record, so a checkpoint
    resumption in the log says where the member stopped."""
    tpath = summary_path(stem, st)[:-len("_summary.json")] + "_trace.jsonl"
    try:
        with open(tpath, "rb") as fh:
            tail = fh.read()[-4000:].decode(errors="replace").strip().splitlines()
        rec = json.loads(tail[-1])
        return "stopped at phase '%s' after %.0fs: %s" % (
            rec.get("phase"), rec.get("t_inv", 0), rec.get("msg", ""))
    except Exception:
        return "no trace on disk"


def run_all(stem, sts, jobs, deadline, dry):
    todo = [st for st in sts if not os.path.exists(summary_path(stem, st))]
    print("%s: %d settings, %d already on disk, %d to run"
          % (stem, len(sts), len(sts) - len(todo), len(todo)))
    if dry:
        for st in todo[:5]:
            print("   ", " ".join(command(stem, st, deadline)[2:]))
        if len(todo) > 5:
            print("    ... and %d more" % (len(todo) - 5))
        return
    # A member that reaches its deadline exits CLEANLY with its state saved
    # and no summary: that is a checkpoint, not a failure, and the same
    # command resumes it. Re-queue such members up to MAX_TRIES, exactly as
    # the campaign loop re-invokes an arm. Only a non-zero exit is a failure.
    # The target is computed ONCE here and cached, so the members (which
    # may start 50 at a time) all read the same vector instead of each
    # diagonalizing the dump.
    prep = subprocess.run([sys.executable, os.path.join(HERE, "k1c_warmstart.py"),
                           stem, "--prepare-target", "--target", "dense"],
                          capture_output=True, text=True)
    print("  " + (prep.stdout.strip().splitlines() or ["(no output)"])[-1])
    if prep.returncode != 0:
        print("  target preparation FAILED for %s:\n    %s"
              % (stem, prep.stderr.strip().replace("\n", "\n    ")[-1500:]))
        return
    # A pivot rank beyond the state's support points at a determinant of
    # zero amplitude, which the compiler rightly refuses; such settings are
    # dropped here rather than launched (H2 has a support of 2).
    try:
        v0 = np.load(os.path.join(HERE, "data", stem + "_target.npz"))["v0"]
        support = int(np.sum(np.abs(v0) > 1e-10))
    except Exception:
        support = None          # the members recompute the target themselves
    if support is not None:
        keep = [st for st in todo if st["pivot_rank"] < support]
        if len(keep) < len(todo):
            print("  %d setting(s) dropped: pivot rank beyond the support of %d "
                  "determinants" % (len(todo) - len(keep), support))
            todo = keep
    MAX_TRIES = 40
    running, ok, bad, resumed = [], 0, 0, 0
    queue = [(st, 1) for st in todo]
    while queue or running:
        while queue and len(running) < jobs:
            st, tries = queue.pop(0)
            p = subprocess.Popen(command(stem, st, deadline),
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.PIPE)
            running.append((p, st, tries))
        done = [x for x in running if x[0].poll() is not None]
        if not done:
            time.sleep(2.0)
            continue
        for p, st, tries in done:
            running.remove((p, st, tries))
            err = p.stderr.read().decode(errors="replace")
            if os.path.exists(summary_path(stem, st)):
                ok += 1
            elif p.returncode == 0 and tries < MAX_TRIES:
                queue.append((st, tries + 1))       # checkpoint: resume it
                resumed += 1
                print("  resuming pivot %d warm %s (try %d): %s"
                      % (st["pivot_rank"], st["warm"], tries + 1,
                         last_trace_line(stem, st)))
            else:
                bad += 1
                why = ("exit %d" % p.returncode if p.returncode
                       else "no summary after %d attempts" % tries)
                print("  FAILED pivot %d tol %s tie %d warm %s (%s)\n    %s"
                      % (st["pivot_rank"], st["support_tol"], st["tie_seed"],
                         st["warm"], why,
                         err.replace("\n", " ")[-300:] or "(no stderr)"))
        print("  %d done, %d failed, %d resumed, %d running, %d queued   "
              % (ok, bad, resumed, len(running), len(queue)), end="\r")
    print("\n%s: %d certified members produced, %d failed, %d checkpoint "
          "resumptions" % (stem, ok, bad, resumed))


# ------------------------------------------------------------ the family
def load_members(stem):
    """Every certified chain for this state now on disk, with provenance."""
    out = {}
    for p in sorted(glob.glob(os.path.join(CHAINS, stem + "_*_chain.npz"))):
        tag = os.path.basename(p)[len(stem) + 1:-len("_chain.npz")]
        sp = os.path.join(RUNS, "%s_%s_summary.json" % (stem, tag))
        try:
            d = np.load(p, allow_pickle=True)
            word = [(tuple(int(q) for q in h), tuple(int(q) for q in pp))
                    for h, pp in zip(d["subs_h"], d["subs_p"])]
            th = [float(t) for t in d["th"]]
            meta = json.load(open(sp)) if os.path.exists(sp) else {}
        except Exception as ex:
            # A file cut short by a preemption. Drop the member's chain AND
            # summary so the factory re-runs it instead of counting it.
            print("  unreadable member %s (%s): removed, will be re-run"
                  % (os.path.basename(p), ex.__class__.__name__))
            for q in (p, sp):
                if os.path.exists(q):
                    os.remove(q)
            continue
        out[tag] = {"word": word, "th": th, "meta": meta}
    return out


def depth(word):
    last, d = {}, 0
    for hh, pp in word:
        layer = 1 + max((last.get(q, 0) for q in hh + pp), default=0)
        for q in hh + pp:
            last[q] = layer
        d = max(d, layer)
    return d


def f1(a, b):
    ca, cb = Counter(a), Counter(b)
    inter = sum((ca & cb).values())
    if not inter:
        return 0.0
    p, r = inter / sum(ca.values()), inter / sum(cb.values())
    return 2 * p * r / (p + r)


def report(stem):
    M = load_members(stem)
    if len(M) < 2:
        print("%s: %d member(s); nothing to compare" % (stem, len(M)))
        return None
    hashes = {}
    for tag, m in M.items():
        h = hashlib.blake2b(repr(m["word"]).encode(), digest_size=8).hexdigest()
        hashes.setdefault(h, []).append(tag)
    distinct = {v[0]: M[v[0]] for v in hashes.values()}
    tags = sorted(distinct)
    lens = np.array([len(distinct[t]["word"]) for t in tags])
    deps = np.array([depth(distinct[t]["word"]) for t in tags])
    piv = {t: distinct[t]["meta"].get("seed_provenance", {}).get("pivot_rank", 0)
           for t in tags}
    npiv = len(set(piv.values()))
    fs = [f1(distinct[a]["word"], distinct[b]["word"])
          for i, a in enumerate(tags) for b in tags[i + 1:]]
    core = Counter(distinct[tags[0]]["word"])
    union = Counter()
    for t in tags:
        core &= Counter(distinct[t]["word"])
        union |= Counter(distinct[t]["word"])
    fs = np.array(fs)
    print("\n=== %s family ===" % stem)
    print("members on disk %d | distinct chains %d | duplicate groups %d"
          % (len(M), len(distinct), sum(1 for v in hashes.values() if len(v) > 1)))
    print("pivots used %d | length %d-%d (median %d) | depth %d-%d (median %d)"
          % (npiv, lens.min(), lens.max(), int(np.median(lens)),
             deps.min(), deps.max(), int(np.median(deps))))
    print("pairwise content F1 over %d pairs: mean %.3f, median %.3f, "
          "min %.3f, max %.3f" % (len(fs), fs.mean(), np.median(fs),
                                  fs.min(), fs.max()))
    print("invariant core %d letters (%d distinct) of a union of %d (%d "
          "distinct); core is %.1f%% of the median member"
          % (sum(core.values()), len(core), sum(union.values()), len(union),
             100.0 * sum(core.values()) / max(1, int(np.median(lens)))))
    os.makedirs(RUNS, exist_ok=True)
    out = {"stem": stem, "members": len(M), "distinct": len(distinct),
           "pivots": npiv, "len": [int(lens.min()), int(lens.max())],
           "depth": [int(deps.min()), int(deps.max())],
           "f1_mean": float(fs.mean()), "f1_min": float(fs.min()),
           "f1_max": float(fs.max()), "core_mass": sum(core.values()),
           "core_distinct": len(core), "union_mass": sum(union.values()),
           "tags": tags}
    with open(os.path.join(RUNS, "gauge_%s.json" % stem), "w") as fh:
        json.dump(out, fh, indent=1)
    return out


def readable_json(p):
    """True if p exists and parses; a truncated report is removed so the
    family is reported again."""
    if not os.path.exists(p):
        return False
    try:
        with open(p) as fh:
            json.load(fh)
        return True
    except Exception:
        os.remove(p)
        return False


def corpus_stems(corpus_dir, phases=None):
    """Stems from k1_corpus/index.json, smallest sector first, optionally
    restricted to some atlas phases. Dumps that are not on disk are skipped."""
    p = os.path.join(corpus_dir, "index.json")
    if not os.path.exists(p):
        raise SystemExit("no %s; run k1c_corpus.py first" % p)
    with open(p) as fh:
        idx = json.load(fh)
    rows = []
    for stem, e in idx.items():
        if e.get("status") != "done":
            continue
        if phases and e.get("phase") not in phases:
            continue
        if not os.path.exists(os.path.join(corpus_dir, stem + ".npz")):
            continue
        rows.append((e.get("sector_dimension", 0), stem))
    rows.sort()
    print("%d system(s) from %s%s" % (len(rows), p,
          " (phase %s)" % " ".join(map(str, phases)) if phases else ""))
    return [s for _, s in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--raced", action="store_true")
    ap.add_argument("--plan", choices=["quick", "wide", "deep"], default=None)
    ap.add_argument("-j", "--jobs", type=int, default=4)
    ap.add_argument("--deadline", type=float, default=3600,
                    help="seconds per invocation; a member that reaches it\n                         checkpoints and is resumed, so this only sets\n                         how often state is written")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--gate", type=float, default=None,
                    help="certification gate on |r|^2 passed to every member "
                         "(default: K1_GATE env var, else the harness's 1e-12)")
    ap.add_argument("--corpus", default=None,
                    help="k1_corpus directory: take the stems from its "
                         "index.json (written by k1c_corpus.py)")
    ap.add_argument("--phase", type=int, nargs="*", default=None,
                    help="with --corpus: only these atlas phases")
    ap.add_argument("--shard", default=None,
                    help="K/N: take every N-th system starting at K (0-based), "
                         "so N gauge processes can share one machine without "
                         "touching the same system")
    a = ap.parse_args()
    global GATE
    if a.gate is not None:
        GATE = a.gate
    names = list(a.names) + (RACED if a.raced else [])
    if a.corpus:
        names += corpus_stems(a.corpus, a.phase)
    if a.shard:
        k, n = (int(x) for x in a.shard.split("/"))
        names = names[k::n]
        print("shard %d of %d: %d system(s)" % (k, n, len(names)))
    if not names:
        raise SystemExit("give system names, --raced, or --corpus DIR")
    if GATE is not None:
        print("gate for every member: %g" % GATE)
    for n in names:
        if a.corpus and a.plan and not a.dry_run and \
                readable_json(os.path.join(RUNS, "gauge_%s.json" % n)):
            continue                        # family already produced and reported
        if a.plan:
            run_all(n, settings(a.plan), a.jobs, a.deadline, a.dry_run)
        if a.report or (a.plan and not a.dry_run):
            report(n)


if __name__ == "__main__":
    main()

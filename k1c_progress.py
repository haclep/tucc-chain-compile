#!/usr/bin/env python
"""k1c_progress.py -- what the foundry is doing right now, member by member.

status.sh answers "is it running"; this answers "is it getting anywhere":
which family each shard is on, which members are in flight and where
each one is in its solve, how much the finished members cost, and a
rough forecast for the rest of the phase from those costs.

    python k1c_progress.py              # phase 1, quick plan (the foundry's defaults)
    python k1c_progress.py --phase 2 --plan wide
    python k1c_progress.py --all        # every family, not just the ones in flight

Reads k1_corpus/index.json, k1c_runs/, logs/gauge_*.log and the process
table. Writes nothing.
"""
import argparse
import glob
import json
import os
import pickle
import re
import subprocess
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import k1c_gauge as kg                                    # noqa: E402

HERE = kg.HERE
RUNS = kg.RUNS
NOW = time.time()


# ------------------------------------------------------------ helpers
def age(t):
    """Seconds -> '4 min', '3h12m', '2d 5h'."""
    if t is None:
        return "?"
    t = int(t)
    if t < 60:
        return "%ds" % t
    if t < 3600:
        return "%d min" % (t // 60)
    if t < 86400:
        return "%dh%02dm" % (t // 3600, (t % 3600) // 60)
    return "%dd %dh" % (t // 86400, (t % 86400) // 3600)


def hours(s):
    if s < 60:
        return "%.0f s" % s
    if s < 3600:
        return "%.1f min" % (s / 60)
    if s < 86400:
        return "%.1f h" % (s / 3600)
    return "%.1f d" % (s / 86400)


def read_trace(path):
    """Records of a member's trace, total compute seconds (the trace holds
    every invocation; t_inv restarts at each resumption), and the number
    of resumptions. Lines cut short by a preemption are skipped."""
    recs = []
    try:
        with open(path) as fh:
            for line in fh:
                try:
                    recs.append(json.loads(line))
                except Exception:
                    pass
    except OSError:
        return [], 0.0, 0
    total, seg, prev, resumes = 0.0, 0.0, -1.0, 0
    for r in recs:
        t = float(r.get("t_inv", 0.0))
        if t < prev:
            total += seg
            seg = 0.0
            resumes += 1
        seg = max(seg, t)
        prev = t
    return recs, total + seg, resumes


class _Stub:
    def __init__(self, *a, **k):
        pass

    def __setstate__(self, state):
        pass


class _Unpickler(pickle.Unpickler):
    """Reads a checkpoint without the compiler's classes (they become stubs);
    the counters at the top level are all that is wanted here."""
    def find_class(self, module, name):
        try:
            return super().find_class(module, name)
        except Exception:
            return _Stub


def state_info(path):
    """(invocations so far, phase) from a checkpoint, or (None, None)."""
    try:
        with open(path, "rb") as fh:
            st = _Unpickler(fh).load()
        return int(st.get("k1b", {}).get("invocations", 0)), st.get("phase")
    except Exception:
        return None, None


def member_key(stem, st):
    w = st["warm"]
    return (stem, st["pivot_rank"], "cold" if w is None else "%s%g" % w)


def warm_name(st):
    w = st["warm"]
    return "cold" if w is None else "%s %g" % w


def processes():
    """Solver processes now alive: member key -> (elapsed s, cpu %); the
    number of family (gauge) processes is stored under the key None."""
    out = {}
    try:
        txt = subprocess.run(["ps", "-eo", "etimes,pcpu,args"],
                             capture_output=True, text=True).stdout
    except Exception:
        return out
    n_gauge = 0
    for line in txt.splitlines():
        if "k1c_gauge.py" in line:
            n_gauge += 1
        if "k1c_warmstart.py" not in line or "--prepare-target" in line:
            continue
        parts = line.split()
        try:
            et, cpu = float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            continue
        args = parts[2:]
        try:
            i = [j for j, a in enumerate(args) if a.endswith("k1c_warmstart.py")][0]
            stem = args[i + 1]
            piv = int(args[args.index("--pivot-rank") + 1])
            if "--pred-source" in args:
                w = "%s%g" % (args[args.index("--pred-source") + 1],
                              float(args[args.index("--scale-mult") + 1]))
            else:
                w = "cold"
        except (ValueError, IndexError, StopIteration):
            continue
        out[(stem, piv, w)] = (et, cpu)
    out[None] = n_gauge
    return out


def shard_logs():
    """For each logs/gauge_K.log: the family it is on and its counters."""
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, "logs", "gauge_*.log"))):
        try:
            with open(p, errors="replace") as fh:
                txt = fh.read()
        except OSError:
            continue
        pieces = [x for x in re.split(r"[\r\n]", txt) if x.strip()]
        stem, counters, failed = None, None, []
        for x in pieces:
            m = re.match(r"^(\S+): (\d+) settings, (\d+) already on disk, (\d+) to run", x)
            if m:
                stem, counters, failed = m.group(1), None, []
                continue
            if x.strip().startswith("FAILED pivot"):
                failed.append(x.strip())
            m = re.match(r"^\s*(\d+) done, (\d+) failed, (\d+) resumed, (\d+) running, (\d+) queued", x)
            if m:
                counters = tuple(int(v) for v in m.groups())
        out.append((os.path.basename(p), stem, counters, failed))
    return out


def all_failures():
    """Every FAILED line in the gauge logs with the family it belongs to
    and the stderr tail printed under it."""
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, "logs", "gauge_*.log"))):
        try:
            with open(p, errors="replace") as fh:
                txt = fh.read()
        except OSError:
            continue
        lines = [x.split("\r")[-1] for x in txt.split("\n")]
        stem = None
        for i, x in enumerate(lines):
            m = re.match(r"^(\S+): \d+ settings,", x)
            if m:
                stem = m.group(1)
            if x.strip().startswith("FAILED pivot"):
                why = lines[i + 1].strip() if i + 1 < len(lines) else ""
                out.append((stem, x.strip(), why))
    return out


# ------------------------------------------------------------ the survey
def survey(phase, plan, only_started):
    """One row per family of the phase, smallest sector first."""
    p = os.path.join(HERE, "k1_corpus", "index.json")
    if not os.path.exists(p):
        raise SystemExit("no %s; nothing has been minted here" % p)
    with open(p) as fh:
        idx = json.load(fh)
    sts = kg.settings(plan)
    rows = []
    for stem, e in idx.items():
        if e.get("status") != "done" or (phase and e.get("phase") != phase):
            continue
        if not os.path.exists(os.path.join(HERE, "k1_corpus", stem + ".npz")):
            continue
        planned = kg.pending(stem, sts) + \
            [st for st in sts if os.path.exists(kg.summary_path(stem, st))]
        members = []
        for st in planned:
            sp = kg.summary_path(stem, st)
            tp = sp[:-len("_summary.json")] + "_trace.jsonl"
            done = os.path.exists(sp)
            started = done or os.path.exists(tp)
            members.append({"st": st, "key": member_key(stem, st), "done": done,
                            "started": started, "summary": sp, "trace": tp})
        n_done = sum(m["done"] for m in members)
        reported = os.path.exists(os.path.join(RUNS, "gauge_%s.json" % stem))
        rows.append({"stem": stem, "label": e.get("label", "?"),
                     "dim": int(e.get("sector_dimension", 0)),
                     "members": members, "n": len(members), "done": n_done,
                     "started": sum(m["started"] for m in members),
                     "reported": reported and n_done == len(members)})
    rows.sort(key=lambda r: (r["dim"], r["stem"]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", type=int, default=1)
    ap.add_argument("--plan", default="quick")
    ap.add_argument("--all", action="store_true", help="list every family")
    ap.add_argument("--hours", type=float, default=24.0,
                    help="window for the 'recent' line")
    a = ap.parse_args()

    rows = survey(a.phase, a.plan, not a.all)
    n_fam = len(rows)
    n_rep = sum(r["reported"] for r in rows)
    n_mem = sum(r["n"] for r in rows)
    n_done = sum(r["done"] for r in rows)
    print("=== foundry progress  %s   phase %d, plan %s (%d members per family)"
          % (time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(NOW)), a.phase, a.plan,
             len(kg.settings(a.plan))))
    print("families   %d complete of %d          members  %d certified of %d (%.0f%%)"
          % (n_rep, n_fam, n_done, n_mem, 100.0 * n_done / max(n_mem, 1)))

    # ---- recent activity, from summary and report mtimes
    win = a.hours * 3600
    recent, newest, fam_recent = 0, None, 0
    for r in rows:
        for m in r["members"]:
            if not m["done"]:
                continue
            try:
                t = os.path.getmtime(m["summary"])
            except OSError:
                continue
            if NOW - t < win:
                recent += 1
            newest = t if newest is None else max(newest, t)
        if r["reported"]:
            try:
                if NOW - os.path.getmtime(os.path.join(RUNS, "gauge_%s.json" % r["stem"])) < win:
                    fam_recent += 1
            except OSError:
                pass
    print("last %s  %d members certified, %d families completed; newest certificate %s ago"
          % (age(win) if a.hours != 24 else "24 h", recent, fam_recent,
             age(NOW - newest) if newest else "never"))

    # ---- workers
    procs = processes()
    n_gauge = procs.pop(None, 0)
    if procs:
        busy = sum(1 for et, cpu in procs.values() if cpu >= 50)
        print("workers    %d solver processes alive, %d busy (>=50%% cpu), longest running %s; %d family processes"
              % (len(procs), busy, age(max(et for et, _ in procs.values())), n_gauge))
    else:
        print("workers    no solver process alive; %d family processes" % n_gauge)

    # ---- in flight
    shards = shard_logs()
    live_stems = set(k[0] for k in procs)
    on_shard = set(s[1] for s in shards if s[1])
    running = [r for r in rows if r["stem"] in live_stems or
               (r["stem"] in on_shard and not r["reported"])]
    leftover = [r for r in rows if r["started"] and not r["reported"] and r not in running]

    def family_line(r):
        shard = next((s[0].replace(".log", "") for s in shards if s[1] == r["stem"]), "")
        n_run = sum(1 for m in r["members"] if m["key"] in procs)
        failed = next((len(s[3]) for s in shards if s[1] == r["stem"]), 0)
        waiting = r["started"] - r["done"] - n_run
        queued = r["n"] - r["started"]
        print("  %-8s %-24s dim %-6d %2d of %2d done, %d running, %d checkpointed and waiting, %d queued, %d failed"
              % (shard, r["stem"], r["dim"], r["done"], r["n"], n_run, waiting, queued, failed))

    def member_lines(r):
        for m in r["members"]:
            if m["done"] or not m["started"]:
                continue
            recs, tot, res = read_trace(m["trace"])
            last = recs[-1] if recs else {}
            try:
                tage = NOW - os.path.getmtime(m["trace"])
            except OSError:
                tage = None
            pr = procs.get(m["key"])
            state = ("running, cpu %.0f%%" % pr[1]) if pr else "waiting for a slot"
            inv, _ = state_info(m["trace"][:-len("_trace.jsonl")] + "_state.pkl")
            res = (inv - 1) if inv else res
            rn = last.get("rn")
            print("           pv%-2d %-12s %-7s len %-5s |r| %-9s  %s in, %d resumption%s, last record %s ago  [%s]"
                  % (m["st"]["pivot_rank"], warm_name(m["st"]), last.get("phase", "?"),
                     last.get("len", "?"), ("%.1e" % rn) if isinstance(rn, (int, float)) else "?",
                     hours(tot), res, "" if res == 1 else "s", age(tage), state))
            if res >= 3 and tot < 120.0 * res:
                stuck.append((r["stem"], m["st"]["pivot_rank"], warm_name(m["st"])))

    stuck = []
    print("\nin flight now" + ("" if n_gauge else "  (no family process alive: this is where it stopped)"))
    if not running:
        print("  nothing")
    for r in running:
        family_line(r)
        member_lines(r)
    if stuck:
        print("\n  WARNING: %d member(s) keep checkpointing without doing work (many resumptions, "
              "almost no compute):" % len(stuck))
        for stem, pv, w in stuck:
            print("    %s pv%d %s" % (stem, pv, w))
        print("    The solver checkpoints when it judges one slice of iterations will not fit before the "
              "deadline, so on a system this size DEADLINE is too short. Relaunch with a larger "
              "DEADLINE (for example DEADLINE=14400); nothing is lost.")
    if leftover:
        print("\npartly done, not being worked on (a shard picks these up when it reaches them, "
              "or at the next launch)")
        for r in leftover:
            family_line(r)
            if a.all:
                member_lines(r)
    if a.all:
        print("\nevery family")
        for r in rows:
            print("  %-24s dim %-6d %2d of %2d %s" % (r["stem"], r["dim"], r["done"], r["n"],
                                                     "complete" if r["reported"] else ""))

    # ---- cost so far, per label
    by_label = defaultdict(list)
    dim_of = {}
    for r in rows:
        dim_of[r["label"]] = r["dim"]
        for m in r["members"]:
            if m["done"]:
                _, tot, _ = read_trace(m["trace"])
                if tot > 0:
                    by_label[r["label"]].append(tot)
    print("\ncost per certified member so far (average compute time, by system;"
          " warm-started members are cheap, cold ones carry the cost)")
    fit_x, fit_y = [], []
    spent = 0.0
    avg_of = {}
    for label in sorted(by_label, key=lambda l: dim_of[l]):
        v = sorted(by_label[label])
        avg = sum(v) / len(v)
        avg_of[label] = avg
        spent += sum(v)
        print("  dim %-6d %-14s avg %-10s over %d members (slowest %s)"
              % (dim_of[label], label, hours(avg), len(v), hours(v[-1])))
        if dim_of[label] >= 200 and len(v) >= 8:
            import math
            fit_x.append(math.log(dim_of[label]))
            fit_y.append(math.log(avg))
    print("  compute spent on certified members: %s of worker time" % hours(spent))

    # ---- forecast
    remaining = [(r["label"], r["dim"], r["n"] - r["done"]) for r in rows if r["done"] < r["n"]]
    n_rem = sum(x[2] for x in remaining)
    if procs:
        workers, note = len(procs), ""
    else:
        workers, note = max((os.cpu_count() or 3) - 2, 1), " (none alive; assumed from the core count)"
    print("\nremaining: %d families, %d members, on %d workers%s" % (
        sum(1 for r in rows if not r["reported"]), n_rem, workers, note))
    if by_label:
        # (a) flat: every remaining member costs what the most expensive
        #     finished system's members cost
        top = max(by_label, key=lambda l: dim_of[l])
        flat = avg_of[top] * n_rem
        print("  if every remaining member cost what a %s member costs (%s):  %s of worker time -> about %s wall"
              % (top, hours(avg_of[top]), hours(flat), hours(flat / workers)))
        # (b) what the members still in flight are costing: the first members
        #     of a family to finish are its cheapest, so (a) is a floor
        run_tot = [read_trace(m["trace"])[1] for r in rows for m in r["members"]
                   if m["started"] and not m["done"]]
        run_tot = [t for t in run_tot if t > 0]
        if run_tot:
            print("  members in flight: %d, averaging %s of compute so far and not finished, so the "
                  "true cost at this size is above the %s average of the finished ones"
                  % (len(run_tot), hours(sum(run_tot) / len(run_tot)), hours(avg_of[top])))
        print("  the cost of a member is set by its chain length (the size of the state's support), "
              "not by the sector dimension alone; MnH and NH3 share a dimension and differ 6x.")

    # ---- failures
    fails = all_failures()
    if fails:
        print("\nmember failures in the logs (%d)" % len(fails))
        for stem, line, why in fails:
            print("  %s: %s\n      %s" % (stem, line, why[:200]))


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass

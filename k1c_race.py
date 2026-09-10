#!/usr/bin/env python
"""k1c_race.py -- run K1c arms on a list of systems and tabulate rotations
to the gate from k1c_runs/*_summary.json.

    python k1c_race.py k1_h6_chain_19 k1_h6_ring_19            # file arms
    python k1c_race.py --live k1_h6_chain_19 k1_h6_ring_19     # live tangent sweep
    python k1c_race.py --table-only                             # table only
    python k1c_race.py --arms cold tangent_quarter k1_h6_ring_19

File arms (need k1c_proposals from k1c_model.py --write-proposals):
  cold, tangent, model_s0, poolall, oracle_content
Live arms (computed at the insertion state, no file):
  tangent_live (pool-sized), tangent_half, tangent_quarter, tangent_double,
  poolall_live
All arms run under post-joint insertion with a dense target. The table
lists every arm found, cold first.
"""
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILE_ARMS = {
    "cold": ["--arm", "cold"],
    "tangent": ["--arm", "pred", "--pred-tag", "tangent"],
    "model_s0": ["--arm", "pred", "--pred-tag", "model_s0"],
    "poolall": ["--arm", "pred", "--pred-tag", "poolall"],
    "oracle_content": ["--arm", "oracle_content"],
}
LIVE_ARMS = {
    "tangent_live": ["--arm", "pred", "--pred-source", "tangent",
                     "--pred-tag", "tangent_live"],
    "tangent_half": ["--arm", "pred", "--pred-source", "tangent",
                     "--scale-mult", "0.5", "--pred-tag", "tangent_half"],
    "tangent_quarter": ["--arm", "pred", "--pred-source", "tangent",
                        "--scale-mult", "0.25", "--pred-tag", "tangent_quarter"],
    "tangent_double": ["--arm", "pred", "--pred-source", "tangent",
                       "--scale-mult", "2.0", "--pred-tag", "tangent_double"],
    "poolall_live": ["--arm", "pred", "--pred-source", "poolall",
                     "--pred-tag", "poolall_live"],
    "topk_quarter": ["--arm", "pred", "--pred-source", "topk",
                     "--scale-mult", "0.25", "--pred-tag", "topk_quarter"],
    "topk_half": ["--arm", "pred", "--pred-source", "topk",
                  "--scale-mult", "0.5", "--pred-tag", "topk_half"],
    "cold40": ["--arm", "cold", "--prejoint-iters", "40"],
    "topk_quarter40": ["--arm", "pred", "--pred-source", "topk",
                       "--scale-mult", "0.25", "--pred-tag", "topk_quarter",
                       "--prejoint-iters", "40"],
    "cold20": ["--arm", "cold", "--prejoint-iters", "20"],
    "topk_quarter20": ["--arm", "pred", "--pred-source", "topk",
                       "--scale-mult", "0.25", "--pred-tag", "topk_quarter",
                       "--prejoint-iters", "20"],
    "cold10": ["--arm", "cold", "--prejoint-iters", "10"],
    "topk_quarter10": ["--arm", "pred", "--pred-source", "topk",
                       "--scale-mult", "0.25", "--pred-tag", "topk_quarter",
                       "--prejoint-iters", "10"],
}


def run(stem, arms):
    for name in arms:
        extra = FILE_ARMS.get(name) or LIVE_ARMS.get(name)
        if extra is None:
            print("unknown arm", name)
            continue
        cmd = [sys.executable, os.path.join(HERE, "k1c_warmstart.py"), stem,
               "--insert", "post-joint", "--target", "dense"] + extra
        if name in ("tangent", "model_s0", "poolall"):
            cmd += ["--pred-file", os.path.join(HERE, "k1c_proposals",
                                                "%s_%s.pkl" % (stem, name))]
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE, text=True)
        if r.returncode != 0:
            print("FAILED %s %s:\n%s" % (stem, name, r.stderr[-1500:]))


def table():
    rows = {}
    for p in glob.glob(os.path.join(HERE, "k1c_runs", "*_summary.json")):
        s = json.load(open(p))
        tag = os.path.basename(p)[:-len("_summary.json")]
        stem = s["stem"]
        arm = tag[len(stem) + 1:].replace("_pj", "")
        if arm.startswith("pred_"):
            arm = arm[5:]
        rows.setdefault(stem, {})[arm] = s
    print("%-16s %-16s %12s %6s %6s %6s %6s %8s %12s %8s" % (
        "system", "arm", "rotations", "GNit", "rounds", "len", "seed",
        "saving", "k1b_cur", "sav_k1b"))
    for stem in sorted(rows):
        arms = rows[stem]
        order = sorted(arms, key=lambda a: (not a.startswith("cold"), a))
        for arm in order:
            s = arms.get(arm)
            if not s:
                continue
            # baseline: the cold run with the same prefix cap suffix, e.g.
            # "topk_quarter40" compares against "cold40", plain against "cold"
            suffix = ""
            m = re.search(r"(\d+)$", arm)
            if m and not arm.startswith("model_s") and arm != "cold":
                suffix = m.group(1)
            cs = arms.get("cold" + suffix) or arms.get("cold") or {}
            c = cs.get("cost_rot")
            ck = (cs.get("cost_rot", 0) + cs.get("rot_prep_uncharged", 0)) if cs else None
            tot = s["cost_rot"] + s.get("rot_prep_uncharged", 0)
            sav = "%+.1f%%" % (100 * (1 - s["cost_rot"] / c)) if c else "-"
            savk = "%+.1f%%" % (100 * (1 - tot / ck)) if ck else "-"
            print("%-16s %-16s %12d %6d %6d %6d %6d %8s %12d %8s" % (
                stem, arm, s["cost_rot"], s["cost_gn_iters"], s["rounds"],
                s["final_len"], s["n_seed"], sav, tot, savk))


if __name__ == "__main__":
    args = sys.argv[1:]
    arms = None
    if "--arms" in args:
        i = args.index("--arms")
        arms = []
        j = i + 1
        while j < len(args) and not args[j].startswith("--") \
                and not args[j].startswith("k1_") and args[j] != "h8_chain":
            arms.append(args[j])
            j += 1
        args = args[:i] + args[j:]
    live = "--live" in args
    stems = [a for a in args if not a.startswith("--")]
    if arms is None:
        arms = list(LIVE_ARMS) if live else list(FILE_ARMS)
    if "--table-only" not in args:
        for st in stems:
            run(st, arms)
    table()

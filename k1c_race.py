#!/usr/bin/env python
"""k1c_race.py -- run the K1c arms on a list of systems and tabulate
rotations to the gate from k1c_runs/*_summary.json.

    python k1c_race.py k1_h6_chain_19 k1_h6_ring_19          # run + table
    python k1c_race.py --table-only                           # table only
Arms: cold, tangent (predicted scale), model_s0, poolall, oracle_content,
all under post-joint insertion with a dense target. Proposal files come
from: python k1c_model.py --seeds 0 --write-proposals k1c_proposals
"""
import glob, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = [("cold", []), ("tangent", ["--arm", "pred", "--pred-tag", "tangent"]),
        ("model_s0", ["--arm", "pred", "--pred-tag", "model_s0"]),
        ("poolall", ["--arm", "pred", "--pred-tag", "poolall"]),
        ("oracle_content", ["--arm", "oracle_content"])]

def run(stem):
    for name, extra in ARMS:
        cmd = [sys.executable, os.path.join(HERE, "k1c_warmstart.py"), stem,
               "--insert", "post-joint", "--target", "dense"] + extra
        if name in ("tangent", "model_s0", "poolall"):
            cmd += ["--pred-file", os.path.join(HERE, "k1c_proposals",
                                                "%s_%s.pkl" % (stem, name))]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def table():
    rows = {}
    for p in glob.glob(os.path.join(HERE, "k1c_runs", "*_summary.json")):
        s = json.load(open(p)); tag = os.path.basename(p)[:-13]
        stem = s["stem"]; arm = tag[len(stem) + 1:].replace("_pj", "")
        if arm.startswith("pred_"): arm = arm[5:]
        rows.setdefault(stem, {})[arm] = s
    print("%-16s %-15s %12s %6s %6s %6s %6s %8s" % (
        "system", "arm", "rotations", "GNit", "rounds", "len", "seed", "saving"))
    for stem in sorted(rows):
        c = rows[stem].get("cold", {}).get("cost_rot")
        for arm in ("cold", "tangent", "model_s0", "poolall", "oracle_content"):
            s = rows[stem].get(arm)
            if not s: continue
            sav = "%+.1f%%" % (100 * (1 - s["cost_rot"] / c)) if c else "-"
            print("%-16s %-15s %12d %6d %6d %6d %6d %8s" % (
                stem, arm, s["cost_rot"], s["cost_gn_iters"], s["rounds"],
                s["final_len"], s["n_seed"], sav))

if __name__ == "__main__":
    stems = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--table-only" not in sys.argv:
        for st in stems: run(st)
    table()

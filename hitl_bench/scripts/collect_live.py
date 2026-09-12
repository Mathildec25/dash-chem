# -*- coding: utf-8 -*-
"""Collect what the chemists did on the live page into two tables.

Reads every forms/live/<chemist>__<benchmark>__seed<NN>.json written by
hitl_bench/live.py and writes:

    results/live_campaigns.csv   one row per chemist x campaign: where it ended,
                                 what the control ended at, experiments spent,
                                 how many alerts, how each was answered
    results/live_decisions.csv   one row per alert answered: the choice, P* at
                                 that moment, the justification, the imposed
                                 point and what the optimiser would have run

The comparison with the control is paired at equal experiment count: a
chemist's campaign is read at its last experiment, the control at that same
experiment, and again at the full budget. A stopped campaign is therefore
compared both to "the optimiser at the same point" and to "the optimiser left
to run", which is the open question of CLAUDE.md made visible rather than
settled here.

Usage, from the repository root:

    python -m hitl_bench.scripts.collect_live
"""

import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(HERE, "forms", "live")
ARMS = os.path.join(HERE, "results", "arms")
RESULTS = os.path.join(HERE, "results")


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main():
    campaigns, decisions = [], []
    for path in sorted(glob.glob(os.path.join(LIVE, "*__*__seed*.json"))):
        state = load(path)
        chemist, benchmark, seed = state["chemist"], state["benchmark"], state["seed"]
        parent = load(os.path.join(ARMS, "%s__no_hitl__seed%02d.json" % (benchmark, seed)))
        mx = parent["reference"]["max_hypervolume"]
        n = len(state["experiments"])
        own = state["experiments"][-1]["hypervolume"] / mx
        control_same = parent["experiments"][n - 1]["hypervolume"] / mx
        control_full = parent["experiments"][-1]["hypervolume"] / mx
        choices = [d["choice"] for d in state["decisions"]]
        campaigns.append({
            "chemist": chemist, "field": state.get("field", ""), "benchmark": benchmark,
            "seed": seed, "started": state["started"],
            "experiments": n, "budget": state["budget"],
            "stopped_at": state["stopped_at"], "mode_at_end": state["mode"],
            "final_fraction": round(own, 3),
            "control_at_same_experiment": round(control_same, 3),
            "control_at_full_budget": round(control_full, 3),
            "gain_vs_control_same": round(own - control_same, 3),
            "gain_vs_control_full": round(own - control_full, 3),
            "n_alerts": len(choices),
            "n_continue": choices.count("optimiser"),
            "n_imposed": choices.count("chemist"),
            "n_stop": choices.count("stop"),
            "unanswered_alert": state["pending_alert"]["experiment"] if state["pending_alert"] else None,
        })
        for d in state["decisions"]:
            decisions.append({
                "chemist": chemist, "benchmark": benchmark, "seed": seed,
                "at_experiment": d["at_experiment"], "p_star": round(d["p_star"], 3),
                "choice": d["choice"], "when": d["when"], "why": d.get("why", ""),
                "imposed_point": json.dumps(d["point"]) if d.get("point") else "",
                "optimiser_proposal": json.dumps(d.get("optimiser_proposal")),
            })

    os.makedirs(RESULTS, exist_ok=True)
    for name, rows in (("live_campaigns.csv", campaigns), ("live_decisions.csv", decisions)):
        if not rows:
            continue
        with open(os.path.join(RESULTS, name), "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    print("%d campaigns, %d decisions" % (len(campaigns), len(decisions)))
    for c in campaigns:
        print("  %-10s %-18s seed %2d | %2d/%d exp | ends %5.1f %% | control %5.1f %% at same exp, "
              "%5.1f %% at 40 | alerts %d: continue %d, imposed %d, stop %d%s"
              % (c["chemist"], c["benchmark"], c["seed"], c["experiments"], c["budget"],
                 100 * c["final_fraction"], 100 * c["control_at_same_experiment"],
                 100 * c["control_at_full_budget"], c["n_alerts"], c["n_continue"],
                 c["n_imposed"], c["n_stop"],
                 " | UNANSWERED alert at %d" % c["unanswered_alert"] if c["unanswered_alert"] else ""))
    empty = sum(1 for d in decisions if not d["why"].strip())
    if empty:
        print("%d of %d decisions carry no justification" % (empty, len(decisions)))


if __name__ == "__main__":
    main()

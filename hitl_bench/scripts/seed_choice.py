# -*- coding: utf-8 -*-
"""Which seed to hand the chemists, for each of the three benchmarks of the human study.

The human study is a case study on trapped initial designs (CLAUDE.md, 12
September): the initial design alone decides whether plain BO ends on the front,
so the campaign each chemist receives is chosen by its seed. This script lays
out what that choice rests on, one figure and one table per benchmark:

    figures/seed_choice_<benchmark>.png   the hypervolume curve of every control
                                          campaign, alerts of the frozen trigger
                                          marked, trapped campaigns in orange
    results/seed_choice_<benchmark>.csv   one row per seed: how often the
                                          front-carrying ligand was drawn in the
                                          initial design, what it yielded there,
                                          where the campaign ends, when the
                                          trigger first calls

The suggestion printed at the end is a heuristic, not a decision: trapped,
alerted with enough budget left for an intervention to matter, and with the
front ligand present in the initial design so that a chemist reading the data
could notice it was dismissed. The study owner chooses.

Usage, from the repository root:

    python -m hitl_bench.scripts.seed_choice
"""

import collections
import csv
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hitl_bench import triggers
from hitl_bench.scripts.make_chemist_form import catalyst_names, label_value

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = os.path.join(HERE, "results", "arms")
RESULTS = os.path.join(HERE, "results")
FIGURES = os.path.join(HERE, "figures")

BENCHMARKS = ["i", "ii", "edbo_ch_arylation"]
TITLES = {"i": "Suzuki — cas I", "ii": "Suzuki — cas II",
          "edbo_ch_arylation": "Arylation C–H (EDBO+)"}
TARGET = 0.90                     # same "reached the front" threshold as the reports
LATEST_USEFUL_ALERT = 22          # an alert later than this leaves under 18 experiments
ECHEC, REUSSITE, ALERTE = "#eb6834", "#2a78d6", "#c1121f"


def load_controls(benchmark):
    out = []
    for path in sorted(glob.glob(os.path.join(ARMS, "%s__no_hitl__seed*.json" % benchmark))):
        if "__rep" in os.path.basename(path):
            continue
        with open(path, encoding="utf-8") as handle:
            out.append(json.load(handle))
    return out


def ligand_name(code, names):
    return label_value("ligand", code, names).split(" (")[0]


def describe(log, names):
    """One row of the table, from one control campaign."""
    records = log["experiments"]
    n_init = log["config"]["n_init"]
    front = set(log["reference"]["front_levels"])
    lhs = records[:n_init]
    on_front = [r for r in lhs if r["ligand"] in front]
    yield_key = "yield"
    alerts = triggers.firing_times(triggers.pace_ratio, records, n_init, len(records))
    tail = collections.Counter(r["ligand"] for r in records[-10:]).most_common(1)[0][0]
    return {
        "seed": log["config"]["seed"],
        "final_fraction": round(log["analysis"]["hv_final_fraction"], 3),
        "trapped": log["analysis"]["hv_final_fraction"] < TARGET,
        "front_ligand_in_lhs": len(on_front),
        "front_ligand_lhs_yield": round(max(r[yield_key] for r in on_front), 1) if on_front else None,
        "best_lhs_yield": round(max(r[yield_key] for r in lhs), 1),
        "best_lhs_ligand": ligand_name(max(lhs, key=lambda r: r[yield_key])["ligand"], names),
        "bo_on_front_ligand": log["analysis"]["bo_experiments_on_front_ligand"],
        "first_alert": alerts[0] if alerts else None,
        "n_alerts": len(alerts),
        "end_ligand": ligand_name(tail, names),
        "_alerts": alerts,
        "_curve": [h / log["reference"]["max_hypervolume"] for h in log["curves"]["hypervolume"]],
        "_n_init": n_init,
    }


def figure(benchmark, rows, front_names):
    n = len(rows)
    cols = 5
    lines = (n + cols - 1) // cols
    fig, axes = plt.subplots(lines, cols, figsize=(2.9 * cols, 2.3 * lines),
                             sharex=True, sharey=True, squeeze=False)
    for k, row in enumerate(rows):
        axis = axes[k // cols][k % cols]
        colour = ECHEC if row["trapped"] else REUSSITE
        x = range(1, len(row["_curve"]) + 1)
        axis.axvspan(0.5, row["_n_init"] + 0.5, color="#e8e8e8", lw=0)
        axis.step(x, row["_curve"], where="post", color=colour, lw=1.6)
        for a in row["_alerts"]:
            axis.axvline(a, color=ALERTE, ls="--", lw=0.9)
        axis.set_title("graine %d · %.0f %% · ligand du front ×%d dans le LHS"
                       % (row["seed"], 100 * row["final_fraction"], row["front_ligand_in_lhs"]),
                       fontsize=7.5, color=colour)
        axis.set_ylim(0, 1.02)
        axis.set_xlim(0.5, len(row["_curve"]) + 0.5)
        axis.tick_params(labelsize=7)
        axis.grid(alpha=0.25)
    for k in range(n, lines * cols):
        axes[k // cols][k % cols].axis("off")
    for r in range(lines):
        axes[r][0].set_ylabel("fraction du front", fontsize=7.5)
    for c in range(cols):
        axes[lines - 1][c].set_xlabel("expérience", fontsize=7.5)
    fig.suptitle("%s — BO seule, %d graines ; le front est porté par %s.\n"
                 "Orange : finit sous %.0f %% du front ; gris : plan initial ; "
                 "pointillés rouges : alertes du trigger (P*, W=5, seuil 0,30)"
                 % (TITLES[benchmark], n, ", ".join(front_names), 100 * TARGET), fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    path = os.path.join(FIGURES, "seed_choice_%s.png" % benchmark)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def suggest(rows):
    """Trapped, called early enough, and the front ligand was in the initial design."""
    candidates = [r for r in rows if r["trapped"] and r["first_alert"]
                  and r["first_alert"] <= LATEST_USEFUL_ALERT and r["front_ligand_in_lhs"] > 0]
    return sorted(candidates, key=lambda r: (r["first_alert"], r["final_fraction"]))


COLUMNS = ["seed", "final_fraction", "trapped", "front_ligand_in_lhs", "front_ligand_lhs_yield",
           "best_lhs_yield", "best_lhs_ligand", "bo_on_front_ligand", "first_alert",
           "n_alerts", "end_ligand"]


def main():
    os.makedirs(FIGURES, exist_ok=True)
    names = catalyst_names()
    for benchmark in BENCHMARKS:
        logs = load_controls(benchmark)
        if not logs:
            print("%s : aucun témoin" % benchmark)
            continue
        front_names = [ligand_name(c, names) for c in logs[0]["reference"]["front_levels"]]
        rows = [describe(log, names) for log in logs]
        path = figure(benchmark, rows, front_names)
        with open(os.path.join(RESULTS, "seed_choice_%s.csv" % benchmark), "w",
                  newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

        print("\n%s — front sur %s — %d témoins, %d coincés (< %.0f %%) — %s"
              % (TITLES[benchmark], "/".join(front_names), len(rows),
                 sum(r["trapped"] for r in rows), 100 * TARGET, os.path.relpath(path, HERE)))
        print("| graine | fin | %s dans LHS | meilleur rdt LHS sur ce ligand | meilleur rdt LHS (ligand) "
              "| essais BO sur ce ligand | 1re alerte | alertes | ligand de fin |" % "/".join(front_names))
        print("|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            print("| %d | %.0f %% | %d | %s | %.0f (%s) | %d/30 | %s | %d | %s |"
                  % (r["seed"], 100 * r["final_fraction"], r["front_ligand_in_lhs"],
                     "—" if r["front_ligand_lhs_yield"] is None else "%.0f" % r["front_ligand_lhs_yield"],
                     r["best_lhs_yield"], r["best_lhs_ligand"], r["bo_on_front_ligand"],
                     r["first_alert"] or "jamais", r["n_alerts"], r["end_ligand"]))
        best = suggest(rows)
        print("suggestion (coincée, alerte <= %d, ligand du front vu dans le LHS) : %s"
              % (LATEST_USEFUL_ALERT,
                 ", ".join("graine %d (alerte %d, %.0f %%)" % (r["seed"], r["first_alert"], 100 * r["final_fraction"])
                           for r in best[:3]) or "aucune"))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
r"""Characterise plain Bayesian optimisation on every benchmark, honestly.

This answers one question: on which benchmarks does a standard multi-objective
BO campaign fail often enough to be worth studying, and rarely enough that an
intervention could still show an effect. Nothing here runs an optimiser; it
reads the campaign logs that run_screening.py and run_other_benchmarks.py wrote.

**Success** is the brief's definition: the final hypervolume reaches 90% of the
benchmark's reference hypervolume. On a complete grid that reference is exact -
the front is computed from the table, not sampled - so the fraction means what
it says. Single-objective benchmarks compare the best observed value with the
grid's best, in the same normalised units.

The failure rate carries a Wilson interval rather than a plain proportion,
because at twenty seeds the difference matters: 12 failures out of 20 is 60%,
but the interval still runs from 39% to 78%.

Two things this deliberately does not do. It never tunes anything to make
failures appear - only the budget and the size of the initial design may change,
and every setting tried is reported. And it reports the shape of the final
hypervolume distribution with a histogram and two cluster means rather than a
test: with twenty seeds no test of bimodality would be worth trusting.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/analyse_plain_bo.py
"""

import argparse
import collections
import csv
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")
FIGURES = os.path.join(HERE, "figures")

SUCCESS_FRACTION = 0.90
# The brief's target band: below this a benchmark leaves nothing to repair,
# above it nothing can be shown to help.
TARGET = (0.30, 0.60)
LAST_PROPOSALS = 10


def wilson(successes, total, z=1.96):
    """Interval for a proportion that stays sane at n = 20 and at k = 0."""
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    spread = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, centre - spread), min(1.0, centre + spread)


def mean(values):
    return sum(values) / len(values) if values else 0.0


def stdev(values):
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def load_campaigns(stem):
    out = []
    for path in sorted(glob.glob(os.path.join(RESULTS, "%s__*__seed*.json" % stem))):
        with open(path, encoding="utf-8") as handle:
            log = json.load(handle)
        if log["config"].get("arm", "no_hitl") != "no_hitl":
            continue
        out.append((os.path.basename(path), log))
    return out


def categorical_key(log):
    """The categorical a chemist would call the choice: the one with most levels."""
    record = log["experiments"][0]
    objectives = set(log["config"]["objectives"])
    texts = [k for k, v in record.items()
             if isinstance(v, str) and k not in objectives and k != "phase"]
    if not texts:
        return None
    return max(texts, key=lambda k: len({r[k] for r in log["experiments"]}))


def auc_after_init(log):
    """Area under the hypervolume curve after the initial design, normalised
    by its own length so campaigns of different budgets stay comparable."""
    curve = log["curves"]["hypervolume"]
    n_init = log["config"]["n_init"]
    tail = curve[n_init - 1:]
    if len(tail) < 2:
        return 0.0
    # trapezoid over unit steps
    total = sum((a + b) / 2 for a, b in zip(tail, tail[1:]))
    return total / (len(tail) - 1)


def front_levels(stem, key):
    """The levels that actually carry the benchmark's reference Pareto front.

    Read from the grid itself, not inferred from the campaigns, so "the campaign
    never tried the winning catalyst again after experiment 14" is a statement
    about the benchmark and not about what our seeds happened to find. Returns
    None when the grid cannot be located, and the report then says the trap
    metrics are unavailable rather than guessing.
    """
    import numpy as np
    import pandas as pd
    from hitl_bench import metrics
    from hitl_bench.scripts.make_chemist_form import catalyst_names, label_value

    data = os.path.join(HERE, "data")
    suzuki = stem.replace("summit_", "") in ("i", "ii", "iii", "iv")
    path = (os.path.join(data, "suzuki_%s.csv" % stem) if suzuki
            else os.path.join(data, "other", "%s.csv" % stem))
    if not os.path.exists(path):
        return None
    grid = pd.read_csv(path)

    log = load_campaigns(stem)[0][1]
    objectives = log["config"]["objectives"]
    goals = log["config"].get("goals") or ["maximize"] * len(objectives)
    sign = np.array([1.0 if g == "maximize" else -1.0 for g in goals])
    raw = grid[objectives].to_numpy(dtype=float) * sign
    low, high = raw.min(axis=0), raw.max(axis=0)
    mask = metrics.pareto_mask((raw - low) / (high - low))

    if suzuki:
        codes = [c for c in grid.columns if c.startswith("L") and c[1:].isdigit()]
        chosen = [codes[i] for i in np.argmax(grid[codes].to_numpy(), axis=1)]
        names = catalyst_names()
        levels = {label_value("ligand", chosen[i], names) for i in np.flatnonzero(mask)}
    else:
        if key not in grid.columns:
            return None
        levels = set(grid[key].to_numpy()[mask])
    return levels


def describe(stem, campaigns):
    """Everything the summary row and the report need, for one benchmark."""
    fractions = [log["analysis"]["hv_final_fraction"] for _, log in campaigns]
    successes = sum(1 for f in fractions if f >= SUCCESS_FRACTION)
    total = len(fractions)
    low, high = wilson(total - successes, total)

    config = campaigns[0][1]["config"]
    row = {
        "benchmark": stem,
        "surrogate": "summit" if stem.startswith("summit_") else "olympus/table",
        "n_seeds": total,
        "n_init": config["n_init"],
        "n_iterations": config["n_iterations"],
        "noise": "none",
        "objectives": "|".join(config["objectives"]),
        "reference_known": "exact (complete grid)",
        "failure_rate": round(1 - successes / total, 3),
        "failure_low": round(low, 3),
        "failure_high": round(high, 3),
        "in_target_band": TARGET[0] <= 1 - successes / total <= TARGET[1],
        "hv_final_mean": round(mean(fractions), 4),
        "hv_final_sd": round(stdev(fractions), 4),
        "hv_final_min": round(min(fractions), 4),
        "hv_final_max": round(max(fractions), 4),
        "auc_mean": round(mean([auc_after_init(log) for _, log in campaigns]), 4),
        "seconds_per_campaign": round(mean([log["runtime_seconds"] for _, log in campaigns])),
    }

    # Bimodality, described rather than tested: split at the midpoint of the
    # observed range and report the two group means and sizes.
    cut = (min(fractions) + max(fractions)) / 2
    low_group = [f for f in fractions if f < cut]
    high_group = [f for f in fractions if f >= cut]
    row["cluster_low_n"] = len(low_group)
    row["cluster_low_mean"] = round(mean(low_group), 4) if low_group else ""
    row["cluster_high_n"] = len(high_group)
    row["cluster_high_mean"] = round(mean(high_group), 4) if high_group else ""
    row["gap_between_clusters"] = (round(mean(high_group) - mean(low_group), 4)
                                   if low_group and high_group else "")

    key = categorical_key(campaigns[0][1])
    row["categorical"] = key or ""
    settled = collections.Counter()
    winners = front_levels(stem, key) if key else None
    row["front_levels"] = "|".join(sorted(map(str, winners))) if winners else ""

    tested, abandoned, settled_on_winner = [], [], 0
    if key:
        for _, log in campaigns:
            labels = [_label(key, r[key], stem) for r in log["experiments"]]
            tail = labels[-LAST_PROPOSALS:]
            lands_on = collections.Counter(tail).most_common(1)[0][0]
            settled[lands_on] += 1
            if winners:
                if lands_on in winners:
                    settled_on_winner += 1
                hits = [i for i, v in enumerate(labels) if v in winners]
                tested.append(len(hits))
                # experiment after which the winning level was never proposed
                # again; absent when it was still being proposed near the end
                last = (hits[-1] + 1) if hits else 0
                if last < len(labels) - 5:
                    abandoned.append(last)

    row["settled_levels"] = "|".join("%s:%d" % kv for kv in settled.most_common())
    row["settled_on_front_level"] = settled_on_winner if winners else ""
    row["best_level_tests_mean"] = round(mean(tested), 2) if tested else ""
    row["abandoned_best_level_n"] = len(abandoned) if winners else ""
    row["abandoned_after_mean"] = round(mean(abandoned), 1) if abandoned else ""
    return row, fractions, settled


def _label(key, value, stem):
    """Codes are unreadable in a figure and in a report: L4 becomes PCy3."""
    if key != "ligand" or not stem.replace("summit_", "") in ("i", "ii", "iii", "iv"):
        return str(value)
    from hitl_bench.scripts.make_chemist_form import catalyst_names, label_value
    return label_value("ligand", value, catalyst_names())


def figure(stem, campaigns, fractions, settled):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3 if settled else 2, figsize=(13 if settled else 9, 3.6))
    curves = [log["curves"]["hypervolume"] for _, log in campaigns]
    reference = campaigns[0][1]["reference"]["max_hypervolume"]

    for curve in curves:
        axes[0].plot([v / reference for v in curve], color="#2a78d6", alpha=0.25, lw=1)
    longest = max(len(c) for c in curves)
    average = [mean([c[i] / reference for c in curves if len(c) > i]) for i in range(longest)]
    axes[0].plot(average, color="#eb6834", lw=2.2, label="moyenne")
    axes[0].axhline(SUCCESS_FRACTION, color="#1baf7a", ls="--", lw=1.2, label="seuil de succes")
    axes[0].axvline(campaigns[0][1]["config"]["n_init"] - 0.5, color="#8b93a1", lw=0.8)
    axes[0].set_xlabel("experience"); axes[0].set_ylabel("fraction du front global")
    axes[0].set_ylim(0, 1.05); axes[0].legend(fontsize=8, frameon=False)

    axes[1].hist(fractions, bins=10, range=(0, 1), color="#2a78d6")
    axes[1].axvline(SUCCESS_FRACTION, color="#1baf7a", ls="--", lw=1.2)
    axes[1].set_xlabel("fraction finale"); axes[1].set_ylabel("campagnes")
    axes[1].yaxis.get_major_locator().set_params(integer=True)

    if settled:
        labels = [k for k, _ in settled.most_common()]
        axes[2].bar(range(len(labels)), [settled[k] for k in labels], color="#eb6834")
        axes[2].set_xticks(range(len(labels)))
        axes[2].set_xticklabels(labels, rotation=40, ha="right", fontsize=8)
        axes[2].set_ylabel("campagnes finissant la")
        axes[2].yaxis.get_major_locator().set_params(integer=True)

    fig.suptitle("%s - %d graines" % (stem, len(fractions)), fontsize=11)
    fig.tight_layout()
    os.makedirs(FIGURES, exist_ok=True)
    path = os.path.join(FIGURES, "plain_bo_%s.png" % stem)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


COLUMNS = ["benchmark", "surrogate", "n_seeds", "n_init", "n_iterations", "noise",
           "objectives", "reference_known", "failure_rate", "failure_low",
           "failure_high", "in_target_band", "hv_final_mean", "hv_final_sd",
           "hv_final_min", "hv_final_max", "auc_mean", "seconds_per_campaign",
           "cluster_low_n", "cluster_low_mean", "cluster_high_n",
           "cluster_high_mean", "gap_between_clusters", "categorical",
           "front_levels", "settled_levels", "settled_on_front_level",
           "best_level_tests_mean", "abandoned_best_level_n",
           "abandoned_after_mean"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmarks", nargs="*", help="par defaut, tout ce qui existe")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args()

    stems = args.benchmarks
    if not stems:
        stems = sorted({os.path.basename(p).split("__")[0]
                        for p in glob.glob(os.path.join(RESULTS, "*__no_hitl__seed*.json"))})

    rows = []
    for stem in stems:
        campaigns = load_campaigns(stem)
        if not campaigns:
            print("%-22s aucune campagne" % stem)
            continue
        row, fractions, settled = describe(stem, campaigns)
        rows.append(row)
        marque = "  <-- cible 30-60 %" if row["in_target_band"] else ""
        print("%-22s n=%2d | echec %4.0f%% [%3.0f-%3.0f] | HV %.3f +- %.3f%s"
              % (stem, row["n_seeds"], 100 * row["failure_rate"],
                 100 * row["failure_low"], 100 * row["failure_high"],
                 row["hv_final_mean"], row["hv_final_sd"], marque))
        if not args.no_figures:
            try:
                print("   figure : %s" % figure(stem, campaigns, fractions, settled))
            except Exception as exc:            # matplotlib absent ou backend casse
                print("   figure impossible : %s" % exc)

    rows.sort(key=lambda r: -r["failure_rate"])
    target = os.path.join(RESULTS, "plain_bo_summary.csv")
    with open(target, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print("\necrit : %s (%d lignes)" % (target, len(rows)))


if __name__ == "__main__":
    main()

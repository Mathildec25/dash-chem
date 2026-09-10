# -*- coding: utf-8 -*-
r"""Compare the arms, and write what an article and its supporting information need.

Reads the logs written by run_arms.py and produces:

    results/arms_summary.csv        one row per campaign, everything per campaign
    results/arms_interventions.csv  one row per intervention, everything per point
    results/arms_report.md          the numbers in prose, with their caveats
    figures/arms_*.png              the figures

**Paired, always.** A random arm is never compared with the average of the
no-HITL arm: it is compared with *its own parent*, the campaign it branched
from. The shared prefix cancels exactly, which is what lets a five-campaign
human arm mean anything later. An unpaired comparison would need far more
campaigns to see the same effect and would be reporting a different quantity.

**Per intervention as well as per campaign.** The human arm will be small: a
handful of chemists answering a handful of checkpoints. A chemist's single
answer can only be judged against the distribution of what chance achieved *at
that same checkpoint*, so the intervention-level table is the one that will
carry the eventual comparison, and the per-campaign table is context.

**Two outcomes, deliberately.** Quality is the fraction of the reference front
reached at the end. Time is the number of experiments needed to reach a
threshold, with campaigns that never reach it recorded as censored rather than
dropped - dropping them would flatter whichever arm fails more often.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/analyse_arms.py --benchmark edbo_ch_arylation
"""

import argparse
import csv
import glob
import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = os.path.join(HERE, "results", "arms")
RESULTS = os.path.join(HERE, "results")
FIGURES = os.path.join(HERE, "figures")

TARGET = 0.90            # "reached the front" and the time-to-target threshold
ECHEC, REUSSITE, ALERTE = "#eb6834", "#2a78d6", "#c1121f"


def load(benchmark, arm):
    out = []
    pattern = os.path.join(ARMS, "%s__%s__*.json" % (benchmark, arm))
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as handle:
            out.append(json.load(handle))
    return out


def curve_fraction(log):
    reference = log["reference"]["max_hypervolume"]
    return [v / reference for v in log["curves"]["hypervolume"]]


def time_to_target(log, target=TARGET):
    """Experiments needed to reach `target` of the front, or None if never.

    None is a censored observation, not a missing one: the campaign ran its full
    budget and did not get there. Reporting a mean over the ones that arrived
    would quietly delete the failures.
    """
    for value, record in zip(curve_fraction(log), log["experiments"]):
        if value >= target:
            return record["experiment"]
    return None


def mean(values):
    return statistics.fmean(values) if values else float("nan")


def wilson(successes, total, z=1.96):
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    d = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / d
    spread = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return max(0.0, centre - spread), min(1.0, centre + spread)


# --- per-campaign and per-intervention tables ------------------------------
CAMPAIGN_COLUMNS = [
    "benchmark", "arm", "seed", "repeat", "n_init", "budget",
    "hv_final", "hv_final_fraction", "hv_curve_auc", "igd_plus_final",
    "reached_target", "time_to_target", "censored",
    "n_interventions", "intervention_experiments",
    "hv_final_fraction_gain", "hv_curve_auc_gain", "time_to_target_gain",
    "settled_level", "runtime_seconds",
]


def campaign_row(log, parents):
    config = log["config"]
    arm = config.get("arm", "no_hitl")
    seed = config.get("parent_seed", config["seed"])
    parent = parents.get(seed)
    fraction = curve_fraction(log)
    ttt = time_to_target(log)

    key = None
    for candidate in ("ligand", "catalyst", "base"):
        if candidate in log["experiments"][0]:
            key = candidate
            break
    tail = [r[key] for r in log["experiments"][-10:]] if key else []

    row = {
        "benchmark": config.get("benchmark") or config.get("case"),
        "arm": arm,
        "seed": seed,
        "repeat": config.get("repeat", ""),
        "n_init": config["n_init"],
        "budget": len(log["experiments"]),
        "hv_final": round(log["analysis"]["hv_final"], 6),
        "hv_final_fraction": round(fraction[-1], 6),
        "hv_curve_auc": round(log["analysis"]["hv_curve_auc"], 6),
        "igd_plus_final": round(log["analysis"].get("igd_plus_final", float("nan")), 6),
        "reached_target": int(fraction[-1] >= TARGET),
        "time_to_target": ttt if ttt is not None else "",
        "censored": int(ttt is None),
        "n_interventions": log["analysis"].get("n_interventions", 0),
        "intervention_experiments": "|".join(
            str(i["injected_at"]) for i in log.get("interventions", [])),
        "settled_level": max(set(tail), key=tail.count) if tail else "",
        "runtime_seconds": log.get("runtime_seconds", ""),
    }
    if parent is not None and arm != "no_hitl":
        parent_ttt = time_to_target(parent)
        row["hv_final_fraction_gain"] = round(
            fraction[-1] - curve_fraction(parent)[-1], 6)
        row["hv_curve_auc_gain"] = round(
            log["analysis"]["hv_curve_auc"] - parent["analysis"]["hv_curve_auc"], 6)
        # Only defined when both arms got there; otherwise the pair is censored.
        row["time_to_target_gain"] = (
            ttt - parent_ttt if (ttt is not None and parent_ttt is not None) else "")
    else:
        row["hv_final_fraction_gain"] = ""
        row["hv_curve_auc_gain"] = ""
        row["time_to_target_gain"] = ""
    return row


INTERVENTION_COLUMNS = [
    "benchmark", "seed", "repeat", "rank", "alert_experiment", "injected_at",
    "p_star_at_alert", "draw_seed", "point",
    "fraction_before", "fraction_after", "immediate_gain",
    "fraction_final_arm", "fraction_final_parent", "final_gain",
    "level", "level_on_front",
]


def intervention_rows(log, parents, front_levels=(), categorical=None):
    config = log["config"]
    seed = config.get("parent_seed", config["seed"])
    parent = parents.get(seed)
    fraction = curve_fraction(log)
    rows = []
    for rank, item in enumerate(log.get("interventions", [])):
        at = item["injected_at"]
        rows.append({
            "benchmark": config.get("benchmark") or config.get("case"),
            "seed": seed,
            "repeat": config.get("repeat", ""),
            "rank": rank + 1,
            "alert_experiment": item["alert_experiment"],
            "injected_at": at,
            "p_star_at_alert": (round(item["p_star_at_alert"], 4)
                                if item.get("p_star_at_alert") is not None else ""),
            "draw_seed": item["draw_seed"],
            "point": json.dumps(item["point"], ensure_ascii=False),
            "fraction_before": round(fraction[at - 2], 6) if at >= 2 else "",
            "fraction_after": round(fraction[at - 1], 6),
            # The immediate gain is almost always zero: an injected point rarely
            # improves the front on the spot. What an intervention is worth shows
            # up downstream, which is why the final gain is the column to read.
            "immediate_gain": round(fraction[at - 1] - fraction[at - 2], 6) if at >= 2 else "",
            "fraction_final_arm": round(fraction[-1], 6),
            "fraction_final_parent": (round(curve_fraction(parent)[-1], 6)
                                      if parent else ""),
            "final_gain": (round(fraction[-1] - curve_fraction(parent)[-1], 6)
                           if parent else ""),
            # Le point injecte portait-il un niveau du front ? C'est la question
            # qui rend le resultat explicatif : un gain venu d'un point tombe sur
            # le bon ligand n'a pas le meme sens qu'un gain venu d'ailleurs.
            "level": (item["point"] or {}).get(categorical, "") if categorical else "",
            "level_on_front": int(bool(categorical) and
                                  (item["point"] or {}).get(categorical) in front_levels),
        })
    return rows


# --- figures ---------------------------------------------------------------
def figure_paired(benchmark, parents, randoms, seeds_shown):
    """Small multiples: each parent against its own random branches.

    Only a few campaigns are drawn. Twenty panels is a wall, not a figure, and
    the point here is that a reader can follow one campaign and its branches;
    the full set belongs in the supporting information.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    seeds = sorted(seeds_shown)
    fig, axes = plt.subplots(1, len(seeds), figsize=(2.7 * len(seeds), 3.2),
                             sharey=True, squeeze=False)
    for axis, seed in zip(axes[0], seeds):
        parent = parents[seed]
        axis.axhline(TARGET, color="#8b93a1", ls="--", lw=0.9)
        axis.axvline(parent["config"]["n_init"] + 0.5, color="#c9ced6", lw=0.9)
        for branch in [r for r in randoms
                       if r["config"].get("parent_seed") == seed]:
            axis.plot(range(1, len(branch["experiments"]) + 1),
                      curve_fraction(branch), color=ALERTE, alpha=0.85, lw=1.4)
            for item in branch.get("interventions", []):
                x = item["injected_at"]
                axis.plot(x, curve_fraction(branch)[x - 1], marker="v", ms=4,
                          color=ALERTE, mec="white", mew=0.5, zorder=5)
        axis.plot(range(1, len(parent["experiments"]) + 1), curve_fraction(parent),
                  color=REUSSITE, lw=2.4, zorder=3)
        axis.set_title("campagne %d — BO seule %.0f%%"
                       % (seed, 100 * curve_fraction(parent)[-1]), fontsize=9)
        axis.set_xlabel("expérience")
        axis.set_ylim(0, 1.05)
        axis.grid(alpha=0.25, lw=0.5)
    axes[0][0].set_ylabel("fraction du front")
    fig.suptitle("%s — bleu : BO seule ; rouge : mêmes campagnes avec un point "
                 "au hasard à chaque alerte (▼)" % benchmark, fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    os.makedirs(FIGURES, exist_ok=True)
    path = os.path.join(FIGURES, "arms_paired_%s.png" % benchmark)
    fig.savefig(path, dpi=145)
    plt.close(fig)
    return path


def figure_effect(benchmark, rows):
    """What the intervention was worth, paired, as a distribution rather than a mean."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    gains = [100 * r["hv_final_fraction_gain"] for r in rows
             if r["arm"] != "no_hitl" and r["hv_final_fraction_gain"] != ""]
    if not gains:
        return None
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    axes[0].hist(gains, bins=15, color=REUSSITE)
    axes[0].axvline(0, color="black", lw=1.2)
    axes[0].axvline(mean(gains), color=ALERTE, lw=1.6, ls="--",
                    label="moyenne %.1f pt" % mean(gains))
    axes[0].set_xlabel("gain de fraction du front (points de %)")
    axes[0].set_ylabel("branches")
    axes[0].legend(fontsize=8, frameon=False)

    ameliorees = sum(1 for g in gains if g > 0)
    low, high = wilson(ameliorees, len(gains))
    axes[1].bar(["améliorée", "inchangée", "dégradée"],
                [ameliorees, sum(1 for g in gains if g == 0),
                 sum(1 for g in gains if g < 0)],
                color=[REUSSITE, "#c9ced6", ECHEC])
    axes[1].set_ylabel("branches")
    axes[1].set_title("%d/%d améliorées, IC 95%% [%.0f%% ; %.0f%%]"
                      % (ameliorees, len(gains), 100 * low, 100 * high), fontsize=9)
    fig.suptitle("%s — effet apparié d'un point au hasard à chaque alerte" % benchmark,
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    path = os.path.join(FIGURES, "arms_effect_%s.png" % benchmark)
    fig.savefig(path, dpi=145)
    plt.close(fig)
    return path


def write_report(benchmark, rows, interventions, no_hitl, randoms):
    """The numbers in prose, with the caveats attached to them.

    Written by the same pass that computes them, so the text cannot drift from
    the tables the way a hand-written summary does.
    """
    base = [r for r in rows if r["arm"] == "no_hitl"]
    branch = [r for r in rows if r["arm"] != "no_hitl"]
    gains = [r["hv_final_fraction_gain"] for r in branch
             if r["hv_final_fraction_gain"] != ""]
    ameliorees = sum(1 for g in gains if g > 0)
    low, high = wilson(ameliorees, len(gains)) if gains else (0, 1)

    atteint_base = sum(r["reached_target"] for r in base)
    atteint_branche = sum(r["reached_target"] for r in branch)
    temps_base = [r["time_to_target"] for r in base if r["time_to_target"] != ""]
    temps_branche = [r["time_to_target"] for r in branch if r["time_to_target"] != ""]

    lignes = [
        "# %s — BO seule contre intervention aléatoire" % benchmark,
        "",
        "Écrit par `analyse_arms.py`, donc toujours à jour des campagnes présentes.",
        "",
        "## Ce que contient ce lot",
        "",
        "- **%d campagnes** de BO seule, 10 tirages initiaux puis 30 itérations" % len(base),
        "- **%d branches** avec un point tiré au hasard à chaque alerte du trigger" % len(branch),
        "- **%d interventions** au total, soit %.1f par branche"
        % (len(interventions), len(interventions) / len(branch) if branch else 0),
        "",
        "## Qualité : fraction du front atteinte",
        "",
        "| | campagnes | fraction moyenne | atteignent %d %% |" % int(100 * TARGET),
        "|---|---|---|---|",
        "| BO seule | %d | %.3f | %d (%.0f %%) |"
        % (len(base), mean([r["hv_final_fraction"] for r in base]), atteint_base,
           100 * atteint_base / len(base) if base else 0),
        "| + point au hasard | %d | %.3f | %d (%.0f %%) |"
        % (len(branch), mean([r["hv_final_fraction"] for r in branch]), atteint_branche,
           100 * atteint_branche / len(branch) if branch else 0),
        "",
    ]

    if gains:
        lignes += [
            "**Gain apparié moyen : %+.1f points de fraction du front.** Chaque branche "
            "est comparée à *sa propre* campagne parente, pas à la moyenne du bras "
            "témoin : les deux partagent leur histoire jusqu'à la première alerte, "
            "donc le préfixe commun s'annule et l'écart est attribuable à "
            "l'intervention." % (100 * mean(gains)),
            "",
            "%d branches sur %d s'améliorent, intervalle de Wilson à 95 %% "
            "[%.0f %% ; %.0f %%]. Étendue des gains : %+.1f à %+.1f points."
            % (ameliorees, len(gains), 100 * low, 100 * high,
               100 * min(gains), 100 * max(gains)),
            "",
        ]

    lignes += [
        "## Temps : expériences pour atteindre %d %% du front" % int(100 * TARGET),
        "",
        "| | y arrivent | expériences (moyenne) | censurées |",
        "|---|---|---|---|",
        "| BO seule | %d / %d | %s | %d |"
        % (len(temps_base), len(base),
           "%.1f" % mean(temps_base) if temps_base else "—",
           sum(r["censored"] for r in base)),
        "| + point au hasard | %d / %d | %s | %d |"
        % (len(temps_branche), len(branch),
           "%.1f" % mean(temps_branche) if temps_branche else "—",
           sum(r["censored"] for r in branch)),
        "",
        "Les campagnes qui n'atteignent jamais le seuil sont **censurées**, pas "
        "supprimées : les retirer de la moyenne flatterait le bras qui échoue le "
        "plus souvent. La moyenne ci-dessus ne porte donc que sur celles qui y "
        "arrivent, et la colonne de droite dit combien ont été laissées de côté.",
        "",
        "## À lire avec précaution",
        "",
        "- Le gain immédiat d'une intervention est presque toujours nul : un point "
        "injecté améliore rarement le front sur-le-champ. Ce qu'il vaut se voit en "
        "aval, d'où la colonne `final_gain` de `arms_interventions.csv`.",
        "- Comme on intervient à **chaque** alerte, seule la première est commune "
        "entre deux répétitions d'une même graine. Situer une réponse de chimiste "
        "par un percentile demande beaucoup de tirages **au même checkpoint**, ce "
        "que ce lot ne fournit pas : il donne l'effet moyen du hasard, pas la "
        "distribution à un instant donné.",
        "",
        "## Fichiers",
        "",
        "- `arms_summary.csv` — une ligne par campagne",
        "- `arms_interventions.csv` — une ligne par intervention",
        "- `figures/arms_paired_%s.png` — campagnes appariées, éventail des résultats"
        % benchmark,
        "- `figures/arms_effect_%s.png` — distribution du gain apparié" % benchmark,
        "",
    ]

    path = os.path.join(RESULTS, "arms_report_%s.md" % benchmark)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(chr(10).join(lignes))
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--show", type=int, default=5,
                        help="campagnes tracees dans la figure principale")
    args = parser.parse_args()

    no_hitl = load(args.benchmark, "no_hitl")
    randoms = load(args.benchmark, "hitl_random")
    if not no_hitl:
        raise SystemExit("aucune campagne pour %s" % args.benchmark)
    parents = {log["config"]["seed"]: log for log in no_hitl}

    rows = [campaign_row(log, parents) for log in no_hitl + randoms]
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "arms_summary.csv"), "w", newline="",
              encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CAMPAIGN_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    from hitl_bench.scripts.run_arms import load_benchmark
    reference = load_benchmark(args.benchmark)
    front_levels = set(getattr(reference, "front_levels", []) or [])
    categorical = getattr(reference, "categorical_key", None)

    interventions = []
    for log in randoms:
        interventions += intervention_rows(log, parents, front_levels, categorical)
    with open(os.path.join(RESULTS, "arms_interventions.csv"), "w", newline="",
              encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INTERVENTION_COLUMNS)
        writer.writeheader()
        writer.writerows(interventions)

    print("%-22s %d campagnes BO seule | %d branches aleatoires | %d interventions"
          % (args.benchmark, len(no_hitl), len(randoms), len(interventions)))

    base = [r for r in rows if r["arm"] == "no_hitl"]
    branch = [r for r in rows if r["arm"] != "no_hitl"]
    print("   BO seule    : HV %.3f | %d/%d atteignent %.0f%% du front"
          % (mean([r["hv_final_fraction"] for r in base]),
             sum(r["reached_target"] for r in base), len(base), 100 * TARGET))
    if branch:
        gains = [r["hv_final_fraction_gain"] for r in branch
                 if r["hv_final_fraction_gain"] != ""]
        print("   HITL random : HV %.3f | %d/%d atteignent %.0f%% | gain apparie moyen %+.1f pt"
              % (mean([r["hv_final_fraction"] for r in branch]),
                 sum(r["reached_target"] for r in branch), len(branch),
                 100 * TARGET, 100 * mean(gains)))

    # Les campagnes tracees couvrent l'eventail des resultats plutot que les
    # premieres graines : montrer 1 a 5 serait arbitraire, et vingt panneaux
    # seraient un mur. Les vingt figurent en supporting information.
    classees = sorted(parents, key=lambda s: curve_fraction(parents[s])[-1])
    if len(classees) <= args.show:
        seeds_shown = classees
    else:
        pas = (len(classees) - 1) / (args.show - 1)
        seeds_shown = [classees[round(i * pas)] for i in range(args.show)]
    sur_front = [r for r in interventions if r["level_on_front"]]
    if interventions:
        gains_front = [r["final_gain"] for r in sur_front if r["final_gain"] != ""]
        autres = [r["final_gain"] for r in interventions
                  if not r["level_on_front"] and r["final_gain"] != ""]
        print("   points injectes sur un niveau du front : %d / %d"
              % (len(sur_front), len(interventions)))
        if gains_front and autres:
            print("      gain final moyen : %+.1f pt quand oui, %+.1f pt quand non"
                  % (100 * mean(gains_front), 100 * mean(autres)))

    print("   rapport : %s" % write_report(args.benchmark, rows, interventions,
                                             no_hitl, randoms))
    try:
        print("   figure : %s" % figure_paired(args.benchmark, parents, randoms, seeds_shown))
        path = figure_effect(args.benchmark, rows)
        if path:
            print("   figure : %s" % path)
    except Exception as exc:
        print("   figures impossibles : %s" % exc)


if __name__ == "__main__":
    main()

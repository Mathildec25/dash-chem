# -*- coding: utf-8 -*-
r"""Turn the arm-1 campaigns into the checkpoints a chemist is asked to judge.

One JSON per (benchmark, seed, alert): everything needed to show a campaign and
collect a suggestion, and nothing else. The format is deliberately neutral - it
is consumed by the REACTO page, and a notebook or a static page could consume it
just as well without regenerating anything.

**The answer never travels with the question.** What the campaign went on to do
is written to a separate `_key` file. A single file holding both would leak
through a browser's developer tools, through a notebook's variables, or through
one careless forward of an attachment, and a participant who has seen the answer
is no longer a participant.

**Every proposable point is a grid point.** The dropdowns are built from the
benchmark grid, so a chemist cannot suggest conditions we are unable to
evaluate, and the levels are shown with real units and chemical names rather
than the codes the optimiser works in.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/make_checkpoints.py --benchmark edbo_ch_arylation
"""

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = os.path.join(HERE, "results", "arms")
OUT = os.path.join(HERE, "forms", "checkpoints")
KEYS = os.path.join(HERE, "forms", "checkpoint_keys")

# What a chemist is told about each reaction. Written from what the data and the
# cited source actually establish; where the source does not say, this says so
# rather than inventing chemistry.
REACTIONS = {
    "edbo_ch_arylation": {
        "titre": "Arylation C–H",
        "intro": [
            "Une campagne d'optimisation en criblage à haut débit. À chaque essai "
            "on choisit une base, un ligand, un solvant, une concentration et une "
            "température, et on mesure deux choses : le rendement, et le coût des "
            "réactifs consommés.",
            "Les deux objectifs sont réellement indépendants — leur corrélation sur "
            "l'ensemble des 1728 conditions mesurées est de −0,002. Améliorer le "
            "rendement n'améliore pas le coût, et inversement : il faut arbitrer.",
        ],
        "reserve": "Les données proviennent d'un criblage réel publié (Torres et al., "
                   "J. Am. Chem. Soc. 2022, 144, 19999-20007). Le substrat exact n'est "
                   "pas redistribué avec le jeu de données, donc nous ne pouvons pas "
                   "vous le montrer : raisonnez sur les réactifs et les conditions, "
                   "comme vous le feriez devant un criblage dont on vous donnerait le "
                   "tableau sans la structure.",
        "objectifs": {
            "yield": ("Rendement", "%", "maximiser"),
            "cost": ("Coût des réactifs", "", "minimiser"),
        },
        "variables": {
            "base": ("Base", ""),
            "ligand": ("Ligand", ""),
            "solvent": ("Solvant", ""),
            "concentration": ("Concentration", "M"),
            "temperature": ("Température", "°C"),
        },
    },
    "suzuki": {
        "titre": "Couplage de Suzuki-Miyaura en flux continu",
        "intro": [
            "Un montage de chimie en flux teste une condition à la fois. À chaque "
            "essai on choisit une paire précatalyseur-ligand au palladium, un temps "
            "de séjour, une température et une charge en palladium.",
            "On mesure le rendement et le nombre de rotations du catalyseur (TON). "
            "Les deux vont largement dans le même sens sur cette chimie.",
        ],
        "reserve": "Données issues des campagnes en flux de Reizman, Wang, Buchwald et "
                   "Jensen (React. Chem. Eng. 2016, 1, 658-666), interpolées sur une "
                   "grille complète. Deux des sept paires précatalyseur-ligand n'ont "
                   "pas de nom publié et gardent leur code.",
        "objectifs": {
            "yield": ("Rendement", "%", "maximiser"),
            "turnover": ("TON", "", "maximiser"),
        },
        "variables": {
            "ligand": ("Catalyseur", ""),
            "res_time": ("Temps de séjour", "s"),
            "temperature": ("Température", "°C"),
            "catalyst_loading": ("Charge en Pd", "mol%"),
        },
    },
}


def presentation(name):
    if name in ("i", "ii", "iii", "iv") or name.startswith("summit_"):
        return REACTIONS["suzuki"]
    if name in REACTIONS:
        return REACTIONS[name]
    raise SystemExit("aucune presentation pour %r" % name)


def french(value, digits=6):
    text = ("%." + str(digits) + "g") % float(value)
    return text.replace(".", ",")


def label(benchmark, key, value):
    """A chemist reads names and French numbers, never codes and never 2.515."""
    if isinstance(value, str):
        if key == "ligand" and value.startswith("L") and value[1:].isdigit():
            from hitl_bench.scripts.make_chemist_form import catalyst_names, label_value
            return label_value("ligand", value, catalyst_names())
        return value
    return french(value, 4)


def levels_of(benchmark, key):
    import pandas as pd
    column = benchmark.grid[key] if key in benchmark.grid.columns else None
    if column is None:                      # Suzuki : le ligand est en one-hot
        from hitl_bench.benchmark import LIGANDS
        return [label(benchmark, "ligand", code) for code in LIGANDS]
    values = sorted(column.unique(), key=lambda v: (isinstance(v, str), v))
    if pd.api.types.is_numeric_dtype(column):
        return [french(v) for v in values]
    return [str(v) for v in values]


def build(benchmark, log, at, pres):
    name = log["config"].get("benchmark") or log["config"].get("case")
    records = log["experiments"][:at]
    budget = log["config"]["n_init"] + log["config"]["n_iterations"]
    params = benchmark.parameter_keys
    objectives = benchmark.objectives

    table = []
    for r in records:
        row = {"n": r["experiment"], "phase": r["phase"]}
        for k in params:
            row[k] = label(benchmark, k, r[k])
        for o in objectives:
            row[o] = french(r[o], 4)
        table.append(row)

    return {
        "id": "%s__seed%02d__exp%02d" % (name, log["config"]["seed"], at),
        "benchmark": name,
        "seed": log["config"]["seed"],
        "stop_at": at,
        "budget": budget,
        "n_init": log["config"]["n_init"],
        "titre": pres["titre"],
        "intro": pres["intro"],
        "reserve": pres["reserve"],
        "variables": [{"cle": k,
                       "titre": pres["variables"].get(k, (k, ""))[0],
                       "unite": pres["variables"].get(k, (k, ""))[1],
                       "niveaux": levels_of(benchmark, k)} for k in params],
        "objectifs": [{"cle": o,
                       "titre": pres["objectifs"].get(o, (o, "", "maximiser"))[0],
                       "unite": pres["objectifs"].get(o, (o, "", "maximiser"))[1],
                       "sens": pres["objectifs"].get(o, (o, "", "maximiser"))[2]}
                      for o in objectives],
        "essais": table,
    }


def build_key(log, at):
    """What the campaign did next. For the study owner only."""
    curve = log["curves"]["hypervolume"]
    reference = log["reference"]["max_hypervolume"]
    return {
        "id": "%s__seed%02d__exp%02d" % (
            log["config"].get("benchmark") or log["config"].get("case"),
            log["config"]["seed"], at),
        "fraction_at_alert": curve[at - 1] / reference,
        "fraction_final": curve[-1] / reference,
        "gain_still_to_come": (curve[-1] - curve[at - 1]) / curve[-1] if curve[-1] else 0.0,
        "all_firing_times": log["analysis"].get("firing_times"),
        "front_levels": log["reference"].get("front_levels"),
        "next_experiments": [
            {k: r[k] for k in list(r) if k in ("experiment", "ligand", "base", "solvent",
                                               "concentration", "temperature", "res_time",
                                               "catalyst_loading", "yield", "turnover",
                                               "cost", "hypervolume")}
            for r in log["experiments"][at:at + 5]],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--max-per-campaign", type=int, default=2,
                        help="alertes retenues par campagne, les premieres d'abord")
    parser.add_argument("--seeds", nargs="*", type=int,
                        help="par defaut, toutes les campagnes disponibles")
    args = parser.parse_args()

    from hitl_bench.scripts.run_arms import load_benchmark, firing_times
    benchmark = load_benchmark(args.benchmark)
    pres = presentation(args.benchmark)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(KEYS, exist_ok=True)

    pattern = os.path.join(ARMS, "%s__no_hitl__seed*.json" % args.benchmark)
    n = 0
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as handle:
            log = json.load(handle)
        if args.seeds and log["config"]["seed"] not in args.seeds:
            continue
        for at in firing_times(log)[: args.max_per_campaign]:
            payload = build(benchmark, log, at, pres)
            with open(os.path.join(OUT, payload["id"] + ".json"), "w",
                      encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=1)
            key = build_key(log, at)
            with open(os.path.join(KEYS, key["id"] + "_key.json"), "w",
                      encoding="utf-8") as handle:
                json.dump(key, handle, ensure_ascii=False, indent=1)
            n += 1
    print("%d checkpoints ecrits dans %s" % (n, OUT))
    print("   reponses attendues, a ne pas diffuser : %s" % KEYS)


if __name__ == "__main__":
    main()

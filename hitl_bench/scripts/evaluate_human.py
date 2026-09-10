# -*- coding: utf-8 -*-
r"""Score a chemist's suggestion against the same campaign, and against chance.

Reads the answers written by REACTO's Chemist input page, replays the campaign
they were shown while injecting their point, and reports two numbers:

    the paired gain      what their suggestion changed on that very campaign,
                         the shared prefix cancelling exactly
    the percentile       where that gain falls among the random draws made at
                         the same checkpoint

The percentile is the one that answers the study's question. A chemist's single
answer, on its own, cannot be told apart from luck; placed inside the
distribution of what random points achieved at the same moment on the same
campaign, it can. "Better than 85% of random draws" is a statement a five-person
study can support; "gained 4 points of hypervolume" is not.

A suggestion that reads "continue" or "stop" is recorded and not replayed: those
are decisions about the campaign, not points, and they are scored separately -
stopping is right when the campaign had nothing left to give, which the key file
knows and the participant did not.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/evaluate_human.py
"""

import argparse
import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = os.path.join(HERE, "results", "arms")
REPONSES = os.path.join(HERE, "forms", "reponses")
KEYS = os.path.join(HERE, "forms", "checkpoint_keys")
RESULTS = os.path.join(HERE, "results")


def to_number(text):
    """French decimals come back from the page as they were shown."""
    return float(str(text).replace(" ", "").replace(",", "."))


def reverse_label(benchmark_name, key, shown):
    """Map what the chemist saw back onto what the grid stores.

    The page shows names and French numbers; the benchmark indexes on codes and
    floats. Getting this wrong would silently evaluate a different experiment
    from the one that was suggested, so an unmatched label raises rather than
    guessing.
    """
    if key == "ligand" and benchmark_name in ("i", "ii", "iii", "iv") \
            or (key == "ligand" and benchmark_name.startswith("summit_")):
        from hitl_bench.scripts.make_chemist_form import catalyst_names, label_value
        names = catalyst_names()
        for code in names["mapping"]:
            if label_value("ligand", code, names) == shown:
                return code
        raise KeyError("catalyseur non reconnu : %r" % shown)
    try:
        return to_number(shown)
    except ValueError:
        return shown


def build_point(benchmark, name, proposition):
    point = {}
    for key in benchmark.parameter_keys:
        if key not in proposition:
            raise KeyError("condition manquante : %s" % key)
        point[key] = reverse_label(name, key, proposition[key])
    return point


def random_gains_at(interventions_csv, benchmark, seed, injected_at):
    """The gains obtained by random draws at this exact checkpoint."""
    gains = []
    if not os.path.exists(interventions_csv):
        return gains
    with open(interventions_csv, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if (row["benchmark"] == benchmark and int(row["seed"]) == seed
                    and int(row["injected_at"]) == injected_at
                    and row["final_gain"] not in ("", None)):
                gains.append(float(row["final_gain"]))
    return gains


def percentile_of(value, sample):
    if not sample:
        return None
    return 100.0 * sum(1 for s in sample if s < value) / len(sample)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses", default=REPONSES)
    parser.add_argument("--out", default=os.path.join(RESULTS, "human_arm.csv"))
    args = parser.parse_args()

    from hitl_bench.runtime import pin_numerics
    pin_numerics()
    import warnings
    warnings.filterwarnings("ignore")
    from hitl_bench.runtime import limit_acquisition_memory, pin_torch_threads
    pin_torch_threads()
    limit_acquisition_memory()
    from hitl_bench.campaign import fork_campaign
    from hitl_bench.scripts.run_arms import load_benchmark

    files = sorted(glob.glob(os.path.join(args.responses, "*.json")))
    if not files:
        raise SystemExit("aucune reponse dans %s" % args.responses)

    interventions_csv = os.path.join(RESULTS, "arms_interventions.csv")
    rows, benchmarks = [], {}

    for path in files:
        with open(path, encoding="utf-8") as handle:
            answer = json.load(handle)
        name = answer["benchmark"]
        seed, at = answer["seed"], answer["stop_at"]

        parent_path = os.path.join(ARMS, "%s__no_hitl__seed%02d.json" % (name, seed))
        if not os.path.exists(parent_path):
            print("  %s : campagne parente absente" % os.path.basename(path))
            continue
        with open(parent_path, encoding="utf-8") as handle:
            parent = json.load(handle)
        key_path = os.path.join(KEYS, "%s__seed%02d__exp%02d_key.json" % (name, seed, at))
        key = json.load(open(key_path, encoding="utf-8")) if os.path.exists(key_path) else {}

        row = {
            "fichier": os.path.basename(path),
            "qui": answer.get("qui", ""),
            "domaine": answer.get("domaine", ""),
            "benchmark": name,
            "seed": seed,
            "stop_at": at,
            "decision": answer["decision"],
            "reaction_connue": answer.get("reaction_connue", ""),
            "surete": answer.get("surete", ""),
            "avis": answer.get("avis", "").replace("\n", " ")[:500],
            "pourquoi": answer.get("pourquoi", "").replace("\n", " ")[:500],
            "fraction_at_alert": round(key.get("fraction_at_alert", float("nan")), 4),
            "fraction_final_parent": round(key.get("fraction_final", float("nan")), 4),
            "gain_still_to_come": round(key.get("gain_still_to_come", float("nan")), 4),
        }

        if answer["decision"] != "propose":
            # Une decision, pas un point : rien a rejouer. Elle se juge sur ce
            # qu'il restait a gagner, que la cle connait et que le participant
            # ne connaissait pas.
            row.update({"point": "", "fraction_final_humain": "", "gain_humain": "",
                        "percentile_vs_hasard": "", "n_tirages_hasard": ""})
            rows.append(row)
            print("  %-38s %s (pas de point a evaluer)"
                  % (row["qui"], answer["decision"]))
            continue

        if name not in benchmarks:
            benchmarks[name] = load_benchmark(name)
        benchmark = benchmarks[name]
        try:
            point = build_point(benchmark, name, answer["proposition"])
        except KeyError as exc:
            print("  %s : %s" % (os.path.basename(path), exc))
            continue

        branch = fork_campaign(benchmark, parent, at_experiment=at, draw_seed=None,
                               injected_point=point)
        reference = branch["reference"]["max_hypervolume"]
        fraction = branch["curves"]["hypervolume"][-1] / reference
        parent_fraction = parent["curves"]["hypervolume"][-1] / reference
        gain = fraction - parent_fraction
        sample = random_gains_at(interventions_csv, name, seed, at + 1)

        row.update({
            "point": json.dumps(point, ensure_ascii=False),
            "fraction_final_humain": round(fraction, 4),
            "gain_humain": round(gain, 4),
            "percentile_vs_hasard": (round(percentile_of(gain, sample), 1)
                                     if sample else ""),
            "n_tirages_hasard": len(sample),
        })
        rows.append(row)
        print("  %-12s %s graine %d exp %d | gain %+.1f pt | mieux que %s des tirages"
              % (row["qui"], name, seed, at, 100 * gain,
                 ("%.0f%%" % percentile_of(gain, sample)) if sample else "?"))

    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("\necrit : %s (%d reponses)" % (args.out, len(rows)))


if __name__ == "__main__":
    main()

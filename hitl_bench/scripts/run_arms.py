# -*- coding: utf-8 -*-
r"""Run the study's arms: BO alone, and BO with a random suggestion at every alert.

Three arms are planned. This script produces the two that need no human:

    no_hitl        the campaign as the optimiser runs it, 10 LHS + 30 BO
    hitl_random    the same campaign, but every time the trigger fires the next
                   experiment is drawn at random from the untested grid points
                   instead of being proposed by the optimiser

The third arm, `hitl_human`, replaces that random draw with a chemist's
suggestion at the very same experiments, which is what makes the comparison
readable: chemist against random against nothing, at identical moments on
identical histories.

**Paired by construction.** An arm is not a fresh campaign. It branches from a
saved one, keeping its history verbatim up to the alert, so the two arms differ
only by what was injected. The prefix cancels in any difference, which is what
lets a five-campaign human arm say anything at all. This only works because
campaigns are now replayable: a fork with no intervention reproduces its parent
exactly (see runtime.py).

**Budget is preserved.** The injected point *replaces* the optimiser's proposal
for that experiment; it is not added. Both arms therefore spend exactly 40
experiments, and a difference cannot be bought with extra measurements.

**Repetitions, not one draw.** The random arm is run several times per parent
with different draws. A single random point says nothing about what "a random
point" achieves at that moment, and the human arm will have few campaigns: to
place one chemist's answer we need the distribution of what chance achieves at
the same checkpoint, not one sample from it.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/run_arms.py --benchmark edbo_ch_arylation ^
        --arm no_hitl --seeds 20
    .venv\Scripts\python.exe hitl_bench/scripts/run_arms.py --benchmark edbo_ch_arylation ^
        --arm hitl_random --seeds 20 --repeats 5
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hitl_bench.runtime import pin_numerics  # noqa: E402

pin_numerics()

import warnings  # noqa: E402

warnings.filterwarnings("ignore")

from hitl_bench import triggers  # noqa: E402
from hitl_bench.runtime import limit_acquisition_memory, pin_torch_threads  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results", "arms")


def load_benchmark(name):
    if name in ("i", "ii", "iii", "iv") or name.startswith("summit_"):
        from hitl_bench.benchmark import GridBenchmark
        return GridBenchmark(name)
    from hitl_bench.scripts.run_other_benchmarks import TableBenchmark
    return TableBenchmark(name)


def firing_times(log):
    """Where the study's trigger fires on a campaign, with the frozen settings."""
    records = log["experiments"]
    return triggers.firing_times(triggers.pace_ratio, records,
                                 log["config"]["n_init"], len(records))


def draw_seed(campaign_seed, repeat, rank):
    """Deterministic seed for the rank-th injection of one repetition.

    Replayability again: the whole arm has to be reconstructible from the three
    integers that name it, or a result cannot be checked a year from now.
    """
    return 900000 + 10000 * int(campaign_seed) + 100 * int(repeat) + int(rank)


def run_random_arm(benchmark, parent, repeat):
    """Cascade: intervene at every alert, recomputing them as the campaign changes.

    An intervention moves the campaign, so the alerts of the parent are not the
    alerts of the branch. After each injection the trigger is evaluated again on
    the new history and only alerts strictly after the last injection count -
    otherwise the same experiment would be intervened on twice.
    """
    from hitl_bench.campaign import fork_campaign

    current = parent
    interventions = []
    last = parent["config"]["n_init"]          # nothing before the initial design
    budget = len(parent["experiments"])

    while True:
        fires = [e for e in firing_times(current) if e > last]
        if not fires:
            break
        at = fires[0]
        if not (parent["config"]["n_init"] <= at < budget):
            break
        seed = draw_seed(parent["config"]["seed"], repeat, len(interventions))
        started = time.time()
        current = fork_campaign(benchmark, current, at_experiment=at, draw_seed=seed)
        injected = current["fork"]["injected"]
        interventions.append({
            "alert_experiment": at,
            "injected_at": at + 1,
            "draw_seed": seed,
            "point": injected,
            "p_star_at_alert": triggers.pace_ratio_value(
                current["experiments"][:at], budget),
            "seconds": round(time.time() - started, 1),
        })
        last = at + 1

    current["config"]["arm"] = "hitl_random"
    current["config"]["repeat"] = repeat
    current["config"]["parent_seed"] = parent["config"]["seed"]
    current["interventions"] = interventions
    current["analysis"]["n_interventions"] = len(interventions)
    # The paired quantities. Both arms spent 40 experiments, so these are
    # differences at equal budget, and the shared prefix cancels exactly.
    for key in ("hv_final", "hv_final_fraction", "hv_curve_auc"):
        current["analysis"][key + "_gain"] = (
            current["analysis"][key] - parent["analysis"][key])
    return current


def path_for(benchmark, arm, seed, repeat=None):
    name = "%s__%s__seed%02d" % (benchmark, arm, seed)
    if repeat is not None:
        name += "__rep%02d" % repeat
    return os.path.join(RESULTS, name + ".json")


def save(log, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(log, handle, indent=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--arm", choices=["no_hitl", "hitl_random"], required=True)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--start-seed", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=5,
                        help="tirages aleatoires par campagne parente")
    args = parser.parse_args()

    pin_torch_threads()
    limit_acquisition_memory()
    from hitl_bench.campaign import run_campaign

    benchmark = load_benchmark(args.benchmark)
    print("%s | %d points | front %d | HV max %.4f"
          % (args.benchmark, len(benchmark.grid), len(benchmark.true_front),
             benchmark.max_hypervolume), flush=True)

    for seed in range(args.start_seed, args.start_seed + args.seeds):
        parent_path = path_for(args.benchmark, "no_hitl", seed)

        if args.arm == "no_hitl":
            if os.path.exists(parent_path):
                print("  graine %2d : deja faite" % seed, flush=True)
                continue
            started = time.time()
            log = run_campaign(benchmark, seed)
            log["config"]["arm"] = "no_hitl"
            log["analysis"]["firing_times"] = firing_times(log)
            save(log, parent_path)
            print("  graine %2d | %5.1f min | HV %.1f%% du front | alertes %s"
                  % (seed, (time.time() - started) / 60,
                     100 * log["analysis"]["hv_final_fraction"],
                     log["analysis"]["firing_times"]), flush=True)
            continue

        # --- hitl_random : il faut la campagne parente -----------------------
        if not os.path.exists(parent_path):
            print("  graine %2d : parente absente, lancez d'abord --arm no_hitl" % seed,
                  flush=True)
            continue
        with open(parent_path, encoding="utf-8") as handle:
            parent = json.load(handle)

        for repeat in range(1, args.repeats + 1):
            target = path_for(args.benchmark, "hitl_random", seed, repeat)
            if os.path.exists(target):
                continue
            started = time.time()
            log = run_random_arm(benchmark, parent, repeat)
            save(log, target)
            print("  graine %2d rep %d | %4.1f min | %d interventions | "
                  "HV %.1f%% (parente %.1f%%) | gain %+.1f pt"
                  % (seed, repeat, (time.time() - started) / 60,
                     log["analysis"]["n_interventions"],
                     100 * log["analysis"]["hv_final_fraction"],
                     100 * parent["analysis"]["hv_final_fraction"],
                     100 * log["analysis"]["hv_final_fraction_gain"]), flush=True)


if __name__ == "__main__":
    main()

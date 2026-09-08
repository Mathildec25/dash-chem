r"""Build the gain table: what an intervention is worth, and when.

For every saved no-intervention campaign, branch it at a range of experiments,
inject a point drawn at random among those not yet run, and carry the campaign
to the same budget. The saved campaign is the control branch of each pair, so
the comparison is exact and the shared prefix cancels.

The table answers the study's main question directly - when should a chemist
intervene? - and it doubles as the bench on which candidate triggers are
scored, since a trigger just picks a firing time and the gain is read off.

Selection and blind validation. Cases i and ii are the selection set; cases iii
and iv are held out and must not influence any choice. Forking a held-out case
therefore needs an explicit flag, so that it cannot happen by accident.

Run from the dash-chem directory:

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/run_forks.py --case ii

Already-written forks are skipped, so an interrupted run resumes by simply
being launched again.
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# --- configuration ---------------------------------------------------------
# Fork points as fractions of the total budget, not as counts of experiments:
# "intervene at 40% of the budget" transfers to a campaign of a different
# length, "intervene at experiment 16" does not. On the frozen budget of 40
# these are experiments 13, 16, 19, 22 and 25.
FORK_FRACTIONS = [0.325, 0.400, 0.475, 0.550, 0.625]
# Random draws per fork point. The intervention is a random point, so the gain
# is a random variable and this is what we average over; it is also the only
# stochastic ingredient left, the optimisation step being deterministic.
DRAWS_PER_FORK = 3
SELECTION_CASES = ["i", "ii"]
VALIDATION_CASES = ["iii", "iv"]
THREADS = 1
# Rough, only used to warn before a long run.
SECONDS_PER_ITERATION = 13


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="ii", help="suzuki case to fork")
    parser.add_argument("--draws", type=int, default=DRAWS_PER_FORK)
    parser.add_argument("--allow-validation-cases", action="store_true",
                        help="required to fork cases iii or iv, which are held out")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.case in VALIDATION_CASES and not args.allow_validation_cases:
        parser.error(
            "case %s is held out for blind validation. Using it now would spend "
            "the only unbiased measurement the study has. Pass "
            "--allow-validation-cases if that is really what you mean." % args.case)

    import torch
    torch.set_num_threads(THREADS)

    from hitl_bench.benchmark import GridBenchmark
    from hitl_bench.campaign import fork_campaign
    from hitl_bench.campaign_log import RESULTS_DIR, campaign_filename, load_campaign

    parents = sorted(
        os.path.join(RESULTS_DIR, name)
        for name in os.listdir(RESULTS_DIR)
        if name.startswith("%s__no_hitl__" % args.case) and name.endswith(".json")
    )
    if not parents:
        parser.error("no no_hitl campaign for case %s yet; run the screening first"
                     % args.case)

    benchmark = GridBenchmark(args.case)
    print(benchmark, flush=True)

    jobs = []
    for path in parents:
        saved = load_campaign(path)
        budget = saved["config"]["n_init"] + saved["config"]["n_iterations"]
        for fraction in FORK_FRACTIONS:
            at = int(round(fraction * budget))
            for draw in range(1, args.draws + 1):
                jobs.append((saved, at, draw, budget))

    iterations = sum(budget - at - 1 for _, at, _, budget in jobs)
    print("%d forks from %d campaigns, about %d optimisation steps in total, "
          "roughly %.1f hours\n"
          % (len(jobs), len(parents), iterations,
             iterations * SECONDS_PER_ITERATION / 3600.0), flush=True)

    done, skipped, started = 0, 0, time.time()
    for saved, at, draw, budget in jobs:
        preview = {"config": dict(saved["config"], arm="fixed:%d" % at),
                   "fork": {"draw_seed": draw}}
        target = os.path.join(RESULTS_DIR, campaign_filename(preview))
        if os.path.exists(target) and not args.overwrite:
            skipped += 1
            continue

        step = time.time()
        log = fork_campaign(benchmark, saved, at_experiment=at, draw_seed=draw)
        with open(target, "w", encoding="utf-8") as handle:
            import json
            log["written_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            json.dump(log, handle, indent=2)
        done += 1

        analysis, injected = log["analysis"], log["fork"]["injected"]
        print("seed %2d  fork at %2d  draw %d  | %4.1f min | injected %-3s -> yield %5.1f "
              "| HV final %5.1f%% (%+.1f) | AUC gain %+.4f"
              % (saved["config"]["seed"], at, draw, (time.time() - step) / 60.0,
                 injected["ligand"], injected["yield"],
                 100 * analysis["hv_final_fraction"],
                 100 * analysis["hv_final_fraction_gain"],
                 analysis["hv_curve_auc_gain"]), flush=True)

    print("\n%d forks written, %d already there, %.1f min"
          % (done, skipped, (time.time() - started) / 60.0))


if __name__ == "__main__":
    main()

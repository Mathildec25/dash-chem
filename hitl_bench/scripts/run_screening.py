r"""Run no-intervention campaigns over several seeds and report what happened.

This is the screening step: it establishes how a plain campaign behaves on a
case before any human intervention is involved, which is what the intervention
arms are later compared against.

Run it from the dash-chem directory so that `utils` and `hitl_bench` are both
importable:

    cd C:\Users\mathi\REACTO\dash-chem
    .venv\Scripts\python.exe hitl_bench/scripts/run_screening.py --case ii --seeds 5

One campaign is roughly 8 minutes on this machine, so five seeds take about 40
minutes sequentially, or about a quarter of that spread over four workers.
Each worker is held to a couple of BLAS threads, otherwise the processes fight
over the same cores and the whole thing gets slower rather than faster.
"""

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# --- configuration ---------------------------------------------------------
DEFAULT_CASE = "ii"
DEFAULT_SEEDS = 5
DEFAULT_WORKERS = 1
# BLAS threads per worker. The acquisition step is the cost here and it does
# not parallelise well, so more workers beats more threads per worker.
THREADS_PER_WORKER = 2


def run_one(job):
    """Run a single campaign in this process and save its log."""
    case, seed, overwrite = job

    import torch
    torch.set_num_threads(THREADS_PER_WORKER)

    from hitl_bench.benchmark import GridBenchmark
    from hitl_bench.campaign import run_campaign
    from hitl_bench.campaign_log import save_campaign

    started = time.time()
    benchmark = GridBenchmark(case)
    log = run_campaign(benchmark, seed=seed)
    path = save_campaign(log, overwrite=overwrite)
    analysis = log["analysis"]
    return {
        "seed": seed,
        "path": path,
        "minutes": (time.time() - started) / 60.0,
        "hv_auc_fraction": analysis["hv_curve_auc_fraction"],
        "hv_final_fraction": analysis["hv_final_fraction"],
        "igd_plus_final": analysis["igd_plus_final"],
        "bo_chose_a_front_ligand": analysis["bo_chose_a_front_ligand"],
        "bo_fraction_on_front_ligand": analysis["bo_fraction_on_front_ligand"],
        "ligand_counts": analysis["ligand_counts"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default=DEFAULT_CASE, help="suzuki case: i, ii, iii or iv")
    parser.add_argument("--seeds", type=int, default=DEFAULT_SEEDS, help="run seeds 1..N")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help="1 runs in this process, which is the frugal option")
    parser.add_argument("--start-seed", type=int, default=1,
                        help="first seed, to resume a series that was interrupted")
    parser.add_argument("--overwrite", action="store_true", help="replace existing logs")
    args = parser.parse_args()

    from hitl_bench.benchmark import GridBenchmark
    benchmark = GridBenchmark(args.case)
    print(benchmark, flush=True)
    print("running seeds 1..%d on %d workers\n" % (args.seeds, args.workers), flush=True)

    seeds = range(args.start_seed, args.start_seed + args.seeds)
    jobs = [(args.case, seed, args.overwrite) for seed in seeds]
    started = time.time()
    results = []
    # With one worker we run in this very process. A ProcessPoolExecutor would
    # otherwise hold a second interpreter with torch and BoFire loaded, and on
    # a memory-tight machine that second copy is what gets the run killed.
    if args.workers == 1:
        outcomes = (run_one(job) for job in jobs)
    else:
        pool = ProcessPoolExecutor(max_workers=args.workers)
        outcomes = pool.map(run_one, jobs)
    try:
        for result in outcomes:
            results.append(result)
            print("seed %2d done in %4.1f min | AUC %.3f | HV final %.3f (%.1f%% of global) "
                  "| IGD+ %.3f | BO on front ligand: %s"
                  % (result["seed"], result["minutes"], result["hv_auc_fraction"],
                     result["hv_final_fraction"] * benchmark.max_hypervolume,
                     result["hv_final_fraction"] * 100.0, result["igd_plus_final"],
                     "yes" if result["bo_chose_a_front_ligand"] else "NO"), flush=True)
    finally:
        if args.workers != 1:
            pool.shutdown()

    print("\n%d campaigns in %.1f min" % (len(results), (time.time() - started) / 60.0))
    fractions = sorted(r["hv_final_fraction"] * 100.0 for r in results)
    print("final hypervolume, %% of the global front : %s"
          % ", ".join("%.1f" % f for f in fractions))
    trapped = [r for r in results if not r["bo_chose_a_front_ligand"]]
    print("campaigns whose BO never chose a front ligand: %d / %d"
          % (len(trapped), len(results)))


if __name__ == "__main__":
    main()

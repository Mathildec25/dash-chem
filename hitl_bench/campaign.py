"""One optimisation campaign on a grid benchmark.

The protocol, frozen: a Latin-hypercube initial design of 10 points, then 30
sequential Bayesian-optimisation iterations proposing one point at a time, 40
experiments in total. The optimiser is REACTO's own `bayesian_optimization`,
so the in-silico study and a real campaign run through exactly the same code.

Seeding. `torch.manual_seed(seed)` is set once at the start, and the seed is
also handed to the initial design explicitly: BoFire's RandomStrategy carries
its own generator, and without that the initial design is not reproducible.
On the grid the acquisition step is evaluated exhaustively over every untested
point, which makes it near-deterministic given the data, so in practice the
seed acts almost entirely through the initial design.
"""

import time

import pandas as pd
import torch

from hitl_bench import metrics
from hitl_bench.benchmark import OBJECTIVES, PARAMETER_KEYS, VALID_KEYS
from utils.bofire_optimization import bayesian_optimization, sampling

# --- frozen protocol -------------------------------------------------------
N_INIT = 10                 # Latin-hypercube points
N_ITERATIONS = 30           # sequential BO iterations after the initial design
BATCH_SIZE = 1              # one experiment at a time
SAMPLING_METHOD = "LHS"
ARM_NO_HITL = "no_hitl"

EXPERIMENT_COLUMNS = PARAMETER_KEYS + OBJECTIVES + VALID_KEYS


def run_campaign(benchmark, seed, arm=ARM_NO_HITL, n_init=N_INIT,
                 n_iterations=N_ITERATIONS, progress=None):
    """Run one campaign and return its log as a plain dict.

    Args:
        benchmark: a GridBenchmark.
        seed: campaign seed, driving both the initial design and torch.
        arm: which arm this campaign belongs to. Only "no_hitl" is implemented
            here; the trigger, fixed:t and paired-fork arms build on this loop.
        n_init, n_iterations: budget, defaulting to the frozen protocol.
        progress: optional callable(experiment_number, record) called after
            every experiment, for live feedback on long runs.

    Returns:
        dict: configuration, every experiment in order, the metric curves and
            the summary numbers. Safe to serialise as JSON.
    """
    if arm != ARM_NO_HITL:
        raise NotImplementedError(
            "arm %r is not implemented yet; only %r is" % (arm, ARM_NO_HITL))

    torch.manual_seed(seed)
    started = time.time()

    # --- initial design ---------------------------------------------------
    initial = sampling(benchmark.domain, SAMPLING_METHOD, n_init, seed=seed)
    experiments = pd.DataFrame(
        [benchmark.evaluate(row) for _, row in initial.iterrows()],
        columns=EXPERIMENT_COLUMNS,
    )

    records, hv_curve, igd_curve = [], [], []
    for position in range(len(experiments)):
        so_far = experiments.iloc[: position + 1]
        record = {
            "experiment": position + 1,
            "phase": "lhs",
            "iteration": None,
            "seconds": None,
            **{key: _plain(experiments.iloc[position][key]) for key in PARAMETER_KEYS},
            **{key: float(experiments.iloc[position][key]) for key in OBJECTIVES},
        }
        hv_curve.append(benchmark.hypervolume(so_far))
        igd_curve.append(benchmark.igd_plus(so_far))
        record["hypervolume"] = hv_curve[-1]
        record["igd_plus"] = igd_curve[-1]
        records.append(record)
        if progress:
            progress(record["experiment"], record)

    # --- optimisation loop ------------------------------------------------
    for iteration in range(1, n_iterations + 1):
        step_started = time.time()
        candidate = bayesian_optimization(
            benchmark.domain, experiments, n_candidates=BATCH_SIZE, verbose=False,
        ).iloc[0]
        evaluated = benchmark.evaluate(candidate)
        experiments = pd.concat(
            [experiments, pd.DataFrame([evaluated], columns=EXPERIMENT_COLUMNS)],
            ignore_index=True,
        )

        hv_curve.append(benchmark.hypervolume(experiments))
        igd_curve.append(benchmark.igd_plus(experiments))
        record = {
            "experiment": len(experiments),
            "phase": "bo",
            "iteration": iteration,
            "seconds": round(time.time() - step_started, 2),
            **{key: _plain(evaluated[key]) for key in PARAMETER_KEYS},
            **{key: float(evaluated[key]) for key in OBJECTIVES},
            "hypervolume": hv_curve[-1],
            "igd_plus": igd_curve[-1],
        }
        records.append(record)
        if progress:
            progress(record["experiment"], record)

    return {
        "config": {
            "case": benchmark.case,
            "arm": arm,
            "seed": seed,
            "n_init": n_init,
            "n_iterations": n_iterations,
            "batch_size": BATCH_SIZE,
            "sampling_method": SAMPLING_METHOD,
            "grid_points": len(benchmark.grid),
            "objectives": list(OBJECTIVES),
        },
        "reference": {
            "max_hypervolume": benchmark.max_hypervolume,
            "front_size": len(benchmark.true_front),
            "front_ligands": list(benchmark.front_ligands),
        },
        "experiments": records,
        "curves": {"hypervolume": hv_curve, "igd_plus": igd_curve},
        "analysis": _summarise(benchmark, records, hv_curve, igd_curve, n_init),
        "runtime_seconds": round(time.time() - started, 1),
    }


def _summarise(benchmark, records, hv_curve, igd_curve, n_init):
    """The reported numbers, primary metric first.

    The primary metric is the area under the post-LHS hypervolume curve. The
    integration starts at the last initial-design point so that the first BO
    increment is counted. `..._fraction` divides by the area a campaign sitting
    on the global front from the very first iteration would obtain, which makes
    campaigns on different cases comparable.
    """
    start = n_init - 1
    span = len(hv_curve) - 1 - start
    ideal = benchmark.max_hypervolume * span
    auc = metrics.curve_auc(hv_curve, start=start)

    # When did the campaign first touch a ligand that carries the global front?
    # The initial design touching one by chance says nothing: what matters is
    # whether the optimiser then went for it, or walked away and got trapped
    # on another ligand. So we track the two phases separately.
    first_touch, first_touch_bo = {}, {}
    for ligand in benchmark.front_ligands:
        hits = [r["experiment"] for r in records if r["ligand"] == ligand]
        bo_hits = [r["experiment"] for r in records
                   if r["ligand"] == ligand and r["phase"] == "bo"]
        first_touch[ligand] = hits[0] if hits else None
        first_touch_bo[ligand] = bo_hits[0] if bo_hits else None
    bo_records = [r for r in records if r["phase"] == "bo"]
    on_front_ligand = [r for r in bo_records if r["ligand"] in benchmark.front_ligands]

    return {
        "hv_curve_auc": auc,
        "hv_curve_auc_fraction": auc / ideal if ideal else 0.0,
        "hv_mean_post_lhs": metrics.mean_after(hv_curve, start=start),
        "hv_after_lhs": hv_curve[n_init - 1],
        "hv_final": hv_curve[-1],
        "hv_final_fraction": hv_curve[-1] / benchmark.max_hypervolume,
        "igd_plus_final": igd_curve[-1],
        "igd_plus_mean_post_lhs": metrics.mean_after(igd_curve, start=start),
        "front_ligand_first_experiment": first_touch,
        "front_ligand_first_bo_experiment": first_touch_bo,
        "found_a_front_ligand": any(v is not None for v in first_touch.values()),
        "bo_chose_a_front_ligand": any(v is not None for v in first_touch_bo.values()),
        "bo_experiments_on_front_ligand": len(on_front_ligand),
        "bo_fraction_on_front_ligand": (
            len(on_front_ligand) / len(bo_records) if bo_records else 0.0),
        "ligand_counts": {
            ligand: sum(1 for r in records if r["ligand"] == ligand)
            for ligand in sorted({r["ligand"] for r in records})
        },
    }


def _plain(value):
    """numpy scalars are not JSON-serialisable; pandas hands us plenty."""
    return value.item() if hasattr(value, "item") else value

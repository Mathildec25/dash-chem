r"""Run plain Bayesian optimisation on the candidate benchmarks beyond Suzuki.

Why a separate runner. The Suzuki pipeline in hitl_bench/campaign.py is
validated and its campaigns reproduce to the digit; generalising it to arbitrary
column names would put that at risk for no gain here. This script drives the
same optimiser, REACTO's `bayesian_optimization`, over a benchmark described by
a spec, and writes logs in the same shape.

Every benchmark here is a **complete factorial grid** taken from Olympus, so the
Pareto front is known exactly and evaluating a point is a table lookup. The
selection criterion was that a chemist can name what the variables are: a lipid,
a ligand, a base. Datasets whose categories are anonymous codes were rejected.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/run_other_benchmarks.py --list
    .venv\Scripts\python.exe hitl_bench/scripts/run_other_benchmarks.py --benchmark lnp3 --seeds 3
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hitl_bench.runtime import pin_numerics, pin_torch_threads  # noqa: E402

pin_numerics()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data", "other")
RESULTS = os.path.join(HERE, "results")

N_INIT, N_ITERATIONS = 10, 30

# name -> file, objectives with their goal, and a one-line description in the
# terms a chemist would use.
BENCHMARKS = {
    "lnp3": {
        "file": "lnp3.csv",
        "objectives": [("drug_loading", "maximize"),
                       ("encap_efficiency", "maximize"),
                       ("particle_diameter", "minimize")],
        "about": "Lipid nanoparticle formulation: how much drug is carried, how "
                 "efficiently it is encapsulated, and how small the particles are.",
    },
    "snar": {
        "file": "snar.csv",
        "objectives": [("sty", "maximize"), ("e_factor", "minimize")],
        "about": "Nucleophilic aromatic substitution in flow: how much product per "
                 "litre per hour against how much waste per kilo of product. The two "
                 "genuinely pull against each other, correlation -0.37.",
    },
    "dye_lasers": {
        "file": "dye_lasers.csv",
        "objectives": [("peak_score", "maximize"),
                       ("spectral_overlap", "minimize"),
                       ("fluo_rate", "maximize")],
        "about": "Laser dyes assembled from three fragments; brightness against "
                 "self-absorption.",
    },
}
for letter in "abcde":
    BENCHMARKS["buchwald_%s" % letter] = {
        "file": "buchwald_%s.csv" % letter,
        "objectives": [("yield", "maximize")],
        "about": "Buchwald-Hartwig C-N coupling, aryl halide %s: which ligand, "
                 "base and additive give the best yield." % letter,
    }


class TableBenchmark:
    """A complete grid: its BoFire domain, its lookup table and its true front."""

    def __init__(self, name):
        spec = BENCHMARKS[name]
        self.name = name
        self.about = spec["about"]
        self.grid = pd.read_csv(os.path.join(DATA, spec["file"]))
        self.objectives = [o for o, _ in spec["objectives"]]
        self.goals = [g for _, g in spec["objectives"]]
        self.parameter_keys = [c for c in self.grid.columns if c not in self.objectives]
        self.valid_keys = ["valid_%s" % o for o in self.objectives]
        self.domain = self._domain()
        self._lookup = {self._key(r): tuple(float(r[o]) for o in self.objectives)
                        for _, r in self.grid.iterrows()}

        # Everything is turned into a maximisation and scaled to [0, 1] by the
        # grid's own bounds, so the hypervolume is dimensionless and the
        # reference point is the origin, as for the Suzuki benchmarks.
        raw = self.grid[self.objectives].to_numpy(dtype=float)
        self.sign = np.array([1.0 if g == "maximize" else -1.0 for g in self.goals])
        flipped = raw * self.sign
        self.low, self.high = flipped.min(axis=0), flipped.max(axis=0)
        normalised = self.normalise(raw)
        from hitl_bench import metrics
        mask = metrics.pareto_mask(normalised)
        self.true_front = normalised[mask]
        self.max_hypervolume = _hypervolume(self.true_front)
        self.front_rows = self.grid[mask]

    def _is_text(self, key):
        """True for a categorical column. pandas 3 gives strings their own
        dtype, so testing against `object` silently fails."""
        return not pd.api.types.is_numeric_dtype(self.grid[key])

    # --- domain -----------------------------------------------------------
    def _domain(self):
        from bofire.data_models.api import Domain, Inputs, Outputs
        from bofire.data_models.features.api import (
            CategoricalInput, ContinuousOutput, DiscreteInput,
        )
        from bofire.data_models.objectives.api import MaximizeObjective, MinimizeObjective

        features = []
        for key in self.parameter_keys:
            column = self.grid[key]
            if self._is_text(key):
                features.append(CategoricalInput(
                    key=key, categories=[str(v) for v in sorted(column.unique())]))
            else:
                features.append(DiscreteInput(
                    key=key, values=sorted(float(v) for v in column.unique())))
        outputs = [
            ContinuousOutput(key=o, objective=(MaximizeObjective(w=1.0) if g == "maximize"
                                               else MinimizeObjective(w=1.0)))
            for o, g in zip(self.objectives, self.goals)
        ]
        return Domain(inputs=Inputs(features=features), outputs=Outputs(features=outputs))

    # --- evaluation -------------------------------------------------------
    def _key(self, row):
        out = []
        for key in self.parameter_keys:
            value = row[key]
            out.append(str(value) if self._is_text(key) else round(float(value), 6))
        return tuple(out)

    def evaluate(self, row):
        values = self._lookup[self._key(row)]
        record = {key: (str(row[key]) if self._is_text(key) else float(row[key]))
                  for key in self.parameter_keys}
        record.update({o: float(v) for o, v in zip(self.objectives, values)})
        record.update({k: 1 for k in self.valid_keys})
        return record

    def normalise(self, raw):
        flipped = np.asarray(raw, dtype=float) * self.sign
        return (flipped - self.low) / (self.high - self.low)

    def hypervolume(self, frame):
        return _hypervolume(self.normalise(frame[self.objectives].to_numpy(dtype=float)))


def _hypervolume(points):
    """Dominated hypervolume against the origin, any number of objectives."""
    import torch
    from botorch.utils.multi_objective.hypervolume import Hypervolume
    from botorch.utils.multi_objective.pareto import is_non_dominated

    Y = torch.as_tensor(np.asarray(points), dtype=torch.double)
    if Y.ndim == 1:
        Y = Y.unsqueeze(-1)
    Y = Y[(Y >= 0).all(dim=1)]
    if Y.numel() == 0:
        return 0.0
    if Y.shape[1] == 1:                      # single objective: just the best value
        return float(Y.max())
    ref = torch.zeros(Y.shape[1], dtype=torch.double)
    return float(Hypervolume(ref_point=ref).compute(Y[is_non_dominated(Y)]))


def run_campaign(benchmark, seed, progress=None):
    import torch
    from hitl_bench.runtime import limit_acquisition_memory
    from utils.bofire_optimization import bayesian_optimization, sampling

    limit_acquisition_memory()
    torch.manual_seed(seed)
    started = time.time()
    columns = benchmark.parameter_keys + benchmark.objectives + benchmark.valid_keys

    initial = sampling(benchmark.domain, "LHS", N_INIT, seed=seed)
    experiments = pd.DataFrame([benchmark.evaluate(r) for _, r in initial.iterrows()],
                               columns=columns)
    records, curve = [], []
    for position in range(len(experiments)):
        curve.append(benchmark.hypervolume(experiments.iloc[: position + 1]))
        records.append({"experiment": position + 1, "phase": "lhs", "hypervolume": curve[-1],
                        **{k: _plain(experiments.iloc[position][k])
                           for k in benchmark.parameter_keys + benchmark.objectives}})

    for iteration in range(1, N_ITERATIONS + 1):
        step = time.time()
        candidate = bayesian_optimization(benchmark.domain, experiments,
                                          n_candidates=1, verbose=False).iloc[0]
        evaluated = benchmark.evaluate(candidate)
        experiments = pd.concat([experiments, pd.DataFrame([evaluated], columns=columns)],
                                ignore_index=True)
        curve.append(benchmark.hypervolume(experiments))
        records.append({"experiment": len(experiments), "phase": "bo", "iteration": iteration,
                        "seconds": round(time.time() - step, 2), "hypervolume": curve[-1],
                        **{k: _plain(evaluated[k])
                           for k in benchmark.parameter_keys + benchmark.objectives}})
        if progress:
            progress(records[-1])

    return {
        "config": {"benchmark": benchmark.name, "arm": "no_hitl", "seed": seed,
                   "n_init": N_INIT, "n_iterations": N_ITERATIONS,
                   "objectives": benchmark.objectives, "goals": benchmark.goals,
                   "grid_points": len(benchmark.grid), "num_threads": _threads()},
        "reference": {"max_hypervolume": benchmark.max_hypervolume,
                      "front_size": int(len(benchmark.true_front)), "about": benchmark.about},
        "experiments": records,
        "curves": {"hypervolume": curve},
        "analysis": {"hv_final": curve[-1],
                     "hv_final_fraction": curve[-1] / benchmark.max_hypervolume
                     if benchmark.max_hypervolume else 0.0},
        "runtime_seconds": round(time.time() - started, 1),
    }


def _plain(value):
    return value.item() if hasattr(value, "item") else value


def _threads():
    import torch
    return torch.get_num_threads()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", help="which benchmark to run")
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--list", action="store_true", help="describe every benchmark and stop")
    args = parser.parse_args()

    pin_torch_threads()
    os.makedirs(RESULTS, exist_ok=True)

    if args.list or not args.benchmark:
        for name in BENCHMARKS:
            b = TableBenchmark(name)
            print("%-14s %5d points | %d objectifs | front %3d points | %s"
                  % (name, len(b.grid), len(b.objectives), len(b.true_front), b.about),
                  flush=True)
        return

    b = TableBenchmark(args.benchmark)
    print("%s | %d points | front %d | HV max %.4f"
          % (b.name, len(b.grid), len(b.true_front), b.max_hypervolume), flush=True)
    for seed in range(1, args.seeds + 1):
        target = os.path.join(RESULTS, "%s__no_hitl__seed%02d.json" % (b.name, seed))
        if os.path.exists(target):
            print("seed %d deja fait" % seed, flush=True)
            continue
        log = run_campaign(b, seed)
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(log, handle, indent=2)
        print("seed %2d | %5.1f min | HV final %.4f = %.1f%% du front global"
              % (seed, log["runtime_seconds"] / 60, log["analysis"]["hv_final"],
                 100 * log["analysis"]["hv_final_fraction"]), flush=True)


if __name__ == "__main__":
    main()

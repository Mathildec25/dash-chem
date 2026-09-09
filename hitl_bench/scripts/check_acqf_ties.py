r"""Does the acquisition function still discriminate between candidates?

Late in a campaign on edbo_ch_arylation, three seeds with unrelated histories
proposed the same ligands and solvents in alphabetical order. That is what an
acquisition function with a tied maximum looks like: `optimize_acqf_discrete`
returns the first index of a flat maximum, so enumeration order, not the model,
decides the experiment.

This script rebuilds the strategy from a finished campaign's own history at a
chosen experiment, scores every untested candidate, and reports how many are
tied at the maximum. It also reports whether each tied candidate sits in a
categorical cell the campaign has already visited, which is the explanation:
a GP has nothing to separate two never-visited cells, so their posteriors, and
therefore their acquisition values, are identical.

Measured with this script (see CLAUDE.md):

    Suzuki i, ii, iii, iv at experiments 20, 30, 40 : maximum unique, no ties.
    edbo_ch_arylation at experiment 30 : 175 of 1698 candidates tied, all of
    them in one of the 175 categorical cells out of 192 never visited.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/check_acqf_ties.py ^
        --log edbo_ch_arylation__no_hitl__seed01 --at 30
    .venv\Scripts\python.exe hitl_bench/scripts/check_acqf_ties.py --suzuki
"""

import argparse
import json
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hitl_bench.runtime import pin_numerics  # noqa: E402

pin_numerics()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402

from hitl_bench.runtime import limit_acquisition_memory, pin_torch_threads  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")

# Two candidates whose acquisition values differ by less than this, relative to
# the maximum, cannot be told apart by the optimiser: the order they were
# enumerated in decides which one is proposed.
RELATIVE_TIE = 1e-9


def load_benchmark(name):
    if name in ("i", "ii", "iii", "iv"):
        from hitl_bench.benchmark import GridBenchmark
        return GridBenchmark(name)
    from hitl_bench.scripts.run_other_benchmarks import TableBenchmark
    return TableBenchmark(name)


def probe(stem, at):
    """Rebuild the strategy after `at` experiments and score every candidate."""
    import bofire.strategies.api as strategies
    from bofire.data_models.acquisition_functions.api import qLogNEHVI
    from bofire.data_models.strategies.api import MoboStrategy

    with open(os.path.join(RESULTS, stem + ".json"), encoding="utf-8") as handle:
        log = json.load(handle)
    config = log["config"]
    name = config.get("benchmark") or config.get("case")
    seed = config["seed"]
    benchmark = load_benchmark(name)

    history = pd.DataFrame(log["experiments"]).head(at)
    columns = benchmark.parameter_keys + benchmark.objectives + benchmark.valid_keys
    experiments = pd.DataFrame([benchmark.evaluate(row) for _, row in history.iterrows()],
                               columns=columns)

    strategy = strategies.map(MoboStrategy(domain=benchmark.domain,
                                           acquisition_function=qLogNEHVI(), seed=seed))
    strategy.tell(experiments)

    candidates = benchmark.grid[benchmark.parameter_keys]
    tested = {benchmark._key(row) for _, row in experiments.iterrows()}
    keep = [i for i, (_, row) in enumerate(candidates.iterrows())
            if benchmark._key(row) not in tested]
    candidates = candidates.iloc[keep].reset_index(drop=True)

    transformed = strategy.domain.inputs.transform(candidates,
                                                   strategy.input_preprocessing_specs)
    tensor = torch.from_numpy(transformed.values.astype(float)).to(torch.double).unsqueeze(-2)
    with torch.no_grad():
        values = strategy._get_acqfs(1)[0](tensor).cpu().numpy()

    top = values.max()
    tied = np.flatnonzero(values >= top - RELATIVE_TIE * (abs(top) + 1e-30))
    print("%s apres %d experiences | %d candidats restants" % (stem, at, len(values)))
    print("   acquisition : max %.6g, mediane %.6g, min %.6g" %
          (top, np.median(values), values.min()))
    print("   ex aequo au maximum : %d (%.1f%%)" % (len(tied), 100.0 * len(tied) / len(values)))

    # Which categorical cells has the campaign actually visited? A tie is
    # expected between two cells it has never seen, and would be a bug between
    # two it has.
    keys = [k for k in benchmark.parameter_keys
            if not pd.api.types.is_numeric_dtype(benchmark.grid[k])]
    if keys and len(tied) > 1:
        def cell(frame, position):
            return tuple(frame.iloc[position][k] for k in keys)
        seen = {cell(experiments, i) for i in range(len(experiments))}
        total = len(benchmark.grid.groupby(keys, observed=True).size())
        unseen = sum(1 for i in tied if cell(candidates, i) not in seen)
        print("   cellules %s visitees : %d / %d" % ("x".join(keys), len(seen), total))
        print("   ex aequo dans une cellule jamais visitee : %d / %d" % (unseen, len(tied)))
    return len(tied)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", help="log stem, e.g. edbo_ch_arylation__no_hitl__seed01")
    parser.add_argument("--at", type=int, default=30, help="experiments to replay")
    parser.add_argument("--suzuki", action="store_true",
                        help="check the four Suzuki cases at 20, 30 and 40 experiments")
    args = parser.parse_args()

    warnings.filterwarnings("ignore")
    pin_torch_threads()
    limit_acquisition_memory()

    if args.suzuki:
        for case in ("i", "ii", "iii", "iv"):
            for at in (20, 30, 40):
                probe("%s__no_hitl__seed01" % case, at)
        return
    if not args.log:
        raise SystemExit("donnez --log ou --suzuki")
    probe(args.log, args.at)


if __name__ == "__main__":
    main()

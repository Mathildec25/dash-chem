"""One-off provenance check for the Minerva benchmark grids.

The four CSV grids in this directory come from the Minerva repository
(https://github.com/schwallergroup/minerva, benchmark_datasets/olympus_suzuki).
They already carry the `yield` and `turnover` columns, so the benchmark itself
never needs Olympus. This script exists only to document, once, that those
columns really are the output of the matching Olympus emulator.

It is NOT part of the benchmark and is not needed to reproduce any result.
Running it requires the separate Olympus environment:

    conda activate olympus_env
    export PYTHONPATH=".../olympus/src"
    export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
    python verify_grids_against_olympus.py

Recorded output is reproduced in README.md next to this file.
"""

import os

import numpy as np
import pandas as pd

# --- configuration ---------------------------------------------------------
CASES = ["i", "ii", "iii", "iv"]
EMULATOR_MODEL = "BayesNeuralNet"
# Forward passes averaged per point. The emulator is a Bayesian neural net, so
# a single pass is stochastic; 50 keeps the residual noise well below the
# agreement we are trying to demonstrate.
NUM_SAMPLES = 50
# Points drawn from each 5670-point grid. The full grid would work too; a
# subsample keeps the check quick and the conclusion is identical.
N_POINTS = 3000
RANDOM_SEED = 0
HERE = os.path.dirname(os.path.abspath(__file__))


def load_grid(case):
    """Return the grid and its conditions as Olympus expects them.

    The CSV stores the ligand one-hot encoded across columns L0..L6; Olympus
    wants the ligand label back, followed by the three continuous variables.
    """
    df = pd.read_csv(os.path.join(HERE, "suzuki_%s.csv" % case), index_col=0)
    ligand_columns = [c for c in df.columns if c.startswith("L")]
    ligands = np.array(ligand_columns)[df[ligand_columns].to_numpy().argmax(axis=1)]
    conditions = [
        [ligand, float(t), float(temp), float(load)]
        for ligand, t, temp, load in zip(
            ligands, df.res_time, df.temperature, df.catalyst_loading
        )
    ]
    return df, conditions


def compare(grid_case, emulator_case):
    """Compare a grid's stored yields against a freshly run Olympus emulator."""
    from olympus import Emulator

    df, conditions = load_grid(grid_case)
    rng = np.random.RandomState(RANDOM_SEED)
    picked = rng.choice(len(conditions), size=min(N_POINTS, len(conditions)), replace=False)

    emulator = Emulator(dataset="suzuki_%s" % emulator_case, model=EMULATOR_MODEL)
    predicted = np.asarray(emulator.run([conditions[i] for i in picked], num_samples=NUM_SAMPLES)[0])

    stored = df["yield"].to_numpy()[picked]
    fresh = predicted[:, 0]
    return {
        "grid": grid_case,
        "emulator": emulator_case,
        "r": float(np.corrcoef(stored, fresh)[0, 1]),
        "mean_abs_error": float(np.mean(np.abs(stored - fresh))),
        "bias": float(np.mean(fresh - stored)),
    }


def main():
    print("%-6s %-9s %8s %10s %8s" % ("grid", "emulator", "r", "mean|err|", "bias"))
    for case in CASES:
        row = compare(case, case)
        print("%-6s %-9s %8.4f %10.2f %+8.2f"
              % (row["grid"], row["emulator"], row["r"], row["mean_abs_error"], row["bias"]))

    # Control. The suzuki_ii grid was laid out on case I's catalyst-loading
    # bounds, so we check explicitly that its yields are not case I's either.
    row = compare("ii", "i")
    print("\nControl, grid ii against the WRONG emulator (i):")
    print("%-6s %-9s %8.4f %10.2f %+8.2f"
          % (row["grid"], row["emulator"], row["r"], row["mean_abs_error"], row["bias"]))


if __name__ == "__main__":
    main()

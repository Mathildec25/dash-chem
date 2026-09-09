"""The benchmark landscape: a pre-evaluated grid of reaction conditions.

A benchmark is one of the four Reizman-Suzuki cases, stored as a complete grid
of 5670 conditions with their yield and turnover already computed (see
data/README.md for provenance). Nothing is emulated at run time: evaluating a
point is a table lookup, so a campaign is limited by the optimiser, not by the
chemistry model.

The grid is the exact Cartesian product of its levels, which lets us hand
BoFire a purely combinatorial domain: seven ligands as a CategoricalInput and
the three process variables as DiscreteInputs. BoFire then enumerates every
combination, drops the ones already run, and evaluates the acquisition function
on all the rest. That is exactly the protocol's "on a grid, the acquisition is
evaluated on every untested point".
"""

import os

import numpy as np
import pandas as pd
from bofire.data_models.api import Domain, Inputs, Outputs
from bofire.data_models.features.api import (
    CategoricalInput,
    ContinuousOutput,
    DiscreteInput,
)
from bofire.data_models.objectives.api import MaximizeObjective

from hitl_bench import metrics

# --- frozen description of the benchmark -----------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CASES = ["i", "ii", "iii", "iv"]
LIGANDS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
LIGAND_KEY = "ligand"
PROCESS_KEYS = ["res_time", "temperature", "catalyst_loading"]
PARAMETER_KEYS = [LIGAND_KEY] + PROCESS_KEYS
OBJECTIVES = ["yield", "turnover"]
# BoFire tags every objective column with a companion validity flag and adds it
# in place to whatever frame it is handed. We carry them ourselves so that rows
# appended later keep the same columns.
VALID_KEYS = ["valid_%s" % objective for objective in OBJECTIVES]
# Grid levels are exact floats read from the CSV, so rounding only guards
# against a float that has been through BoFire's transform and back.
KEY_DECIMALS = 6


class GridBenchmark:
    """One Suzuki case: its grid, its BoFire domain and its reference values."""

    def __init__(self, case, data_dir=DATA_DIR):
        if case not in CASES:
            raise ValueError("unknown case %r, expected one of %s" % (case, CASES))
        self.case = case
        self.path = os.path.join(data_dir, "suzuki_%s.csv" % case)
        # Exposed as attributes so that the campaign loop works with any
        # benchmark, not only this one. The module constants stay as the
        # defaults for this family.
        self.parameter_keys = list(PARAMETER_KEYS)
        self.objectives = list(OBJECTIVES)
        self.valid_keys = list(VALID_KEYS)
        self.name = "suzuki_%s" % case

        grid = pd.read_csv(self.path, index_col=0)
        grid[LIGAND_KEY] = np.array(LIGANDS)[grid[LIGANDS].to_numpy().argmax(axis=1)]
        self.grid = grid

        self.levels = {key: sorted(grid[key].unique().tolist()) for key in PROCESS_KEYS}
        self.domain = self._build_domain()
        self._lookup = {self._key(row): (row["yield"], row["turnover"])
                        for _, row in grid.iterrows()}

        # Normalisation bounds and reference values, taken over the whole grid:
        # the global front is known exactly because the grid is exhaustive.
        raw = grid[OBJECTIVES].to_numpy(dtype=float)
        self.objective_min = raw.min(axis=0)
        self.objective_max = raw.max(axis=0)
        self.true_front = metrics.pareto_front(self.normalise(raw))
        self.max_hypervolume = metrics.hypervolume(self.true_front)
        # Which ligands carry the global front. For case ii this is L4 alone,
        # which is what makes it a ligand-selection trap.
        self.front_ligands = sorted(set(grid[LIGAND_KEY].to_numpy()[
            metrics.pareto_mask(self.normalise(raw))]))

    # --- domain -----------------------------------------------------------
    def _build_domain(self):
        inputs = Inputs(features=(
            [CategoricalInput(key=LIGAND_KEY, categories=list(LIGANDS))]
            + [DiscreteInput(key=key, values=self.levels[key]) for key in PROCESS_KEYS]
        ))
        outputs = Outputs(features=[
            ContinuousOutput(key=objective, objective=MaximizeObjective(w=1.0))
            for objective in OBJECTIVES
        ])
        return Domain(inputs=inputs, outputs=outputs)

    # --- evaluation -------------------------------------------------------
    @staticmethod
    def _key(row):
        return (row[LIGAND_KEY],) + tuple(
            round(float(row[key]), KEY_DECIMALS) for key in PROCESS_KEYS
        )

    def evaluate(self, row):
        """Look one set of conditions up in the grid.

        Returns a dict holding the conditions, both objectives and the validity
        flags, ready to be appended to an experiments frame.
        """
        key = self._key(row)
        if key not in self._lookup:
            raise KeyError("conditions are not on the grid: %r" % (key,))
        yield_, turnover = self._lookup[key]
        record = {name: row[name] for name in PARAMETER_KEYS}
        record["yield"] = float(yield_)
        record["turnover"] = float(turnover)
        for valid_key in VALID_KEYS:
            record[valid_key] = 1
        return record

    # --- objectives -------------------------------------------------------
    def normalise(self, raw):
        """Map raw objectives onto [0, 1] using the grid's own min and max."""
        raw = np.asarray(raw, dtype=float)
        return (raw - self.objective_min) / (self.objective_max - self.objective_min)

    def hypervolume(self, experiments):
        """Normalised hypervolume held by a set of experiments."""
        return metrics.hypervolume(self.normalise(experiments[OBJECTIVES].to_numpy()))

    def igd_plus(self, experiments):
        """IGD+ of a set of experiments against the grid's true front."""
        return metrics.igd_plus(self.true_front,
                                self.normalise(experiments[OBJECTIVES].to_numpy()))

    def __repr__(self):
        return ("GridBenchmark(case=%r, points=%d, front=%d points on %s, max HV=%.4f)"
                % (self.case, len(self.grid), len(self.true_front),
                   "/".join(self.front_ligands), self.max_hypervolume))

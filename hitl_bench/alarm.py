# -*- coding: utf-8 -*-
"""The study's alarm, applied to a real REACTO campaign.

A REACTO project is an Excel sheet of experiments: a "Point type" column
(Init, BO, or whatever the user writes), the parameters, the objectives. This
module reads that sheet the way the bench reads its own logs, computes the
progress curve, and asks the frozen trigger where it fires:

    P* = recent pace / average pace, both per experiment
    W = 5, threshold 0.30, cooldown 5, first alert after 5 optimiser proposals

The bench expresses those as fractions of a 40-experiment budget; a real
campaign has no budget, so the fractions are evaluated at 40 here, which gives
exactly the frozen absolute values whatever the campaign's length.

Progress is measured on the completed experiments only, in sheet order:
- one objective: the best value so far;
- two objectives: the hypervolume of the bench (`hitl_bench.metrics`);
- three or more: BoTorch's hypervolume.
Objectives are normalised to [0, 1] by their observed range and oriented so
that more is better, so the curve is unit-free and a minimised objective counts
the right way. The normalisation is recomputed each time the sheet changes;
P* being a ratio of gains, that costs nothing.

What the user decided at each alert is kept in the project's metadata
(`hitl_log`), so that an answered alert does not come back and a stopped
campaign stays stopped.
"""

import datetime

import numpy as np

from hitl_bench import metrics, triggers

BUDGET_FOR_WINDOWS = 40        # the frozen fractions x 40 = 5 experiments each
INIT_TYPES = {"init", "lhs", "initial", "start"}
CHEMIST_TYPES = {"chemist", "human", "manual"}
CHOICES = ("continue", "chemist", "stop")


def _complete(value):
    if value is None or value == "":
        return False
    try:
        return not np.isnan(float(value))
    except (TypeError, ValueError):
        return False


def completed_rows(table_rows, objective_names):
    """The experiments that have every objective filled, in sheet order."""
    return [r for r in table_rows if all(_complete(r.get(o)) for o in objective_names)]


def _phase(row):
    kind = str(row.get("Point type", "") or "").strip().lower()
    if kind in INIT_TYPES:
        return "lhs"
    if kind in CHEMIST_TYPES:
        return "chemist"
    return "bo"


def progress_curve(rows, objectives):
    """Unit-free progress after each completed experiment, non-decreasing."""
    names = [o["name"] for o in objectives]
    if not rows:
        return []
    raw = np.array([[float(r[n]) for n in names] for r in rows], dtype=float)
    sign = np.array([-1.0 if str(o.get("direction", "max")).lower().startswith("min") else 1.0
                     for o in objectives])
    oriented = raw * sign
    lo, hi = oriented.min(axis=0), oriented.max(axis=0)
    span = np.where(hi - lo > 0, hi - lo, 1.0)
    F = (oriented - lo) / span
    curve = []
    if F.shape[1] == 1:
        for i in range(len(F)):
            curve.append(float(F[: i + 1, 0].max()))
    elif F.shape[1] == 2:
        for i in range(len(F)):
            curve.append(metrics.hypervolume(F[: i + 1]))
    else:
        import torch
        from botorch.utils.multi_objective.hypervolume import Hypervolume
        hv = Hypervolume(ref_point=torch.zeros(F.shape[1], dtype=torch.double))
        from botorch.utils.multi_objective.pareto import is_non_dominated
        for i in range(len(F)):
            Y = torch.as_tensor(F[: i + 1], dtype=torch.double)
            curve.append(float(hv.compute(Y[is_non_dominated(Y)])))
    return curve


def records(table_rows, objectives):
    """The completed experiments as the trigger reads them."""
    names = [o["name"] for o in objectives]
    rows = completed_rows(table_rows, names)
    curve = progress_curve(rows, objectives)
    return [{"experiment": i + 1, "phase": _phase(r), "hypervolume": h}
            for i, (r, h) in enumerate(zip(rows, curve))]


def state(table_rows, objectives, log):
    """Where the campaign stands with respect to the alarm.

    Returns a dict: `n_done` completed experiments, `n_init` of them from the
    initial design, `alerts` (every experiment at which the trigger fires on
    this history), `pending` (the latest alert not yet answered, or None),
    `p_star` at the last experiment, `stopped` (the user answered "stop").
    """
    log = log or []
    recs = records(table_rows, objectives)
    n_init = sum(1 for r in recs if r["phase"] == "lhs")
    alerts = triggers.firing_times(triggers.pace_ratio, recs, n_init, BUDGET_FOR_WINDOWS) if recs else []
    answered = {int(entry["experiment"]) for entry in log}
    stopped = any(entry.get("choice") == "stop" for entry in log)
    pending = None
    if alerts and not stopped:
        last = alerts[-1]
        # only the latest alert can be pending: an older one the user never
        # answered has been overtaken by the experiments run since
        if last not in answered and last == len(recs):
            pending = last
    p_star = triggers.pace_ratio_value(recs, BUDGET_FOR_WINDOWS) if recs else None
    return {"n_done": len(recs), "n_init": n_init, "alerts": alerts, "pending": pending,
            "p_star": p_star, "stopped": stopped}


def log_entry(experiment, choice, why, p_star):
    if choice not in CHOICES:
        raise ValueError("unknown choice %r" % choice)
    return {"experiment": int(experiment), "choice": choice, "why": why,
            "p_star": None if p_star is None else round(float(p_star), 4),
            "when": datetime.datetime.now().isoformat(timespec="seconds")}

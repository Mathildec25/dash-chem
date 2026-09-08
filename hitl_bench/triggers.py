"""Candidate stall signals, and the driver that turns one into firing times.

Every signal shares one signature: it is handed the campaign's own history up
to the current experiment and answers yes or no. Nothing here may look at the
global front, the true Pareto set or anything else a running campaign could not
know, otherwise the comparison is rigged.

Two design rules, both aimed at transferring to a reaction we have not seen:

- **As few parameters as possible.** Each one is a chance to overfit the two
  cases we are allowed to choose on.
- **Dimensionless quantities only.** A threshold in yield points means nothing
  across reactions: case ii tops out at 44% yield and case iv at 91%. Windows
  are fractions of the budget, thresholds are ratios or multiples of the
  model's own uncertainty.

`plateau` reads the hypervolume curve alone. The other three read what the
surrogate expected of the point it proposed, which campaigns log from
`Record what the surrogate expected of each proposed point` onwards; run them
on an older log and they simply never fire.
"""

import numpy as np

from hitl_bench import metrics
from hitl_bench.benchmark import OBJECTIVES

EPS = 1e-12

# --- shared firing discipline ---------------------------------------------
# Counted in experiments, initial design included.
BURN_IN_FRACTION = 0.075     # ~3 experiments past the initial design on a budget of 40
COOLDOWN_FRACTION = 0.075    # ~3 experiments between two firings


def _window(budget, fraction, floor=2):
    return max(floor, int(round(fraction * budget)))


def _bo_records(history):
    return [r for r in history if r["phase"] == "bo"]


def _beliefs(history, key):
    """The model's recorded belief for each BO experiment, newest last."""
    out = []
    for record in _bo_records(history):
        model = record.get("model") or {}
        value = model.get(key)
        if value is not None:
            out.append(float(value))
    return out


# --- the candidates --------------------------------------------------------
def plateau(history, budget, fraction=0.125):
    """No hypervolume improvement for the last K experiments.

    The honest representative of the hypervolume-curve family, kept as the
    floor every other candidate has to beat. K is a fraction of the budget so
    that it means the same thing on a campaign of 40 or of 100 experiments.
    """
    k = _window(budget, fraction)
    curve = [r["hypervolume"] for r in history]
    if len(curve) <= k:
        return False
    return curve[-1] - curve[-1 - k] <= EPS


def over_optimism(history, budget, fraction=0.15, threshold=0.5):
    """The model keeps promising more than it delivers.

    Averages the standardised residual over a window: how far reality fell
    short of the posterior mean, in units of the model's own standard
    deviation. Firing when that average drops below -threshold catches a
    surrogate that is systematically wrong in the optimistic direction, which
    is what a campaign extrapolating from one over-exploited region looks like.
    """
    w = _window(budget, fraction)
    surprises = []
    for objective in OBJECTIVES:
        values = _beliefs(history, "%s_surprise" % objective)
        if len(values) >= w:
            surprises.append(np.mean(values[-w:]))
    if not surprises:
        return False
    return float(np.mean(surprises)) < -threshold


def exhausted_promises(history, budget, fraction=0.1):
    """The model proposes points it predicts to be dominated by what we have.

    When the surrogate can no longer name a point it believes would improve the
    front, it has stopped expecting anything. That happens both when a campaign
    has genuinely converged and when it has convinced itself, on thin evidence,
    that the rest of the space is worthless. We do not try to tell those apart:
    intervening on a converged campaign costs one experiment, missing a trapped
    one costs the campaign.
    """
    w = _window(budget, fraction)
    bo = _bo_records(history)
    if len(bo) < w:
        return False

    for record in bo[-w:]:
        model = record.get("model") or {}
        predicted = [model.get("%s_pred" % o) for o in OBJECTIVES]
        if any(p is None for p in predicted):
            return False
        # The front as it stood before this experiment was run.
        index = history.index(record)
        achieved = np.array([[h[o] for o in OBJECTIVES] for h in history[:index]], dtype=float)
        if len(achieved) == 0:
            return False
        front = achieved[metrics.pareto_mask(achieved)]
        promise = np.array(predicted, dtype=float)
        dominated = ((front >= promise).all(axis=1) & (front > promise).any(axis=1)).any()
        if not dominated:
            return False        # it still promised something at least once
    return True


def confidence_without_evidence(history, budget, fraction=0.5):
    """The model's uncertainty has collapsed relative to its own early value.

    Expressed as a ratio to the median uncertainty over the first BO
    iterations of this same campaign, so it carries no units and needs no
    knowledge of the reaction's scale. A surrogate whose uncertainty has fallen
    this far believes it has nothing left to learn.
    """
    reference_window = _window(budget, 0.125)
    ratios = []
    for objective in OBJECTIVES:
        deviations = _beliefs(history, "%s_sd" % objective)
        if len(deviations) < reference_window + 1:
            continue
        early = float(np.median(deviations[:reference_window]))
        if early > EPS:
            ratios.append(deviations[-1] / early)
    if not ratios:
        return False
    return float(np.mean(ratios)) < fraction


CANDIDATES = {
    "plateau": plateau,
    "over_optimism": over_optimism,
    "exhausted_promises": exhausted_promises,
    "confidence_without_evidence": confidence_without_evidence,
}


# --- driver ----------------------------------------------------------------
def firing_times(signal, records, n_init, budget):
    """Every experiment at which `signal` would fire over a finished campaign.

    Applies the shared discipline: nothing before the burn-in, and nothing
    within the cooldown of a previous firing. Both are counted in experiments,
    initial design included, and both are fractions of the budget.
    """
    burn_in = n_init + _window(budget, BURN_IN_FRACTION)
    cooldown = _window(budget, COOLDOWN_FRACTION)
    fires, last = [], None
    for position in range(len(records)):
        experiment = records[position]["experiment"]
        if experiment < burn_in:
            continue
        if last is not None and experiment - last <= cooldown:
            continue
        if signal(records[: position + 1], budget):
            fires.append(experiment)
            last = experiment
    return fires

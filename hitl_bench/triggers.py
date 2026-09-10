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
# One fraction of the budget governs all three timings, which is both simpler
# and forced: they are not independent. On a budget of 40 it makes each of them
# 5 experiments.
#
# The lookback W is the window the recent pace is measured over. Five rather
# than three: averaging over five steps stops a single flat experiment from
# looking like a stall, at the cost of needing five experiments of stagnation
# before the ratio collapses.
#
# The burn-in is then *forced* to n_init + W, not chosen. A shorter one would
# let the lookback window reach back into the initial design, so the "recent
# pace" would mix LHS draws with BO proposals - two different processes, one of
# which is not optimisation at all. With W = 3 and a burn-in of n_init + 3 that
# happened to be exactly avoided; with W = 5 it no longer is, so the burn-in
# follows W instead of carrying its own constant.
#
# The cooldown stays 5. Measured on the ten selection campaigns: 2.7
# solicitations per campaign against 3.5 at a cooldown of 3, worst case 4
# rather than 6, and every campaign still gets at least one. A cooldown cannot
# change a first firing, only the ones after it, so this costs nothing in
# detection and only lightens what the chemist is asked.
WINDOW_FRACTION = 0.125
COOLDOWN_FRACTION = WINDOW_FRACTION
# Nobody is disturbed before the optimiser has actually proposed something: at
# least five BO experiments past the initial design, whatever the lookback. Two
# separate reasons converge on the same number and both must hold, so the
# burn-in is the larger of the two.
#
#   - a floor on evidence: three proposals are not a campaign, and asking a
#     chemist to judge one is asking them to judge the initial design;
#   - a floor forced by the window: the lookback must not reach back into the
#     LHS, or the "recent pace" would be measured partly on draws that were
#     never proposals. That requires burn-in >= n_init + W.
#
# On a budget of 40 the first firing can therefore be experiment 15 at the
# earliest, for W = 3 as well as for W = 5.
MIN_BO_FRACTION = 0.125

# The threshold P* is compared to. 0.30 reads as "advancing three times more
# slowly than this campaign has been", and it is chosen with W = 5 rather than
# separately: detection is set by the pair, not by either alone.
#
# Measured on the 18 case II campaigns, cooldown 5, every setting reaching full
# coverage of the failed campaigns:
#
#     W=3 threshold 0.10  3.1 alerts  0 silent  first firing 19.4  35% left
#     W=5 threshold 0.30  2.5 alerts  1 silent  first firing 22.6  26% left
#
# W = 5 with 0.30 was adopted: it costs three experiments of lateness and nine
# points of remaining margin, and saves 0.6 solicitation per campaign - more on
# the arylation, 3.7 against 4.3. Its single silent campaign is the one that
# ends at 100% of the front, which is the only campaign it is right never to
# interrupt. At W = 5 a threshold of 0.10 would leave four campaigns silent, two
# of them failures: the threshold is not independent of the window.
THRESHOLD = 0.30


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


def pace_ratio(history, budget, fraction=WINDOW_FRACTION, threshold=THRESHOLD):
    """The campaign's recent pace against its own average pace. The study's trigger.

    This is the study owner's original signal with its denominator fixed. Hers
    divided the recent gain by the gain accumulated since the initial design,
    which makes the ratio fall like 1/t whatever the campaign does: under
    perfectly steady progress it equals W/(t - n_init), so the threshold was
    silently encoding a firing time. With a lookback of 3, a threshold of 0.05
    is reached by that decay alone at experiment 70 and one of 0.30 at
    experiment 20.

    Dividing by that same decay removes it. P* is the recent pace over the
    average pace, so it equals 1 while a campaign progresses steadily, at any
    point in the campaign, and a threshold of 0.10 means what it says: the
    campaign is advancing ten times more slowly than it has been.

    A campaign that has gained nothing at all since the initial design is the
    most stalled case there is, so it scores 0 and fires, where the original
    formula divided by zero.

    Known blind spot, and it has no fix inside the campaign's own history: a
    campaign that crawls slowly but *steadily* has a recent pace equal to its
    average pace, scores 1, and never fires. Saying "this campaign is slow"
    needs a reference for how fast it should be going, and the only one
    available live is the model's own expectation, which is what over_optimism
    reads.
    """
    value = pace_ratio_value(history, budget, fraction)
    return value is not None and value < threshold


def pace_ratio_value(history, budget, fraction=WINDOW_FRACTION):
    """P* itself, or None where it is not defined yet.

    Split out of `pace_ratio` so that a figure can plot the very number the
    trigger compares to its threshold. A plotting script that recomputes the
    signal is a figure that will eventually disagree with the trigger it
    claims to illustrate, which is how the earlier plot_triggers.py drifted.
    """
    window = _window(budget, fraction, floor=3)
    # The lookback must not reach into the initial design, or the recent
    # pace would be measured partly on draws that were never proposals.
    curve = [record["hypervolume"] for record in history]
    experiment = len(curve)
    n_init = sum(1 for record in history if record["phase"] == "lhs")
    if experiment <= max(window, n_init):
        return None

    total = curve[-1] - curve[n_init - 1]
    if total <= EPS:
        # Nothing gained at all since the initial design: the most stalled a
        # campaign can be, so it scores zero rather than dividing by zero.
        return 0.0
    recent_pace = (curve[-1] - curve[-1 - window]) / window
    average_pace = total / (experiment - n_init)
    return recent_pace / average_pace


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


def original_ratio(history, budget, fraction=0.075, threshold=0.05):
    """The study owner's first signal, kept runnable so it can be compared.

    Recent gain over the gain accumulated since the initial design. It is the
    formula pace_ratio replaced, and it is here for one reason: an article that
    says "we adopted this trigger" has to be able to show what it was measured
    against, and the first version is the most relevant comparison of all.

    Its defect is arithmetic rather than empirical. Under perfectly steady
    progress with gain g per experiment, the numerator is W*g and the
    denominator (t - n_init)*g, so the ratio equals W/(t - n_init) and falls
    like 1/t whatever the campaign does. The threshold therefore encodes a
    firing time rather than a state: with W = 3, a threshold of 0.05 is crossed
    by that decay alone around experiment 70, and one of 0.30 around experiment
    20. Defaults are the owner's own: lookback 3, threshold 0.05.
    """
    value = original_ratio_value(history, budget, fraction)
    return value is not None and value < threshold


def original_ratio_value(history, budget, fraction=0.075):
    """The original ratio itself, so a figure can show what it compares."""
    window = _window(budget, fraction, floor=3)
    curve = [record["hypervolume"] for record in history]
    experiment = len(curve)
    n_init = sum(1 for record in history if record["phase"] == "lhs")
    if experiment <= max(window, n_init):
        return None
    total = curve[-1] - curve[n_init - 1]
    if total <= EPS:
        return 0.0                       # elle divisait par zero ici
    return (curve[-1] - curve[-1 - window]) / total


CANDIDATES = {
    "pace_ratio": pace_ratio,
    "original_ratio": original_ratio,
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
    burn_in = n_init + max(_window(budget, MIN_BO_FRACTION),
                           _window(budget, WINDOW_FRACTION))
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

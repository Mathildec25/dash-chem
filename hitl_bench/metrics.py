"""Performance metrics for a multi-objective campaign.

Everything here works on **normalised** objectives: each objective is mapped to
[0, 1] by its minimum and maximum over the whole benchmark grid, and both are
maximised. The hypervolume reference point is therefore (0, 0).

That convention is the one frozen in the study protocol. It is also, up to a
constant factor, the one used by Minerva (Sin et al., Nat. Commun. 2025), who
keep raw units and take the element-wise worst point of the dataset as the
reference: normalising by the range and referencing (0, 0) divides their
hypervolume by (range of objective 1) x (range of objective 2). Verified
numerically on all four Suzuki grids, identical to six decimals. Expressed as a
fraction of the grid's total hypervolume, the two conventions give the same
number.
"""

import numpy as np


def pareto_mask(F):
    """Boolean mask of the non-dominated rows of F. All columns are maximised.

    A row is dominated when another row is at least as good on every objective
    and strictly better on at least one.
    """
    F = np.asarray(F, dtype=float)
    keep = np.ones(len(F), dtype=bool)
    for i in range(len(F)):
        if not keep[i]:
            continue
        dominated_by_any = ((F >= F[i]).all(axis=1) & (F > F[i]).any(axis=1)).any()
        if dominated_by_any:
            keep[i] = False
    return keep


def pareto_front(F):
    """The non-dominated rows of F, sorted by the first objective, descending."""
    F = np.asarray(F, dtype=float)
    front = F[pareto_mask(F)]
    return front[np.argsort(-front[:, 0])]


def hypervolume(F, ref=(0.0, 0.0)):
    """Hypervolume of a two-objective maximisation set against `ref`.

    Points that fall below the reference on either objective contribute
    nothing and are dropped, which is what the reference point is for.
    """
    F = np.asarray(F, dtype=float)
    ref = np.asarray(ref, dtype=float)
    F = F[(F >= ref).all(axis=1)]
    if len(F) == 0:
        return 0.0
    front = pareto_front(F)
    volume, previous = 0.0, ref[1]
    for x, y in front:
        volume += (x - ref[0]) * (y - previous)
        previous = y
    return float(volume)


def igd_plus(true_front, approx_set):
    """IGD+ between the true Pareto front and the points found so far.

    For every point of the true front we measure how far the best point found
    falls short of it, counting only the objectives on which it is actually
    worse, then average over the true front. Lower is better; zero means every
    point of the true front has been matched or dominated.

    Unlike the hypervolume, this degrades gracefully. On a front of three
    points the hypervolume advances in steps and barely moves until a campaign
    lands exactly on one of them, whereas IGD+ rewards getting close.
    """
    true_front = np.asarray(true_front, dtype=float)
    approx_set = np.asarray(approx_set, dtype=float)
    if len(approx_set) == 0:
        return float("inf")
    # shortfall[t, a, k] = how much approx point a misses true point t on
    # objective k, zero where the approx point is already at least as good
    shortfall = np.clip(true_front[:, None, :] - approx_set[None, :, :], 0.0, None)
    distances = np.sqrt((shortfall ** 2).sum(axis=2))
    return float(distances.min(axis=1).mean())


def curve_auc(values, start=0):
    """Area under a curve sampled at unit intervals, from index `start` on.

    Trapezoidal rule over the experiment index. `start` is where the count
    begins, used to drop the initial design so that only the optimisation
    phase is scored.
    """
    values = np.asarray(values, dtype=float)[start:]
    if len(values) < 2:
        return 0.0
    return float(np.trapezoid(values)) if hasattr(np, "trapezoid") else float(np.trapz(values))


def mean_after(values, start=0):
    """Mean of a curve after `start`.

    This is curve_auc divided by its span, so it carries the same information
    on a fixed budget but stays readable as "the average fraction of the
    hypervolume held during the optimisation phase".
    """
    values = np.asarray(values, dtype=float)[start:]
    return float(values.mean()) if len(values) else 0.0

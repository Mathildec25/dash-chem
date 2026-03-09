"""
utils/constrained_mobo.py
==========================
Constrained Multi-Objective Bayesian Optimization via direct BoTorch.

This module bypasses BoFire's MoboStrategy acquisition function construction
to support outcome_constraints — i.e., keeping the same output as BOTH a
Pareto objective AND a feasibility constraint (e.g. Yield is maximized while
also requiring Yield >= 80).

Architecture:
    1. BoFire fits the GP models (via MoboStrategy.tell) → reuses all its
       input encoding (CategoricalDescriptorInput, DiscreteInput, etc.)
    2. A large candidate pool is generated and preprocessed into the model's
       input space (encoded + normalized)
    3. BoTorch's qLogNoisyExpectedHypervolumeImprovement is built with
       outcome_constraints callables derived from the user's thresholds
    4. The acquisition function is evaluated on the pool
    5. The top-scoring candidates are returned in original domain space

Why pool-based instead of gradient-based optimize_acqf?
    Mixed discrete/categorical search spaces (the norm in chemistry) make
    gradient-based optimization meaningless after decoding. Evaluating the
    acq function on a large feasible pool is the standard practical approach
    for such spaces (cf. Shields et al. Nature 2021, EDBO).

Usage:
    from utils.constrained_mobo import constrained_mobo_botorch

    output_constraints = [
        {
            'output_key': 'Yield',
            'direction': '>=',   # or '<='
            'threshold': 80.0,
        }
    ]
    candidates = constrained_mobo_botorch(
        domain=domain,
        experiments=experiments,
        n_candidates=1,
        output_constraints=output_constraints,
    )
"""

import numpy as np
import pandas as pd
import torch

import bofire.strategies.api as strategies
from bofire.data_models.acquisition_functions.api import qLogNEHVI
from bofire.data_models.strategies.api import MoboStrategy, RandomStrategy as RandomStrategyDM
from bofire.data_models.objectives.api import MinimizeObjective, MaximizeObjective


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def constrained_mobo_botorch(
    domain,
    experiments: pd.DataFrame,
    n_candidates: int = 1,
    output_constraints: list = None,
) -> pd.DataFrame:
    """
    Run MOBO with outcome constraints (threshold on one measured output).

    The constrained output remains a full Pareto objective AND is subject to
    a PoF (Probability of Feasibility) weight in the acquisition function.
    This is not possible with BoFire's MoboStrategy alone.

    Args:
        domain:             BoFire Domain object (all objectives as min/max).
        experiments:        DataFrame of completed experiments.
        n_candidates:       Number of candidates to return.
        output_constraints: List of constraint dicts:
            [{'output_key': str, 'direction': '>=' or '<=', 'threshold': float}]

    Returns:
        DataFrame with suggested candidates in original domain space.
    """
    output_constraints = output_constraints or []

    print("🔒 Constrained MOBO (BoTorch direct) — "
          f"{len(output_constraints)} outcome constraint(s)")
    for c in output_constraints:
        print(f"   Constraint: {c['output_key']} {c['direction']} {c['threshold']}")

    # ------------------------------------------------------------------
    # Step 1 — Fit GP models via BoFire (reuses all its preprocessing)
    # ------------------------------------------------------------------
    data_model = MoboStrategy(domain=domain, acquisition_function=qLogNEHVI())
    strat = strategies.map(data_model)
    strat.tell(experiments=experiments)
    model = strat.model  # fitted ModelListGP

    # ------------------------------------------------------------------
    # Step 2 — Generate candidate pool in original domain space
    # ------------------------------------------------------------------
    candidate_pool_df = _generate_candidate_pool(domain, n_pool=2048)
    print(f"   📊 Candidate pool: {len(candidate_pool_df)} points")

    # ------------------------------------------------------------------
    # Step 3 — Preprocess pool to model input space (encode + normalize)
    # ------------------------------------------------------------------
    X_pool_norm = _preprocess_to_model_space(candidate_pool_df, domain, model)
    print(f"   📐 Preprocessed shape: {X_pool_norm.shape}")

    # ------------------------------------------------------------------
    # Step 4 — Build outcome_constraints callables for BoTorch
    # ------------------------------------------------------------------
    constraint_callables = _build_constraint_callables(
        domain, output_constraints
    )

    # ------------------------------------------------------------------
    # Step 5 — Build reference point from existing data
    # ------------------------------------------------------------------
    ref_point = _compute_ref_point(domain, experiments)
    print(f"   🎯 Reference point: {ref_point.tolist()}")

    # ------------------------------------------------------------------
    # Step 6 — Build constrained qLogNEHVI
    # ------------------------------------------------------------------
    X_baseline = _get_x_baseline(model)

    from botorch.acquisition.multi_objective.logei import (
        qLogNoisyExpectedHypervolumeImprovement,
    )

    acq = qLogNoisyExpectedHypervolumeImprovement(
        model=model,
        ref_point=ref_point,
        X_baseline=X_baseline,
        constraints=constraint_callables if constraint_callables else None,
        prune_baseline=True,
        cache_root=False,
    )

    # ------------------------------------------------------------------
    # Step 7 — Evaluate acq function on candidate pool
    # ------------------------------------------------------------------
    acq.eval()
    model.eval()

    batch_size = 256  # avoid OOM
    acq_values_list = []
    with torch.no_grad():
        for i in range(0, len(X_pool_norm), batch_size):
            batch = X_pool_norm[i : i + batch_size].unsqueeze(-2)
            vals = acq(batch)
            acq_values_list.append(vals)
    acq_values = torch.cat(acq_values_list, dim=0)

    # ------------------------------------------------------------------
    # Step 8 — Select top-n candidates
    # ------------------------------------------------------------------
    n_select = min(n_candidates, len(candidate_pool_df))
    top_indices = acq_values.topk(n_select).indices.cpu().numpy()

    best_candidates = candidate_pool_df.iloc[top_indices].reset_index(drop=True)

    best_val = acq_values[top_indices[0]].item()
    print(f"✅ Constrained MOBO done — best acq value: {best_val:.4f}")

    return best_candidates


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _generate_candidate_pool(domain, n_pool: int = 2048) -> pd.DataFrame:
    """
    Generate a pool of feasible candidates using BoFire's RandomStrategy.
    Falls back to manual discrete sampling if the domain is fully discrete
    with constraints (known BoFire bug).
    """
    from bofire.data_models.features.api import DiscreteInput

    all_discrete = all(
        isinstance(f, DiscreteInput) for f in domain.inputs.features
    )
    has_constraints = (
        domain.constraints and len(domain.constraints.constraints) > 0
    )

    if all_discrete and has_constraints:
        # Use existing REACTO fallback
        from utils.bofire_optimization import _manual_discrete_sampling
        return _manual_discrete_sampling(domain, n_pool)

    try:
        random_strat = strategies.map(RandomStrategyDM(domain=domain))
        return random_strat.ask(n_pool)
    except Exception as e:
        print(f"   ⚠️ RandomStrategy failed ({e}), falling back to manual pool")
        return _manual_pool_fallback(domain, n_pool)


def _manual_pool_fallback(domain, n_pool: int) -> pd.DataFrame:
    """Simple random pool generation as last resort."""
    from bofire.data_models.features.api import (
        ContinuousInput, DiscreteInput, CategoricalInput,
        CategoricalDescriptorInput,
    )
    rng = np.random.default_rng(42)
    rows = []
    for _ in range(n_pool):
        row = {}
        for feat in domain.inputs.features:
            if isinstance(feat, (CategoricalInput, CategoricalDescriptorInput)):
                row[feat.key] = rng.choice(list(feat.categories))
            elif isinstance(feat, DiscreteInput):
                row[feat.key] = float(rng.choice(feat.values))
            elif isinstance(feat, ContinuousInput):
                lb, ub = feat.bounds
                row[feat.key] = float(rng.uniform(lb, ub))
        rows.append(row)
    return pd.DataFrame(rows)


def _preprocess_to_model_space(
    candidate_pool_df: pd.DataFrame,
    domain,
    model,
) -> torch.Tensor:
    """
    Encode (descriptor expansion) and normalize candidates to match the
    input space the fitted GP model expects.
    """
    from bofire.data_models.features.api import CategoricalDescriptorInput
    from bofire.data_models.enum import CategoricalEncodingEnum

    # Build encoding specs: CategoricalDescriptorInput → descriptors
    specs = {}
    for feat in domain.inputs.features:
        if isinstance(feat, CategoricalDescriptorInput):
            specs[feat.key] = CategoricalEncodingEnum.DESCRIPTOR

    # Apply BoFire's encoding transform
    X_encoded = domain.inputs.transform(candidate_pool_df, specs=specs)
    X_tensor = torch.tensor(X_encoded.values, dtype=torch.double)

    # Apply normalization using the bounds stored in the model's input_transform
    lb, ub = _get_normalization_bounds(model, X_tensor.shape[-1])
    if lb is not None:
        range_ = ub - lb
        range_[range_ == 0] = 1.0  # avoid division by zero
        X_norm = (X_tensor - lb) / range_
    else:
        # Fallback: column-wise min-max from the tensor itself
        col_min = X_tensor.min(0).values
        col_max = X_tensor.max(0).values
        range_ = col_max - col_min
        range_[range_ == 0] = 1.0
        X_norm = (X_tensor - col_min) / range_

    return X_norm.clamp(0.0, 1.0)


def _get_normalization_bounds(model, d: int):
    """
    Extract normalization bounds from the BoTorch model's input_transform.
    Returns (lb_tensor, ub_tensor) or (None, None) if not found.
    """
    try:
        # ModelListGP: each sub-model might share the transform
        first_model = (
            model.models[0] if hasattr(model, "models") else model
        )
        it = getattr(first_model, "input_transform", None)
        if it is None:
            return None, None

        # ChainedInputTransform: iterate over sub-transforms
        if hasattr(it, "values"):
            for sub in it.values():
                if hasattr(sub, "bounds") and sub.bounds is not None:
                    lb = sub.bounds[0].double()
                    ub = sub.bounds[1].double()
                    if lb.shape[-1] == d:
                        return lb, ub
        # Direct Normalize
        if hasattr(it, "bounds") and it.bounds is not None:
            lb = it.bounds[0].double()
            ub = it.bounds[1].double()
            if lb.shape[-1] == d:
                return lb, ub
    except Exception as e:
        print(f"   ⚠️ Could not extract normalization bounds: {e}")
    return None, None


def _get_x_baseline(model) -> torch.Tensor:
    """
    Extract the normalized training inputs (X_baseline) from the fitted model.
    Used as baseline for qLogNEHVI's noisy variant.
    """
    try:
        if hasattr(model, "models"):
            return model.models[0].train_inputs[0]
        return model.train_inputs[0]
    except Exception:
        raise RuntimeError(
            "Could not extract X_baseline from model. "
            "Ensure strat.tell() was called before constrained_mobo_botorch()."
        )


def _build_constraint_callables(domain, output_constraints: list) -> list:
    """
    Build BoTorch outcome_constraints callables from user-defined thresholds.

    Convention (BoTorch): callable(Y) returns a tensor that is NEGATIVE
    when the constraint is satisfied (feasible) and POSITIVE when violated.

    BoFire internal convention:
        - MaximizeObjective outputs: GP predicts Y directly (not negated)
        - MinimizeObjective outputs: GP predicts -Y (negated so BoTorch maximizes)

    So for a MinimizeObjective output with constraint Y >= threshold:
        The model stores -Y, constraint becomes -Y <= -threshold.
        callable(-Y) = -threshold - (-Y) = Y - threshold  ← wrong sign
        Actually: callable returns negative when feasible.
        Feasible: -Y <= -threshold  →  -Y - (-threshold) <= 0
        callable(Y_stored) = Y_stored + threshold  ... no.
        
    Let's be systematic:
        Y_stored = -Y_original  (for MinimizeObjective)
        Constraint: Y_original >= threshold
        Equivalent: -Y_stored >= threshold  →  Y_stored <= -threshold
        BoTorch convention: callable returns negative when feasible
        callable(Y_stored) = Y_stored - (-threshold) = Y_stored + threshold
        Feasible: Y_stored + threshold <= 0  →  Y_stored <= -threshold ✓
    """
    obj_keys = [f.key for f in domain.outputs.features]
    obj_feats = {f.key: f for f in domain.outputs.features}
    callables = []

    for c in output_constraints:
        key = c.get("output_key")
        direction = c.get("direction", ">=")
        threshold = float(c.get("threshold", 0.0))

        if key not in obj_keys:
            print(f"   ⚠️ Constraint key '{key}' not found in domain outputs — skipped")
            continue

        idx = obj_keys.index(key)
        feat = obj_feats[key]
        is_minimize = isinstance(feat.objective, MinimizeObjective)

        if direction == ">=":
            if is_minimize:
                # Y_stored = -Y_original; feasible: Y_stored <= -threshold
                t = -threshold
                def make_c(i, t_):
                    return lambda Y: Y[..., i] - t_  # negative when Y_stored <= -threshold
                callables.append(make_c(idx, t))
            else:
                # Y_stored = Y_original; feasible: Y_stored >= threshold
                t = threshold
                def make_c(i, t_):
                    return lambda Y: t_ - Y[..., i]  # negative when Y[i] >= threshold
                callables.append(make_c(idx, t))

        elif direction == "<=":
            if is_minimize:
                # Y_stored = -Y_original; feasible: Y_stored >= -threshold
                t = -threshold
                def make_c(i, t_):
                    return lambda Y: t_ - Y[..., i]  # negative when Y_stored >= -threshold
                callables.append(make_c(idx, t))
            else:
                # Y_stored = Y_original; feasible: Y_stored <= threshold
                t = threshold
                def make_c(i, t_):
                    return lambda Y: Y[..., i] - t_  # negative when Y[i] <= threshold
                callables.append(make_c(idx, t))

        else:
            print(f"   ⚠️ Unknown constraint direction '{direction}' — skipped")

    return callables


def _compute_ref_point(domain, experiments: pd.DataFrame) -> torch.Tensor:
    """
    Compute a pessimistic reference point for hypervolume computation.

    For MaximizeObjective: ref = min(observed) - 10% slack
    For MinimizeObjective: ref = -max(observed) - 10% slack
        (negated because BoFire stores -Y for minimization)
    """
    ref = []
    for feat in domain.outputs.features:
        key = feat.key
        vals = pd.to_numeric(experiments[key], errors="coerce").dropna().values

        if len(vals) == 0:
            ref.append(-1.0)
            continue

        if isinstance(feat.objective, MinimizeObjective):
            # BoFire internally negates → model stores -Y
            # ref for maximized -Y: smallest -Y observed = -max(Y)
            worst = -float(np.max(vals))
            slack = 0.1 * abs(worst) if worst != 0 else 0.1
            ref.append(worst - slack)
        else:
            worst = float(np.min(vals))
            slack = 0.1 * abs(worst) if worst != 0 else 0.1
            ref.append(worst - slack)

    return torch.tensor(ref, dtype=torch.double)


# ---------------------------------------------------------------------------
# Utility: detect if a domain has output constraints
# ---------------------------------------------------------------------------

def extract_output_constraints_from_objectives(objectives: list) -> list:
    """
    Extract output_constraints from the objectives list stored in domain_data.

    Each objective dict may have:
        'is_constrained': bool
        'constraint_direction': '>=' or '<='
        'constraint_threshold': float

    Returns a list of constraint dicts for constrained_mobo_botorch().
    """
    constraints = []
    for obj in objectives:
        if obj.get("is_constrained", False):
            constraints.append({
                "output_key": obj["name"],
                "direction": obj.get("constraint_direction", ">="),
                "threshold": float(obj.get("constraint_threshold", 0.0)),
            })
    return constraints


def has_output_constraints(objectives: list) -> bool:
    """Return True if any objective has a threshold constraint."""
    return any(obj.get("is_constrained", False) for obj in objectives)
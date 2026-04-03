"""
Bayesian Optimization utilities using BoFire
Sampling and optimization strategies
"""

import warnings
import pandas as pd
import numpy as np

import torch

import bofire.strategies.api as strategies
from bofire.data_models.enum import SamplingMethodEnum
from bofire.data_models.acquisition_functions.api import (
    qLogNEI, qLogNEHVI, qEI, qNEI, qPI, qUCB, qSR
)
from bofire.data_models.strategies.api import RandomStrategy, SoboStrategy, MoboStrategy

from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from itertools import product as itertools_product

# ── torch device ──────────────────────────────────────────────────────────────
_tkwargs = {
    "dtype": torch.double,
    "device": torch.device("cuda" if torch.cuda.is_available() else "cpu"),
}


def sampling(domain, sampling_method: str, nb_points: int):
    """
    Run a sampling method for a given domain.
    Falls back to manual enumeration + random selection for fully discrete
    domains with constraints (BoFire bug workaround).

    Args:
        domain (Domain): BoFire domain.
        sampling_method (str): Name of SamplingMethodEnum (e.g., 'LHS', 'UNIFORM', 'SOBOL').
        nb_points (int): Number of points to sample.

    Returns:
        pd.DataFrame: Sampled points.
    """
    from bofire.data_models.features.api import DiscreteInput

    try:
        method_enum = SamplingMethodEnum[sampling_method]
    except KeyError:
        raise ValueError(f"Invalid sampling method '{sampling_method}'. Must be one of {list(SamplingMethodEnum.__members__.keys())}.")

    # ===== WORKAROUND: BoFire bug with fully discrete + constraints =====
    all_discrete = all(
        isinstance(f, DiscreteInput) for f in domain.inputs.features
    )
    has_constraints = domain.constraints and len(domain.constraints.constraints) > 0

    if all_discrete and has_constraints:
        print("⚠️ Fully discrete domain with constraints detected — using manual sampling fallback")
        return _manual_discrete_sampling(domain, nb_points)

    datamodel = RandomStrategy(domain=domain, fallback_sampling_method=method_enum)
    sampler = strategies.map(datamodel)
    return sampler.ask(nb_points)


def _manual_discrete_sampling(domain, nb_points: int):
    """
    Manual sampling for fully discrete domains with constraints.
    """
    from bofire.data_models.features.api import DiscreteInput

    feature_keys = [f.key for f in domain.inputs.features]
    all_values = {}

    for feature in domain.inputs.features:
        if isinstance(feature, DiscreteInput):
            all_values[feature.key] = list(feature.values)
        else:
            raise ValueError(f"Unexpected feature type for {feature.key}: {type(feature)}")

    total = 1
    for v in all_values.values():
        total *= len(v)
    print(f"   📊 Total combinations: {total}")

    if total > 500_000:
        print(f"   ⚠️ Large space ({total}), using random subset of 100,000")
        rng = np.random.default_rng(42)
        candidates = []
        for _ in range(100_000):
            combo = {k: float(rng.choice(v)) for k, v in all_values.items()}
            candidates.append(combo)
        df_candidates = pd.DataFrame(candidates)
    else:
        value_lists = [all_values[k] for k in feature_keys]
        candidates = [
            dict(zip(feature_keys, combo))
            for combo in itertools_product(*value_lists)
        ]
        df_candidates = pd.DataFrame(candidates)

    feasible_mask = pd.Series(True, index=df_candidates.index)
    for constraint in domain.constraints.constraints:
        if hasattr(constraint, 'is_fulfilled'):
            fulfilled = constraint.is_fulfilled(df_candidates, tol=1e-6)
            feasible_mask &= fulfilled

    df_feasible = df_candidates[feasible_mask].reset_index(drop=True)
    print(f"   ✅ {len(df_feasible)} feasible out of {len(df_candidates)} candidates")

    if len(df_feasible) == 0:
        raise ValueError("No feasible points found. Check constraints and parameter bounds.")

    if nb_points >= len(df_feasible):
        print(f"   ⚠️ Requested {nb_points} but only {len(df_feasible)} feasible — returning all")
        return df_feasible[feature_keys]

    selected = df_feasible.sample(n=nb_points, random_state=42).reset_index(drop=True)
    return selected[feature_keys]


def kmeans_sampling(domain, nb_points: int, constraints_config: dict = None, random_state: int = 42):
    """
    Initial sampling via k-Means clustering in reaction parameter space.
    """
    from bofire.data_models.features.api import (
        CategoricalDescriptorInput, CategoricalInput, DiscreteInput, ContinuousInput
    )

    feature_keys = [f.key for f in domain.inputs.features]
    feature_types = {}
    all_values = {}

    for feature in domain.inputs.features:
        key = feature.key
        if isinstance(feature, (CategoricalDescriptorInput, CategoricalInput)):
            all_values[key] = list(feature.categories)
            feature_types[key] = 'cat'
        elif isinstance(feature, DiscreteInput):
            all_values[key] = list(feature.values)
            feature_types[key] = 'num'
        elif isinstance(feature, ContinuousInput):
            lb, ub = feature.bounds
            step = (ub - lb) / 20
            all_values[key] = [round(v, 6) for v in np.arange(lb, ub + step / 2, step)]
            feature_types[key] = 'num'

    total = 1
    for v in all_values.values():
        total *= len(v)

    if total > 100_000:
        print(f"   ⚠️ Large space ({total}), using random subset of 100,000")
        rng = np.random.default_rng(random_state)
        value_lists_for_random = [all_values[k] for k in feature_keys]
        candidate_pool = []
        for _ in range(100_000):
            combo = {k: rng.choice(v) for k, v in zip(feature_keys, value_lists_for_random)}
            candidate_pool.append(combo)
    else:
        value_lists = [all_values[k] for k in feature_keys]
        candidate_pool = [
            dict(zip(feature_keys, combo))
            for combo in itertools_product(*value_lists)
        ]

    if constraints_config and (constraints_config.get('constraints') or constraints_config.get('inequality_constraints')):
        feasible = _filter_constraints(candidate_pool, constraints_config)
    else:
        feasible = candidate_pool

    if len(feasible) == 0:
        raise ValueError("No feasible points found. Check constraints and parameter bounds.")

    if nb_points >= len(feasible):
        return pd.DataFrame(feasible)[feature_keys]

    cat_maps = {}
    for key in feature_keys:
        if feature_types[key] == 'cat':
            cats = sorted(set(p[key] for p in feasible))
            cat_maps[key] = {c: i for i, c in enumerate(cats)}

    X = np.zeros((len(feasible), len(feature_keys)))
    for j, key in enumerate(feature_keys):
        if feature_types[key] == 'cat':
            X[:, j] = [cat_maps[key][p[key]] for p in feasible]
        else:
            X[:, j] = [float(p[key]) for p in feasible]

    scaler = MinMaxScaler()
    X_norm = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=nb_points, random_state=random_state, n_init=20)
    kmeans.fit(X_norm)

    selected_indices = []
    for centroid in kmeans.cluster_centers_:
        distances = np.linalg.norm(X_norm - centroid, axis=1)
        for idx in np.argsort(distances):
            if idx not in selected_indices:
                selected_indices.append(idx)
                break

    return pd.DataFrame([feasible[i] for i in selected_indices])[feature_keys]


def _filter_constraints(candidate_pool, constraints_config):
    """Filter candidate points by BP/MP constraints AND linear constraints."""
    safety_margin = constraints_config.get('safety_margin', 5.0)
    solvent_param = constraints_config.get('solvent_param_name')
    boiling_points = constraints_config.get('boiling_points', {})
    melting_points = constraints_config.get('melting_points', {})

    feasible = []
    for point in candidate_pool:
        valid = True
        solvent_name = point.get(solvent_param)

        if solvent_name:
            for c in constraints_config.get('constraints', []):
                param_val = point.get(c.get('parameter_name'))
                if param_val is None:
                    continue
                if c['type'] == 'less_than_bp':
                    bp = boiling_points.get(solvent_name)
                    if bp is not None and param_val >= (bp - safety_margin):
                        valid = False
                        break
                elif c['type'] == 'greater_than_mp':
                    mp = melting_points.get(solvent_name)
                    if mp is not None and param_val <= (mp + safety_margin):
                        valid = False
                        break

        if valid:
            for ineq in constraints_config.get('inequality_constraints', []):
                left = ineq['param_left']
                right = ineq['param_right']
                offset = ineq.get('offset', 0.0)
                relation = ineq.get('relation', 'leq')

                val_left = point.get(left)
                val_right = point.get(right)

                if val_left is not None and val_right is not None:
                    try:
                        vl = float(val_left)
                        vr = float(val_right)
                        if relation == "eq":
                            if abs(vl - (vr + offset)) > 1e-6:
                                valid = False
                                break
                        else:
                            if vl > vr + offset:
                                valid = False
                                break
                    except (ValueError, TypeError):
                        pass

        if valid:
            feasible.append(point)

    return feasible


def get_available_acquisition_functions(is_multi_objective=False):
    """Get available acquisition functions for single or multi-objective optimization."""
    if is_multi_objective:
        return {'qLogNEHVI (default)': qLogNEHVI}
    else:
        return {
            'qLogNEI (default)': qLogNEI,
            'qEI (Expected Improvement)': qEI,
            'qNEI (Noisy Expected Improvement)': qNEI,
            'qPI (Probability of Improvement)': qPI,
            'qUCB (Upper Confidence Bound)': qUCB,
            'qSR (Simple Regret)': qSR,
        }


def create_acquisition_function_from_name(acq_name, is_multi_objective=False):
    """Create an acquisition function instance from its name."""
    if acq_name == 'qLogNEI (default)' or acq_name == 'qLogNEHVI (default)':
        return None

    acq_functions = get_available_acquisition_functions(is_multi_objective)
    acq_class = acq_functions.get(acq_name)

    if acq_class is None:
        return None

    try:
        return acq_class()
    except Exception as e:
        print(f"Warning: Could not instantiate {acq_name}, using default. Error: {e}")
        return None


# =============================================================================
# ENCODING HELPERS (shared by constrained MOBO and MultiTaskGP)
# =============================================================================

def _build_encoding_metadata(domain):
    """
    Extract per-feature encoding info from a BoFire domain.

    Returns a list of dicts:
      continuous  → {'key', 'type':'continuous', 'bounds':(lb, ub)}
      discrete    → {'key', 'type':'discrete',   'values':[…], 'bounds':(min, max)}
      categorical → {'key', 'type':'categorical', 'categories':[…]}
    """
    from bofire.data_models.features.api import (
        ContinuousInput, DiscreteInput, CategoricalInput, CategoricalDescriptorInput
    )
    col_info = []
    for feat in domain.inputs.features:
        if isinstance(feat, ContinuousInput):
            col_info.append({
                'key': feat.key, 'type': 'continuous', 'bounds': feat.bounds
            })
        elif isinstance(feat, DiscreteInput):
            vals = sorted(feat.values)
            col_info.append({
                'key': feat.key, 'type': 'discrete',
                'values': vals, 'bounds': (vals[0], vals[-1])
            })
        elif isinstance(feat, (CategoricalInput, CategoricalDescriptorInput)):
            col_info.append({
                'key': feat.key, 'type': 'categorical',
                'categories': list(feat.categories)
            })
    return col_info


def _get_total_dim(col_info):
    """Total dimension of the encoded input space."""
    return sum(len(ci['categories']) if ci['type'] == 'categorical' else 1
               for ci in col_info)


def _encode_experiments(experiments, col_info):
    """Encode a DataFrame of experiments to a (n, D) torch tensor in [0,1]^D."""
    rows = []
    for _, row in experiments.iterrows():
        encoded = []
        for ci in col_info:
            if ci['type'] in ('continuous', 'discrete'):
                lb, ub = ci['bounds']
                val  = float(row[ci['key']])
                norm = (val - lb) / (ub - lb) if ub > lb else 0.5
                encoded.append(max(0.0, min(1.0, norm)))
            else:  # categorical → OHE
                encoded.extend(
                    1.0 if c == str(row[ci['key']]) else 0.0
                    for c in ci['categories']
                )
        rows.append(encoded)
    return torch.tensor(rows, **_tkwargs)


def _decode_candidate(x_1d, col_info):
    """Decode a 1-D tensor back to a parameter dict (original units)."""
    result, idx = {}, 0
    for ci in col_info:
        if ci['type'] == 'continuous':
            lb, ub = ci['bounds']
            result[ci['key']] = lb + float(x_1d[idx].item()) * (ub - lb)
            idx += 1
        elif ci['type'] == 'discrete':
            lb, ub = ci['bounds']
            val_raw = lb + float(x_1d[idx].item()) * (ub - lb)
            result[ci['key']] = min(ci['values'], key=lambda v: abs(v - val_raw))
            idx += 1
        else:  # categorical
            n = len(ci['categories'])
            result[ci['key']] = ci['categories'][x_1d[idx:idx + n].argmax().item()]
            idx += n
    return result


def _build_fixed_features_list(col_info):
    """
    Build fixed_features_list for optimize_acqf_mixed.
    Returns None when there are no categorical features.
    """
    cat_info, total_idx = [], 0
    for ci in col_info:
        if ci['type'] == 'categorical':
            cat_info.append({'start': total_idx, 'n': len(ci['categories'])})
            total_idx += len(ci['categories'])
        else:
            total_idx += 1

    if not cat_info:
        return None

    fixed_list = []
    for combo in itertools_product(*[range(ci['n']) for ci in cat_info]):
        fixed = {}
        for ci_info, cat_idx in zip(cat_info, combo):
            for k in range(ci_info['n']):
                fixed[ci_info['start'] + k] = 1.0 if k == cat_idx else 0.0
        fixed_list.append(fixed)
    return fixed_list


def _build_fixed_features_list_with_task(col_info, D_TOTAL):
    """
    Like _build_fixed_features_list but also fixes the task column
    (index D_TOTAL) to 1.0 (target task).

    Used by MultiTaskGP to simultaneously enumerate OHE combinations
    and lock the task dimension to the target reaction.
    """
    base_list = _build_fixed_features_list(col_info)

    if base_list is None:
        # No categorical features — just fix the task column
        return [{D_TOTAL: 1.0}]

    # Add task=1 to every OHE combination
    return [{**combo, D_TOTAL: 1.0} for combo in base_list]


# =============================================================================
# CONSTRAINED MOBO — MAIN BOTORCH BYPASS
# =============================================================================

def constrained_mobo_botorch(domain, experiments, outcome_constraint, n_candidates=1):
    """
    Constrained MOBO via direct BoTorch bypass.

    Implements qLogNoisyExpectedHypervolumeImprovement with an outcome constraint,
    following the BoTorch constrained MOBO tutorial exactly (C2-DTLZ2 structure).

    BoFire cannot assign both 'Pareto objective' and 'outcome constraint' roles to the
    same output feature — this bypass is therefore necessary for constrained MOBO.

    Args:
        domain            : BoFire Domain
        experiments       : pd.DataFrame  (param columns + objective columns, complete rows)
        outcome_constraint: dict with keys
                              'objective'  – name of the objective to constrain
                              'direction'  – '>=' or '<='
                              'threshold'  – float, in the same units as the data
        n_candidates      : int (default 1)

    Returns:
        pd.DataFrame with suggested parameter values (one row per candidate)
    """
    from botorch import fit_gpytorch_mll
    from botorch.exceptions import BadInitialCandidatesWarning
    from botorch.models.gp_regression import SingleTaskGP
    from botorch.models.model_list_gp_regression import ModelListGP
    from botorch.sampling.normal import SobolQMCNormalSampler
    from botorch.acquisition.multi_objective.logei import (
        qLogNoisyExpectedHypervolumeImprovement
    )
    from botorch.acquisition.multi_objective.objective import IdentityMCMultiOutputObjective
    from botorch.optim.optimize import optimize_acqf_mixed, optimize_acqf
    from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood
    from bofire.data_models.objectives.api import MinimizeObjective

    warnings.filterwarnings("ignore", category=BadInitialCandidatesWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    print("🔒 Constrained MOBO (BoTorch bypass) — starting…")

    con_obj_name  = outcome_constraint['objective']
    con_direction = outcome_constraint['direction']
    con_threshold = float(outcome_constraint['threshold'])

    print(f"   Constraint : {con_obj_name} {con_direction} {con_threshold}")
    print(f"   Convention : c(x) <= 0 is feasible (BoTorch)")

    col_info = _build_encoding_metadata(domain)
    D_TOTAL  = _get_total_dim(col_info)

    obj_feats = domain.outputs.features
    obj_names = [f.key for f in obj_feats]
    n_obj     = len(obj_names)

    train_x = _encode_experiments(experiments, col_info)

    obj_data = []
    for _, row in experiments.iterrows():
        vals = []
        for feat in obj_feats:
            v = float(row[feat.key])
            vals.append(-v if isinstance(feat.objective, MinimizeObjective) else v)
        obj_data.append(vals)
    train_obj = torch.tensor(obj_data, **_tkwargs)

    con_data = []
    for _, row in experiments.iterrows():
        v = float(row[con_obj_name])
        c = (con_threshold - v) if con_direction == '>=' else (v - con_threshold)
        con_data.append([c])
    train_con = torch.tensor(con_data, **_tkwargs)

    is_feas    = (train_con <= 0).squeeze(-1)
    n_feasible = is_feas.sum().item()
    print(f"   Feasible points: {n_feasible}/{len(experiments)}")

    ref_vals = []
    for feat in obj_feats:
        if isinstance(feat.objective, MinimizeObjective):
            ref_vals.append(-float(feat.objective.upper_bound))
        else:
            ref_vals.append(float(feat.objective.lower_bound))
    ref_point = ref_vals
    print(f"   Ref point (from domain bounds): {[f'{v:.4f}' for v in ref_point]}")

    train_y = torch.cat([train_obj, train_con], dim=-1)
    model   = ModelListGP(*[
        SingleTaskGP(train_x, train_y[..., i:i + 1])
        for i in range(train_y.shape[-1])
    ])
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    fit_gpytorch_mll(mll)
    print("   ✅ ModelListGP fitted")

    sampler         = SobolQMCNormalSampler(sample_shape=torch.Size([128]))
    obj_indices     = list(range(n_obj))
    standard_bounds = torch.zeros(2, D_TOTAL, **_tkwargs)
    standard_bounds[1] = 1.0

    acq = qLogNoisyExpectedHypervolumeImprovement(
        model          = model,
        ref_point      = ref_point,
        X_baseline     = train_x,
        sampler        = sampler,
        prune_baseline = True,
        objective      = IdentityMCMultiOutputObjective(outcomes=obj_indices),
        constraints    = [lambda Z: Z[..., -1]],
    )

    fixed_features_list = _build_fixed_features_list(col_info)

    if fixed_features_list:
        print(f"   Using optimize_acqf_mixed ({len(fixed_features_list)} categorical combinations)")
        candidates, _ = optimize_acqf_mixed(
            acq_function        = acq,
            bounds              = standard_bounds,
            q                   = n_candidates,
            num_restarts        = 10,
            raw_samples         = 128,
            fixed_features_list = fixed_features_list,
            options             = {"batch_limit": 5, "maxiter": 200},
        )
    else:
        print("   Using optimize_acqf (no categorical features)")
        candidates, _ = optimize_acqf(
            acq_function = acq,
            bounds       = standard_bounds,
            q            = n_candidates,
            num_restarts = 10,
            raw_samples  = 128,
        )

    results = []
    for i in range(n_candidates):
        x_1d    = candidates[i].detach() if candidates.dim() > 1 else candidates.squeeze(0).detach()
        decoded = _decode_candidate(x_1d, col_info)
        results.append(decoded)
        print(f"   ✅ Candidate {i + 1}: {decoded}")

    return pd.DataFrame(results)


# =============================================================================
# TRANSFER LEARNING — MULTITASKGP (BoTorch bypass)
# =============================================================================

def multitask_bayesian_optimization(domain, target_experiments, source_experiments,
                                    n_candidates=1):
    """
    Transfer Learning SOBO via MultiTaskGP (BoTorch direct bypass).

    Uses BoTorch's MultiTaskGP with ICM kernel to jointly model a source reaction
    (task=0) and the current target reaction (task=1). Predictions and acquisition
    function optimization are performed exclusively for the target task.

    This mirrors the implementation used in Taylor et al., ACS Central Science 2023
    (github.com/sustainable-processes/multitask).

    Architecture:
      - Task column appended as last input dimension  →  task_feature=-1
      - output_tasks=[1]  →  only predict for the target reaction
      - Acquisition: qLogNoisyExpectedImprovement  (X_baseline = target obs only)
      - Categorical variables: handled via optimize_acqf_mixed + fixed_features_list
        (OHE combinations × task=1 fixed simultaneously)

    Args:
        domain              : BoFire Domain (must be SOBO — single output)
        target_experiments  : pd.DataFrame — current campaign observations
        source_experiments  : pd.DataFrame — past campaign observations (same domain)
        n_candidates        : int, number of candidates to suggest (default 1)

    Returns:
        pd.DataFrame with suggested parameter values
    """
    from botorch import fit_gpytorch_mll
    from botorch.exceptions import BadInitialCandidatesWarning
    from botorch.models.multitask import MultiTaskGP
    from botorch.acquisition.logei import qLogNoisyExpectedImprovement
    from botorch.optim.optimize import optimize_acqf_mixed
    from gpytorch.mlls.exact_marginal_log_likelihood import ExactMarginalLogLikelihood
    from bofire.data_models.objectives.api import MinimizeObjective

    warnings.filterwarnings("ignore", category=BadInitialCandidatesWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    print("🔁 MultiTaskGP Transfer Learning (BoTorch bypass) — starting…")

    # ── Validate: SOBO only ───────────────────────────────────────────────
    obj_feats = domain.outputs.features
    if len(obj_feats) != 1:
        raise ValueError(
            "Transfer learning is only supported for single-objective optimization (SOBO). "
            f"Current domain has {len(obj_feats)} objectives."
        )

    obj_feat   = obj_feats[0]
    obj_name   = obj_feat.key
    is_minimize = isinstance(obj_feat.objective, MinimizeObjective)

    # ── Encoding metadata ─────────────────────────────────────────────────
    col_info = _build_encoding_metadata(domain)
    D_TOTAL  = _get_total_dim(col_info)

    print(f"   Source : {len(source_experiments)} experiments (task=0)")
    print(f"   Target : {len(target_experiments)} experiments (task=1)")
    print(f"   Input dim : {D_TOTAL} + 1 (task) = {D_TOTAL + 1}")

    # ── Encode inputs ─────────────────────────────────────────────────────
    source_x = _encode_experiments(source_experiments, col_info)  # (n_src, D)
    target_x = _encode_experiments(target_experiments, col_info)  # (n_tgt, D)

    # ── Encode outputs (sign flip for MinimizeObjective) ──────────────────
    def _encode_y(df):
        vals = []
        for _, row in df.iterrows():
            v = float(row[obj_name])
            vals.append(-v if is_minimize else v)
        return torch.tensor(vals, **_tkwargs).unsqueeze(-1)

    source_y = _encode_y(source_experiments)   # (n_src, 1)
    target_y = _encode_y(target_experiments)   # (n_tgt, 1)

    # ── Append task column (Summit convention: task appended last) ────────
    task_src = torch.zeros(len(source_x), 1, **_tkwargs)   # task=0
    task_tgt = torch.ones(len(target_x),  1, **_tkwargs)   # task=1

    source_x_task = torch.cat([source_x, task_src], dim=-1)  # (n_src, D+1)
    target_x_task = torch.cat([target_x, task_tgt], dim=-1)  # (n_tgt, D+1)

    train_x = torch.cat([source_x_task, target_x_task], dim=0)  # (n_src+n_tgt, D+1)
    train_y = torch.cat([source_y,      target_y],      dim=0)  # (n_src+n_tgt, 1)

    # ── Fit MultiTaskGP ───────────────────────────────────────────────────
    model = MultiTaskGP(
        train_X      = train_x,
        train_Y      = train_y,
        task_feature = -1,      # last column is the task index
        output_tasks = [1],     # predict only for the target reaction
    )
    mll = ExactMarginalLogLikelihood(model.likelihood, model)
    fit_gpytorch_mll(mll)
    print("   ✅ MultiTaskGP fitted")

    # ── Log inter-task covariance (diagnostic) ────────────────────────────
    try:
        with torch.no_grad():
            tcov = model.task_covar_module._eval_covar_matrix().cpu().numpy()
        print(f"   Inter-task covariance matrix:\n{tcov}")
        print(f"   → Source–Target correlation : {tcov[0, 1]:.4f}")
    except Exception as e:
        print(f"   (Could not retrieve task covariance: {e})")

    # ── Acquisition function ──────────────────────────────────────────────
    # X_baseline = target observations only (mirrors Summit's NewMTBO)
    acqf = qLogNoisyExpectedImprovement(
        model          = model,
        X_baseline     = target_x_task,
        prune_baseline = True,
    )

    # ── Bounds (D_TOTAL continuous/OHE dims + 1 task dim) ────────────────
    bounds_with_task = torch.zeros(2, D_TOTAL + 1, **_tkwargs)
    bounds_with_task[1] = 1.0

    # ── fixed_features_list: OHE combos × task=1 fixed simultaneously ────
    fixed_features_list = _build_fixed_features_list_with_task(col_info, D_TOTAL)

    print(f"   Using optimize_acqf_mixed ({len(fixed_features_list)} combinations, task fixed to 1)")
    candidates, _ = optimize_acqf_mixed(
        acq_function        = acqf,
        bounds              = bounds_with_task,
        q                   = n_candidates,
        num_restarts        = 10,
        raw_samples         = 128,
        fixed_features_list = fixed_features_list,
        options             = {"batch_limit": 5, "maxiter": 200},
    )

    # ── Decode (drop task column before decoding) ─────────────────────────
    results = []
    for i in range(n_candidates):
        x_with_task = candidates[i].detach() if candidates.dim() > 1 else candidates.squeeze(0).detach()
        x_no_task   = x_with_task[:D_TOTAL]   # strip the task dimension
        decoded     = _decode_candidate(x_no_task, col_info)
        results.append(decoded)
        print(f"   ✅ Candidate {i + 1}: {decoded}")

    return pd.DataFrame(results)


# =============================================================================
# MAIN OPTIMIZATION ENTRY POINT
# =============================================================================

def bayesian_optimization(domain, experiments, n_candidates=1,
                           acquisition_function=None, outcome_constraint=None,
                           source_experiments=None):
    """
    Run Bayesian optimization using the appropriate strategy.

    - Single objective (SOBO):
        • With source_experiments → MultiTaskGP transfer learning (BoTorch bypass)
        • Without                 → SoboStrategy (default: qLogNEI)
    - Multiple objectives (MOBO):
        • With outcome_constraint → constrained_mobo_botorch() (BoTorch bypass)
        • Without                 → MoboStrategy (default: qLogNEHVI)
      Note: transfer learning is not supported for MOBO.

    Args:
        domain              : BoFire Domain object
        experiments         : DataFrame with completed experiments (params + objectives)
        n_candidates        : Number of candidates to suggest (default: 1)
        acquisition_function: Custom acquisition function instance (optional)
        outcome_constraint  : dict or None — {'enabled':bool, 'objective':str,
                              'direction':'>=', 'threshold':float}
        source_experiments  : pd.DataFrame or None — past campaign data for TL (SOBO only)

    Returns:
        DataFrame with suggested candidates
    """

    n_obj = len(domain.outputs.features)

    if n_obj == 1:
        # ── Transfer Learning path ────────────────────────────────────────
        if source_experiments is not None and len(source_experiments) > 0:
            print(f"🔁 Transfer Learning active — routing to MultiTaskGP")
            return multitask_bayesian_optimization(
                domain, experiments, source_experiments, n_candidates
            )

        # ── Standard SOBO ─────────────────────────────────────────────────
        acq_func   = acquisition_function if acquisition_function is not None else qLogNEI()
        data_model = SoboStrategy(domain=domain, acquisition_function=acq_func)

    elif n_obj >= 2:
        # ── Constrained MOBO ──────────────────────────────────────────────
        if (outcome_constraint
                and outcome_constraint.get('enabled')
                and outcome_constraint.get('objective')
                and outcome_constraint.get('threshold') is not None):
            print(f"🔒 Outcome constraint detected — routing to constrained_mobo_botorch()")
            return constrained_mobo_botorch(
                domain, experiments, outcome_constraint, n_candidates
            )

        # ── Standard MOBO ─────────────────────────────────────────────────
        acq_func   = acquisition_function if acquisition_function is not None else qLogNEHVI()
        data_model = MoboStrategy(domain=domain, acquisition_function=acq_func)

    else:
        raise ValueError("Domain must have at least one objective")

    # ── BoFire strategy path ──────────────────────────────────────────────
    strat = strategies.map(data_model)

    print("🔍 DEBUG - Domain features:")
    for feat in domain.inputs.features:
        print(f"   - {feat.key}: {type(feat).__name__}")
        if hasattr(feat, 'categories'):
            print(f"     Categories: {feat.categories}")
        if hasattr(feat, 'descriptors'):
            print(f"     Descriptors: {feat.descriptors}")
            print(f"     Values: {feat.values}")

    print("🔍 DEBUG - Experiments DataFrame:")
    print(experiments)
    print("\n🔍 DEBUG - Unique values per column:")
    for col in experiments.columns:
        unique_vals = experiments[col].unique()
        print(f"   - {col}: {len(unique_vals)} unique values → {list(unique_vals)[:5]}")

    print("\n🔍 DEBUG - Checking data transformation:")
    from bofire.data_models.enum import CategoricalEncodingEnum
    specs = {}
    for feat in domain.inputs.features:
        if hasattr(feat, 'descriptors') and feat.descriptors:
            specs[feat.key] = CategoricalEncodingEnum.DESCRIPTOR
            print(f"   Setting {feat.key} encoding to DESCRIPTOR")

    param_names = [feat.key for feat in domain.inputs.features]
    if specs:
        try:
            X_transformed = domain.inputs.transform(experiments[param_names], specs=specs)
            print(f"   Transformed columns: {list(X_transformed.columns)}")
            print(f"   Transformed shape: {X_transformed.shape}")
            for col in X_transformed.columns:
                n_unique = X_transformed[col].nunique()
                print(f"   Column '{col}': {n_unique} unique values")
                if n_unique == 1:
                    print(f"   ⚠️ WARNING: Column '{col}' has only 1 unique value!")
        except Exception as e:
            print(f"   ⚠️ Error during transformation test: {e}")

    strat.tell(experiments=experiments)

    if hasattr(strat, 'model'):
        print("🔍 Model type:", type(strat.model))
        print("🔍 Input transform:", getattr(strat.model, 'input_transform', 'NONE'))
        print("🔍 Outcome transform:", getattr(strat.model, 'outcome_transform', 'NONE'))

    return strat.ask(candidate_count=n_candidates)


def get_optimization_type(domain):
    """Determine if optimization is SOBO or MOBO based on domain."""
    n_obj = len(domain.outputs.features)
    return 'SOBO' if n_obj == 1 else 'MOBO'
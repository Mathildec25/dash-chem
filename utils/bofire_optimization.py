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
    # RandomStrategy returns a scalar instead of a Series when all features
    # are DiscreteInput and constraints are present, causing a TypeError
    # in validate_candidates. We detect this case and fall back to manual sampling.
    all_discrete = all(
        isinstance(f, DiscreteInput) for f in domain.inputs.features
    )
    has_constraints = domain.constraints and len(domain.constraints.constraints) > 0

    if all_discrete and has_constraints:
        print("⚠️ Fully discrete domain with constraints detected — using manual sampling fallback")
        return _manual_discrete_sampling(domain, nb_points)

    # Normal BoFire sampling
    datamodel = RandomStrategy(domain=domain, fallback_sampling_method=method_enum)
    sampler = strategies.map(datamodel)
    return sampler.ask(nb_points)


def _manual_discrete_sampling(domain, nb_points: int):
    """
    Manual sampling for fully discrete domains with constraints.
    Enumerates combinations, validates against domain constraints,
    then randomly selects nb_points.

    Args:
        domain: BoFire Domain object (all DiscreteInput features)
        nb_points: Number of points to sample

    Returns:
        pd.DataFrame: Sampled feasible points
    """
    from bofire.data_models.features.api import DiscreteInput

    feature_keys = [f.key for f in domain.inputs.features]
    all_values = {}

    for feature in domain.inputs.features:
        if isinstance(feature, DiscreteInput):
            all_values[feature.key] = list(feature.values)
        else:
            raise ValueError(f"Unexpected feature type for {feature.key}: {type(feature)}")

    # Calculate total combinations
    total = 1
    for v in all_values.values():
        total *= len(v)
    print(f"   📊 Total combinations: {total}")

    if total > 500_000:
        # Too large to enumerate: random sample then filter
        print(f"   ⚠️ Large space ({total}), using random subset of 100,000")
        rng = np.random.default_rng(42)
        candidates = []
        for _ in range(100_000):
            combo = {k: float(rng.choice(v)) for k, v in all_values.items()}
            candidates.append(combo)
        df_candidates = pd.DataFrame(candidates)
    else:
        # Enumerate all combinations
        value_lists = [all_values[k] for k in feature_keys]
        candidates = [
            dict(zip(feature_keys, combo))
            for combo in itertools_product(*value_lists)
        ]
        df_candidates = pd.DataFrame(candidates)

    # Filter by domain constraints using BoFire's is_fulfilled
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

    # Random selection
    selected = df_feasible.sample(n=nb_points, random_state=42).reset_index(drop=True)
    return selected[feature_keys]


def kmeans_sampling(domain, nb_points: int, constraints_config: dict = None, random_state: int = 42):
    """
    Initial sampling via k-Means clustering in reaction parameter space.
    
    Generates a large candidate pool (like LHS/Sobol), filters by constraints,
    then selects nb_points via k-Means for optimal space-filling coverage.
    
    References:
        - Shields et al., Nature 590, 89-96 (2021)
        - Kaneko, ACS Omega 7, 47789-47795 (2022)
    
    Args:
        domain: BoFire Domain object
        nb_points: Number of initial experiments to select
        constraints_config: Constraints config from Dash store (optional)
        random_state: Random seed for reproducibility
    
    Returns:
        pd.DataFrame: same format as sampling()
    """
    from bofire.data_models.features.api import (
        CategoricalDescriptorInput, CategoricalInput, DiscreteInput, ContinuousInput
    )
    
    # ===== 1. ENUMERATE ALL FEASIBLE COMBINATIONS =====
    feature_keys = [f.key for f in domain.inputs.features]
    feature_types = {}   # 'cat' or 'num'
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
    
    # Total combinations
    total = 1
    for v in all_values.values():
        total *= len(v)
    
    if total > 100_000:
        # Too large to enumerate: manual random sampling
        # (BoFire RandomStrategy bugs on fully discrete + constraints)
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
    
    # ===== 2. FILTER BY CONSTRAINTS (BP/MP + linear) =====
    if constraints_config and (constraints_config.get('constraints') or constraints_config.get('inequality_constraints')):
        feasible = _filter_constraints(candidate_pool, constraints_config)
    else:
        feasible = candidate_pool
    
    if len(feasible) == 0:
        raise ValueError("No feasible points found. Check constraints and parameter bounds.")
    
    if nb_points >= len(feasible):
        return pd.DataFrame(feasible)[feature_keys]
    
    # ===== 3. ENCODE FOR k-MEANS =====
    # Categoricals -> integer index, numerics -> raw value
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
    
    # ===== 4. NORMALIZE + k-MEANS =====
    scaler = MinMaxScaler()
    X_norm = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=nb_points, random_state=random_state, n_init=20)
    kmeans.fit(X_norm)
    
    # ===== 5. SELECT NEAREST FEASIBLE POINT PER CENTROID =====
    selected_indices = []
    for centroid in kmeans.cluster_centers_:
        distances = np.linalg.norm(X_norm - centroid, axis=1)
        for idx in np.argsort(distances):
            if idx not in selected_indices:
                selected_indices.append(idx)
                break
    
    return pd.DataFrame([feasible[i] for i in selected_indices])[feature_keys]


def _filter_constraints(candidate_pool, constraints_config):
    """Filter candidate points by BP/MP constraints AND linear constraints (inequality + equality)."""
    safety_margin = constraints_config.get('safety_margin', 5.0)
    solvent_param = constraints_config.get('solvent_param_name')
    boiling_points = constraints_config.get('boiling_points', {})
    melting_points = constraints_config.get('melting_points', {})
    
    feasible = []
    for point in candidate_pool:
        valid = True
        solvent_name = point.get(solvent_param)
        
        # ===== PHASE CONSTRAINTS (BP/MP) =====
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
        
        # ===== LINEAR INEQUALITY CONSTRAINTS =====
        if valid:
            for ineq in constraints_config.get('inequality_constraints', []):
                left = ineq['param_left']
                right = ineq['param_right']
                offset = ineq.get('offset', 0.0)
                relation = ineq.get('relation', 'leq')  # ✅ NEW: backward compatible
                
                val_left = point.get(left)
                val_right = point.get(right)
                
                if val_left is not None and val_right is not None:
                    try:
                        vl = float(val_left)
                        vr = float(val_right)
                        if relation == "eq":
                            # ✅ Equality: must be exactly equal (with tolerance)
                            if abs(vl - (vr + offset)) > 1e-6:
                                valid = False
                                break
                        else:
                            # Inequality: val_left ≤ val_right + offset
                            if vl > vr + offset:
                                valid = False
                                break
                    except (ValueError, TypeError):
                        pass  # Skip non-numeric values
        
        if valid:
            feasible.append(point)
    
    return feasible


def get_available_acquisition_functions(is_multi_objective=False):
    """
    Get available acquisition functions for single or multi-objective optimization.
    
    Args:
        is_multi_objective: Boolean indicating if multi-objective
    
    Returns:
        dict: Dictionary mapping display names to acquisition function classes
    """
    if is_multi_objective:
        # Multi-objective acquisition functions
        return {
            'qLogNEHVI (default)': qLogNEHVI,
        }
    else:
        # Single-objective acquisition functions
        return {
            'qLogNEI (default)': qLogNEI,
            'qEI (Expected Improvement)': qEI,
            'qNEI (Noisy Expected Improvement)': qNEI,
            'qPI (Probability of Improvement)': qPI,
            'qUCB (Upper Confidence Bound)': qUCB,
            'qSR (Simple Regret)': qSR,
        }


def create_acquisition_function_from_name(acq_name, is_multi_objective=False):
    """
    Create an acquisition function instance from its name.
    
    Args:
        acq_name: Name of the acquisition function
        is_multi_objective: Boolean indicating if multi-objective
    
    Returns:
        Acquisition function instance or None for default
    """
    if acq_name == 'qLogNEI (default)' or acq_name == 'qLogNEHVI (default)':
        return None  # Will use default in bayesian_optimization
    
    acq_functions = get_available_acquisition_functions(is_multi_objective)
    
    # Get the class from the dict
    acq_class = acq_functions.get(acq_name)
    
    if acq_class is None:
        # Fallback to default (return None)
        return None
    
    # Instantiate the acquisition function
    try:
        return acq_class()
    except Exception as e:
        print(f"Warning: Could not instantiate {acq_name}, using default. Error: {e}")
        return None


# =============================================================================
# CONSTRAINED MOBO — ENCODING HELPERS (BoTorch bypass)
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

    The constraint GP is trained on c(x) = threshold - value  (direction '>=')
    or c(x) = value - threshold  (direction '<=').
    BoTorch convention: c(x) <= 0 means feasible.

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

    # ── 1. Parse constraint config ────────────────────────────────────────
    con_obj_name  = outcome_constraint['objective']
    con_direction = outcome_constraint['direction']   # '>=' or '<='
    con_threshold = float(outcome_constraint['threshold'])

    print(f"   Constraint : {con_obj_name} {con_direction} {con_threshold}")
    print(f"   Convention : c(x) <= 0 is feasible (BoTorch)")

    # ── 2. Build encoding metadata ────────────────────────────────────────
    col_info = _build_encoding_metadata(domain)
    D_TOTAL  = _get_total_dim(col_info)

    obj_feats = domain.outputs.features
    obj_names = [f.key for f in obj_feats]
    n_obj     = len(obj_names)

    # ── 3. Encode inputs ──────────────────────────────────────────────────
    train_x = _encode_experiments(experiments, col_info)   # (n, D)

    # ── 4. Build train_obj (sign flip for MinimizeObjective) ──────────────
    obj_data = []
    for _, row in experiments.iterrows():
        vals = []
        for feat in obj_feats:
            v = float(row[feat.key])
            vals.append(-v if isinstance(feat.objective, MinimizeObjective) else v)
        obj_data.append(vals)
    train_obj = torch.tensor(obj_data, **_tkwargs)          # (n, n_obj)

    # ── 5. Build train_con: c(x) <= 0 means feasible ─────────────────────
    con_data = []
    for _, row in experiments.iterrows():
        v = float(row[con_obj_name])
        c = (con_threshold - v) if con_direction == '>=' else (v - con_threshold)
        con_data.append([c])
    train_con = torch.tensor(con_data, **_tkwargs)           # (n, 1)

    # ── 6. Ref point from objective bounds defined at domain creation ────────
    # The user already specified lower_bound / upper_bound for each objective
    # when creating the campaign — these are the natural ref point values.
    # For MinimizeObjective the sign is flipped in train_obj, so we negate
    # the upper bound (worst acceptable value for a minimised objective).
    is_feas    = (train_con <= 0).squeeze(-1)
    n_feasible = is_feas.sum().item()
    print(f"   Feasible points: {n_feasible}/{len(experiments)}")

    ref_vals = []
    for feat in obj_feats:
        if isinstance(feat.objective, MinimizeObjective):
            # minimise → sign-flipped in train_obj → ref = -upper_bound
            ref_vals.append(-float(feat.objective.upper_bound))
        else:
            # maximise → ref = lower_bound
            ref_vals.append(float(feat.objective.lower_bound))
    ref_point = ref_vals
    print(f"   Ref point (from domain bounds): {[f'{v:.4f}' for v in ref_point]}")

    # ── 7. ModelListGP: [GP_obj1, …, GP_objN, GP_constraint] ─────────────
    train_y = torch.cat([train_obj, train_con], dim=-1)     # (n, n_obj+1)
    model   = ModelListGP(*[
        SingleTaskGP(train_x, train_y[..., i:i + 1])
        for i in range(train_y.shape[-1])
    ])
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    fit_gpytorch_mll(mll)
    print("   ✅ ModelListGP fitted")

    # ── 8. Acquisition function with outcome constraint ───────────────────
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
        constraints    = [lambda Z: Z[..., -1]],   # last GP output = constraint
    )

    # ── 9. Optimize ───────────────────────────────────────────────────────
    fixed_features_list = _build_fixed_features_list(col_info)

    if fixed_features_list:
        print(f"   Using optimize_acqf_mixed "
              f"({len(fixed_features_list)} categorical combinations)")
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

    # ── 10. Decode ────────────────────────────────────────────────────────
    results = []
    for i in range(n_candidates):
        x_1d    = candidates[i].detach() if candidates.dim() > 1 else candidates.squeeze(0).detach()
        decoded = _decode_candidate(x_1d, col_info)
        results.append(decoded)
        print(f"   ✅ Candidate {i + 1}: {decoded}")

    return pd.DataFrame(results)


# =============================================================================
# MAIN OPTIMIZATION ENTRY POINT
# =============================================================================

def bayesian_optimization(domain, experiments, n_candidates=1,
                           acquisition_function=None, outcome_constraint=None):
    """
    Run Bayesian optimization using the appropriate strategy based on the number of objectives.
    
    - Single objective: SoboStrategy (default: qLogNEI)
    - Multiple objectives: MoboStrategy (default: qLogNEHVI)
      With outcome_constraint active: constrained_mobo_botorch() (BoTorch bypass)
    
    Args:
        domain: BoFire Domain object
        experiments: DataFrame with completed experiments (params + objectives)
        n_candidates: Number of candidates to suggest (default: 1)
        acquisition_function: Custom acquisition function instance (optional). If None, defaults are used.
                              Ignored when outcome_constraint is active.
        outcome_constraint: dict or None — {'enabled':bool, 'objective':str,
                            'direction':'>=', 'threshold':float}
    
    Returns:
        DataFrame with suggested candidates
    """
    
    # Determine number of objectives
    n_obj = len(domain.outputs.features)
    
    # Select strategy and acquisition function based on objective count
    if n_obj == 1:
        # Single-objective optimization (SOBO)
        acq_func = acquisition_function if acquisition_function is not None else qLogNEI()
        data_model = SoboStrategy(domain=domain, acquisition_function=acq_func)
    elif n_obj >= 2:
        # ── Route to constrained BoTorch bypass when a valid constraint is set ──
        if (outcome_constraint
                and outcome_constraint.get('enabled')
                and outcome_constraint.get('objective')
                and outcome_constraint.get('threshold') is not None):
            print(f"🔒 Outcome constraint detected — routing to constrained_mobo_botorch()")
            return constrained_mobo_botorch(
                domain, experiments, outcome_constraint, n_candidates
            )
        # Standard MOBO via BoFire
        acq_func = acquisition_function if acquisition_function is not None else qLogNEHVI()
        data_model = MoboStrategy(domain=domain, acquisition_function=acq_func)
    else:
        raise ValueError("Domain must have at least one objective")

    # Initialize strategy
    strat = strategies.map(data_model)
    
    # ===== DEBUGGING =====
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
    
    # ===== CHECK ENCODING TRANSFORMATION =====
    print("\n🔍 DEBUG - Checking data transformation:")
    
    from bofire.data_models.enum import CategoricalEncodingEnum
    
    # Build encoding specs for CategoricalDescriptorInput features
    specs = {}
    for feat in domain.inputs.features:
        if hasattr(feat, 'descriptors') and feat.descriptors:  # CategoricalDescriptorInput
            specs[feat.key] = CategoricalEncodingEnum.DESCRIPTOR
            print(f"   Setting {feat.key} encoding to DESCRIPTOR")
    
    # Get parameter names (exclude objectives)
    param_names = [feat.key for feat in domain.inputs.features]
    
    # Transform and check
    if specs:
        try:
            X_transformed = domain.inputs.transform(experiments[param_names], specs=specs)
            print(f"   Transformed columns: {list(X_transformed.columns)}")
            print(f"   Transformed shape: {X_transformed.shape}")
            print(f"   Transformed dtypes:\n{X_transformed.dtypes}")
            print(f"   First few rows:\n{X_transformed.head()}")
            
            # Check for cardinality issues
            for col in X_transformed.columns:
                n_unique = X_transformed[col].nunique()
                print(f"   Column '{col}': {n_unique} unique values")
                if n_unique == 1:
                    print(f"   ⚠️ WARNING: Column '{col}' has only 1 unique value!")
        except Exception as e:
            print(f"   ⚠️ Error during transformation test: {e}")
    
    # ===== END DEBUGGING =====
    
    # Provide past experiments
    strat.tell(experiments=experiments)
    

    # Inspect the underlying BoTorch model

    if hasattr(strat, 'model'):
        print("🔍 Model type:", type(strat.model))
        print("🔍 Input transform:", getattr(strat.model, 'input_transform', 'NONE'))
        print("🔍 Outcome transform:", getattr(strat.model, 'outcome_transform', 'NONE'))
    
    # Ask for next candidates
    return strat.ask(candidate_count=n_candidates)


def get_optimization_type(domain):
    """
    Determine if optimization is single or multi-objective based on domain.
    
    Args:
        domain: BoFire Domain object
    
    Returns:
        str: 'SOBO' for single objective, 'MOBO' for multi-objective
    """
    n_obj = len(domain.outputs.features)
    return 'SOBO' if n_obj == 1 else 'MOBO'
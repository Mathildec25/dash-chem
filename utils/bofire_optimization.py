"""
Bayesian Optimization utilities using BoFire
Sampling and optimization strategies
"""

import pandas as pd
import numpy as np

import bofire.strategies.api as strategies
from bofire.data_models.enum import SamplingMethodEnum
from bofire.data_models.acquisition_functions.api import (
    qLogNEI, qLogNEHVI, qEI, qNEI, qPI, qUCB, qSR
)
from bofire.data_models.strategies.api import RandomStrategy, SoboStrategy, MoboStrategy

from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from itertools import product as itertools_product


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
        
        # ===== LINEAR CONSTRAINTS (inequality + equality) =====
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


def bayesian_optimization(domain, experiments, n_candidates=1, acquisition_function=None):
    """
    Run Bayesian optimization using the appropriate strategy based on the number of objectives.
    
    - Single objective: SoboStrategy (default: qLogNEI)
    - Multiple objectives: MoboStrategy (default: qLogNEHVI)
    
    Args:
        domain: BoFire Domain object
        experiments: DataFrame with completed experiments (params + objectives)
        n_candidates: Number of candidates to suggest (default: 1)
        acquisition_function: Custom acquisition function instance (optional). If None, defaults are used.
    
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
        # Multi-objective optimization (MOBO)
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
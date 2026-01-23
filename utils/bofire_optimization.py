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


def sampling(domain, sampling_method: str, nb_points: int):
    """
    Run a sampling method for a given domain.

    Args:
        domain (Domain): BoFire domain.
        sampling_method (str): Name of SamplingMethodEnum (e.g., 'LHS', 'UNIFORM', 'SOBOL').
        nb_points (int): Number of points to sample.

    Returns:
        pd.DataFrame: Sampled points.
    """
    try:
        method_enum = SamplingMethodEnum[sampling_method]
    except KeyError:
        raise ValueError(f"Invalid sampling method '{sampling_method}'. Must be one of {list(SamplingMethodEnum.__members__.keys())}.")

    datamodel = RandomStrategy(domain=domain, fallback_sampling_method=method_enum)
    sampler = strategies.map(datamodel)
    return sampler.ask(nb_points)


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
    
        # Inspecte le modèle BoTorch sous-jacent
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
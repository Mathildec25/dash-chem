"""
BoFire utilities for Bayesian Optimization
Based on working code from user
Enhanced with advanced customization options
Enhanced version with configurable parameters
"""

import pandas as pd
import numpy as np

import bofire.strategies.api as strategies
from bofire.data_models.enum import SamplingMethodEnum
from bofire.data_models.acquisition_functions.api import (
    qLogNEI, qLogNEHVI, qEI, qNEI, qPI, qUCB, qSR
)
from bofire.data_models.acquisition_functions.api import (
    qLogNEI, 
    qLogNEHVI,
    qEI,
    qNEHVI,
    qUCB
)
from bofire.data_models.api import Domain, Inputs, Outputs
from bofire.data_models.features.api import (
    ContinuousInput, 
    DiscreteInput, 
    CategoricalInput, 
    ContinuousOutput
)
from bofire.data_models.objectives.api import MinimizeObjective, MaximizeObjective
from bofire.data_models.strategies.api import RandomStrategy, SoboStrategy, MoboStrategy


def create_bofire_domain_from_store(parameter_data, objective_data=None):
    """
    Create a BoFire Domain using saved parameters and objectives from Dash stores.

    Args:
        parameter_data (list of dicts): Output from parameter-store.
        objective_data (list of dicts): Output from objective-store.
            Each has 'name', 'direction', 'lower_bound', 'upper_bound'.

    Returns:
        Domain: BoFire domain object.
    """
    if not parameter_data:
        raise ValueError("No parameters provided to create domain.")

    # --- Create Input features ---
    input_features = []
    for param in parameter_data:
        typ = param.get("type")
        name = param.get("name")
        type_info = param.get("type_info", {})

        if typ == "float":  # Continuous
            lb, ub = type_info.get("range", [None, None])
            if lb is None or ub is None:
                raise ValueError(f"Parameter '{name}' missing bounds.")
            unit = type_info.get("unit", None)
            input_features.append(ContinuousInput(key=name, bounds=[lb, ub], unit=unit))

        elif typ == "int":  # Discrete
            values = type_info.get("range", [])
            if not values:
                raise ValueError(f"Discrete parameter '{name}' has no values.")
            unit = type_info.get("unit", None)
            input_features.append(DiscreteInput(key=name, values=values, unit=unit))

        elif typ == "cat":  # Categorical
            values = type_info.get("values", [])
            if not values:
                raise ValueError(f"Categorical parameter '{name}' has no values.")
            input_features.append(CategoricalInput(key=name, categories=values))

        else:
            raise ValueError(f"Unknown parameter type '{typ}' for parameter '{name}'.")

    inputs = Inputs(features=input_features)

    # --- Create Output features ---
    output_features = []
    if objective_data:
        for obj in objective_data:
            obj_name = obj.get("name")
            direction = obj.get("direction")
            lower = obj.get("lower_bound", 0.0)
            upper = obj.get("upper_bound", 1.0)

            if not obj_name or not direction:
                continue

            bounds = [lower, upper]

            if direction.lower() in ["max", "maximize"]:
                objective = MaximizeObjective(w=1.0, bounds=bounds)
            elif direction.lower() in ["min", "minimize"]:
                objective = MinimizeObjective(w=1.0, bounds=bounds)
            else:
                raise ValueError(f"Unknown objective direction '{direction}' for '{obj_name}'.")

            output_features.append(
                ContinuousOutput(key=obj_name, objective=objective)
            )

    outputs = Outputs(features=output_features)

    # --- Create domain ---
    return Domain(inputs=inputs, outputs=outputs)


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
def bayesian_optimization(
    domain, 
    experiments, 
    n_candidates=1,
    acquisition_function="qLogNEI",
    strategy_type="auto",
    num_restarts=20,
    raw_samples=512,
    ucb_beta=2.0,
    sequential=False
):
    """
    Run Bayesian optimization with configurable parameters.
    
    Args:
        domain: BoFire Domain object
        experiments: DataFrame with completed experiments (params + objectives)
        n_candidates: Number of candidates to suggest (default: 1)
        acquisition_function: Custom acquisition function instance (optional). If None, defaults are used.
        domain (Domain): BoFire Domain object
        experiments (DataFrame): DataFrame with completed experiments (params + objectives)
        n_candidates (int): Number of candidates to suggest (default: 1)
        acquisition_function (str): Acquisition function to use:
            - "qLogNEI" (recommended for single objective)
            - "qLogNEHVI" (recommended for multi-objective)
            - "qEI" (Expected Improvement)
            - "qUCB" (Upper Confidence Bound)
            - "qNEHVI" (Noisy Expected Hypervolume Improvement)
        strategy_type (str): "auto", "sobo", or "mobo"
            - "auto": automatically select based on number of objectives
            - "sobo": force single-objective strategy
            - "mobo": force multi-objective strategy
        num_restarts (int): Number of optimization restarts (default: 20)
        raw_samples (int): Number of raw samples for acquisition optimization (default: 512)
        ucb_beta (float): Beta parameter for UCB acquisition function (default: 2.0)
        sequential (bool): Use sequential optimization (default: False)
    
    Returns:
        DataFrame: Suggested candidates
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
    # Auto-select strategy if needed
    if strategy_type == "auto":
        strategy_type = "sobo" if n_obj == 1 else "mobo"
    
    # Validate strategy selection
    if strategy_type == "sobo" and n_obj > 1:
        print(f"⚠️ Warning: SOBO strategy selected but {n_obj} objectives detected. Using MOBO instead.")
        strategy_type = "mobo"
    elif strategy_type == "mobo" and n_obj == 1:
        print(f"⚠️ Warning: MOBO strategy selected but only 1 objective detected. Using SOBO instead.")
        strategy_type = "sobo"
    
    # Create acquisition function based on selection
    acq_func = None
    
    if acquisition_function == "qLogNEI":
        acq_func = qLogNEI()
    elif acquisition_function == "qLogNEHVI":
        acq_func = qLogNEHVI()
    elif acquisition_function == "qEI":
        acq_func = qEI()
    elif acquisition_function == "qNEHVI":
        acq_func = qNEHVI()
    elif acquisition_function == "qUCB":
        acq_func = qUCB(beta=ucb_beta)
    else:
        # Default fallback
        if strategy_type == "sobo":
            acq_func = qLogNEI()
        else:
            acq_func = qLogNEHVI()
        print(f"⚠️ Unknown acquisition function '{acquisition_function}'. Using default.")
    
    # Create appropriate strategy
    if strategy_type == "sobo":
        # Validate acquisition function is suitable for single-objective
        if acquisition_function in ["qLogNEHVI", "qNEHVI"]:
            print(f"⚠️ Warning: {acquisition_function} is for multi-objective. Using qLogNEI instead.")
            acq_func = qLogNEI()
        
        data_model = SoboStrategy(
            domain=domain, 
            acquisition_function=acq_func
        )
    else:  # mobo
        # Validate acquisition function is suitable for multi-objective
        if acquisition_function in ["qLogNEI", "qEI", "qUCB"]:
            print(f"⚠️ Warning: {acquisition_function} is for single-objective. Using qLogNEHVI instead.")
            acq_func = qLogNEHVI()
        
        data_model = MoboStrategy(
            domain=domain, 
            acquisition_function=acq_func
        )
    
    # Initialize strategy
    strat = strategies.map(data_model)
    
    # Provide past experiments
    strat.tell(experiments=experiments)
    
    # Ask for next candidates
    print(f"🎯 Strategy: {strategy_type.upper()}")
    print(f"📊 Acquisition: {acquisition_function}")
    print(f"🔢 Requesting {n_candidates} candidate(s)")
    
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


def get_acquisition_functions_for_strategy(n_objectives):
    """
    Get list of suitable acquisition functions based on number of objectives.
    
    Args:
        n_objectives (int): Number of objectives
    
    Returns:
        list: List of dictionaries with acquisition function options
    """
    if n_objectives == 1:
        return [
            {"label": "qLogNEI (Recommended)", "value": "qLogNEI"},
            {"label": "qEI (Expected Improvement)", "value": "qEI"},
            {"label": "qUCB (Upper Confidence Bound)", "value": "qUCB"},
        ]
    else:
        return [
            {"label": "qLogNEHVI (Recommended)", "value": "qLogNEHVI"},
            {"label": "qNEHVI (Noisy EHVI)", "value": "qNEHVI"},
        ]


def validate_bo_config(config, n_objectives):
    """
    Validate and adjust BO configuration if needed.
    
    Args:
        config (dict): BO configuration dictionary
        n_objectives (int): Number of objectives in the problem
    
    Returns:
        dict: Validated and corrected configuration
    """
    validated = config.copy()
    
    # Ensure n_candidates is reasonable
    if validated.get('n_candidates', 1) < 1:
        validated['n_candidates'] = 1
    elif validated.get('n_candidates', 1) > 10:
        validated['n_candidates'] = 10
    
    # Auto-adjust strategy based on objectives
    if validated.get('strategy_type') == 'auto':
        validated['strategy_type'] = 'sobo' if n_objectives == 1 else 'mobo'
    
    # Adjust acquisition function if incompatible with strategy
    strategy = validated.get('strategy_type', 'auto')
    acq_func = validated.get('acquisition_function', 'qLogNEI')
    
    multi_obj_funcs = ['qLogNEHVI', 'qNEHVI']
    single_obj_funcs = ['qLogNEI', 'qEI', 'qUCB']
    
    if strategy == 'sobo' and acq_func in multi_obj_funcs:
        validated['acquisition_function'] = 'qLogNEI'
        print(f"⚠️ Adjusted acquisition function to qLogNEI for single-objective optimization")
    elif strategy == 'mobo' and acq_func in single_obj_funcs:
        validated['acquisition_function'] = 'qLogNEHVI'
        print(f"⚠️ Adjusted acquisition function to qLogNEHVI for multi-objective optimization")
    
    return validated
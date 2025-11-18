"""
BoFire utilities for Bayesian Optimization
Based on working code from user
"""

import pandas as pd
import numpy as np

import bofire.strategies.api as strategies
from bofire.data_models.enum import SamplingMethodEnum
from bofire.data_models.acquisition_functions.api import qLogNEI, qLogNEHVI
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


def bayesian_optimization(domain, experiments, n_candidates=1):
    """
    Run Bayesian optimization using the appropriate strategy based on the number of objectives.
    
    - Single objective: SoboStrategy + qLogNEI
    - Multiple objectives: MoboStrategy + qLogNEHVI
    
    Args:
        domain: BoFire Domain object
        experiments: DataFrame with completed experiments (params + objectives)
        n_candidates: Number of candidates to suggest
    
    Returns:
        DataFrame with suggested candidates
    """
    
    # Determine number of objectives
    n_obj = len(domain.outputs.features)
    
    # Select strategy and acquisition function based on objective count
    if n_obj == 1:
        data_model = SoboStrategy(domain=domain, acquisition_function=qLogNEI())
    elif n_obj >= 2:
        data_model = MoboStrategy(domain=domain, acquisition_function=qLogNEHVI())
    else:
        raise ValueError("Domain must have at least one objective")

    # Initialize strategy
    strat = strategies.map(data_model)
    
    # Provide past experiments
    strat.tell(experiments=experiments)
    
    # Ask for next candidates
    return strat.ask(candidate_count=n_candidates)
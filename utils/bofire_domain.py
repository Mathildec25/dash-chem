"""
BoFire domain creation with descriptor support
Uses threading to avoid Flask context interference with Pydantic validators
"""

import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import threading

from bofire.data_models.api import Domain, Inputs, Outputs
from bofire.data_models.features.api import (
    ContinuousInput,
    DiscreteInput,
    CategoricalInput,
    CategoricalDescriptorInput,
    ContinuousOutput
)
from bofire.data_models.objectives.api import MinimizeObjective, MaximizeObjective

from utils.descriptor_data import get_descriptor_values

# Global thread executor for creating CategoricalDescriptorInput
# This avoids Flask context interference with Pydantic validators
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='bofire_creator')


def _create_categorical_descriptor_safely(name, categories, descriptors, values):
    """
    Creates a CategoricalDescriptorInput in a separate thread.
    """
    print(f"   🧵 Thread {threading.current_thread().name}: Creating CategoricalDescriptorInput")
    
    # Create allowed list explicitly
    allowed_list = [True for _ in categories]
    
    # Try normal constructor FIRST (like test.py does)
    try:
        feature = CategoricalDescriptorInput(
            key=name,
            categories=categories,
            allowed=allowed_list,
            descriptors=descriptors,
            values=values
        )
        print(f"   ✅ Created with normal constructor")
        return feature
    except KeyError as e:
        # Only if normal constructor fails, use model_construct as fallback
        print(f"   ⚠️ Normal constructor failed ({e}), trying model_construct...")
        feature = CategoricalDescriptorInput.model_construct(
            key=name,
            categories=categories,
            allowed=allowed_list,
            descriptors=descriptors,
            values=values
        )
        print(f"   ✅ Created with model_construct")
        return feature


def create_bofire_domain_from_store(parameter_data, objective_data=None, solvent_config=None, base_config=None):
    """
    Create a BoFire Domain using saved parameters and objectives from Dash stores.
    
    Args:
        parameter_data (list of dicts): Output from parameter-store.
        objective_data (list of dicts): Output from objective-store.
        solvent_config (dict): Configuration for solvent parameter with descriptors.
        base_config (dict): Configuration for base parameter with descriptors.
    
    Returns:
        Domain: BoFire domain object.
    """
    if not parameter_data:
        raise ValueError("No parameters provided to create domain.")
    
    print(f"🔍 solvent_config: {solvent_config}")
    print(f"🔍 base_config: {base_config}")

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
            
            # Check if this is a solvent/base with descriptors
            if solvent_config and solvent_config.get('param_id') == param.get('id'):
                # This is a Solvent parameter with descriptors
                categories = list(solvent_config.get('solvents', []))
                descriptors = list(solvent_config.get('descriptors', []))
                
                if descriptors and categories:
                    print(f"✅ Creating CategoricalDescriptorInput for Solvent")
                    print(f"   Categories: {categories}")
                    print(f"   Descriptors: {descriptors}")
                    
                    descriptor_values = get_descriptor_values(categories, descriptors, 'solvent')
                    print(f"   Values matrix: {descriptor_values}")
                    
                    # Execute in separate thread to avoid Flask context interference
                    future = _executor.submit(
                        _create_categorical_descriptor_safely,
                        name, categories, descriptors, descriptor_values
                    )
                    feature = future.result()  # Block until complete
                    
                    input_features.append(feature)
                    continue
            
            elif base_config and base_config.get('param_id') == param.get('id'):
                # This is a Base parameter with descriptors
                categories = list(base_config.get('bases', []))
                descriptors = list(base_config.get('descriptors', []))
                
                if descriptors and categories:
                    print(f"✅ Creating CategoricalDescriptorInput for Base")
                    print(f"   Categories: {categories}")
                    print(f"   Descriptors: {descriptors}")
                    
                    descriptor_values = get_descriptor_values(categories, descriptors, 'base')
                    print(f"   Values matrix: {descriptor_values}")
                    
                    # Execute in separate thread to avoid Flask context interference
                    future = _executor.submit(
                        _create_categorical_descriptor_safely,
                        name, categories, descriptors, descriptor_values
                    )
                    feature = future.result()  # Block until complete
                    
                    input_features.append(feature)
                    continue
            
            # Standard categorical without descriptors
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
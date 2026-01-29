"""
BoFire domain creation with descriptor support, DISCRETE CONSTRAINTS, and normalization utilities
Uses threading to avoid Flask context interference with Pydantic validators

MODIFICATIONS FOR DISCRETE + NATIVE CONSTRAINTS:
- Converts float parameters to DiscreteInput when discretization step is provided
- Uses CategoricalExcludeConstraint for native boiling point AND melting point constraints
- Eliminates need for post-filtering of suggestions

Best Practices for Bayesian Optimization in Chemistry:
- Normalize inputs to [0, 1] for better GP performance
- Standardize outputs (Y) for numerical stability
- Handle different parameter scales appropriately
- Use constraints to enforce physical limits (e.g., MP < temperature < BP)
"""

import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import List, Dict, Optional, Tuple, Any

from bofire.data_models.api import Domain, Inputs, Outputs, Constraints
from bofire.data_models.features.api import (
    ContinuousInput,
    DiscreteInput,
    CategoricalInput,
    CategoricalDescriptorInput,
    ContinuousOutput
)
from bofire.data_models.objectives.api import MinimizeObjective, MaximizeObjective

# ✅ IMPORTS FOR NATIVE CONSTRAINTS
from bofire.data_models.constraints.api import (
    LinearInequalityConstraint,
    CategoricalExcludeConstraint,
    SelectionCondition,
    ThresholdCondition
)

from utils.descriptor_data import get_descriptor_values

# Global thread executor for creating CategoricalDescriptorInput
# This avoids Flask context interference with Pydantic validators
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='bofire_creator')


# ==============================================================================
# NORMALIZATION UTILITIES - Best Practices for BO in Chemistry
# ==============================================================================

class InputNormalizer:
    """
    Handles normalization/denormalization of input parameters for Bayesian Optimization.
    
    Note: BoFire internally handles normalization for the GP model, but this class
    can be useful for custom preprocessing or debugging.
    """
    
    def __init__(self):
        self.bounds = {}
        self.is_fitted = False
    
    def fit(self, domain: Domain, experiments: pd.DataFrame = None):
        """
        Extract bounds from domain for normalization.
        
        Args:
            domain: BoFire domain
            experiments: Optional DataFrame to compute bounds from data
        """
        for feature in domain.inputs.features:
            if isinstance(feature, ContinuousInput):
                self.bounds[feature.key] = {
                    'lower': feature.bounds[0],
                    'upper': feature.bounds[1],
                    'type': 'continuous'
                }
            elif isinstance(feature, DiscreteInput):
                self.bounds[feature.key] = {
                    'lower': min(feature.values),
                    'upper': max(feature.values),
                    'type': 'discrete'
                }
        self.is_fitted = True
        return self
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize continuous parameters to [0, 1]."""
        if not self.is_fitted:
            raise ValueError("InputNormalizer must be fitted before normalizing")
        
        result = df.copy()
        for col, bounds in self.bounds.items():
            if col in result.columns and bounds['type'] == 'continuous':
                lb, ub = bounds['lower'], bounds['upper']
                if ub > lb:
                    result[col] = (result[col] - lb) / (ub - lb)
        return result
    
    def denormalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert normalized values back to original scale."""
        if not self.is_fitted:
            raise ValueError("InputNormalizer must be fitted before denormalizing")
        
        result = df.copy()
        for col, bounds in self.bounds.items():
            if col in result.columns and bounds['type'] == 'continuous':
                lb, ub = bounds['lower'], bounds['upper']
                result[col] = result[col] * (ub - lb) + lb
        return result


class OutputStandardizer:
    """
    Handles standardization of outputs (Y) for Bayesian Optimization.
    
    Note: BoFire internally handles output standardization, but this class
    can be useful for custom preprocessing or debugging.
    """
    
    def __init__(self):
        self.stats = {}
        self.is_fitted = False
    
    def fit(self, experiments: pd.DataFrame, objective_columns: List[str]):
        """Compute mean and std for each objective."""
        for col in objective_columns:
            if col in experiments.columns:
                values = experiments[col].dropna()
                self.stats[col] = {
                    'mean': values.mean(),
                    'std': values.std() if len(values) > 1 else 1.0
                }
        self.is_fitted = True
        return self
    
    def standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize objectives to zero mean, unit variance."""
        if not self.is_fitted:
            raise ValueError("OutputStandardizer must be fitted before standardizing")
        
        result = df.copy()
        for col, stats in self.stats.items():
            if col in result.columns:
                std = stats['std'] if stats['std'] > 0 else 1.0
                result[col] = (result[col] - stats['mean']) / std
        return result
    
    def destandardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert standardized values back to original scale."""
        if not self.is_fitted:
            raise ValueError("OutputStandardizer must be fitted before destandardizing")
        
        result = df.copy()
        for col, stats in self.stats.items():
            if col in result.columns:
                std = stats['std'] if stats['std'] > 0 else 1.0
                result[col] = result[col] * std + stats['mean']
        return result


def check_parameter_scales(domain: Domain) -> List[str]:
    """
    Check parameter scales and provide recommendations for Bayesian Optimization.
    
    Args:
        domain: BoFire domain
    
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Collect continuous parameter ranges
    ranges = []
    for feature in domain.inputs.features:
        if isinstance(feature, ContinuousInput):
            lb, ub = feature.bounds
            param_range = ub - lb
            ranges.append((feature.key, param_range, lb, ub))
    
    if not ranges:
        return recommendations
    
    # Check for scale differences
    range_values = [r[1] for r in ranges]
    if len(range_values) > 1:
        max_range = max(range_values)
        min_range = min(range_values)
        if max_range / (min_range + 1e-10) > 100:
            recommendations.append(
                f"⚠️ Large scale differences detected between parameters. "
                f"Consider rescaling or using log-scale."
            )
    
    # Check for parameters that might benefit from log-scale
    for name, param_range, lb, ub in ranges:
        if lb > 0 and ub / lb > 100:
            recommendations.append(
                f"📊 Parameter '{name}' spans multiple orders of magnitude. "
                f"Consider log-transform for better GP performance."
            )
    
    return recommendations


# ==============================================================================
# DOMAIN CREATION FUNCTIONS
# ==============================================================================

def _create_categorical_descriptor_safely(name, categories, descriptors, values):
    """
    Creates a CategoricalDescriptorInput in a separate thread.
    This avoids Flask context interference with Pydantic validators.
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


def create_bofire_domain_from_store(
    parameter_data: List[Dict],
    objective_data: Optional[List[Dict]] = None,
    solvent_config: Optional[Dict] = None,
    base_config: Optional[Dict] = None,
    constraints_config: Optional[Dict] = None,
    discretization_config: Optional[Dict] = None
) -> Domain:
    """
    Create a BoFire Domain using saved parameters and objectives from Dash stores.
    
    ✅ UPDATED: Supports both boiling point (BP) and melting point (MP) constraints
    
    Args:
        parameter_data (list of dicts): Output from parameter-store.
        objective_data (list of dicts): Output from objective-store.
        solvent_config (dict): Configuration for solvent parameter with descriptors.
        base_config (dict): Configuration for base parameter with descriptors.
        constraints_config (dict): Configuration for constraints (BP and MP limits).
        discretization_config (dict): Configuration for discretization steps.
            Example: {'Temperature': 5.0, 'Concentration': 0.1}
    
    Returns:
        Domain: BoFire domain object.
    """
    if not parameter_data:
        raise ValueError("No parameters provided to create domain.")
    
    print(f"🔍 solvent_config: {solvent_config}")
    print(f"🔍 base_config: {base_config}")
    print(f"🔍 constraints_config: {constraints_config}")
    print(f"🔍 discretization_config: {discretization_config}")

    # --- Create Input features ---
    input_features = []
    for param in parameter_data:
        typ = param.get("type")
        name = param.get("name")
        type_info = param.get("type_info", {})

        if typ == "float":  # Continuous → check if we need to discretize
            lb, ub = type_info.get("range", [None, None])
            if lb is None or ub is None:
                raise ValueError(f"Parameter '{name}' missing bounds.")
            unit = type_info.get("unit", None)
            
            # ✅ CHECK FOR DISCRETIZATION
            if discretization_config and name in discretization_config:
                step = discretization_config[name]
                if step and step > 0:
                    # Create discrete values grid
                    values = list(np.arange(lb, ub + step/2, step))  # Include upper bound
                    values = [round(v, 6) for v in values]  # Avoid floating point errors
                    
                    print(f"   🎯 Discretizing '{name}': {len(values)} values from {lb} to {ub} (step={step})")
                    input_features.append(DiscreteInput(key=name, values=values, unit=unit))
                    continue
            
            # Default: use continuous
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
            obj_direction = obj.get("direction")
            lower = obj.get("lower_bound", 0.0)
            upper = obj.get("upper_bound", 1.0)

            if not obj_name:
                continue

            # Accept both short and long forms
            if obj_direction in ["minimize", "min"]:
                objective = MinimizeObjective(w=1.0, bounds=(lower, upper))
            elif obj_direction in ["maximize", "max"]:
                objective = MaximizeObjective(w=1.0, bounds=(lower, upper))
            else:
                raise ValueError(f"Unknown objective direction: {obj_direction}")

            output_features.append(
                ContinuousOutput(key=obj_name, objective=objective)
            )

    outputs = Outputs(features=output_features)

    # ===== ✅ CREATE NATIVE CONSTRAINTS (BP AND MP) =====
    constraint_list = []
    
    # Read constraints from base_config (where constraint callback stores them)
    if base_config and base_config.get('constraints'):
        print(f"🔧 Processing {len(base_config['constraints'])} constraint(s)...")
        
        # Get solvent info from solvent_config
        solvent_param_name = None
        bp_dict = {}
        mp_dict = {}
        
        if solvent_config:
            from bofire_solvent_descriptors import SOLVENT_DESCRIPTORS
            
            solvents = solvent_config.get('solvents', [])
            solvent_param_name = solvent_config.get('param_name', 'Solvent')
            
            # Calculate bp_dict and mp_dict from SOLVENT_DESCRIPTORS
            for s in solvents:
                if s in SOLVENT_DESCRIPTORS:
                    if 'bp' in SOLVENT_DESCRIPTORS[s]:
                        bp_dict[s] = SOLVENT_DESCRIPTORS[s]['bp']
                    if 'mp' in SOLVENT_DESCRIPTORS[s]:
                        mp_dict[s] = SOLVENT_DESCRIPTORS[s]['mp']
            
            print(f"✅ Found {len(bp_dict)} solvents with boiling points")
            print(f"✅ Found {len(mp_dict)} solvents with melting points")
            print(f"✅ Using solvent_param_name: '{solvent_param_name}'")
        else:
            print(f"⚠️ No solvent_config provided, cannot create constraints")
        
        # Verify that solvent parameter exists in input features
        solvent_feature = next((f for f in input_features if f.key == solvent_param_name), None) if solvent_param_name else None
        
        if not solvent_feature:
            print(f"⚠️ Solvent parameter '{solvent_param_name}' not found in inputs!")
            print(f"   Available parameters: {[f.key for f in input_features]}")
            print(f"   Skipping constraint creation")
        elif not bp_dict and not mp_dict:
            print(f"⚠️ No boiling/melting points available, skipping constraint creation")
        else:
            print(f"✅ Found solvent parameter: {solvent_param_name}")
            
            # Get safety margin from base_config
            safety_margin = base_config.get('safety_margin', 5.0)
            
            # Process each constraint
            for constraint in base_config.get('constraints', []):
                constraint_type = constraint.get('type', 'less_than_bp')
                param_name = constraint['parameter_name']
                
                # Check if parameter exists in input features
                param_feature = next((f for f in input_features if f.key == param_name), None)
                
                if not param_feature:
                    print(f"   ⚠️ Parameter '{param_name}' not found in inputs, skipping constraint")
                    continue
                
                # ===== CONSTRAINT TYPE: less_than_bp (Boiling Point) =====
                if constraint_type == 'less_than_bp':
                    if not bp_dict:
                        print(f"   ⚠️ No boiling points available, skipping less_than_bp constraint")
                        continue
                    
                    # Create CategoricalExcludeConstraint FOR EACH SOLVENT
                    for solvent_name, bp in bp_dict.items():
                        try:
                            temp_limit = bp - safety_margin
                            
                            # If parameter is discrete, find the appropriate discrete threshold
                            if isinstance(param_feature, DiscreteInput):
                                # Find the first value >= limit (to exclude)
                                invalid_values = [v for v in param_feature.values if v >= temp_limit]
                                if invalid_values:
                                    temp_limit_discrete = min(invalid_values)
                                else:
                                    # All values are valid, no constraint needed for this solvent
                                    print(f"   ℹ️ {solvent_name}: All discrete values below {temp_limit}°C, no BP constraint needed")
                                    continue
                            else:
                                temp_limit_discrete = temp_limit
                            
                            # CategoricalExcludeConstraint excludes combinations where:
                            # Solvent == solvent_name AND Parameter >= temp_limit (too hot!)
                            native_constraint = CategoricalExcludeConstraint(
                                features=[solvent_param_name, param_name],
                                conditions=[
                                    SelectionCondition(selection=[solvent_name]),
                                    ThresholdCondition(threshold=temp_limit_discrete, operator=">="),
                                ],
                            )
                            constraint_list.append(native_constraint)
                            print(f"   ✅ Native constraint (BP): {solvent_name} → {param_name} < {temp_limit_discrete}°C "
                                  f"(BP={bp}°C, margin={safety_margin}°C)")
                            
                        except Exception as e:
                            print(f"   ❌ Failed to create BP constraint for {solvent_name}: {e}")
                            import traceback
                            traceback.print_exc()
                
                # ===== CONSTRAINT TYPE: greater_than_mp (Melting Point) - NEW =====
                elif constraint_type == 'greater_than_mp':
                    if not mp_dict:
                        print(f"   ⚠️ No melting points available, skipping greater_than_mp constraint")
                        continue
                    
                    # Create CategoricalExcludeConstraint FOR EACH SOLVENT
                    for solvent_name, mp in mp_dict.items():
                        try:
                            # T must be > MP, so we exclude T <= (MP + margin)
                            temp_limit = mp + safety_margin
                            
                            # If parameter is discrete, find the appropriate discrete threshold
                            if isinstance(param_feature, DiscreteInput):
                                # Find the last value <= limit (values to exclude)
                                invalid_values = [v for v in param_feature.values if v <= temp_limit]
                                if invalid_values:
                                    temp_limit_discrete = max(invalid_values)
                                else:
                                    # All values are valid (above melting point), no constraint needed
                                    print(f"   ℹ️ {solvent_name}: All discrete values above {temp_limit}°C, no MP constraint needed")
                                    continue
                            else:
                                temp_limit_discrete = temp_limit
                            
                            # CategoricalExcludeConstraint excludes combinations where:
                            # Solvent == solvent_name AND Parameter <= temp_limit (too cold!)
                            native_constraint = CategoricalExcludeConstraint(
                                features=[solvent_param_name, param_name],
                                conditions=[
                                    SelectionCondition(selection=[solvent_name]),
                                    ThresholdCondition(threshold=temp_limit_discrete, operator="<="),
                                ],
                            )
                            constraint_list.append(native_constraint)
                            print(f"   ✅ Native constraint (MP): {solvent_name} → {param_name} > {temp_limit_discrete}°C "
                                  f"(MP={mp}°C, margin={safety_margin}°C)")
                            
                        except Exception as e:
                            print(f"   ❌ Failed to create MP constraint for {solvent_name}: {e}")
                            import traceback
                            traceback.print_exc()
                
                else:
                    print(f"   ⚠️ Unknown constraint type: {constraint_type}")
    else:
        print(f"ℹ️ No constraints configured")
    
    # Create Constraints object if we have any constraints
    if constraint_list:
        constraints = Constraints(constraints=constraint_list)
        print(f"🎯 Created {len(constraint_list)} NATIVE constraint(s) for domain")
    else:
        constraints = None
        print(f"ℹ️ No constraints added to domain")

    # --- Create domain ---
    # Only pass constraints if we have some
    if constraints is not None:
        domain = Domain(inputs=inputs, outputs=outputs, constraints=constraints)
    else:
        domain = Domain(inputs=inputs, outputs=outputs)
    
    # --- Log scale recommendations ---
    recommendations = check_parameter_scales(domain)
    for rec in recommendations:
        print(rec)
    
    return domain


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def create_normalizers_from_domain(
    domain: Domain,
    experiments: pd.DataFrame
) -> Tuple[InputNormalizer, OutputStandardizer]:
    """
    Create fitted normalizer and standardizer from domain and experiment data.
    
    Convenience function that creates and fits both normalizers in one call.
    
    Args:
        domain: BoFire domain
        experiments: DataFrame with experimental data
        
    Returns:
        Tuple of (input_normalizer, output_standardizer)
    """
    # Fit input normalizer
    input_normalizer = InputNormalizer()
    input_normalizer.fit(domain, experiments)
    
    # Fit output standardizer
    objective_columns = [f.key for f in domain.outputs.features]
    output_standardizer = OutputStandardizer()
    output_standardizer.fit(experiments, objective_columns)
    
    return input_normalizer, output_standardizer
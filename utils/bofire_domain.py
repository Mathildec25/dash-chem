"""
BoFire domain creation with descriptor support, DISCRETE CONSTRAINTS, and normalization utilities
Uses threading to avoid Flask context interference with Pydantic validators

MODIFICATIONS FOR DISCRETE + NATIVE CONSTRAINTS:
- Converts float parameters to DiscreteInput when discretization step is provided
- Uses CategoricalExcludeConstraint for native boiling point constraints
- Eliminates need for post-filtering of suggestions

Best Practices for Bayesian Optimization in Chemistry:
- Normalize inputs to [0, 1] for better GP performance
- Standardize outputs (Y) for numerical stability
- Handle different parameter scales appropriately
- Use constraints to enforce physical limits (e.g., temperature < boiling point)
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

# ✅ NEW IMPORTS FOR NATIVE CONSTRAINTS
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
    
    Best Practice: Normalize all continuous/discrete inputs to [0, 1] range
    - Improves GP kernel computation (Matérn, RBF kernels work better in unit hypercube)
    - Ensures equal weighting of all parameters regardless of their natural scale
    - Improves numerical stability of acquisition function optimization
    
    Example:
        normalizer = InputNormalizer()
        normalizer.fit(domain, experiments_df)
        X_normalized = normalizer.transform(experiments_df)
        X_original = normalizer.inverse_transform(X_normalized)
    """
    
    def __init__(self):
        self.bounds: Dict[str, Tuple[float, float]] = {}
        self.param_types: Dict[str, str] = {}  # 'continuous', 'discrete', 'categorical'
        self.categorical_maps: Dict[str, Dict[str, int]] = {}
        self.fitted = False
    
    def fit(self, domain: Domain, data: Optional[pd.DataFrame] = None) -> 'InputNormalizer':
        """
        Fit the normalizer to a BoFire domain.
        
        Args:
            domain: BoFire Domain object
            data: Optional DataFrame of experiments (used for detecting actual ranges)
        
        Returns:
            self (for method chaining)
        """
        for feature in domain.inputs.features:
            key = feature.key
            
            if isinstance(feature, ContinuousInput):
                self.param_types[key] = 'continuous'
                lb, ub = feature.bounds
                self.bounds[key] = (float(lb), float(ub))
                
            elif isinstance(feature, DiscreteInput):
                self.param_types[key] = 'discrete'
                values = feature.values
                self.bounds[key] = (float(min(values)), float(max(values)))
                
            elif isinstance(feature, (CategoricalInput, CategoricalDescriptorInput)):
                self.param_types[key] = 'categorical'
                categories = feature.categories
                # Map categories to integers for one-hot or ordinal encoding
                self.categorical_maps[key] = {cat: i for i, cat in enumerate(categories)}
        
        self.fitted = True
        return self
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize input data to [0, 1] range for continuous/discrete parameters.
        Categorical parameters are left as-is (BoFire handles encoding internally).
        
        Args:
            data: DataFrame with parameter columns
            
        Returns:
            Normalized DataFrame
        """
        if not self.fitted:
            raise ValueError("InputNormalizer must be fit before transform")
        
        normalized = data.copy()
        
        for col in data.columns:
            if col in self.bounds and self.param_types.get(col) in ['continuous', 'discrete']:
                lb, ub = self.bounds[col]
                if ub > lb:  # Avoid division by zero
                    normalized[col] = (data[col] - lb) / (ub - lb)
                else:
                    normalized[col] = 0.5  # Constant parameter
        
        return normalized
    
    def inverse_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Denormalize data from [0, 1] back to original scale.
        
        Args:
            data: Normalized DataFrame
            
        Returns:
            DataFrame in original scale
        """
        if not self.fitted:
            raise ValueError("InputNormalizer must be fit before inverse_transform")
        
        denormalized = data.copy()
        
        for col in data.columns:
            if col in self.bounds and self.param_types.get(col) in ['continuous', 'discrete']:
                lb, ub = self.bounds[col]
                denormalized[col] = data[col] * (ub - lb) + lb
        
        return denormalized
    
    def get_bounds_info(self) -> pd.DataFrame:
        """
        Get a summary of parameter bounds for debugging/logging.
        
        Returns:
            DataFrame with parameter names, types, and bounds
        """
        info = []
        for key in self.param_types:
            if key in self.bounds:
                lb, ub = self.bounds[key]
                info.append({
                    'parameter': key,
                    'type': self.param_types[key],
                    'lower_bound': lb,
                    'upper_bound': ub,
                    'range': ub - lb
                })
        return pd.DataFrame(info)


class OutputStandardizer:
    """
    Handles standardization (z-score normalization) of output variables.
    
    Best Practice: Standardize outputs to mean=0, std=1
    - Improves GP conditioning and numerical stability
    - Makes different objectives comparable in multi-objective optimization
    - Prevents numerical issues in matrix inversion
    
    Example:
        standardizer = OutputStandardizer()
        standardizer.fit(experiments_df, objective_columns=['Yield', 'Purity'])
        Y_standardized = standardizer.transform(experiments_df)
        Y_original = standardizer.inverse_transform(Y_standardized)
    """
    
    def __init__(self):
        self.means: Dict[str, float] = {}
        self.stds: Dict[str, float] = {}
        self.fitted = False
    
    def fit(self, data: pd.DataFrame, objective_columns: List[str]) -> 'OutputStandardizer':
        """
        Fit the standardizer to output data.
        
        Args:
            data: DataFrame containing objective columns
            objective_columns: List of column names to standardize
            
        Returns:
            self (for method chaining)
        """
        for col in objective_columns:
            if col in data.columns:
                self.means[col] = data[col].mean()
                self.stds[col] = data[col].std()
                
                # Handle constant columns
                if self.stds[col] < 1e-10:
                    self.stds[col] = 1.0
        
        self.fitted = True
        return self
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize output data to z-scores.
        
        Args:
            data: DataFrame with objective columns
            
        Returns:
            Standardized DataFrame
        """
        if not self.fitted:
            raise ValueError("OutputStandardizer must be fit before transform")
        
        standardized = data.copy()
        
        for col in self.means:
            if col in data.columns:
                standardized[col] = (data[col] - self.means[col]) / self.stds[col]
        
        return standardized
    
    def inverse_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Reverse standardization back to original scale.
        
        Args:
            data: Standardized DataFrame
            
        Returns:
            DataFrame in original scale
        """
        if not self.fitted:
            raise ValueError("OutputStandardizer must be fit before inverse_transform")
        
        denormalized = data.copy()
        
        for col in self.means:
            if col in data.columns:
                denormalized[col] = data[col] * self.stds[col] + self.means[col]
        
        return denormalized
    
    def get_stats(self) -> pd.DataFrame:
        """
        Get standardization statistics.
        
        Returns:
            DataFrame with objective names, means, and standard deviations
        """
        info = []
        for col in self.means:
            info.append({
                'objective': col,
                'mean': self.means[col],
                'std': self.stds[col]
            })
        return pd.DataFrame(info)


def check_parameter_scales(domain: Domain) -> List[str]:
    """
    Check parameter scales and provide recommendations for better GP performance.
    
    Args:
        domain: BoFire domain
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Check for parameters with very different scales
    ranges = []
    for feature in domain.inputs.features:
        if isinstance(feature, ContinuousInput):
            lb, ub = feature.bounds
            param_range = ub - lb
            ranges.append((feature.key, param_range, lb, ub))
        elif isinstance(feature, DiscreteInput):
            values = feature.values
            param_range = max(values) - min(values)
            ranges.append((feature.key, param_range, min(values), max(values)))
    
    if len(ranges) >= 2:
        # Check if ranges differ by more than 2 orders of magnitude
        range_values = [r[1] for r in ranges]
        max_range = max(range_values)
        min_range = min([r for r in range_values if r > 0])
        
        if max_range / min_range > 100:
            recommendations.append(
                f"⚠️ Parameter scales differ by {max_range/min_range:.1f}x. "
                f"Normalization is strongly recommended."
            )
    
    # Check for very small ranges
    for name, param_range, lb, ub in ranges:
        if param_range < 1e-6:
            recommendations.append(
                f"📊 Parameter '{name}' has very small range [{lb}, {ub}]. "
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
    discretization_config: Optional[Dict] = None  # ✅ NEW
) -> Domain:
    """
    Create a BoFire Domain using saved parameters and objectives from Dash stores.
    
    ✅ NEW: Supports discretization of continuous parameters and native constraints
    
    Args:
        parameter_data (list of dicts): Output from parameter-store.
        objective_data (list of dicts): Output from objective-store.
        solvent_config (dict): Configuration for solvent parameter with descriptors.
        base_config (dict): Configuration for base parameter with descriptors.
        constraints_config (dict): Configuration for constraints (e.g., boiling point limits).
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
    print(f"🔍 discretization_config: {discretization_config}")  # ✅ NEW
    
    # ✅ WORKAROUND: Read constraints from either constraints_config or base_config
    # Sometimes the callback writes to the wrong store
    effective_constraints_config = constraints_config
    if not effective_constraints_config and base_config and 'constraints' in base_config:
        print("⚠️ Reading constraints from base_config (should be in constraints_config)")
        effective_constraints_config = base_config
    
    print(f"🔍 effective_constraints_config: {effective_constraints_config}")

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

    # ===== ✅ NEW: CREATE NATIVE CONSTRAINTS =====
    constraint_list = []
    
    if effective_constraints_config and effective_constraints_config.get('constraints'):
        print(f"🔧 Processing {len(effective_constraints_config['constraints'])} constraint(s)...")
        
        # Get solvent configuration
        solvent_param_name = None
        solvents_list = []
        bp_dict = effective_constraints_config.get('boiling_points', {})
        
        if solvent_config:
            solvent_param_name = solvent_config.get('param_name')
            solvents_list = solvent_config.get('solvents', [])
        
        # ✅ Fallback: read solvent_param_name from effective_constraints_config
        if not solvent_param_name and effective_constraints_config:
            solvent_param_name = effective_constraints_config.get('solvent_param_name')
        
        # Last resort: assume it's called "Solvent"
        if not solvent_param_name:
            solvent_param_name = "Solvent"
            print(f"⚠️ No solvent_param_name found, using default: 'Solvent'")
        else:
            print(f"✅ Using solvent_param_name: '{solvent_param_name}'")
        
        # ✅ Verify that solvent parameter exists in input features
        solvent_feature = next((f for f in input_features if f.key == solvent_param_name), None)
        if not solvent_feature:
            print(f"❌ Solvent parameter '{solvent_param_name}' not found in inputs!")
            print(f"   Available parameters: {[f.key for f in input_features]}")
            print(f"   Cannot create constraints without solvent parameter")
        else:
            print(f"✅ Found solvent parameter: {solvent_param_name}")
        
        # Get safety margin from effective_constraints_config or use default
        safety_margin = effective_constraints_config.get('safety_margin', 10.0)  # °C
        
        # Only create constraints if we have solvent parameter
        if not solvent_feature:
            print(f"⚠️ Skipping constraint creation (no solvent parameter)")
        else:
            for constraint in effective_constraints_config.get('constraints', []):
                if constraint['type'] == 'less_than_bp':
                    param_name = constraint['parameter_name']
                    
                    # Check if parameter exists in input features
                    param_feature = next((f for f in input_features if f.key == param_name), None)
                    
                    if not param_feature:
                        print(f"   ⚠️ Parameter '{param_name}' not found in inputs, skipping constraint")
                        continue
                    
                    if not solvent_param_name or not bp_dict:
                        print(f"   ⚠️ No solvent configuration, cannot create BP constraint")
                        continue
                    
                    # ✅ CREATE CategoricalExcludeConstraint FOR EACH SOLVENT
                    for solvent_name, bp in bp_dict.items():
                        try:
                            temp_limit = bp - safety_margin
                            
                            # If parameter is discrete, find the appropriate discrete threshold
                            if isinstance(param_feature, DiscreteInput):
                                # Find the largest discrete value that's still below the limit
                                valid_values = [v for v in param_feature.values if v < temp_limit]
                                if valid_values:
                                    # Threshold should be the first value >= limit
                                    invalid_values = [v for v in param_feature.values if v >= temp_limit]
                                    if invalid_values:
                                        temp_limit_discrete = min(invalid_values)
                                    else:
                                        # All values are valid, no constraint needed for this solvent
                                        print(f"   ℹ️ {solvent_name}: All discrete values below {temp_limit}°C, no constraint needed")
                                        continue
                                else:
                                    print(f"   ⚠️ {solvent_name}: No valid discrete values below {temp_limit}°C!")
                                    continue
                            else:
                                temp_limit_discrete = temp_limit
                            
                            # CategoricalExcludeConstraint excludes combinations where:
                            # Solvent == solvent_name AND Parameter >= temp_limit
                            native_constraint = CategoricalExcludeConstraint(
                                features=[solvent_param_name, param_name],
                                conditions=[
                                    SelectionCondition(selection=[solvent_name]),
                                    ThresholdCondition(threshold=temp_limit_discrete, operator=">="),
                                ],
                            )
                            constraint_list.append(native_constraint)
                            print(f"   ✅ Native constraint: {solvent_name} → {param_name} < {temp_limit_discrete}°C "
                                  f"(BP={bp}°C, margin={safety_margin}°C)")
                            
                        except Exception as e:
                            print(f"   ❌ Failed to create constraint for {solvent_name}: {e}")
                            import traceback
                            traceback.print_exc()
    
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
"""
BoFire domain creation with descriptor support and normalization utilities
Uses threading to avoid Flask context interference with Pydantic validators

Best Practices for Bayesian Optimization in Chemistry:
- Normalize inputs to [0, 1] for better GP performance
- Standardize outputs (Y) for numerical stability
- Handle different parameter scales appropriately
"""

import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import List, Dict, Optional, Tuple, Any

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
            DataFrame with parameter bounds and types
        """
        info = []
        for key, ptype in self.param_types.items():
            if ptype in ['continuous', 'discrete']:
                lb, ub = self.bounds[key]
                info.append({
                    'parameter': key,
                    'type': ptype,
                    'lower_bound': lb,
                    'upper_bound': ub,
                    'range': ub - lb
                })
            else:
                n_cats = len(self.categorical_maps.get(key, {}))
                info.append({
                    'parameter': key,
                    'type': ptype,
                    'lower_bound': None,
                    'upper_bound': None,
                    'range': f"{n_cats} categories"
                })
        return pd.DataFrame(info)


class OutputStandardizer:
    """
    Handles standardization of output (objective) values for Bayesian Optimization.
    
    Best Practice: Standardize outputs to zero mean, unit variance
    - Improves GP fitting, especially when objectives are on very different scales
    - Helps with multi-objective optimization when objectives have different ranges
    - Improves numerical conditioning of the posterior
    
    Example:
        standardizer = OutputStandardizer()
        standardizer.fit(experiments_df[['Yield', 'Cost']])
        Y_standardized = standardizer.transform(experiments_df[['Yield', 'Cost']])
        Y_original = standardizer.inverse_transform(Y_standardized)
    """
    
    def __init__(self, method: str = 'standardize'):
        """
        Args:
            method: 'standardize' (z-score) or 'normalize' (min-max to [0,1])
        """
        self.method = method
        self.means: Dict[str, float] = {}
        self.stds: Dict[str, float] = {}
        self.mins: Dict[str, float] = {}
        self.maxs: Dict[str, float] = {}
        self.fitted = False
    
    def fit(self, data: pd.DataFrame) -> 'OutputStandardizer':
        """
        Fit the standardizer to objective data.
        
        Args:
            data: DataFrame with objective columns
            
        Returns:
            self (for method chaining)
        """
        for col in data.columns:
            values = data[col].dropna()
            
            if self.method == 'standardize':
                self.means[col] = float(values.mean())
                self.stds[col] = float(values.std())
                # Handle constant objective (std = 0)
                if self.stds[col] == 0:
                    self.stds[col] = 1.0
            else:  # normalize
                self.mins[col] = float(values.min())
                self.maxs[col] = float(values.max())
                # Handle constant objective
                if self.maxs[col] == self.mins[col]:
                    self.maxs[col] = self.mins[col] + 1.0
        
        self.fitted = True
        return self
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize/normalize objective values.
        
        Args:
            data: DataFrame with objective columns
            
        Returns:
            Standardized/normalized DataFrame
        """
        if not self.fitted:
            raise ValueError("OutputStandardizer must be fit before transform")
        
        transformed = data.copy()
        
        for col in data.columns:
            if col in self.means:
                if self.method == 'standardize':
                    transformed[col] = (data[col] - self.means[col]) / self.stds[col]
                else:
                    transformed[col] = (data[col] - self.mins[col]) / (self.maxs[col] - self.mins[col])
        
        return transformed
    
    def inverse_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Reverse the standardization/normalization.
        
        Args:
            data: Standardized/normalized DataFrame
            
        Returns:
            DataFrame in original scale
        """
        if not self.fitted:
            raise ValueError("OutputStandardizer must be fit before inverse_transform")
        
        inverse = data.copy()
        
        for col in data.columns:
            if col in self.means:
                if self.method == 'standardize':
                    inverse[col] = data[col] * self.stds[col] + self.means[col]
                else:
                    inverse[col] = data[col] * (self.maxs[col] - self.mins[col]) + self.mins[col]
        
        return inverse
    
    def get_stats_info(self) -> pd.DataFrame:
        """
        Get statistics summary for debugging/logging.
        
        Returns:
            DataFrame with standardization statistics
        """
        info = []
        for col in self.means.keys():
            info.append({
                'objective': col,
                'mean': self.means.get(col),
                'std': self.stds.get(col),
                'min': self.mins.get(col),
                'max': self.maxs.get(col)
            })
        return pd.DataFrame(info)


# ==============================================================================
# DATA VALIDATION UTILITIES
# ==============================================================================

def validate_experiments_for_bo(
    experiments: pd.DataFrame,
    domain: Domain,
    min_experiments: int = 2
) -> Tuple[bool, List[str]]:
    """
    Validate experiment data before running Bayesian Optimization.
    
    Best Practice: Validate data quality before fitting GP
    - Check for sufficient data points
    - Check for constant columns (no variation = no learning)
    - Check for missing values in objectives
    - Check categorical values match domain
    
    Args:
        experiments: DataFrame with experiment data
        domain: BoFire Domain object
        min_experiments: Minimum required experiments (default: 2 for GP)
    
    Returns:
        Tuple of (is_valid, list_of_warnings)
    """
    warnings = []
    is_valid = True
    
    # Check minimum experiments
    if len(experiments) < min_experiments:
        warnings.append(f"⚠️ Only {len(experiments)} experiments. Recommend at least {min_experiments} for reliable BO.")
        # Not a hard failure, but a warning
    
    # Check for missing objective values
    obj_names = [f.key for f in domain.outputs.features]
    for obj in obj_names:
        if obj in experiments.columns:
            n_missing = experiments[obj].isna().sum()
            if n_missing > 0:
                warnings.append(f"⚠️ Objective '{obj}' has {n_missing} missing values")
                is_valid = False
    
    # Check for constant parameters (no variation)
    param_names = [f.key for f in domain.inputs.features]
    for param in param_names:
        if param in experiments.columns:
            n_unique = experiments[param].nunique()
            if n_unique == 1:
                warnings.append(f"⚠️ Parameter '{param}' has only 1 unique value - GP cannot learn its effect")
    
    # Check categorical values are in domain
    for feature in domain.inputs.features:
        if isinstance(feature, (CategoricalInput, CategoricalDescriptorInput)):
            if feature.key in experiments.columns:
                valid_cats = set(feature.categories)
                actual_cats = set(experiments[feature.key].dropna().unique())
                invalid = actual_cats - valid_cats
                if invalid:
                    warnings.append(f"⚠️ Parameter '{feature.key}' has invalid categories: {invalid}")
                    is_valid = False
    
    # Check for infinite values
    numeric_cols = experiments.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        n_inf = np.isinf(experiments[col]).sum()
        if n_inf > 0:
            warnings.append(f"⚠️ Column '{col}' has {n_inf} infinite values")
            is_valid = False
    
    return is_valid, warnings


def check_parameter_scales(domain: Domain) -> List[str]:
    """
    Check if parameter scales are appropriate for BO.
    
    Best Practice: Identify potential scale issues
    - Flag parameters with very large or very small ranges
    - Flag parameters with ranges spanning multiple orders of magnitude
    
    Args:
        domain: BoFire Domain object
    
    Returns:
        List of recommendations
    """
    recommendations = []
    
    ranges = []
    for feature in domain.inputs.features:
        if isinstance(feature, ContinuousInput):
            lb, ub = feature.bounds
            param_range = ub - lb
            ranges.append((feature.key, param_range, lb, ub))
    
    if not ranges:
        return recommendations
    
    # Check for vastly different scales
    all_ranges = [r[1] for r in ranges]
    max_range = max(all_ranges)
    min_range = min(all_ranges) if min(all_ranges) > 0 else 1e-10
    
    if max_range / min_range > 100:
        recommendations.append(
            f"📊 Large scale disparity detected (ratio: {max_range/min_range:.0f}x). "
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
    base_config: Optional[Dict] = None
) -> Domain:
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
        domain: BoFire Domain object
        experiments: DataFrame with all experiment data
    
    Returns:
        Tuple of (InputNormalizer, OutputStandardizer)
    """
    # Create and fit input normalizer
    input_normalizer = InputNormalizer()
    input_normalizer.fit(domain, experiments)
    
    # Get objective names and create output standardizer
    obj_names = [f.key for f in domain.outputs.features]
    obj_data = experiments[[col for col in obj_names if col in experiments.columns]]
    
    output_standardizer = OutputStandardizer(method='standardize')
    if len(obj_data.columns) > 0 and len(obj_data.dropna()) > 0:
        output_standardizer.fit(obj_data.dropna())
    
    return input_normalizer, output_standardizer


def prepare_experiments_for_bo(
    experiments: pd.DataFrame,
    domain: Domain,
    normalize_inputs: bool = True,
    standardize_outputs: bool = True
) -> Tuple[pd.DataFrame, Optional[InputNormalizer], Optional[OutputStandardizer]]:
    """
    Prepare experiment data for Bayesian Optimization with optional normalization.
    
    Best Practice: Always normalize inputs for chemistry BO
    
    Args:
        experiments: Raw experiment DataFrame
        domain: BoFire Domain object
        normalize_inputs: Whether to normalize inputs (recommended: True)
        standardize_outputs: Whether to standardize outputs (recommended: True)
    
    Returns:
        Tuple of (prepared_df, input_normalizer, output_standardizer)
    """
    # Validate first
    is_valid, warnings = validate_experiments_for_bo(experiments, domain)
    for w in warnings:
        print(w)
    
    if not is_valid:
        raise ValueError("Experiment data validation failed. See warnings above.")
    
    prepared = experiments.copy()
    input_normalizer = None
    output_standardizer = None
    
    # Get column names
    param_names = [f.key for f in domain.inputs.features]
    obj_names = [f.key for f in domain.outputs.features]
    
    if normalize_inputs:
        input_normalizer = InputNormalizer()
        input_normalizer.fit(domain)
        param_cols = [c for c in param_names if c in prepared.columns]
        if param_cols:
            prepared[param_cols] = input_normalizer.transform(prepared[param_cols])
            print("✅ Inputs normalized to [0, 1]")
    
    if standardize_outputs:
        obj_cols = [c for c in obj_names if c in prepared.columns]
        obj_data = prepared[obj_cols].dropna()
        if len(obj_data) > 0:
            output_standardizer = OutputStandardizer(method='standardize')
            output_standardizer.fit(obj_data)
            prepared[obj_cols] = output_standardizer.transform(prepared[obj_cols])
            print("✅ Outputs standardized (zero mean, unit variance)")
    
    return prepared, input_normalizer, output_standardizer
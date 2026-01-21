"""
BoFire utilities for Bayesian Optimization
Based on working code from user
Enhanced with advanced customization options and descriptor support
"""

import pandas as pd
import numpy as np

import bofire.strategies.api as strategies
from bofire.data_models.enum import SamplingMethodEnum
from bofire.data_models.acquisition_functions.api import (
    qLogNEI, qLogNEHVI, qEI, qNEI, qPI, qUCB, qSR
)
from bofire.data_models.api import Domain, Inputs, Outputs
from bofire.data_models.features.api import (
    ContinuousInput, 
    DiscreteInput, 
    CategoricalInput,
    CategoricalDescriptorInput,
    ContinuousOutput
)
from bofire.data_models.objectives.api import MinimizeObjective, MaximizeObjective
from bofire.data_models.strategies.api import RandomStrategy, SoboStrategy, MoboStrategy

import pydantic
import bofire
print(f"Pydantic: {pydantic.__version__}")
print(f"BoFire: {bofire.__version__}")

def get_descriptor_values(categories, descriptors, descriptor_type='solvent'):
    """
    Get descriptor values for given categories.
    
    Args:
        categories: List of category names (e.g., solvent names)
        descriptors: List of descriptor names
        descriptor_type: Type of descriptor ('solvent' or 'base')
    
    Returns:
        List of lists with descriptor values for each category
    """
    # Database of known descriptor values
    SOLVENT_DESCRIPTORS = {
        'Water': {
            'Polarity': 1.0,
            'Boiling point': 100.0,
            'Viscosity': 0.89,
            'Dielectric constant': 80.1,
            'Dipole moment': 1.85,
            'Hydrogen bond donor': 2.0,
            'Hydrogen bond acceptor': 2.0,
            'Surface tension': 72.8,
            'Refractive index': 1.333,
            'Density': 1.0
        },
        'Methanol': {
            'Polarity': 0.762,
            'Boiling point': 64.7,
            'Viscosity': 0.544,
            'Dielectric constant': 32.6,
            'Dipole moment': 1.70,
            'Hydrogen bond donor': 1.0,
            'Hydrogen bond acceptor': 2.0,
            'Surface tension': 22.6,
            'Refractive index': 1.329,
            'Density': 0.792
        },
        'Ethanol': {
            'Polarity': 0.654,
            'Boiling point': 78.4,
            'Viscosity': 1.074,
            'Dielectric constant': 24.3,
            'Dipole moment': 1.69,
            'Hydrogen bond donor': 1.0,
            'Hydrogen bond acceptor': 2.0,
            'Surface tension': 22.1,
            'Refractive index': 1.361,
            'Density': 0.789
        },
        'Acetone': {
            'Polarity': 0.355,
            'Boiling point': 56.0,
            'Viscosity': 0.306,
            'Dielectric constant': 20.7,
            'Dipole moment': 2.88,
            'Hydrogen bond donor': 0.0,
            'Hydrogen bond acceptor': 1.0,
            'Surface tension': 23.7,
            'Refractive index': 1.359,
            'Density': 0.784
        },
        'DMSO': {
            'Polarity': 0.444,
            'Boiling point': 189.0,
            'Viscosity': 1.996,
            'Dielectric constant': 46.7,
            'Dipole moment': 3.96,
            'Hydrogen bond donor': 0.0,
            'Hydrogen bond acceptor': 2.0,
            'Surface tension': 43.0,
            'Refractive index': 1.479,
            'Density': 1.092
        },
        'DMF': {
            'Polarity': 0.386,
            'Boiling point': 153.0,
            'Viscosity': 0.794,
            'Dielectric constant': 36.7,
            'Dipole moment': 3.82,
            'Hydrogen bond donor': 0.0,
            'Hydrogen bond acceptor': 1.0,
            'Surface tension': 37.1,
            'Refractive index': 1.430,
            'Density': 0.944
        },
        'Acetonitrile': {
            'Polarity': 0.460,
            'Boiling point': 81.6,
            'Viscosity': 0.369,
            'Dielectric constant': 37.5,
            'Dipole moment': 3.92,
            'Hydrogen bond donor': 0.0,
            'Hydrogen bond acceptor': 1.0,
            'Surface tension': 29.3,
            'Refractive index': 1.344,
            'Density': 0.786
        },
        'THF': {
            'Polarity': 0.207,
            'Boiling point': 66.0,
            'Viscosity': 0.456,
            'Dielectric constant': 7.6,
            'Dipole moment': 1.75,
            'Hydrogen bond donor': 0.0,
            'Hydrogen bond acceptor': 1.0,
            'Surface tension': 26.4,
            'Refractive index': 1.407,
            'Density': 0.889
        },
        'Dichloromethane': {
            'Polarity': 0.309,
            'Boiling point': 39.6,
            'Viscosity': 0.413,
            'Dielectric constant': 8.9,
            'Dipole moment': 1.60,
            'Hydrogen bond donor': 0.0,
            'Hydrogen bond acceptor': 0.0,
            'Surface tension': 26.5,
            'Refractive index': 1.424,
            'Density': 1.325
        },
        'Chloroform': {
            'Polarity': 0.259,
            'Boiling point': 61.2,
            'Viscosity': 0.537,
            'Dielectric constant': 4.8,
            'Dipole moment': 1.04,
            'Hydrogen bond donor': 0.0,
            'Hydrogen bond acceptor': 0.0,
            'Surface tension': 27.2,
            'Refractive index': 1.446,
            'Density': 1.492
        },
        'Toluene': {
            'Polarity': 0.099,
            'Boiling point': 110.6,
            'Viscosity': 0.560,
            'Dielectric constant': 2.4,
            'Dipole moment': 0.36,
            'Hydrogen bond donor': 0.0,
            'Hydrogen bond acceptor': 0.0,
            'Surface tension': 28.5,
            'Refractive index': 1.497,
            'Density': 0.867
        },
        'Hexane': {
            'Polarity': 0.009,
            'Boiling point': 68.7,
            'Viscosity': 0.300,
            'Dielectric constant': 1.9,
            'Dipole moment': 0.00,
            'Hydrogen bond donor': 0.0,
            'Hydrogen bond acceptor': 0.0,
            'Surface tension': 18.4,
            'Refractive index': 1.375,
            'Density': 0.655
        },
        'Diethyl ether': {
            'Polarity': 0.117,
            'Boiling point': 34.6,
            'Viscosity': 0.224,
            'Dielectric constant': 4.3,
            'Dipole moment': 1.15,
            'Hydrogen bond donor': 0.0,
            'Hydrogen bond acceptor': 2.0,
            'Surface tension': 17.0,
            'Refractive index': 1.353,
            'Density': 0.714
        },
        'Ethyl acetate': {
            'Polarity': 0.228,
            'Boiling point': 77.1,
            'Viscosity': 0.423,
            'Dielectric constant': 6.0,
            'Dipole moment': 1.78,
            'Hydrogen bond donor': 0.0,
            'Hydrogen bond acceptor': 2.0,
            'Surface tension': 23.9,
            'Refractive index': 1.372,
            'Density': 0.902
        }
    }
    
    BASE_DESCRIPTORS = {
        'Triethylamine': {
            'pKa': 10.75,
            'Basicity': 0.96,
            'Nucleophilicity': 0.85,
            'Steric hindrance': 0.75,
            'Solubility': 0.60,
            'Boiling point': 89.5,
            'Molecular weight': 101.19,
            'Dipole moment': 0.66
        },
        'Pyridine': {
            'pKa': 5.25,
            'Basicity': 0.65,
            'Nucleophilicity': 0.55,
            'Steric hindrance': 0.20,
            'Solubility': 0.90,
            'Boiling point': 115.2,
            'Molecular weight': 79.10,
            'Dipole moment': 2.19
        },
        'DIPEA': {
            'pKa': 10.98,
            'Basicity': 0.98,
            'Nucleophilicity': 0.40,
            'Steric hindrance': 0.95,
            'Solubility': 0.40,
            'Boiling point': 127.0,
            'Molecular weight': 129.24,
            'Dipole moment': 0.70
        },
        'DBU': {
            'pKa': 12.0,
            'Basicity': 1.00,
            'Nucleophilicity': 0.75,
            'Steric hindrance': 0.60,
            'Solubility': 0.80,
            'Boiling point': 80.0,
            'Molecular weight': 152.24,
            'Dipole moment': 3.80
        },
        'Sodium hydroxide': {
            'pKa': 14.0,
            'Basicity': 1.00,
            'Nucleophilicity': 0.95,
            'Steric hindrance': 0.05,
            'Solubility': 1.00,
            'Boiling point': 1388.0,
            'Molecular weight': 40.00,
            'Dipole moment': 0.00
        },
        'Potassium carbonate': {
            'pKa': 10.33,
            'Basicity': 0.90,
            'Nucleophilicity': 0.70,
            'Steric hindrance': 0.10,
            'Solubility': 0.95,
            'Boiling point': 1200.0,
            'Molecular weight': 138.21,
            'Dipole moment': 0.00
        },
        'Cesium carbonate': {
            'pKa': 10.33,
            'Basicity': 0.95,
            'Nucleophilicity': 0.80,
            'Steric hindrance': 0.15,
            'Solubility': 0.90,
            'Boiling point': 1300.0,
            'Molecular weight': 325.82,
            'Dipole moment': 0.00
        },
        'Sodium bicarbonate': {
            'pKa': 6.35,
            'Basicity': 0.50,
            'Nucleophilicity': 0.40,
            'Steric hindrance': 0.10,
            'Solubility': 0.95,
            'Boiling point': 851.0,
            'Molecular weight': 84.01,
            'Dipole moment': 0.00
        },
        'DMAP': {
            'pKa': 9.70,
            'Basicity': 0.88,
            'Nucleophilicity': 0.90,
            'Steric hindrance': 0.30,
            'Solubility': 0.85,
            'Boiling point': 162.0,
            'Molecular weight': 122.17,
            'Dipole moment': 4.10
        },
        'Imidazole': {
            'pKa': 7.00,
            'Basicity': 0.70,
            'Nucleophilicity': 0.75,
            'Steric hindrance': 0.25,
            'Solubility': 0.95,
            'Boiling point': 256.0,
            'Molecular weight': 68.08,
            'Dipole moment': 3.61
        },
        'Potassium tert-butoxide': {
            'pKa': 16.5,
            'Basicity': 1.00,
            'Nucleophilicity': 0.85,
            'Steric hindrance': 0.85,
            'Solubility': 0.50,
            'Boiling point': 250.0,
            'Molecular weight': 112.21,
            'Dipole moment': 0.00
        },
        'Lithium diisopropylamide': {
            'pKa': 35.7,
            'Basicity': 1.00,
            'Nucleophilicity': 0.60,
            'Steric hindrance': 0.90,
            'Solubility': 0.30,
            'Boiling point': 200.0,
            'Molecular weight': 107.11,
            'Dipole moment': 0.00
        }
    }
    
    # Select appropriate database
    descriptor_db = SOLVENT_DESCRIPTORS if descriptor_type == 'solvent' else BASE_DESCRIPTORS
    
    # Build values matrix
    values_matrix = []
    for category in categories:
        category_values = []
        category_data = descriptor_db.get(category, {})
        
        for descriptor in descriptors:
            # Get value or use default
            value = category_data.get(descriptor, 0.5)  # Default to mid-range
            category_values.append(float(value))
        
        values_matrix.append(category_values)
    
    return values_matrix


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
                categories = solvent_config.get('solvents', [])
                descriptors = solvent_config.get('descriptors', [])
                
                if descriptors and categories:
                    print(f"✅ Creating CategoricalDescriptorInput for Solvent")
                    print(f"   Categories: {categories}")
                    print(f"   Descriptors: {descriptors}")
                    
                    descriptor_values = get_descriptor_values(categories, descriptors, 'solvent')
                    print(f"   Values matrix: {descriptor_values}")
                    
                    
                    input_features.append(
                        CategoricalDescriptorInput(
                            key=name,
                            categories=categories,
                            allowed=[True] * len(categories),
                            descriptors=descriptors,
                            values=descriptor_values
                        )
                    )
                    continue
            
            elif base_config and base_config.get('param_id') == param.get('id'):
                # This is a Base parameter with descriptors
                categories = base_config.get('bases', [])
                descriptors = base_config.get('descriptors', [])
                
                if descriptors and categories:
                    print(f"✅ Creating CategoricalDescriptorInput for Base")
                    print(f"   Categories: {categories}")
                    print(f"   Descriptors: {descriptors}")
                    
                    # Create descriptor values matrix
                    descriptor_values = get_descriptor_values(categories, descriptors, 'base')
                    print(f"   Values matrix: {descriptor_values}")
                    
                    # Create CategoricalDescriptorInput directly (not using from_df)
                    input_features.append(
                        CategoricalDescriptorInput.model_construct(
                            key=name.strip(),
                            categories=categories,
                            allowed=[True] * len(categories),  # ← IMPORTANT: ajouter ce champ
                            descriptors=descriptors,
                            values=descriptor_values
                        )
                    )
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
    # ===== END DEBUGGING =====
    
    # Provide past experiments
    strat.tell(experiments=experiments)
    
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
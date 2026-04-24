"""
Facade module that re-exports the public BoFire helpers from the
specialized submodules:

- ``descriptor_data``      : solvent / base descriptor databases
- ``bofire_domain``        : domain construction with descriptor support
- ``bofire_optimization``  : sampling and Bayesian optimization strategies
"""

from utils.descriptor_data import (
    BASE_DESCRIPTORS,
    SOLVENT_DESCRIPTORS,
    get_descriptor_values,
)
from utils.bofire_domain import create_bofire_domain_from_store
from utils.bofire_optimization import (
    bayesian_optimization,
    create_acquisition_function_from_name,
    get_available_acquisition_functions,
    get_optimization_type,
    sampling,
)

__all__ = [
    # Descriptor data
    "SOLVENT_DESCRIPTORS",
    "BASE_DESCRIPTORS",
    "get_descriptor_values",
    # Domain creation
    "create_bofire_domain_from_store",
    # Optimization
    "sampling",
    "get_available_acquisition_functions",
    "create_acquisition_function_from_name",
    "bayesian_optimization",
    "get_optimization_type",
]

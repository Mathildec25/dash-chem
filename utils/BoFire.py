"""
BoFire utilities for Bayesian Optimization
Main module that re-exports from specialized submodules

This module maintains backward compatibility while organizing code into:
- descriptor_data: Solvent and base descriptor databases
- bofire_domain: Domain creation with descriptor support (uses threading to avoid Flask context issues)
- bofire_optimization: Bayesian optimization strategies and acquisition functions
"""

import sys
print("=" * 60)
print("DIAGNOSTIC IMPORTS - BoFire.py")
print("=" * 60)
print(f"Modules déjà importés: {len(sys.modules)}")
print(f"Flask importé: {'flask' in sys.modules}")
print(f"Dash importé: {'dash' in sys.modules}")

import pydantic
import bofire
print(f"Pydantic: {pydantic.__version__}")
print(f"BoFire: {bofire.__version__}")

# Re-export from submodules for backward compatibility
from utils.descriptor_data import (
    SOLVENT_DESCRIPTORS,
    BASE_DESCRIPTORS,
    get_descriptor_values
)

from utils.bofire_domain import (
    create_bofire_domain_from_store
)

from utils.bofire_optimization import (
    sampling,
    get_available_acquisition_functions,
    create_acquisition_function_from_name,
    bayesian_optimization,
    get_optimization_type
)

# Make everything available at module level
__all__ = [
    # Descriptor data
    'SOLVENT_DESCRIPTORS',
    'BASE_DESCRIPTORS',
    'get_descriptor_values',
    
    # Domain creation
    'create_bofire_domain_from_store',
    
    # Optimization
    'sampling',
    'get_available_acquisition_functions',
    'create_acquisition_function_from_name',
    'bayesian_optimization',
    'get_optimization_type',
]

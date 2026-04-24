"""
Solvent and base descriptor lookups used during BoFire domain creation.

Values come from the auto-generated ``bofire_solvent_descriptors`` and
``bofire_base_descriptors`` modules. When those modules cannot be imported,
empty dictionaries are used so the rest of the app can still boot (domain
creation will then raise a clear ``ValueError``).
"""

from typing import List

import numpy as np

try:
    from bofire_solvent_descriptors import SOLVENT_DESCRIPTORS
    from bofire_base_descriptors import BASE_DESCRIPTORS
    print("Loaded descriptor files for BoFire domain creation")
except ImportError as e:
    print(f"WARNING: Could not import descriptor files: {e}. Using empty fallback.")
    SOLVENT_DESCRIPTORS = {}
    BASE_DESCRIPTORS = {}


_NUCLEOPHILICITY_MAP = {"High": 3.0, "Moderate": 2.0, "Low": 1.0, "None": 0.0}


def get_descriptor_values(
    categories: List[str],
    descriptors: List[str],
    compound_type: str,
) -> List[List[float]]:
    """
    Return a ``(len(categories), len(descriptors))`` matrix of numeric values.

    Args:
        categories: Compound names, e.g. ``['Ethanol', 'Acetone']``.
        descriptors: Descriptor keys, e.g. ``['bp', 'polarity_index']``.
        compound_type: Either ``'solvent'`` or ``'base'``.

    Raises:
        ValueError: If the descriptor database is empty or a compound/descriptor
            is missing.
    """
    if compound_type == "solvent":
        descriptor_dict = SOLVENT_DESCRIPTORS
    elif compound_type == "base":
        descriptor_dict = BASE_DESCRIPTORS
    else:
        raise ValueError(
            f"Unknown compound_type: '{compound_type}'. Must be 'solvent' or 'base'."
        )

    if not descriptor_dict:
        raise ValueError(
            f"No descriptor data available for {compound_type}s. "
            f"Make sure bofire_{compound_type}_descriptors.py exists and is importable."
        )

    values = []
    for category in categories:
        if category not in descriptor_dict:
            available = list(descriptor_dict.keys())[:5]
            raise ValueError(
                f"Compound '{category}' not found in {compound_type} descriptors. "
                f"Available (first 5): {available}..."
            )

        compound_data = descriptor_dict[category]
        row = []
        for descriptor in descriptors:
            if descriptor not in compound_data:
                raise ValueError(
                    f"Descriptor '{descriptor}' not found for {category}. "
                    f"Available: {list(compound_data.keys())}"
                )

            value = compound_data[descriptor]
            if isinstance(value, (int, float)):
                row.append(float(value))
            elif descriptor == "nucleophilicity":
                row.append(_NUCLEOPHILICITY_MAP.get(value, 0.0))
            else:
                print(f"   Non-numeric value for {category}.{descriptor}: {value}, using 0.0")
                row.append(0.0)

        values.append(row)

    values_array = np.array(values)
    for i, descriptor in enumerate(descriptors):
        col = values_array[:, i]
        if len(set(col)) == 1:
            print(
                f"   WARNING: no variation in descriptor '{descriptor}' "
                f"(all values = {col[0]}); BoFire validation may fail."
            )

    return values


def get_available_solvents() -> List[str]:
    """Return a sorted list of solvent names that have descriptor data."""
    return sorted(SOLVENT_DESCRIPTORS.keys())


def get_available_bases() -> List[str]:
    """Return a sorted list of base names that have descriptor data."""
    return sorted(BASE_DESCRIPTORS.keys())


def get_available_descriptors(compound_type: str) -> List[str]:
    """Return a sorted list of descriptor names available for ``compound_type``."""
    if compound_type == "solvent":
        source = SOLVENT_DESCRIPTORS
    elif compound_type == "base":
        source = BASE_DESCRIPTORS
    else:
        raise ValueError(f"Unknown compound_type: '{compound_type}'")

    if not source:
        return []
    first = next(iter(source.values()))
    return sorted(k for k in first.keys() if k != "CAS")

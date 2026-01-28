"""
Descriptor data utilities for BoFire domain creation
Fetches real descriptor values from auto-generated descriptor files
"""

from typing import List
import numpy as np

# ============================================================================
# IMPORT AUTO-GENERATED DESCRIPTORS
# ============================================================================

try:
    from bofire_solvent_descriptors import BOFIRE_SOLVENT_DESCRIPTORS
    from bofire_base_descriptors import BOFIRE_BASE_DESCRIPTORS
    print("✅ Loaded descriptor files for BoFire domain creation")
except ImportError as e:
    print(f"⚠️ WARNING: Could not import descriptor files: {e}")
    print("   Using empty fallback. Run: python advanced_descriptor_calculator.py")
    BOFIRE_SOLVENT_DESCRIPTORS = {}
    BOFIRE_BASE_DESCRIPTORS = {}


def get_descriptor_values(categories: List[str], descriptors: List[str], compound_type: str) -> List[List[float]]:
    """
    Get descriptor values for a list of compounds.
    
    Args:
        categories: List of compound names (e.g., ['Ethanol', 'Acetone', ...])
        descriptors: List of descriptor names (e.g., ['bp', 'polarity_index', ...])
        compound_type: 'solvent' or 'base'
    
    Returns:
        List of lists with descriptor values, shape (n_categories, n_descriptors)
        Example: [[78.4, 5.2, 1, 1], [56.1, 5.1, 1, 0], ...]
    
    Raises:
        ValueError: If descriptor files not loaded or data missing
    """
    # Select appropriate descriptor dictionary
    if compound_type == 'solvent':
        descriptor_dict = BOFIRE_SOLVENT_DESCRIPTORS
    elif compound_type == 'base':
        descriptor_dict = BOFIRE_BASE_DESCRIPTORS
    else:
        raise ValueError(f"Unknown compound_type: '{compound_type}'. Must be 'solvent' or 'base'")
    
    # Check if we have descriptor data
    if not descriptor_dict:
        raise ValueError(
            f"No descriptor data available for {compound_type}s. "
            f"Make sure bofire_{compound_type}_descriptors.py exists and is importable."
        )
    
    # Build values matrix
    values = []
    
    for category in categories:
        if category not in descriptor_dict:
            raise ValueError(
                f"❌ Compound '{category}' not found in {compound_type} descriptors!\n"
                f"   Available {compound_type}s: {list(descriptor_dict.keys())[:5]}..."
            )
        
        compound_data = descriptor_dict[category]
        row = []
        
        for descriptor in descriptors:
            if descriptor not in compound_data:
                raise ValueError(
                    f"❌ Descriptor '{descriptor}' not found for {category}!\n"
                    f"   Available descriptors: {list(compound_data.keys())}"
                )
            
            value = compound_data[descriptor]
            
            # Ensure value is numeric
            if isinstance(value, (int, float)):
                row.append(float(value))
            else:
                # Handle non-numeric descriptors (like nucleophilicity = 'High')
                # Convert to numeric scale
                if descriptor == 'nucleophilicity':
                    nucleophilicity_map = {'High': 3.0, 'Moderate': 2.0, 'Low': 1.0, 'None': 0.0}
                    row.append(nucleophilicity_map.get(value, 0.0))
                else:
                    print(f"   ⚠️ Non-numeric value for {category}.{descriptor}: {value}, using 0.0")
                    row.append(0.0)
        
        values.append(row)
    
    # Verify we have variation in each descriptor
    values_array = np.array(values)
    for i, descriptor in enumerate(descriptors):
        descriptor_values = values_array[:, i]
        if len(set(descriptor_values)) == 1:
            print(f"   ⚠️ WARNING: No variation in descriptor '{descriptor}' (all values = {descriptor_values[0]})")
            print(f"      This may cause BoFire validation errors")
    
    print(f"   ✅ Extracted {len(values)} x {len(descriptors)} descriptor matrix")
    print(f"      Sample values for {categories[0]}: {values[0]}")
    
    return values


def get_available_solvents() -> List[str]:
    """Get list of available solvent names."""
    return sorted(list(BOFIRE_SOLVENT_DESCRIPTORS.keys()))


def get_available_bases() -> List[str]:
    """Get list of available base names."""
    return sorted(list(BOFIRE_BASE_DESCRIPTORS.keys()))


def get_available_descriptors(compound_type: str) -> List[str]:
    """
    Get list of available descriptor names for a compound type.
    
    Args:
        compound_type: 'solvent' or 'base'
    
    Returns:
        List of descriptor names
    """
    if compound_type == 'solvent':
        if not BOFIRE_SOLVENT_DESCRIPTORS:
            return []
        first_solvent = next(iter(BOFIRE_SOLVENT_DESCRIPTORS.values()))
        return sorted([k for k in first_solvent.keys() if k != 'CAS'])
    
    elif compound_type == 'base':
        if not BOFIRE_BASE_DESCRIPTORS:
            return []
        first_base = next(iter(BOFIRE_BASE_DESCRIPTORS.values()))
        return sorted([k for k in first_base.keys() if k != 'CAS'])
    
    else:
        raise ValueError(f"Unknown compound_type: '{compound_type}'")


# ============================================================================
# TESTING / DEBUGGING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("DESCRIPTOR DATA UTILITIES - TEST")
    print("=" * 70)
    
    # Test solvents
    print("\n📊 Testing Solvents:")
    try:
        solvents = ['Ethanol', 'Acetone', 'DMSO']
        descriptors = ['bp', 'polarity_index', 'HBA', 'HBD']
        values = get_descriptor_values(solvents, descriptors, 'solvent')
        
        print(f"   Solvents: {solvents}")
        print(f"   Descriptors: {descriptors}")
        print(f"   Values matrix:")
        for i, solvent in enumerate(solvents):
            print(f"      {solvent}: {values[i]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test bases
    print("\n📊 Testing Bases:")
    try:
        bases = ['Triethylamine', 'DBU', 'Pyridine']
        descriptors = ['pKa', 'basicity', 'MW']
        values = get_descriptor_values(bases, descriptors, 'base')
        
        print(f"   Bases: {bases}")
        print(f"   Descriptors: {descriptors}")
        print(f"   Values matrix:")
        for i, base in enumerate(bases):
            print(f"      {base}: {values[i]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test available compounds
    print("\n📋 Available Compounds:")
    print(f"   Solvents: {len(get_available_solvents())}")
    print(f"   Bases: {len(get_available_bases())}")
    
    print("\n" + "=" * 70)
    print("✅ Test completed")
    print("=" * 70)
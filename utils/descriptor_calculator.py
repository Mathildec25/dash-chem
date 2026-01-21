"""
Molecular descriptor calculator for solvents and bases
Calculates common descriptors from SMILES strings
"""

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Crippen, Lipinski
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    print("⚠️ RDKit not available. Install with: pip install rdkit")


# Predefined descriptors for common solvents (if RDKit not available)
PREDEFINED_SOLVENT_DESCRIPTORS = {
    "Water": {"Polarity": 10.2, "Boiling point": 100.0, "Viscosity": 0.89, "Dielectric constant": 80.1},
    "Methanol": {"Polarity": 6.6, "Boiling point": 64.7, "Viscosity": 0.59, "Dielectric constant": 32.7},
    "Ethanol": {"Polarity": 5.2, "Boiling point": 78.4, "Viscosity": 1.07, "Dielectric constant": 24.5},
    "Acetone": {"Polarity": 5.1, "Boiling point": 56.1, "Viscosity": 0.32, "Dielectric constant": 20.7},
    "DMSO": {"Polarity": 7.2, "Boiling point": 189.0, "Viscosity": 1.99, "Dielectric constant": 46.7},
    "DMF": {"Polarity": 6.4, "Boiling point": 153.0, "Viscosity": 0.92, "Dielectric constant": 36.7},
    "Acetonitrile": {"Polarity": 6.2, "Boiling point": 81.6, "Viscosity": 0.37, "Dielectric constant": 37.5},
    "THF": {"Polarity": 4.0, "Boiling point": 66.0, "Viscosity": 0.48, "Dielectric constant": 7.6},
    "Dichloromethane": {"Polarity": 3.1, "Boiling point": 39.6, "Viscosity": 0.43, "Dielectric constant": 8.9},
    "Chloroform": {"Polarity": 4.1, "Boiling point": 61.2, "Viscosity": 0.57, "Dielectric constant": 4.8},
    "Toluene": {"Polarity": 2.4, "Boiling point": 110.6, "Viscosity": 0.59, "Dielectric constant": 2.4},
    "Hexane": {"Polarity": 0.1, "Boiling point": 68.7, "Viscosity": 0.31, "Dielectric constant": 1.9},
    "Diethyl ether": {"Polarity": 2.8, "Boiling point": 34.6, "Viscosity": 0.22, "Dielectric constant": 4.3},
    "Ethyl acetate": {"Polarity": 4.4, "Boiling point": 77.1, "Viscosity": 0.45, "Dielectric constant": 6.0},
}

# Predefined descriptors for common bases
PREDEFINED_BASE_DESCRIPTORS = {
    "Triethylamine": {"pKa": 10.75, "Basicity": 10.75, "Molecular weight": 101.19},
    "Pyridine": {"pKa": 5.25, "Basicity": 5.25, "Molecular weight": 79.10},
    "DIPEA": {"pKa": 11.0, "Basicity": 11.0, "Molecular weight": 129.24},
    "DBU": {"pKa": 12.0, "Basicity": 12.0, "Molecular weight": 152.24},
    "Sodium hydroxide": {"pKa": 14.0, "Basicity": 14.0, "Molecular weight": 40.00},
    "Potassium carbonate": {"pKa": 10.3, "Basicity": 10.3, "Molecular weight": 138.21},
    "Cesium carbonate": {"pKa": 10.3, "Basicity": 10.3, "Molecular weight": 325.82},
    "Sodium bicarbonate": {"pKa": 6.3, "Basicity": 6.3, "Molecular weight": 84.01},
}


def calculate_descriptors_from_smiles(smiles, descriptor_names):
    """
    Calculate molecular descriptors from SMILES string using RDKit.
    
    Args:
        smiles: SMILES string
        descriptor_names: List of descriptor names to calculate
    
    Returns:
        dict: Dictionary of descriptor_name -> value
    """
    if not RDKIT_AVAILABLE:
        return {name: 0.0 for name in descriptor_names}
    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        print(f"⚠️ Invalid SMILES: {smiles}")
        return {name: 0.0 for name in descriptor_names}
    
    # Mapping of descriptor names to RDKit functions
    descriptor_functions = {
        "Polarity": lambda m: Descriptors.TPSA(m) / 10.0,  # Normalized
        "Boiling point": lambda m: Descriptors.MolWt(m) * 0.5,  # Approximation
        "Viscosity": lambda m: Descriptors.MolLogP(m),
        "Dielectric constant": lambda m: Descriptors.NumHDonors(m) + Descriptors.NumHAcceptors(m),
        "Dipole moment": lambda m: Descriptors.TPSA(m) / 20.0,
        "Hydrogen bond donor": lambda m: Descriptors.NumHDonors(m),
        "Hydrogen bond acceptor": lambda m: Descriptors.NumHAcceptors(m),
        "Surface tension": lambda m: Descriptors.TPSA(m),
        "Refractive index": lambda m: Crippen.MolMR(m) / 10.0,
        "Density": lambda m: Descriptors.MolWt(m) / 100.0,
        "pKa": lambda m: 7.0,  # Placeholder - requires pKa prediction model
        "Basicity": lambda m: 7.0,  # Placeholder
        "Nucleophilicity": lambda m: Descriptors.NumHAcceptors(m),
        "Steric hindrance": lambda m: Descriptors.NumRotatableBonds(m),
        "Solubility": lambda m: Crippen.MolLogP(m),
        "Molecular weight": lambda m: Descriptors.MolWt(m),
    }
    
    result = {}
    for name in descriptor_names:
        if name in descriptor_functions:
            try:
                result[name] = float(descriptor_functions[name](mol))
            except:
                result[name] = 0.0
        else:
            # Unknown descriptor - return 0
            result[name] = 0.0
    
    return result


def get_descriptor_values(compound_name, compound_smiles, descriptor_names, predefined_dict):
    """
    Get descriptor values for a compound (solvent or base).
    
    Priority:
    1. Use predefined values if available
    2. Calculate from SMILES if RDKit available
    3. Return zeros as fallback
    
    Args:
        compound_name: Name of the compound
        compound_smiles: SMILES string (or None)
        descriptor_names: List of descriptor names needed
        predefined_dict: Dictionary of predefined values
    
    Returns:
        dict: descriptor_name -> value
    """
    # Try predefined values first
    if compound_name in predefined_dict:
        predefined = predefined_dict[compound_name]
        result = {}
        for name in descriptor_names:
            result[name] = predefined.get(name, 0.0)
        return result
    
    # Try calculating from SMILES
    if compound_smiles and RDKIT_AVAILABLE:
        return calculate_descriptors_from_smiles(compound_smiles, descriptor_names)
    
    # Fallback to zeros
    print(f"⚠️ No descriptor data for '{compound_name}', using zeros")
    return {name: 0.0 for name in descriptor_names}


def get_solvent_descriptors(solvent_name, solvent_smiles, descriptor_names):
    """Get descriptor values for a solvent"""
    return get_descriptor_values(
        solvent_name, 
        solvent_smiles, 
        descriptor_names, 
        PREDEFINED_SOLVENT_DESCRIPTORS
    )


def get_base_descriptors(base_name, base_smiles, descriptor_names):
    """Get descriptor values for a base"""
    return get_descriptor_values(
        base_name, 
        base_smiles, 
        descriptor_names, 
        PREDEFINED_BASE_DESCRIPTORS
    )
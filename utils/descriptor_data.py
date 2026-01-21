"""
Descriptor data for solvents and bases
Physical and chemical properties database
"""

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

"""
Descriptor dictionary for BoFire CategoricalDescriptorInput
10 solvents selected for flavone synthesis optimization

Descriptors for Bayesian Optimization (6):
  - dielectric (ε): Dielectric constant at 25°C
  - dipole_moment (μ): Dipole moment in Debye
  - HBA: Hydrogen bond acceptor count (RDKit)
  - HBD: Hydrogen bond donor count (RDKit)
  - AN: Gutmann Acceptor Number
  - DN: Gutmann Donor Number (kcal/mol)

Additional properties (for constraints, not used as BO descriptors):
  - bp: Boiling point (°C)
  - mp: Melting point (°C)
  - CAS: CAS registry number

Sources:
  - ε: Reichardt & Welton, Solvents and Solvent Effects in Organic Chemistry, 4th ed.
  - μ: Burdick & Jackson / Stenutz / Chernyak (2006)
  - HBA/HBD: RDKit Lipinski descriptors
  - AN/DN: Gutmann scale
  - bp/mp: Literature values
"""

SOLVENT_DESCRIPTORS = {
    "n-Butanol": {
        "CAS": "71-36-3",
        "dielectric": 17.8,
        "dipole_moment": 1.75,
        "HBA": 1,
        "HBD": 1,
        "AN": 36.8,
        "DN": 19.5,
        "bp": 118.0,
        "mp": -89.5,
    },
    "Ethanol": {
        "CAS": "64-17-5",
        "dielectric": 24.6,
        "dipole_moment": 1.66,
        "HBA": 1,
        "HBD": 1,
        "AN": 37.9,
        "DN": 19.2,
        "bp": 78.4,
        "mp": -114.1,
    },
    "Acetone": {
        "CAS": "67-64-1",
        "dielectric": 20.7,
        "dipole_moment": 2.69,
        "HBA": 1,
        "HBD": 0,
        "AN": 12.5,
        "DN": 17.0,
        "bp": 56.1,
        "mp": -95.0,
    },
    "Acetonitrile": {
        "CAS": "75-05-8",
        "dielectric": 36.6,
        "dipole_moment": 3.44,
        "HBA": 1,
        "HBD": 0,
        "AN": 18.9,
        "DN": 14.1,
        "bp": 81.6,
        "mp": -45.0,
    },
    "Ethyl acetate": {
        "CAS": "141-78-6",
        "dielectric": 6.0,
        "dipole_moment": 1.88,
        "HBA": 2,
        "HBD": 0,
        "AN": 9.3,
        "DN": 17.1,
        "bp": 77.1,
        "mp": -83.6,
    },
    "Ethylene glycol": {
        "CAS": "107-21-1",
        "dielectric": 37.7,
        "dipole_moment": 2.27,
        "HBA": 2,
        "HBD": 2,
        "AN": 44.1,
        "DN": 20.0,
        "bp": 197.0,
        "mp": -12.9,
    },
    "o-Xylene": {
        "CAS": "95-47-6",
        "dielectric": 2.3,
        "dipole_moment": 0.45,
        "HBA": 0,
        "HBD": 0,
        "AN": 0.7,
        "DN": 5.0,
        "bp": 144.0,
        "mp": -25.2,
    },
    "DMSO": {
        "CAS": "67-68-5",
        "dielectric": 46.7,
        "dipole_moment": 4.1,
        "HBA": 1,
        "HBD": 0,
        "AN": 19.3,
        "DN": 29.8,
        "bp": 189.0,
        "mp": 18.5,
    },
    "Propylene carbonate": {
        "CAS": "108-32-7",
        "dielectric": 64.9,
        "dipole_moment": 4.94,
        "HBA": 3,
        "HBD": 0,
        "AN": 18.3,
        "DN": 15.1,
        "bp": 242.0,
        "mp": -48.8,
    },
    "Glycerol carbonate": {
        "CAS": "931-40-8",
        "dielectric": 80.0,
        "dipole_moment": 5.4,
        "HBA": 4,
        "HBD": 1,
        "AN": 29.5,
        "DN": 16.4,
        "bp": 137.0,
        "mp": -69.0,
    },
}
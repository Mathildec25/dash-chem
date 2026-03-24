"""
Descriptor dictionary for BoFire CategoricalDescriptorInput

Descriptors:
  - pKa_DMSO: pKa of conjugate acid in DMSO (higher = stronger base)
  - MW: Molecular weight (g/mol)

Sources:
  - Tshepelevitsh et al., Eur. J. Org. Chem. 2019, 6735–6748
  - Evans pKa table (D.H. Ripin, D.A. Evans), Updated 4/16/2024
"""

BASE_DESCRIPTORS = {
    "Potassium carbonate": {
        "pKa_DMSO": 10.3,   # Estimated, HCO3-/CO32- equilibrium
        "MW": 138.21,
    },
    "Potassium hydroxide": {
        "pKa_DMSO": 31.2,   # Evans table: pKa(H2O) in DMSO
        "MW": 56.11,
    },
    "Potassium tert-butoxide": {
        "pKa_DMSO": 29.4,   # Evans table: pKa(t-BuOH) in DMSO
        "MW": 112.21,
    },
    "Triethylamine": {
        "pKa_DMSO": 9.0,    # Tshepelevitsh 2019, Table 1
        "MW": 101.19,
    },
    "DBU": {
        "pKa_DMSO": 13.9,   # Tshepelevitsh 2019, Table 1
        "MW": 152.24,
    },
    "DBN": {
        "pKa_DMSO": 13.4,   # Tshepelevitsh 2019, Table 1
        "MW": 124.18,
    },
    "TBD": {
        "pKa_DMSO": 15.3,   # Tshepelevitsh 2019, Table 1
        "MW": 139.20,
    },
    "MTBD": {
        "pKa_DMSO": 14.8,   # Tshepelevitsh 2019, Table 1
        "MW": 153.23,
    },
    "TMG": {
        "pKa_DMSO": 13.2,   # Tshepelevitsh 2019, Table 1
        "MW": 115.18,
    },
    "LDA": {
        "pKa_DMSO": 36.0,   # Evans table: pKa(i-Pr2NH) in THF ~36
        "MW": 107.12,
    },
}
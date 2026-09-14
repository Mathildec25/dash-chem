# -*- coding: utf-8 -*-
"""What a chemist is told about each reaction of the human study.

Facts only, each traceable to the source named next to it, and nothing that
would give the answer away: the optima reported by the original papers are
deliberately absent, since the front-carrying catalyst is precisely what the
campaign has to find.

Every structure below was checked before being shown:
- Suzuki substrates, reagents and named ligands: SMILES resolved on PubChem by
  name (RuPhos under its systematic name, PubChem's "RuPhos" being a pesticide
  of the same trade name) and compared canonically with RDKit, 12 September 2026.
  PPh3 and P(t-Bu)3 need no lookup. The Suzuki page shows one drawing with the
  four cases (assets/hitl/reizman_cases_scheme.png, supplied by the study
  owner) rather than a redrawn scheme and gallery.
- C-H arylation partners, product and precatalyst: InChI taken from the EDBO+
  repository (examples/publication/BMS_yield_cost/data/PCI_PMI_cost_full_update.csv)
  and matched against the SMILES written here; ligand, base and solvent SMILES
  copied from the *_dft.csv files of the same folder.
The drawings in assets/hitl/ are produced from these SMILES by
scripts/make_chemistry_figures.py (RDKit; see that file for the environment).
"""

# --- Suzuki-Miyaura, Reizman et al. ------------------------------------------------
# Reizman, Wang, Buchwald & Jensen, React. Chem. Eng. 2016, 1, 658-666,
# doi:10.1039/C6RE00153J (open access, PMC5123644). Base, solvent, reactor and
# the four cases are from the paper's Table 1 and Methods.

SUZUKI_LIGANDS = [
    # code in the grid, precatalyst-ligand pair, ligand name, family, SMILES (None when unnamed)
    ("L0", "P1-L1", "XPhos", "dialkylbiarylphosphine",
     "CC(C)c1cc(C(C)C)c(-c2ccccc2P(C2CCCCC2)C2CCCCC2)c(C(C)C)c1"),
    ("L1", "P1-L2", "SPhos", "dialkylbiarylphosphine",
     "COc1cccc(OC)c1-c1ccccc1P(C1CCCCC1)C1CCCCC1"),
    ("L2", "P1-L3", "RuPhos", "dialkylbiarylphosphine",
     "CC(C)Oc1cccc(OC(C)C)c1-c1ccccc1P(C1CCCCC1)C1CCCCC1"),
    ("L3", "P1-L4", "Xantphos", "bidentate phosphine",
     "CC1(C)c2cccc(P(c3ccccc3)c3ccccc3)c2Oc2c(P(c3ccccc3)c3ccccc3)cccc21"),
    ("L4", "P1-L5", "PCy3", "trialkylphosphine",
     "C1CCC(CC1)P(C1CCCCC1)C1CCCCC1"),
    ("L5", "P1-L6", "PPh3", "triarylphosphine",
     "c1ccc(P(c2ccccc2)c2ccccc2)cc1"),
    ("L6", "P1-L7", "P(t-Bu)3", "trialkylphosphine",
     "CC(C)(C)P(C(C)(C)C)C(C)(C)C"),
    # L6 and L7 are named in Scheme 1 of the article (not in its text): PPh3 and P(t-Bu)3.
]

SUZUKI_CASES = {
    "i": {
        "halide": ("3-bromoquinoline", "Brc1cnc2ccccc2c1"),
        "boron": ("3,5-dimethylisoxazole-4-boronic acid pinacol ester", "Cc1noc(C)c1B1OC(C)(C)C(C)(C)O1"),
        "product": ("3-(3,5-dimethylisoxazol-4-yl)quinoline", "Cc1noc(C)c1-c1cnc2ccccc2c1"),
    },
    "ii": {
        "halide": ("3-chloropyridine", "Clc1cccnc1"),
        "boron": ("3,5-dimethylisoxazole-4-boronic acid pinacol ester", "Cc1noc(C)c1B1OC(C)(C)C(C)(C)O1"),
        "product": ("3-(3,5-dimethylisoxazol-4-yl)pyridine", "Cc1noc(C)c1-c1cccnc1"),
    },
    "iii": {
        "halide": ("3-chloropyridine", "Clc1cccnc1"),
        "boron": ("benzofuran-2-boronic acid", "OB(O)c1cc2ccccc2o1"),
        "product": ("2-(pyridin-3-yl)benzofuran", "c1ccc2oc(-c3cccnc3)cc2c1"),
    },
    "iv": {
        "halide": ("2-chloropyridine", "Clc1ccccn1"),
        "boron": ("1-Boc-pyrrole-2-boronic acid", "CC(C)(C)OC(=O)n1cccc1B(O)O"),
        "product": ("tert-butyl 2-(pyridin-2-yl)pyrrole-1-carboxylate", "CC(C)(C)OC(=O)n1cccc1-c1ccccn1"),
    },
}

SUZUKI = {
    "reaction": "Suzuki–Miyaura cross-coupling",
    "summary": ("Pd-catalysed coupling of a heteroaryl halide with a boronate: oxidative addition, "
                "base-assisted transmetalation, reductive elimination. A chloride is harder to "
                "activate than a bromide, and a nitrogen heterocycle can bind palladium."),
    "conditions": [
        "Palladacycle precatalyst P1 (X = OMs) + one of seven ligands.",
        "Boronate 1.5 equiv., DBU 2.0 equiv., THF/water 5:1, droplet flow, one condition per run.",
    ],
    "variables": [
        ("Catalyst", "one of 7 precatalyst–ligand pairs"),
        ("Residence time", "60–600 s"),
        ("Temperature", "30–110 °C"),
        ("Pd loading", "0.5–2.5 mol%"),
    ],
    "objectives": [
        ("Yield", "%, maximise"),
        ("TON", "mol product / mol catalyst, maximise — favours low loading, yield favours high"),
    ],
    "data": "Values from an emulator of the Reizman campaigns (Olympus), on the complete grid published with Minerva.",
    # The scheme the study owner chose (12 September 2026): general reaction,
    # conditions, precatalyst scaffolds, the seven ligands and the substrates of
    # the four cases in one drawing. Its "optimized conditions" column was cut
    # off before it reached this folder: it named the winning catalyst of each
    # case, which is what the campaign has to find.
    "figure": ("reizman_cases_scheme.png",
               "General reaction, precatalysts, ligands and the substrates of cases I–IV of "
               "Reizman, Wang, Buchwald & Jensen, React. Chem. Eng. 2016, 1, 658."),
    "sources": [
        ("Reizman, Wang, Buchwald & Jensen, React. Chem. Eng. 2016, 1, 658",
         "https://doi.org/10.1039/C6RE00153J"),
        ("Sin et al., Nat. Commun. 2025 (Minerva benchmark grids)",
         "https://www.nature.com/articles/s41467-025-61803-0"),
    ],
}

# --- C-H arylation, Shields et al. / EDBO+ ----------------------------------------------
# Shields et al., Nature 2021, 590, 89-96 (reaction 3, Fig. 4): "the direct
# arylation of imidazoles ... related to a key step in the commercial synthesis
# of the JAK2 inhibitor BMS-911543". Partners, precatalyst, equivalents, scale
# and time from the EDBO+ data file; cost from the same file (total_cost_update).

ARYLATION_LIGANDS = [
    # name in the grid, SMILES (EDBO+ ligand_dft.csv)
    ("BrettPhos", "CC(C)C1=CC(C(C)C)=C(C(C(C)C)=C1)C2=C(P(C3CCCCC3)C4CCCCC4)C(OC)=CC=C2OC"),
    ("CgMe-PPh", "C[C@]1(O2)O[C@](C[C@]2(C)P3C4=CC=CC=C4)(C)O[C@]3(C)C1"),
    ("GorlosPhos HBF4", "CC(OC1=C(P(C2CCCCC2)C3CCCCC3)C(OC(C)C)=CC=C1)C"),
    ("JackiePhos", "FC(F)(F)C1=CC(P(C2=C(C3=C(C(C)C)C=C(C(C)C)C=C3C(C)C)C(OC)=CC=C2OC)C4=CC(C(F)(F)F)=CC(C(F)(F)F)=C4)=CC(C(F)(F)F)=C1"),
    ("PCy3 HBF4", "P(C1CCCCC1)(C2CCCCC2)C3CCCCC3"),
    ("P(fur)3", "P(C1=CC=CO1)(C2=CC=CO2)C3=CC=CO3"),
    ("PPh2Me", "CP(C1=CC=CC=C1)C2=CC=CC=C2"),
    ("PPh3", "P(C1=CC=CC=C1)(C2=CC=CC=C2)C3=CC=CC=C3"),
    ("PPhMe2", "CP(C)C1=CC=CC=C1"),
    ("PPhtBu2", "CC(C)(C)P(C1=CC=CC=C1)C(C)(C)C"),
    ("tBPh-CPhos", "CN(C)C1=CC=CC(N(C)C)=C1C2=CC=CC=C2P(C(C)(C)C)C3=CC=CC=C3"),
    ("X-Phos", "CC(C1=C(C2=CC=CC=C2P(C3CCCCC3)C4CCCCC4)C(C(C)C)=CC(C(C)C)=C1)C"),
]

ARYLATION = {
    "reaction": "Pd-catalysed direct C–H arylation of an imidazole",
    "nucleophile": ("1-methyl-1H-imidazole-4-carbonitrile", "Cn1cnc(C#N)c1"),
    "electrophile": ("1-bromo-2-fluorobenzene", "Fc1ccccc1Br"),
    "product": ("5-(2-fluorophenyl)-1-methyl-1H-imidazole-4-carbonitrile", "Cn1cnc(C#N)c1-c1ccccc1F"),
    "summary": ("Direct arylation of the imidazole C5–H by the aryl bromide; the carboxylate base "
                "takes part in the C–H cleavage (concerted metalation–deprotonation). A step of this "
                "kind is used in the commercial synthesis of the JAK2 inhibitor BMS-911543."),
    "conditions": [
        "[Pd(allyl)Cl]₂ 2.25 mol%, ligand 5 mol%; imidazole 2 equiv., bromide 1 equiv., base 3 equiv.",
        "24 h, 96-well plates in a glovebox, 15 µmol scale, single run per condition.",
    ],
    "variables": [
        ("Ligand", "12 phosphines"),
        ("Base", "KOAc, KOPiv, CsOAc, CsOPiv"),
        ("Solvent", "DMAc, BuOAc, BuCN, p-xylene"),
        ("Concentration", "0.057, 0.100, 0.153 M"),
        ("Temperature", "90, 105, 120 °C"),
    ],
    "objectives": [
        ("Yield", "%, maximise"),
        ("Reagent cost", "$ of ligand + base + solvent for one 15 µmol reaction, minimise"),
    ],
    "data": "All 1,728 conditions were run at Bristol Myers Squibb; every value is a real single measurement.",
    # Catalogue prices behind the cost objective, $/g, from the EDBO+ cost file
    # (X_price.mol / X_MW; e.g. BrettPhos $29.7 for 0.10 g). The solvent mass
    # follows the concentration, so a dilute reaction costs more solvent.
    "prices": [
        ("Ligand", [("tBPh-CPhos", 800), ("JackiePhos", 552), ("BrettPhos", 297), ("CgMe-PPh", 144),
                    ("PPhtBu2", 102), ("P(fur)3", 71), ("GorlosPhos HBF4", 36), ("PPhMe2", 23),
                    ("X-Phos", 23), ("PCy3 HBF4", 22), ("PPh2Me", 7.7), ("PPh3", 0.50)]),
        ("Base", [("CsOPiv", 9.4), ("CsOAc", 6.7), ("KOAc", 2.8), ("KOPiv", 1.8)]),
        ("Solvent", [("BuCN", 0.25), ("BuOAc", 0.19), ("p-Xylene", 0.12), ("DMAc", 0.10)]),
    ],
    # Panel a of Fig. 4 of Shields et al., chosen by the study owner (12 September
    # 2026): reaction 3 with the twelve ligands drawn, the bases, solvents,
    # temperatures and concentrations. Panels b-e (optimiser against human
    # players) were cut off: they are the subject of our own study. Nature is
    # not open access - fine for the participants' page, but an article would
    # need Springer Nature's permission or the redrawn scheme (arylation.svg).
    "figure": ("shields_2021_fig4a.png",
               "Adapted from Shields et al., Nature 2021, 590, 89, Fig. 4a (reaction 3), "
               "© Springer Nature; shown here to the study participants only."),
    "sources": [
        ("Shields et al., Nature 2021, 590, 89 (reaction 3)", "https://doi.org/10.1038/s41586-021-03213-y"),
        ("Torres et al., J. Am. Chem. Soc. 2022, 144, 19999 (EDBO+, yield and cost)",
         "https://doi.org/10.1021/jacs.2c08592"),
        ("Fox et al., J. Org. Chem. 2019, 84, 4661 (the BMS-911543 step)",
         "https://doi.org/10.1021/acs.joc.8b02993"),
    ],
}


def for_benchmark(name):
    """The chemistry block of one benchmark: the shared text plus the case's partners."""
    case = name.replace("summit_", "")
    if case in SUZUKI_CASES:
        block = dict(SUZUKI)
        block["case"] = case
        block["partners"] = SUZUKI_CASES[case]
        block["ligands"] = SUZUKI_LIGANDS
        block["scheme"] = "suzuki_%s" % case
        return block
    if name == "edbo_ch_arylation":
        block = dict(ARYLATION)
        block["partners"] = {"nucleophile": ARYLATION["nucleophile"],
                             "electrophile": ARYLATION["electrophile"],
                             "product": ARYLATION["product"]}
        block["ligands"] = ARYLATION_LIGANDS
        block["scheme"] = "arylation"
        return block
    return None


def figures():
    """Every drawing the page can show: file stem -> (kind, SMILES or reaction SMILES, title)."""
    out = {}
    for case, p in SUZUKI_CASES.items():
        out["suzuki_%s" % case] = ("reaction", "%s.%s>>%s" % (p["halide"][1], p["boron"][1], p["product"][1]),
                                   "%s + %s" % (p["halide"][0], p["boron"][0]))
    a = ARYLATION
    out["arylation"] = ("reaction", "%s.%s>>%s" % (a["nucleophile"][1], a["electrophile"][1], a["product"][1]),
                        "%s + %s" % (a["nucleophile"][0], a["electrophile"][0]))
    for code, pair, ligand, family, smiles in SUZUKI_LIGANDS:
        if smiles:
            out["ligand_%s" % ligand] = ("molecule", smiles, ligand)
    for ligand, smiles in ARYLATION_LIGANDS:
        out["ligand_%s" % ligand.replace(" ", "_").replace("(", "").replace(")", "")] = ("molecule", smiles, ligand)
    return out


def ligand_figure(name):
    """File stem of a ligand's drawing, from the name shown to the chemist."""
    return "ligand_%s" % name.replace(" ", "_").replace("(", "").replace(")", "")

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
    "summary": ("A palladium-catalysed C–C coupling between a heteroaryl halide and a boronic "
                "acid or ester. The catalytic cycle is oxidative addition of the aryl halide to "
                "Pd(0), transmetalation of the aryl group from boron (activated by the base), "
                "and reductive elimination of the biaryl product. A chloride is harder to "
                "activate than a bromide, and an electron-poor or nitrogen-rich heteroarene "
                "can bind palladium and slow the catalyst down."),
    "conditions": [
        "Palladacycle precatalyst P1 (X = OMs) with one of seven ligands, the pairs P1-L1 … P1-L7.",
        "Boron reagent 1.5 equiv.; DBU 2.0 equiv.; THF / water 5 : 1.",
        "Automated droplet-flow microreactor: the reaction runs for one residence time in a heated "
        "Teflon tube under 6.9 bar of argon, one condition at a time.",
    ],
    "variables": [
        ("Catalyst", "one of the seven precatalyst–ligand pairs"),
        ("Residence time", "60 to 600 s, the time the droplet spends in the heated reactor"),
        ("Temperature", "30 to 110 °C"),
        ("Pd loading", "0.5 to 2.5 mol% of palladium"),
    ],
    "objectives": [
        ("Yield", "% of the coupled product, to maximise"),
        ("TON", "turnover number, moles of product per mole of catalyst, to maximise — high TON needs "
                "a low loading, high yield often needs more catalyst: the two pull in opposite directions"),
    ],
    "data": ("The values you will see are not new measurements: they come from a model of the "
             "reaction (an Olympus emulator fitted to the flow campaigns of Reizman et al.) "
             "evaluated on a complete grid of conditions, the grid published with Minerva "
             "(Sin et al., Nat. Commun. 2025). Every condition you can propose exists on that grid."),
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
    "summary": ("The C5–H bond of the imidazole is arylated directly by the aryl bromide, with "
                "no prior functionalisation of the heterocycle. The carboxylate base is not a "
                "spectator: in this class of reaction it takes part in the C–H cleavage step "
                "(concerted metalation–deprotonation), which is why acetate and pivalate are "
                "the bases on offer. The reaction is related to a key step in the commercial "
                "synthesis of the JAK2 inhibitor BMS-911543 (Bristol Myers Squibb)."),
    "conditions": [
        "[Pd(allyl)Cl]₂ 2.25 mol% as precatalyst, ligand 5 mol%.",
        "Imidazole 2 equiv., aryl bromide 1 equiv., base 3 equiv.",
        "24 h; high-throughput screening in 96-well plates in a glovebox, 15 µmol scale, "
        "one run per condition, no replicate.",
    ],
    "variables": [
        ("Ligand", "one of twelve phosphines, drawn below"),
        ("Base", "KOAc, KOPiv, CsOAc or CsOPiv"),
        ("Solvent", "DMAc, BuOAc, BuCN or p-xylene"),
        ("Concentration", "0.057, 0.100 or 0.153 M"),
        ("Temperature", "90, 105 or 120 °C"),
    ],
    "objectives": [
        ("Yield", "% of the arylated product, to maximise"),
        ("Reagent cost", "cost of the ligand, base and solvent used for the reaction, computed by "
                         "the EDBO+ authors from catalogue prices (arbitrary units), to minimise — "
                         "it is set almost entirely by the ligand, and a caesium base costs more "
                         "than a potassium one"),
    ],
    "data": ("Every value you will see is a real measurement: the 1,728 conditions were all run "
             "at Bristol Myers Squibb and published with EDBO+ (Torres et al., JACS 2022). "
             "Yields are single runs, so a surprising number can be a real outlier."),
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

# -*- coding: utf-8 -*-
r"""Draw the reaction schemes and ligand structures shown on the live HITL page.

Reads the SMILES of hitl_bench/chemistry.py and writes one SVG per figure into
assets/hitl/, where REACTO serves them as /assets/hitl/<stem>.svg. The page
never needs RDKit: the drawings are files, committed with the code.

RDKit is not in REACTO's venv. Run this with the conda environment that has it:

    C:\Users\mathi\anaconda3\envs\environement-webBO\python.exe -m hitl_bench.scripts.make_chemistry_figures

from the repository root. Re-run after any change to chemistry.py.
"""

import os
import sys

from rdkit import Chem
from rdkit.Chem import AllChem, rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hitl_bench import chemistry

rdDepictor.SetPreferCoordGen(True)      # cleaner layouts for the biaryl phosphines

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "hitl")


def draw(kind, smiles, width, height):
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts = drawer.drawOptions()
    opts.clearBackground = False            # transparent, so the card colour shows through
    opts.padding = 0.08
    if kind == "reaction":
        rxn = AllChem.ReactionFromSmarts(smiles, useSmiles=True)
        drawer.DrawReaction(rxn)
    else:
        mol = Chem.MolFromSmiles(smiles)
        drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def main():
    os.makedirs(OUT, exist_ok=True)
    for stem, (kind, smiles, title) in chemistry.figures().items():
        width, height = (760, 220) if kind == "reaction" else (220, 170)
        svg = draw(kind, smiles, width, height)
        path = os.path.join(OUT, stem + ".svg")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(svg)
        print("%-28s %-9s %s" % (stem + ".svg", kind, title))


if __name__ == "__main__":
    main()

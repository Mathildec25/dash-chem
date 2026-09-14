# -*- coding: utf-8 -*-
"""Catalyst names for the codes the Suzuki grids use.

The Olympus grids store the seven Reizman catalysts as L0..L6. A chemist is
never shown a code: data/catalyst_names.json maps each one to its
precatalyst-ligand pair and ligand name, established by matching the grids
against Summit's named data (see that file for how, and for the two names
that come from Scheme 1 of the article rather than its text).
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES_PATH = os.path.join(HERE, "data", "catalyst_names.json")


def catalyst_names():
    """The mapping file as a dict, or None when it is absent."""
    if not os.path.exists(NAMES_PATH):
        return None
    with open(NAMES_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def label_value(key, value, names):
    """What a chemist reads for one grid value: L4 becomes 'PCy3 (P1-L5)'."""
    if key == "ligand" and names and str(value) in names["mapping"]:
        entry = names["mapping"][str(value)]
        return ("%s (%s)" % (entry["ligand"], entry["pair"])) if entry.get("ligand") \
            else entry["pair"]
    if isinstance(value, float):
        return "%.3g" % value
    return str(value)

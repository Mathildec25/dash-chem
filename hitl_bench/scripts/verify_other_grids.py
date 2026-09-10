# -*- coding: utf-8 -*-
r"""Establish, and re-establish on demand, where each grid in data/other came from.

This exists because it once did not. The four Suzuki grids have their provenance
written down in data/README.md, down to the repository and the check that was
run; the nine grids added later did not, and a night later nothing remained. Two
of them turned out not to come from where their metadata implied, and one of
those two had been recommended as the study's second benchmark.

So: no grid is usable until this script can name its source. It compares each
CSV in data/other against every dataset shipped by a local Olympus checkout,
matching on the sorted numeric content rather than on row order, and reports the
ones it cannot place. A grid that comes back "AUCUNE" is not necessarily wrong -
snar is a Summit kinetic model and is perfectly legitimate - but it does mean
the source has to be established some other way and written into
data/other/README.md before the grid is used for anything.

Olympus is not imported: only its shipped `data.csv` files are read, so this runs
in REACTO's venv with pandas alone and needs neither olympus_env nor a working
Olympus install.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/verify_other_grids.py ^
        --olympus "C:\Users\mathi\Documents\Thèse\BO\olympus\src\olympus\datasets"
"""

import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OTHER = os.path.join(HERE, "data", "other")
DEFAULT_OLYMPUS = os.path.join(
    os.path.expanduser("~"), "Documents", "Th\u00e8se", "BO",
    "olympus", "src", "olympus", "datasets")

# Sources established by hand, once, and re-checkable. A grid listed here is
# accounted for even when Olympus does not contain it.
KNOWN_ELSEWHERE = {
    "snar": "summit.benchmarks.SnarBenchmark, kinetic model on a 6x6x5x5 factorial "
            "grid; verified by replaying the model on sample points",
    "edbo_ch_arylation":
        "EDBO+ (Torres et al., JACS 2022, 10.1021/jacs.2c08592), file "
        "examples/publication/BMS_yield_cost/data/experiments_yield_and_cost.csv "
        "of github.com/doyle-lab-ucla/edboplus; downloaded and compared "
        "row-for-row, max difference 0.0 on both yield and cost",
}


def numeric(frame):
    """Sorted numeric content, so row order and column names cannot mask a match."""
    values = frame.select_dtypes("number").to_numpy(dtype=float)
    return np.sort(values, axis=0) if values.size else values


def olympus_datasets(root):
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name, "data.csv")
        if not os.path.isfile(path):
            continue
        try:
            yield name, pd.read_csv(path, header=None)
        except Exception:                       # a dataset we cannot parse is not a match
            continue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--olympus", default=DEFAULT_OLYMPUS,
                        help="dossier olympus/src/olympus/datasets")
    args = parser.parse_args()

    if not os.path.isdir(args.olympus):
        raise SystemExit("dossier Olympus introuvable : %s" % args.olympus)
    shipped = list(olympus_datasets(args.olympus))
    print("Olympus : %d jeux de donnees lus dans %s\n" % (len(shipped), args.olympus))

    print("%-22s %7s %5s  %s" % ("grille", "lignes", "cols", "source"))
    unplaced = []
    for path in sorted(glob.glob(os.path.join(OTHER, "*.csv"))):
        name = os.path.basename(path)[:-4]
        ours = pd.read_csv(path)
        mine = numeric(ours)
        source = None
        for dataset, theirs in shipped:
            other = numeric(theirs)
            if other.shape == mine.shape and np.allclose(other, mine, atol=1e-9):
                source = "olympus/%s" % dataset
                break
        if source is None:
            source = KNOWN_ELSEWHERE.get(name)
            if source is None:
                unplaced.append(name)
                source = "*** INCONNUE ***"
        print("%-22s %7d %5d  %s" % (name, ours.shape[0], ours.shape[1], source))

    if unplaced:
        print("\n%d grille(s) sans source etablie : %s" % (len(unplaced), ", ".join(unplaced)))
        print("Ne pas les utiliser tant que data/other/README.md ne les documente pas.")
        return 1
    print("\nToutes les grilles sont rattachees a une source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

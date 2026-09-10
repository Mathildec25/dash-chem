# -*- coding: utf-8 -*-
r"""Evaluate Summit's Reizman emulators on the exact grid the Olympus ones gave us.

We hold two surrogates of the same published experiment: the Olympus Bayesian
neural networks (shipped as ready-made grids by Minerva, see data/README.md) and
Summit's pretrained emulators. On 24 points drawn at random they disagree by 8.8
yield points on average and by up to 34.6, agreeing at the top of the range and
diverging at low temperature where the Olympus grid holds exact zeros.

That matters because the study's trap - case II's front sitting entirely on one
catalyst - could be a property of one surrogate rather than of the chemistry. To
find out, the two have to be compared with everything else held fixed. So this
script does not build a continuous benchmark: it evaluates Summit on the **same
5670 rows**, writing files with the same columns, so that `GridBenchmark` reads
them unchanged, the reference front stays exactly computable, and the only thing
that differs between the two arms is the surrogate.

Runs in `summit_env`, not in REACTO's venv: Summit needs Python 3.10 and its own
torch. It imports nothing from hitl_bench for that reason.

    C:\Users\mathi\anaconda3\envs\summit_env\python.exe ^
        hitl_bench\scripts\make_summit_grids.py

Environment note: Summit's emulators fail with "Could not infer dtype of
numpy.int32" when numpy is older than 1.23, because torch 1.13 is built against
a newer array API. summit_env was moved to numpy 1.23.5 for this.
"""

import argparse
import csv
import json
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")

CASES = {"i": 1, "ii": 2, "iii": 3, "iv": 4}
# Column order of the Olympus grids, reproduced exactly so the files are
# interchangeable from GridBenchmark's point of view.
LIGAND_COLUMNS = ["L%d" % i for i in range(7)]
PROCESS = ["res_time", "temperature", "catalyst_loading"]
OBJECTIVES = ["yield", "turnover"]
# Summit calls the process variables and the objectives something else.
SUMMIT_NAMES = {"res_time": "t_res", "temperature": "temperature",
                "catalyst_loading": "catalyst_loading"}
BATCH = 512


def ligand_map():
    """L0..L6 to Summit's precatalyst-ligand labels, from the frozen mapping."""
    with open(os.path.join(DATA, "catalyst_names.json"), encoding="utf-8") as handle:
        mapping = json.load(handle)["mapping"]
    return {code: mapping[code]["pair"] for code in mapping}


def read_grid(case):
    with open(os.path.join(DATA, "suzuki_%s.csv" % case), newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build(case, number, pairs):
    import pandas as pd
    from summit.benchmarks import get_pretrained_reizman_suzuki_emulator
    from summit.utils.dataset import DataSet

    rows = read_grid(case)
    emulator = get_pretrained_reizman_suzuki_emulator(case=number)

    conditions = []
    for row in rows:
        code = next(c for c in LIGAND_COLUMNS if row[c] not in ("0", "0.0", ""))
        conditions.append({"catalyst": pairs[code],
                           "t_res": float(row["res_time"]),
                           "temperature": float(row["temperature"]),
                           "catalyst_loading": float(row["catalyst_loading"])})

    started = time.time()
    predicted = []
    for start in range(0, len(conditions), BATCH):
        chunk = pd.DataFrame(conditions[start:start + BATCH])
        result = emulator.run_experiments(DataSet.from_df(chunk))
        for position in range(len(chunk)):
            predicted.append((float(result["yld"].iloc[position]),
                              float(result["ton"].iloc[position])))
        print("   %s : %d / %d" % (case, len(predicted), len(conditions)), flush=True)

    target = os.path.join(DATA, "suzuki_summit_%s.csv" % case)
    header = [""] + LIGAND_COLUMNS + PROCESS + OBJECTIVES
    with open(target, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for index, (row, (yld, ton)) in enumerate(zip(rows, predicted)):
            writer.writerow([index]
                            + [row[c] for c in LIGAND_COLUMNS]
                            + [row[k] for k in PROCESS]
                            # Summit reports yield as a percentage on Reizman,
                            # like Olympus; no rescaling is applied on purpose.
                            + ["%.6g" % yld, "%.6g" % ton])

    yields = [y for y, _ in predicted]
    print("%s -> %s | %d lignes en %.0f s | rendement %.1f a %.1f"
          % (case, os.path.basename(target), len(predicted), time.time() - started,
             min(yields), max(yields)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", nargs="*", default=list(CASES))
    args = parser.parse_args()

    pairs = ligand_map()
    for case in args.cases:
        if case not in CASES:
            raise SystemExit("cas inconnu %r" % case)
        build(case, CASES[case], pairs)


if __name__ == "__main__":
    main()

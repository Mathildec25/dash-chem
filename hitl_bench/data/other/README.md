# Benchmark grids beyond the Reizman-Suzuki cases

Nine complete factorial grids, used to look for a second reaction for the
human-in-the-loop study. Each file is pre-evaluated: the optimiser only ever
picks rows from it, so no emulator and no Olympus install is needed to reproduce
a result.

## How to re-check any of this

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/verify_other_grids.py

The script compares every CSV here against every dataset shipped by the local
Olympus checkout, matching sorted numeric content so that row order cannot mask
a match. It exits non-zero while any grid is unaccounted for.

Local Olympus checkout, editable install used by `olympus_env`:
`C:\Users\mathi\Documents\Thèse\BO\olympus\src` (43 readable datasets).

## Provenance

| grid | rows | source | established how |
|---|---|---|---|
| `buchwald_a` … `buchwald_e` | 792 each | `olympus/dataset_buchwald_<x>` | numeric content identical |
| `dye_lasers` | 3458 | `olympus/dataset_dye_lasers` | numeric content identical |
| `lnp3` | 768 | `olympus/dataset_lnp3` | numeric content identical |
| `snar` | 900 | **Summit**, `summit.benchmarks.SnarBenchmark` | model replayed, values match |
| `edbo_ch_arylation` | 1728 | **unknown** | see below |

### snar is not the Olympus SnAr dataset

Olympus ships `dataset_snar` with 66 rows; this grid has 900 = 6 x 6 x 5 x 5. It
is Summit's SnAr **kinetic model** evaluated on a factorial grid, not measured
data. Confirmed by replaying `SnarBenchmark` on sample points in `summit_env`,
which reproduces `sty` and `e_factor` to the last digit:

    tau   equiv   conc      T |  sty grid   sty Summit |  E grid   E Summit
    1.40   1.80   0.40   75.0 |   3053.87      3053.87 |   11.56      11.56
    0.50   5.00   0.40   52.5 |   8884.29      8884.29 |   12.32      12.32
    1.10   4.20   0.20  120.0 |    927.91       927.91 |   50.39      50.39

Being a mechanistic model rather than a fit, it carries no observation noise,
which is why plain BO reaches 100% of its front on every seed tried.

### edbo_ch_arylation has no established source: do not use it

1728 rows = 4 bases x 12 ligands x 4 solvents x 3 concentrations x 3
temperatures, with named reagents and two objectives, `yield` and `cost`. No
Olympus dataset has 1728 rows, no EDBO source exists anywhere on this machine,
and nothing was written down when the grid was added.

The content is consistent with a real high-throughput screen - 29% of yields are
exactly zero, values carry two decimals, and the ligand ranking is chemically
sensible, with X-Phos and CgMe-PPh on top and PPhMe2 and PPhtBu2 dead - but
consistency is not provenance. **The grid is excluded from the study until its
source is named and this table records it.** Everything measured on it stands as
a measurement and none of it is citable.

## What `olympus_meta.json` is, and is not

It records the shape of each grid - row count, whether the grid is a complete
factorial, the levels of each variable - and nothing about where a grid came
from. It is also **out of step with this directory**, because it was written by
the Olympus enumeration pass and two grids were added afterwards by another
route:

    described in the metadata but with no CSV here : perovskites, redoxmers, suzuki_edbo
    CSV present here but absent from the metadata  : snar, edbo_ch_arylation

Read it for shapes. Never read it as provenance; that is what this file and
`verify_other_grids.py` are for.

## Why this file exists

`../README.md` documents the four Suzuki grids properly: repository, paper, DOI,
and the check that was run to prove the numbers are the emulator's. That
standard was not applied when these nine were added. Provenance was checked as
the grids were collected but never written down, and a night later none of it
could be recovered from the repository - which is how a grid with no traceable
source came to be recommended as the study's second benchmark.

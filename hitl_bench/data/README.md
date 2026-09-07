# Benchmark grids: Reizman-Suzuki cases I-IV

Four discretised Suzuki coupling landscapes used as the in-silico benchmark for
the human-in-the-loop study. Each file is a complete, pre-evaluated grid: the
optimiser only ever picks rows from it, so **no emulator and no Olympus install
are needed to reproduce any result in this project.**

## Provenance

Downloaded verbatim from the Minerva repository, `benchmark_datasets/olympus_suzuki`:

- Repository: https://github.com/schwallergroup/minerva (MIT licence)
- Paper: Sin, Chau, Burwood, Püntener, Bigler & Schwaller, *Highly parallel
  optimisation of chemical reactions through automation and machine
  intelligence*, Nature Communications, 2025.
  https://www.nature.com/articles/s41467-025-61803-0

Underneath, the values are predictions of the Olympus `suzuki_i`..`suzuki_iv`
Bayesian-neural-network emulators, themselves fitted to the flow-chemistry
campaigns of Reizman et al. Reusing Minerva's grids rather than regenerating
them makes our results directly comparable to a published benchmark.

## Layout

Each file holds 5670 rows and these columns:

| Column | Meaning |
|---|---|
| `L0`..`L6` | ligand, one-hot encoded (exactly one column is 1) |
| `res_time` | residence time, s |
| `temperature` | temperature, °C |
| `catalyst_loading` | catalyst loading, mol% |
| `yield` | objective 1, to maximise, % |
| `turnover` | objective 2, to maximise |

5670 = 7 ligands x 810 conditions, where 810 = 10 residence times x 9
temperatures x 9 catalyst loadings.

### Grid steps

| Variable | Levels | Step |
|---|---|---|
| `res_time` | 10: 60, 120, ... 600 | uniform, 60 s |
| `temperature` | 9: 30, 40, ... 110 | uniform, 10 °C |
| `catalyst_loading` | 9: 0.498, 0.75, 1.0, ... 2.25, 2.515 | 0.25 mol%, first and last snapped to the domain bounds |

The catalyst-loading step is uniform except at the two ends, which sit on the
true bounds of the experimental domain so that the extremes are reachable. This
has no algorithmic consequence: the surrogate sees the raw numeric values and
the acquisition function is optimised over the set of allowed levels, so the
spacing between levels never enters the computation.

### Seven ligands, not eight

Olympus declares eight ligands (L0..L7) for these datasets, but L7 appears in
none of the ~90 underlying experiments of any case. Predictions for it would be
extrapolation from zero data, returned with a deceptively ordinary uncertainty.
Minerva excludes it and so do we.

## Verification

`verify_grids_against_olympus.py` re-runs the matching Olympus emulator on 3000
conditions drawn from each grid and compares against the stored `yield`. Run
once, in the separate Olympus environment; the benchmark itself does not need it.

| Grid | Emulator | r | mean abs. error | bias |
|---|---|---|---|---|
| i | i | 0.9974 | 1.03 pts | -0.03 |
| ii | ii | 0.9993 | 0.11 pts | +0.00 |
| iii | iii | 0.9988 | 0.55 pts | -0.03 |
| iv | iv | 0.9970 | 1.67 pts | -0.08 |

The residual scatter is consistent with the stochasticity of a Bayesian neural
network averaged over finitely many forward passes; the bias is zero to two
decimals in every case, so there is no systematic offset.

### One anomaly, checked and benign

The `suzuki_ii` grid is laid out on case **I**'s catalyst-loading bounds
(0.498-2.515) rather than case II's (0.492-2.516). Only the coordinates are
affected, not the values: the stored yields match the case II emulator
(r = 0.9993) and emphatically not the case I emulator (r = 0.4408, mean error
13.3 pts, last row of the verification script). The coordinate shift is 0.006
and 0.001 mol% at the two ends, negligible against a ~2 mol% loading, so the
grid is used as published.

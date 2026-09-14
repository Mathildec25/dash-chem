# hitl-bench

Benchmark harness for a study on human-in-the-loop multi-objective Bayesian
optimisation of chemical reactions. The question: when a small-budget campaign
stalls, when and how does a chemist's intervention help?

It lives inside REACTO on purpose. The optimiser is REACTO's own
`utils.bofire_optimization.bayesian_optimization`, imported rather than copied,
so the in-silico study and a real campaign run through the same code. There is
one Bayesian optimisation in this repository, not two.

## Where to start

Read `CLAUDE.md` first: it holds every scientific decision, dated, and the
settings that are frozen. Then, depending on what you need:

| You want to… | Run / read |
|---|---|
| let chemists run the study | the REACTO page `/hitl-live`; `deploy/README.md` for what to install and back up; `docs/protocole_chimistes.md` for what they are told |
| collect what the chemists did | `python -m hitl_bench.scripts.collect_live` → `results/live_campaigns.csv`, `results/live_decisions.csv` |
| recompute the control and random arms | `python -m hitl_bench.scripts.run_arms --benchmark ii --arm no_hitl` then `--arm hitl_random`; `analyse_arms.py` writes the reports and figures |
| see why these three campaigns were assigned | `python -m hitl_bench.scripts.seed_choice` |
| see where the trigger fires with other settings | `scripts/plot_firings.py --signal pace_ratio --window 5 --threshold 0.30` |
| check a grid against its source | `scripts/verify_other_grids.py`; provenance in `data/README.md` and `data/other/README.md` |
| redraw the reaction schemes | `scripts/make_chemistry_figures.py` (needs RDKit, see the file) |

Everything runs from the `dash-chem` directory, in REACTO's own virtualenv,
with `PYTHONIOENCODING=utf-8` set (some REACTO modules print emoji on import,
which the Windows console rejects):

```
cd C:\Users\mathi\REACTO\dash-chem
set PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe -m hitl_bench.scripts.run_arms --benchmark ii --arm no_hitl --seeds 20
```

Do **not** use the `hitl_env` conda environment: its numpy crashes the
interpreter on any BLAS call, so a GP fit dies with no traceback.

## What is where

| File | Role |
|---|---|
| `CLAUDE.md` | the decisions, frozen settings and findings, dated |
| `data/` | the benchmark grids and their provenance (`data/README.md`, `data/other/README.md`) |
| `benchmark.py` | `GridBenchmark`: a Suzuki grid, its BoFire domain, its true front; `scripts/run_other_benchmarks.py` holds `TableBenchmark` for the other grids |
| `campaign.py` | one campaign: initial design, optimisation loop, metrics, forks |
| `triggers.py` | P* (`pace_ratio`) and the candidates kept for comparison |
| `metrics.py` | hypervolume, IGD+, areas under curves |
| `runtime.py` | thread and memory settings that keep a campaign reproducible and under a gigabyte |
| `live.py` | the chemist's campaign as a state machine (replay, alert, three answers, live mode); `chemistry.py` and `names.py` what they are shown |
| `scripts/` | entry points, each with its usage in its docstring |
| `results/arms/` | campaign logs, one JSON each. The three the chemists replay are in git; the rest is raw study data, never delete |
| `forms/live/` | the chemists' answers, written by the page. Not in git: back it up |
| `docs/` | the candidate-reaction study, the chemists' protocol, the night and weekly reports |

## The protocol, frozen

Do not change any of this without asking the study's owner.

- 10 Latin-hypercube points, then 30 sequential BO iterations, one experiment
  at a time: 40 experiments per campaign.
- Acquisition `qLogNEHVI`, through BoFire's `MoboStrategy`.
- Ligand as a `CategoricalInput` over seven ligands, residence time,
  temperature and catalyst loading as `DiscreteInput`s holding the grid levels.
  The domain is then purely combinatorial, and BoFire enumerates every
  combination, drops the ones already run and evaluates the acquisition on all
  the rest, which is the intended "evaluate on every untested point".
- Two objectives, yield and turnover, both maximised, each normalised to [0, 1]
  by its minimum and maximum over the grid. Hypervolume against (0, 0).
- Seeds 1 to 5 while testing, 20 for anything reported.
- Trigger P* with W = 5, threshold 0.30, cooldown 5, first alert at experiment 15.

### Seeding, and why it needs care

`torch.manual_seed(seed)` alone does **not** make a campaign reproducible.
Two generators escape it: BoFire's `RandomStrategy` for the initial design,
and the `MoboStrategy` itself, which without a `seed` draws one from operating
system entropy at every acquisition step. The campaign seed is therefore handed
to `sampling()` and, through `_acquisition_seed(seed, iteration)`, to
`bayesian_optimization(..., seed=)`. With that, two runs coincide to the
twelfth decimal and a fork reproduces its parent exactly. Measured on 12
September: the outcome of a campaign is then a function of its initial design
alone; the acquisition seed changes nothing but the tail of a tied sweep.

## Metrics

Primary, and the one frozen in the protocol:

- **`hv_curve_auc`** — area under the hypervolume curve after the initial
  design. `hv_curve_auc_fraction` divides it by what a campaign sitting on the
  global front from the first iteration would score, so cases compare.

Secondary:

- **`igd_plus`** — average shortfall of the best points found against each
  point of the true front. Reported per experiment. It matters because the
  fronts here are small: case ii's global front is three points, so the
  hypervolume advances in steps and barely moves until a campaign lands exactly
  on one of them, while IGD+ rewards getting close. Minerva report it too.
- **`hv_final_fraction`** — final hypervolume as a fraction of the global one.

Interpretable, and specific to this study:

- **`bo_chose_a_front_ligand`**, `bo_fraction_on_front_ligand`,
  `front_ligand_first_bo_experiment` — did the optimiser go for a ligand that
  carries the global front, and when? The initial design touching one by chance
  says nothing; what matters is whether the optimiser then pursued it or walked
  away. On case ii the whole global front sits on L4 (PCy3) while the optimiser
  tends to settle on L0 (XPhos), so this single number says whether a campaign
  escaped the trap.

## Cost, and the memory ceiling

Measured on the owner's laptop (AMD Ryzen 7 8840HS, 8 physical cores, 13.8 GB):

| | |
|---|---|
| one BO iteration | 10-25 s, rising through a campaign as the model sees more data |
| one campaign, 40 experiments | roughly 10 minutes |
| **peak memory per campaign process** | **about 0.6 GB** |

Memory used to be the binding constraint here, at about 1.5 GB for a single
acquisition step and enough to get runs killed on a laptop with a browser open.
`hitl_bench/runtime.py` caps how many candidates BoTorch scores at once, which
brings the peak down to under 600 MB at no cost in time and with an identical
campaign trajectory. It is a batching detail, not a change of algorithm.

Lowering `n_mc_samples` on the acquisition function would cut the memory
further, but that *would* change the algorithm and would no longer match what a
real REACTO campaign does, so it is not done.

`--workers 1` is the default and runs the campaigns in the calling process; a
pool would otherwise hold a second interpreter with torch and BoFire loaded.
Check free memory before a long series: browsers are the usual culprit, and
Chrome alone was holding 4.9 GB of this machine's 13.8 GB while the first runs
were being killed.

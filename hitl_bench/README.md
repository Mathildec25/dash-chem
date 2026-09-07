# hitl-bench

Benchmark harness for a study on human-in-the-loop multi-objective Bayesian
optimisation of chemical reactions. The question: when a small-budget campaign
stalls, when and how does a chemist's intervention help?

It lives inside REACTO on purpose. The optimiser is REACTO's own
`utils.bofire_optimization.bayesian_optimization`, imported rather than copied,
so the in-silico study and a real campaign run through the same code. There is
one Bayesian optimisation in this repository, not two.

## Running it

Everything runs from the `dash-chem` directory, in REACTO's own virtualenv:

```
cd C:\Users\mathi\REACTO\dash-chem
set PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe hitl_bench/scripts/run_screening.py --case ii --seeds 5
```

Two things that will otherwise waste an afternoon:

- **Run from `dash-chem`.** The harness imports `utils.*`, which is only on the
  path from there.
- **Set `PYTHONIOENCODING=utf-8`.** Some REACTO modules print emoji when
  imported, which raises `UnicodeEncodeError` on the Windows console.

Do **not** use the `hitl_env` conda environment: its numpy crashes the
interpreter on any BLAS call, so a GP fit dies with no traceback.

## What is where

| File | Role |
|---|---|
| `data/` | the four benchmark grids and their provenance, see `data/README.md` |
| `benchmark.py` | `GridBenchmark`: a grid, its BoFire domain, its true front |
| `campaign.py` | one campaign: initial design, optimisation loop, metrics |
| `metrics.py` | hypervolume, IGD+, areas under curves |
| `campaign_log.py` | one JSON file per campaign, under `results/` |
| `scripts/` | entry points |
| `results/` | campaign logs. Raw study data: never delete, not in git |

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

### Seeding, and why it needs care

`torch.manual_seed(seed)` alone does **not** make a campaign reproducible:
BoFire's `RandomStrategy` carries its own generator, so the initial design comes
out different every time. The seed is therefore also handed to `sampling()`
explicitly. On a grid the acquisition step is evaluated exhaustively over every
untested point, which makes it near-deterministic given the data, so in
practice the seed acts almost entirely through the initial design.

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
| **peak memory per campaign process** | **about 2.3 GB** |

The memory figure is the binding constraint, and it is a plateau, not a leak:
about 1.9 GB on the first acquisition call and 2.3 GB from then on, whatever the
number of experiments. It is the cost of evaluating `qLogNEHVI` with its 512
Monte Carlo samples over 5670 candidates. Capping BoTorch's `max_batch_size`
does not reduce it.

So `--workers` is limited by free memory, not by cores:

| Free RAM | Safe workers | 320 campaigns |
|---|---|---|
| ~5 GB, the usual state with a browser and an editor open | 1 | about 55 h |
| ~11 GB, browser and editor closed | 4 | about 14 h |

Two campaigns at once need roughly 5 GB and will be killed on a machine that
only has 5.5 GB free, which is what happens with the usual desktop open. Check
free memory before launching a long run, and prefer a machine with more RAM for
the 20-seed production runs.

Lowering `n_mc_samples` on the acquisition function would cut the memory
several-fold, but it changes the algorithm and would no longer match what a
real REACTO campaign does, so it is not done here.

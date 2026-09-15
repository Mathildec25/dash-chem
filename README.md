# REACTO

![REACTO](assets/REACTO_logo.png)

REACTO is a web application for the Bayesian optimisation of chemical
reactions, written for chemists who run the experiments themselves. A campaign
is an Excel sheet: the app proposes the next experiment, the chemist runs it
and types in the result, and the model updates. It also carries a
**human-in-the-loop** mechanism — an alarm that pauses a stalling campaign and
asks the chemist what to do — together with the in-silico benchmark used to
design and evaluate it.

Built at CiTOS, University of Liège, on [BoFire](https://github.com/experimental-design/bofire)
/ [BoTorch](https://botorch.org) and [Dash](https://dash.plotly.com).

## What it does

**Optimisation.** Define the reaction space — continuous, discrete or
categorical parameters, with solvent and base libraries and boiling-point or
linear constraints — and one or two objectives to maximise or minimise. REACTO
draws an initial design (random, Latin hypercube, Sobol or constrained
k-means), then proposes one experiment at a time with qLogNEI (one objective)
or qLogNEHVI (two). Results, Pareto fronts and parameter effects are shown on
the Results page; a sensitivity screen around the optimum, after Glorius et
al., checks its robustness.

**Human in the loop.** Switched on when a project is created. The campaign's
pace is monitored as

    P* = progress over the last 5 experiments / average progress since the initial design

and when P* falls below 0.30 the campaign pauses and asks the chemist to
choose: let the optimiser continue, propose the next experiment, or stop. The
alarm cannot fire before five optimiser proposals nor more than once every
five experiments; each answer and its reason are recorded with the project.

**In-silico study** (`/hitl-live`). The page used to measure what a chemist's
intervention is worth: participants replay a real campaign that plain
Bayesian optimisation gets wrong — two Suzuki–Miyaura couplings from Reizman
et al. and the C–H arylation of Shields et al. — and answer the same alarm.
Their branch is compared, paired, with the optimiser left alone and with a
random point injected at the same moment. The benchmark, the trigger's
calibration, every decision and its date are in [`hitl_bench/`](hitl_bench/README.md).

## Install and run

Python 3.11.

    git clone https://github.com/Mathildec25/dash-chem.git
    cd dash-chem
    python -m venv .venv
    .venv\Scripts\activate            # Linux / macOS: source .venv/bin/activate
    pip install -r requirements.txt   # on Linux, drop the pywin32 and pywinpty lines
    python app.py

then open <http://localhost:8088>. To serve it to others, `python
deploy/serve.py` runs the same app under a production server; see
[`deploy/README.md`](deploy/README.md) for what to install and what to back up.

Projects live in `data/excel_files/` (the experiments) and `data/domains/`
(the reaction space and the human-in-the-loop log); neither is versioned.

## Repository

| | |
|---|---|
| `app.py`, `pages/`, `components/`, `callbacks/` | the Dash application |
| `utils/` | BoFire domain construction, acquisition functions, descriptors |
| `hitl_bench/` | the human-in-the-loop study: benchmark grids, campaign engine, trigger, analysis scripts, the live page's engine, and `CLAUDE.md` with the frozen decisions |
| `deploy/` | production entry point and deployment notes |

## Citing

A manuscript describing the human-in-the-loop study is in preparation. Until
it is out, please cite this repository.

## Contact

Mathilde Croissant — mathilde.croissant@uliege.be — CiTOS, University of Liège.

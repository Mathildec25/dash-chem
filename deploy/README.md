# Deploying REACTO with the live HITL page

What a chemist needs is one URL. What the server needs is below; everything
else in the repository is for the study's analysis and does not run on the VM.

## What the page reads and writes

| Path | Role | In git? |
|---|---|---|
| `hitl_bench/data/*.csv`, `hitl_bench/data/other/edbo_ch_arylation.csv` | the reaction grids | yes |
| `hitl_bench/data/catalyst_names.json` | catalyst names for the Suzuki codes | yes |
| `hitl_bench/results/arms/<benchmark>__no_hitl__seed<NN>.json` | the control campaign each chemist replays — **only the three named in `assignment.json` are needed**, and those three are committed | yes (those three) |
| `hitl_bench/forms/live/assignment.json` | which campaign each reaction uses | yes |
| `assets/hitl/` | reaction schemes shown to the chemists | yes |
| `hitl_bench/forms/live/<chemist>__*.json` | **the chemists' answers** — written by the page | no: back these up |
| `data/excel_files/hitl_*.xlsx`, `data/domains/hitl_*` | the same campaigns as REACTO projects | no |

The chemists' files are the study. Back `hitl_bench/forms/live/` up daily
(a cron `tar` to somewhere outside the VM is enough) and copy it home before
the VM is ever rebuilt. `python -m hitl_bench.scripts.collect_live` turns the
folder into two CSV tables at any time.

## Run it

Python 3.11, then from the repository root on the `hitl-bench` branch:

    python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
    pip install -r requirements.txt                   # drop pywin32 / pywinpty lines on Linux
    PORT=8088 python deploy/serve.py

`deploy/serve.py` runs the app under waitress: **one process**, eight threads.
Keep it one process — the live page's locks (one tick per campaign, one live
optimiser run at a time on the whole server) live in process memory. Do not
use `gunicorn -w 4` or similar.

The first live optimiser step after a chemist proposes a point takes about ten
seconds and up to two gigabytes of RAM; give the VM at least 4 GB. Replayed
steps cost nothing.

HTTPS: `deploy/nginx-reacto.conf` is the site as installed on fsc-cloud163, with the
certificate SEGI issued in `/etc/nginx/ssl/`; `deploy/reacto.service` keeps the app
running; `deploy/backup.sh` in cron copies the chemists' files nightly. Certbot does
not work there (port 80 is closed to the public internet).

## Before the link goes out

- Open `/hitl-live`, enter a test name, run one campaign through an alert,
  then delete the test files (`hitl_bench/forms/live/<name>__*.json`,
  `data/excel_files/hitl_<name>_*.xlsx`, `data/domains/hitl_<name>_*`).
- Do not change `assignment.json`, the grids or the page while the study runs:
  every participant must see the same thing.
- The Resume list shows every participant's name to every visitor. Ask the
  chemists for initials, not full names, if that matters.

# Desktop build notes

This document describes how the REACTO desktop app is packaged with PyInstaller +
pywebview, what was done to make it run fully offline, and the known limitations
of the resulting executable.

## How to build

```powershell
# from the repo root, with the project venv active
pip install pyinstaller pywebview
pyinstaller --noconfirm --clean reacto.spec
# result: dist\REACTO\REACTO.exe
```

`reacto.spec` ships with `DEBUG_CONSOLE = False` (windowed). Flip it to `True`
while iterating so a console window stays attached and Python tracebacks
remain visible.

The source-mode launches are unchanged:

- `python app.py` — Flask dev server on `0.0.0.0:8088` (VM / gunicorn deployment).
- `python desktop.py` — desktop window (same code path the frozen exe uses).

## Architecture

- `app.py` builds the `dash.Dash` instance and exposes `server` (Flask). It is
  imported by both `desktop.py` and the gunicorn entry point — the desktop build
  does not duplicate any layout or callback wiring.
- `desktop.py` picks a free port on `127.0.0.1`, starts the Flask server in a
  daemon thread (`debug=False`, `use_reloader=False`), waits for the socket to
  accept, then opens a pywebview window pointed at the local URL.
- `reacto.spec` is a one-directory (`onedir`) build. Onefile was rejected because
  unpacking the entire bundle on every launch was slow and caused intermittent
  AV / SmartScreen prompts.

## PyInstaller path resolution

PyInstaller unpacks bundled data files under `sys._MEIPASS`. Dash, on the other
hand, resolves `assets_folder` and `pages_folder` relative to the `__main__`
module's source file by default — which inside a frozen build no longer points
anywhere meaningful, leaving pages and assets unreachable (the usual symptom is
a blank page after launch).

`app.py` defines:

```python
def resource_path(relative_path: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)
```

…and passes `assets_folder=resource_path("assets")` and
`pages_folder=resource_path("pages")` explicitly to `dash.Dash(...)`.

## Network audit

Hard requirement: zero outbound traffic at runtime. The full audit:

1. **`external_stylesheets=[dbc.icons.BOOTSTRAP]`** loaded
   `https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css`
   on every page load. Removed the external stylesheet; bundled
   `bootstrap-icons.css` plus the woff and woff2 fonts under
   `assets/bootstrap-icons/` (Dash auto-serves anything under `assets/`).
2. **`@import url(https://fonts.googleapis.com/css2?family=Open+Sans...)`** in
   `assets/bootstrap.min(6).css` (Bootswatch) silently fetched Open Sans from
   Google. Stripped the `@import` line. The browser falls back to the next
   font in the `font-family` stack (`-apple-system, BlinkMacSystemFont,
   "Segoe UI"`, etc.), which all ship with Windows / macOS.
3. **`serve_locally=True`** is set on the `dash.Dash` constructor so Dash and
   Plotly serve their JS bundles from the Flask app instead of the unpkg CDN.
4. **No `requests` / `httpx` / `urllib` / `urlopen` / `socket.connect` calls**
   in the project's own Python code — verified by grep across all `*.py`. The
   only `https://` literal left in the source is a `doi.org` hyperlink in
   `components/layout_sensitivity.py` rendered as `href=...`, which is a link
   the user can click but not an automatic request.
5. **`utils/online_analysis.py`** — only reads local files (`open(filepath)`),
   no network. Despite the name, "online" here means streaming results from
   an experimental setup writing a local results file, not network polling.
6. **`utils/descriptor_data.py`** — pure dict / numpy lookups against the
   auto-generated `bofire_solvent_descriptors.py` and
   `bofire_base_descriptors.py` modules (both bundled). No I/O.
7. **`utils/descriptor_calculator.py`** — does not exist in this repo; the
   only descriptor-related module is `utils/descriptor_data.py` (audited above).
8. **No `torch.hub` / `from_pretrained` / `load_state_dict_from_url`** in the
   codebase — confirmed by grep. Torch and BoFire do not download anything at
   import time in our usage path.
9. **No update checks or telemetry** in the imported packages we exercise
   (Dash, BoFire, Plotly all default to local serving and have no opt-out
   needed in this configuration).

After all of the above, opening the served `/` page and inspecting the HTML
shows no `cdn.jsdelivr`, no `fonts.googleapis`, no `unpkg`, no `cloudflare` —
only `http://127.0.0.1:<port>/...` references plus inline data-URI SVGs (the
`xmlns="http://www.w3.org/2000/svg"` strings inside `url(data:image/svg+xml,...)`
are SVG namespace identifiers, not network requests).

## hiddenimports added

`reacto.spec` calls `collect_all` on each heavy scientific package because
PyInstaller's static analysis misses dynamic imports and data files. The full
list is in `HEAVY_PACKAGES` in the spec; the entries discovered while iterating
on the build (the ones not obvious from a "package the app" first pass) are:

- **`cvxpy` / `osqp` / `clarabel` / `scs`** — CVXPY's solver stack ships native
  algebra backends (.pyd extensions) that PyInstaller doesn't bundle without
  `collect_all`. Without these, `cvxpy` logs
  `RuntimeError: No algebra backend available!` on the first import. CVXPY is
  pulled in transitively by BoFire / entmoot for constrained acquisition
  function optimization. We do not depend on `ecos` (not installed in the
  current venv), so it is intentionally absent.
- **`pyro` (pyro-ppl)** — BoTorch fully-Bayesian models use Pyro internally;
  it loads NUTS / HMC samplers via lazy imports that PyInstaller misses.
- **`formulaic` / `sympy` / `networkx` / `joblib` / `threadpoolctl`** — pulled
  in by scikit-learn, pandas, and CVXPY at runtime through string-based
  imports the static analyzer cannot follow.

For our own local packages (`callbacks`, `components`, `utils`) we discovered
that `collect_submodules("pages")` returns `pages.Opt-results` — a name that
is not a legal Python import (Python module names cannot contain hyphens).
Putting that non-importable name into `hiddenimports` confuses PyInstaller's
modulegraph enough that it silently drops *adjacent* component modules
(`components.layout_opti_results` and `components.layout_sensitivity` were
both missing from the first build's PYZ even though they were listed in the
collected hiddenimports). The fix in the spec:

1. A local `_enumerate_local_submodules` helper walks `callbacks`,
   `components`, `utils` with `pkgutil.walk_packages` and filters out any
   dotted name with a non-`isidentifier()` part.
2. The `pages` package is no longer in the hiddenimports loop — its `.py`
   files are bundled as data, and Dash imports them by file path at runtime
   via `importlib.util.spec_from_file_location`.
3. `components/`, `callbacks/`, and `utils/` are *also* bundled as on-disk
   data directories alongside being in the PYZ. This is belt-and-suspenders:
   if a future change drops something from the PYZ, importlib can still
   resolve it through the bundled directory tree.

## Verification — runtime is offline

After the build, the running exe was probed with a vanilla `urllib` client
(no firewall change required for this static check):

- `GET /` returns 200, body contains only one external URL pattern:
  `http://127.0.0.1:<port>/...`. No `cdn.jsdelivr`, no `fonts.googleapis`,
  no `unpkg`.
- `/_dash-layout` returns 200 with the page tree serialized — every page
  registered.
- Every page route (`/Optimization_home`, `/About`, `/Opt-results`,
  `/Sensitivity`, `/Tutorial`) returns 200.
- `assets/bootstrap-icons/bootstrap-icons.css` returns 200; the woff2 font
  loads from `assets/bootstrap-icons/fonts/`.
- The Flask access log shows zero outbound requests — every served URL is
  `127.0.0.1:<port>/...`.

To verify with an actually-disabled NIC, run the exe with the network
adapter off; the UI should still render identically.

## Known limitations

- **The exe is unsigned.** Windows SmartScreen and enterprise AppLocker /
  WDAC policies may block first-launch. Sign with a code-signing certificate
  before distributing to customers.
- **`gurobipy` is intentionally excluded from the bundle.** Our optimization
  paths (`SoboStrategy` / `MoboStrategy` / `RandomStrategy` plus the direct
  BoTorch bypasses in `utils/bofire_optimization.py`) never select Gurobi.
  CVXPY probes for it inside `try/except ImportError` blocks and transparently
  falls through to CLARABEL / OSQP / SCS / SCIPY (all of which we bundle).
  The exclude makes that contract explicit and prevents a dev machine that
  happens to have Gurobi installed from accidentally shipping the DLL — which
  would otherwise raise opaque license errors on end-user machines.
- **First launch is slow** (a few seconds) while PyInstaller's bootloader
  unpacks the bundle to a temp directory and Python imports torch + bofire.
- **AV false positives.** Unsigned PyInstaller bundles occasionally trip
  heuristic AV engines. Signing the exe is the fix.

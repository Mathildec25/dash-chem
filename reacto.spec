# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the REACTO desktop build.

Builds a one-directory app launched by ``desktop.py``. Heavy scientific
dependencies (bofire / botorch / gpytorch / linear_operator / rdkit / mordred /
sklearn / scipy / plotly / dash / pydantic / torch) are collected via
``collect_all`` because they pull data files and lazily-imported submodules that
PyInstaller's static analysis misses.

Toggle ``DEBUG_CONSOLE`` for development: keep a console so Python tracebacks are
visible. Set to ``False`` once the build is stable to ship a windowed app.
"""

import os
import pkgutil

from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files


def _enumerate_local_submodules(pkg_dir: str, package_name: str) -> list[str]:
    """List sub-modules of a local package, skipping names Python can't import.

    Dash discovers pages via ``importlib.util.spec_from_file_location`` on
    ``.py`` files, so a hyphenated file like ``Opt-results.py`` can sit in the
    pages folder. ``collect_submodules`` returns ``pages.Opt-results`` which
    is not a legal Python import path — passing it through ``hiddenimports``
    confuses PyInstaller's modulegraph (it silently drops adjacent modules).
    We filter those out and only include importable dotted names.
    """
    names: list[str] = [package_name]
    for _finder, name, _is_pkg in pkgutil.walk_packages([pkg_dir], prefix=package_name + "."):
        if all(part.isidentifier() for part in name.split(".")):
            names.append(name)
    return names

# Flip to True during iteration so Python tracebacks land in a visible console
# window. The shipped (windowed) build keeps this False.
DEBUG_CONSOLE = False

# Packages where collect_all is appropriate (data + submodules + binaries).
HEAVY_PACKAGES = [
    "bofire",
    "botorch",
    "gpytorch",
    "linear_operator",
    "rdkit",
    "mordred",
    "sklearn",
    "scipy",
    "plotly",
    "dash",
    "dash_bootstrap_components",
    "pydantic",
    "torch",
    # transitive but dynamic-import-heavy:
    "pyro",
    "formulaic",
    "sympy",
    "networkx",
    "joblib",
    "threadpoolctl",
    "flask",
    # CVXPY solver stack — OSQP/clarabel/scs each ship native algebra
    # backends as .pyd extension modules that PyInstaller misses without
    # collect_all. Without these, cvxpy logs
    # "RuntimeError: No algebra backend available!" at import time.
    "cvxpy",
    "osqp",
    "clarabel",
    "scs",
]

datas = []
binaries = []
hiddenimports = []

for pkg in HEAVY_PACKAGES:
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# Force every callback / component / utils submodule to be packaged. Dash
# discovers pages via importlib at runtime; without explicit hiddenimports the
# component layouts they pull in are dropped from the bundle (PyInstaller's
# modulegraph does not trace the dynamically-imported page files).
#
# We avoid ``collect_submodules("pages")`` because pages contain hyphenated
# files (e.g. Opt-results.py) and the resulting non-importable name corrupts
# PyInstaller's modulegraph — see _enumerate_local_submodules for the
# workaround. Pages themselves are shipped as data (Dash loads them by file
# path), not as importable modules.
for pkg_name in ("callbacks", "components", "utils"):
    hiddenimports += _enumerate_local_submodules(pkg_name, pkg_name)

# Repo-level data: assets/, pages/, components/, callbacks/, utils/, the
# auto-generated descriptor modules, and the loose .py files referenced
# indirectly. The local-package directories are bundled as data too so
# importlib can resolve them from disk even if a submodule slipped through
# hiddenimports.
datas += [
    ("assets", "assets"),
    ("pages", "pages"),
    ("components", "components"),
    ("callbacks", "callbacks"),
    ("utils", "utils"),
    ("bofire_solvent_descriptors.py", "."),
    ("bofire_base_descriptors.py", "."),
]

# Dev-only / unused at runtime — strip to cut bundle size.
# gurobipy is excluded because it is a commercial solver that needs a license
# at runtime. Our optimization paths (SoboStrategy / MoboStrategy / RandomStrategy
# plus direct BoTorch bypasses) never select it; CVXPY probes for it via
# try/except ImportError and falls through to CLARABEL / OSQP / SCS / SCIPY.
# Bundling it would either tempt PyInstaller to ship a 100+MB DLL on dev
# machines that happen to have a license, or raise opaque license errors at
# runtime on end-user machines.
EXCLUDES = [
    "gurobipy",
    "jupyter",
    "jupyterlab",
    "jupyter_server",
    "jupyter_client",
    "jupyter_core",
    "jupyter_events",
    "jupyter_lsp",
    "jupyterlab_server",
    "jupyterlab_pygments",
    "jupyterlab_widgets",
    "notebook",
    "notebook_shim",
    "nbconvert",
    "nbformat",
    "nbclient",
    "ipykernel",
    "ipython",
    "IPython",
    "ipywidgets",
    "widgetsnbextension",
    "qtconsole",
    "mkdocs",
    "mkdocs_material",
    "mkdocstrings",
    "mkdocs_jupyter",
    "mike",
    "papermill",
    "jupytext",
    "tornado",
    "pytest",
    "coverage",
    "babel",
    "matplotlib.tests",
    "scipy.tests",
    "sklearn.tests",
    "torch.test",
]

block_cipher = None

a = Analysis(
    ["desktop.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="REACTO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=DEBUG_CONSOLE,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="REACTO",
)

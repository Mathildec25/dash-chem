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

from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

DEBUG_CONSOLE = True

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
]

datas = []
binaries = []
hiddenimports = []

for pkg in HEAVY_PACKAGES:
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# Force every callback / component / page submodule to be packaged. Dash discovers
# them via the registry at import time, so missing one shows as a blank page.
for pkg in ("callbacks", "components", "pages", "utils"):
    hiddenimports += collect_submodules(pkg)

# Repo-level data: assets/, pages/, the optional public/ketcher tree, the
# auto-generated descriptor modules, and the loose .py files referenced indirectly.
datas += [
    ("assets", "assets"),
    ("pages", "pages"),
    ("bofire_solvent_descriptors.py", "."),
    ("bofire_base_descriptors.py", "."),
]

# The Ketcher static tree is optional — only bundle it if it actually exists.
import os
_KETCHER_DIR = os.path.join("public", "ketcher")
if os.path.isdir(_KETCHER_DIR):
    datas.append((_KETCHER_DIR, "public/ketcher"))

# Dev-only / unused at runtime — strip to cut bundle size.
EXCLUDES = [
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

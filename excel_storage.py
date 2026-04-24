"""Upload and tracking helpers for Excel project files."""

import os

import dash_bootstrap_components as dbc
import pandas as pd

from config_path import EXCEL_FOLDER, EXCLUDED_FILES, TRACKING_FILE
from utils.safe_excel import safe_excel_read, safe_excel_save


VALID_EXTENSIONS = (".xlsx", ".xls", ".csv")
EXCEL_ONLY_EXTENSIONS = (".xlsx", ".xls")


def get_existing_files():
    """Return all supported files in EXCEL_FOLDER, filtering out tracking files."""
    if not os.path.exists(EXCEL_FOLDER):
        os.makedirs(EXCEL_FOLDER, exist_ok=True)
        return []

    return [
        f for f in os.listdir(EXCEL_FOLDER)
        if f.lower().endswith(VALID_EXTENSIONS)
        and f not in EXCLUDED_FILES
        and os.path.isfile(os.path.join(EXCEL_FOLDER, f))
    ]


def get_uploaded_excel_files():
    """Return Excel filenames recorded in the tracking file, with disk fallback."""
    try:
        if os.path.exists(TRACKING_FILE):
            df, _ = safe_excel_read(TRACKING_FILE)
            if df is not None and "filename" in df.columns:
                return df["filename"][
                    df["filename"].str.lower().str.endswith(EXCEL_ONLY_EXTENSIONS)
                    & ~df["filename"].isin(EXCLUDED_FILES)
                ].tolist()
    except Exception as e:
        print(f"Error reading tracking file: {e}")

    return [f for f in get_existing_files() if f.lower().endswith(EXCEL_ONLY_EXTENSIONS)]


def update_tracking_file(filename):
    """Append ``filename`` to the tracking file if it is a new, supported file."""
    if filename in EXCLUDED_FILES:
        return dbc.Alert(
            f"Skipping tracking file: {filename}",
            color="info", is_open=True, duration=4000,
        )

    if not filename.lower().endswith(VALID_EXTENSIONS):
        return dbc.Alert(
            f"Skipping unsupported file type: {filename}",
            color="warning", is_open=True, duration=4000,
        )

    try:
        os.makedirs(EXCEL_FOLDER, exist_ok=True)

        if os.path.exists(TRACKING_FILE):
            df, _ = safe_excel_read(TRACKING_FILE)
            if df is None:
                df = pd.DataFrame(columns=["filename"])
        else:
            df = pd.DataFrame(columns=["filename"])

        if filename not in df["filename"].values:
            df = pd.concat([df, pd.DataFrame([{"filename": filename}])], ignore_index=True)
            safe_excel_save(
                TRACKING_FILE,
                lambda p: df.to_excel(p, index=False, engine="openpyxl"),
            )

        return None
    except Exception as e:
        return dbc.Alert(
            f"Failed to update tracking: {e}",
            color="danger", is_open=True, duration=4000,
        )


def get_excel_dropdown_options():
    """Return ``{label, value}`` options for all tracked Excel files."""
    return [{"label": f, "value": f} for f in get_uploaded_excel_files()]

"""Filesystem paths and constants used across the application."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXCEL_FOLDER = os.path.join(DATA_DIR, "excel_files")
DOMAIN_FOLDER = os.path.join(DATA_DIR, "domains")

TRACKING_FILENAME = "project_tracking.xlsx"
DOMAIN_TRACKING_FILENAME = "domain_tracking.xlsx"

TRACKING_FILE = os.path.join(DATA_DIR, TRACKING_FILENAME)
DOMAIN_TRACKING_FILE = os.path.join(DATA_DIR, DOMAIN_TRACKING_FILENAME)

EXCLUDED_FILES = [
    TRACKING_FILENAME,
    DOMAIN_TRACKING_FILENAME,
    ".gitkeep",
    "Thumbs.db",
    ".DS_Store",
]

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXCEL_FOLDER, exist_ok=True)
os.makedirs(DOMAIN_FOLDER, exist_ok=True)

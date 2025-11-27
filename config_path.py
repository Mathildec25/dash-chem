"""
Configuration paths for the application
"""

import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data directories
DATA_DIR = os.path.join(BASE_DIR, 'data')
EXCEL_FOLDER = os.path.join(DATA_DIR, 'excel_files')
DOMAIN_FOLDER = os.path.join(DATA_DIR, 'domains')

# Tracking filenames
TRACKING_FILENAME = 'project_tracking.xlsx'
DOMAIN_TRACKING_FILENAME = 'domain_tracking.xlsx'

# Full paths to tracking files
TRACKING_FILE = os.path.join(DATA_DIR, TRACKING_FILENAME)
DOMAIN_TRACKING_FILE = os.path.join(DATA_DIR, DOMAIN_TRACKING_FILENAME)

# Files to exclude from project lists
EXCLUDED_FILES = [TRACKING_FILENAME, DOMAIN_TRACKING_FILENAME, '.gitkeep', 'Thumbs.db', '.DS_Store']

# Create directories if they don't exist
os.makedirs(EXCEL_FOLDER, exist_ok=True)
os.makedirs(DOMAIN_FOLDER, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
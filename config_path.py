import os

## DEFINING SAVING FILES ##

#r"C:\Users\ThBrHu\Dev\dash-chem"
# "/root/dash-chem-main"

# Base save folder
ROOT_FOLDER = r"/root/dash-chem-main"  ###### TO BE CHANGED BEFORE DEPLOYMENT #####


EXCEL_FOLDER = r"/root/dash-chem-main/excels"
os.makedirs(EXCEL_FOLDER, exist_ok=True)

# Excel tracking file
TRACKING_FILE = os.path.join(EXCEL_FOLDER, "Excel_names.xlsx")
TRACKING_FILENAME = os.path.basename(TRACKING_FILE)

# Domain folder and tracking
DOMAIN_FOLDER = os.path.join(ROOT_FOLDER, "domains")
os.makedirs(DOMAIN_FOLDER, exist_ok=True)

DOMAIN_TRACKING_FILE = os.path.join(EXCEL_FOLDER, "domain_tracking.xlsx")
DOMAIN_TRACKING_FILENAME = os.path.basename(DOMAIN_TRACKING_FILE)

# Files to exclude from dropdowns
EXCLUDED_FILES = {TRACKING_FILENAME, DOMAIN_TRACKING_FILENAME}

# ============================================
# OPTIMIZATION SETTINGS
# ============================================

# Default sampling settings
DEFAULT_SAMPLING_METHOD = "latin_hypercube"
DEFAULT_SAMPLING_POINTS = 10

# Column type colors for Excel and table display
COLUMN_COLORS = {
    "extra": "#6C757D",      # Gray
    "parameter": "#007BFF",   # Blue  
    "objective": "#28A745",   # Green
    "unknown": "#DDDDDD"      # Light gray
}

# Sampling methods mapping
SAMPLING_METHODS = {
    "none": None,
    "random": "UNIFORM",
    "latin_hypercube": "LHS",
    "sobol": "SOBOL"
}

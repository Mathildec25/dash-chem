# Global imports (libraries)

print("=" * 60)
print("DÉMARRAGE APP - app.py")
print("=" * 60)

import sys
print(f"Modules au démarrage: {len(sys.modules)}")

from utils.BoFire import create_bofire_domain_from_store  # Import tôt!


import dash 
import dash._utils
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, dash_table, State
from dash.dash_table.Format import Format
import pandas as pd
import os
from flask import send_from_directory

# Local imports (modules)
from callbacks.app_callbacks import register_app_callbacks    
from callbacks.opti_home_callbacks import new_proj_callbacks, already_created_callbacks
from callbacks.opti_param_callbacks import parameter_part, domain_creation, solvents_callbacks, base_callbacks
from callbacks.opti_run_callbacks import run_optimization
from callbacks.opti_results_callbacks import results_analysis
from components.sidebar import generate_sidebar 
from callbacks import advanced_bo_callbacks

# Initialisation of the Dash app 
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.icons.BOOTSTRAP],
    use_pages=True,                     # Specific architecture for multi-page apps (each file in pages is a page on the app)            
    suppress_callback_exceptions=True,   # Allows to imbricate callbacks (Output of one callback in the Input of another)
)


server = app.server

@server.route("/ketcher/<path:filename>")
def serve_ketcher(filename):
    return send_from_directory(os.path.join("public", "ketcher"), filename)

# Create sidebar from function in sidebar.py
sidebar = generate_sidebar()

register_app_callbacks(app)

# Define the layout of the app
app.layout = html.Div([
    dcc.Store(id="selected-excel-store", storage_type='session'),
    dcc.Store(id="selected-sheet-store", storage_type='session'),
    dcc.Store(id='parameter-store', data=[], storage_type="session"),       # Store parameters info for BO part 
    dcc.Store(id='objective-store', data=[], storage_type="session"),       # Store objectives info for BO part
    dcc.Store(id="extra-columns-store", data=[], storage_type="session"),   # Store extre-columns info for BO part
    dcc.Store(id='project-name-store', storage_type='session'),             # Store component to save the project name on BO part
    dcc.Store(id='selected-file-store', storage_type='session'),            # Store file selected to restrat opti
    dcc.Store(id="current-excel-file", storage_type='session'),             # Store file created to start BO
    dcc.Store(id="current-domain", storage_type='session'),                 # Store the domain of the current BO process
    dcc.Location(id="url", refresh="callback-nav"),
    sidebar,  # Fixed + hover-based sidebar
    html.Div(
        id="main-content",
        className="main-content",
        children=[dash.page_container],  # Will render content of the current page
        style={
            "marginLeft": "68px",
        }
    )
])



# Launch the app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8088, debug=True) # Allow to update the app without restarting it (debug mode)
  

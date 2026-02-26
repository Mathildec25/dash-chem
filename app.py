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
from callbacks.opti_param_callbacks import parameter_part, domain_creation, solvents_callbacks, base_callbacks, constraints_callbacks
from callbacks.opti_run_callbacks import run_optimization
from callbacks.opti_results_callbacks import results_analysis
from components.sidebar import generate_sidebar 
from callbacks import advanced_bo_callbacks
from callbacks import sensitivity_callbacks

# Initialisation of the Dash app 
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.icons.BOOTSTRAP],
    use_pages=True,
    suppress_callback_exceptions=True,
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
    dcc.Store(id='parameter-store', data=[], storage_type="session"),
    dcc.Store(id='objective-store', data=[], storage_type="session"),
    dcc.Store(id="extra-columns-store", data=[], storage_type="session"),
    dcc.Store(id='project-name-store', storage_type='session'),
    dcc.Store(id='constraints-store', data=None, storage_type="session"),  # NEW: Store for boiling point constraints
    dcc.Store(id='selected-file-store', storage_type='session'),
    dcc.Store(id="current-excel-file", storage_type='session'),
    dcc.Store(id="current-domain", storage_type='session'),
    dcc.Location(id="url", refresh="callback-nav"),
    sidebar,
    html.Div(
        id="main-content",
        className="main-content",
        children=[dash.page_container],
        style={
            "marginLeft": "68px",
        }
    )
])


# Launch the app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8088, debug=True)
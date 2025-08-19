# Global imports (libraries)
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
from callbacks.opti_param_callbacks import reactant_part, parameter_part, objective_part, other_column_part, sampling_part
from callbacks.opti_run_callbacks import run_part, visualization_part
from components.sidebar import generate_sidebar 
from callbacks import table_callbacks, visu_callbacks, carac_callbacks, home_callbacks

# Initialisation of the Dash app 
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.icons.BOOTSTRAP],
    use_pages=True,                     # Specific architecture for multi-page apps (each file in pages is a page on the app)            
    suppress_callback_exceptions=True,   # Allows to imbricate callbacks (Output of one callback in the Input of another)
)

# ??? (Create the server???)
server = app.server

@server.route("/ketcher/<path:filename>")
def serve_ketcher(filename):
    return send_from_directory(os.path.join("public", "ketcher"), filename)

# Create sidebar from function in sidebar.py
sidebar = generate_sidebar()

# ??? (importing callbacks from other files???)
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
    dcc.Location(id="url", refresh=False),
    sidebar,  # Fixed + hover-based sidebar
    html.Div(
        id="main-content",
        className="main-content",
        children=[dash.page_container],  # Will render content of the current page
        style={
            "margin-left": "68px",
        }
    )
])

### If reacatant drawing is used ####

# ## Like callbacks for js part (drawing mole part)
# app.clientside_callback(
#     """
#     function(n_clicks, current_store) {
#         console.log("Clicked button. n_clicks =", n_clicks);

#         if (!n_clicks) {
#             return window.dash_clientside.no_update;
#         }

#         const smiles = localStorage.getItem("ketcher_latest_smiles");
#         console.log("Collected from localStorage:", smiles);

#         if (!smiles) {
#             return window.dash_clientside.no_update;
#         }

#         localStorage.removeItem("ketcher_latest_smiles");

#         let updated_store = {};

#         if (current_store && typeof current_store === 'object') {
#             updated_store = { ...current_store };
#         }

#         const nextIndex = Object.keys(updated_store).length + 1;
#         updated_store["Reactant" + nextIndex] = [smiles];

#         console.log("Returning updated store:", updated_store);

#         return updated_store;
#     }
#     """,
#     Output("smiles-store", "data"),
#     Input("collect-smiles-btn", "n_clicks"),
#     State("smiles-store", "data"),
#     prevent_initial_call=True
# )

# Launch the app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True) # Allow to update the app without restarting it (debug mode)
  

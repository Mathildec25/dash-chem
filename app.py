# Global imports (libraries)
import dash 
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, dash_table, State
from dash.dash_table.Format import Format
import pandas as pd

# Local imports (modules)
from callbacks.app_callbacks import register_app_callbacks    
from components.sidebar import generate_sidebar 
from callbacks import table_callbacks, graph_callbacks

# Initialisation of the Dash app 
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.icons.BOOTSTRAP],
    use_pages=True,                     # Specific architecture for multi-page apps (each file in pages is a page on the app)            
    suppress_callback_exceptions=True   # Allows to imbricate callbacks (Output of one callback in the Input of another)
)

# ??? (Create the server???)
server = app.server

# Gather excel file name and sheet names
excel_file = "results.xlsx"
sheets_names = pd.ExcelFile(excel_file).sheet_names  # Sheets names

# Create sidebar from function in sidebar.py
sidebar = generate_sidebar(sheets_names)

# ??? (importing callbacks from other files???)
register_app_callbacks(app)


# Define the layout of the app
app.layout = dbc.Container([
    dcc.Store(id="selected-sheet-store", storage_type='session'),     # Store the selected sheet name in session storage to share it with other python files/pages
    dcc.Location(id="url"),                                           # Used to keep track of the current URL
    dbc.Row(id="main-row", children=[
        dbc.Col(                                                       
            id="sidebar-col",
            children=[sidebar],
            width='auto', 
        ),
        dbc.Col(
            children=[
                html.Div([
                    dbc.Button(className = "bi bi-list", id="toggle-btn", n_clicks=0)
                ], style={"marginTop": "6px", "marginBottom": "0px"}),
                dash.page_container         # This is where the content of the selected page will be displayed
            ],
            width=True 
        )
    ], style={
        "display": "flex",
        "flex-wrap": "nowrap",
        "height": "100vh",
        "margin-right": "12rem" 
    })
], fluid=True) 

# Launch the app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True) # Allow to update the app without restarting it (debug mode)
  

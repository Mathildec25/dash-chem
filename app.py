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

app.layout = html.Div([
    dcc.Store(id="selected-sheet-store", storage_type='session'),
    dcc.Location(id="url"),
    sidebar,  # Fixed + hover-based sidebar
    html.Div(
        id="main-content",
        className="main-content",
        children=[dash.page_container],  # Will render content of the current page
        style={
            "margin-left": "85px",
        }
    )
])


# Launch the app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True) # Allow to update the app without restarting it (debug mode)
  

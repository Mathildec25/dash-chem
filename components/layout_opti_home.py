import dash_bootstrap_components as dbc
from dash import dcc, html

# This function creates the layout for the dashboard page 
def create_opti_home_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Location(id="url"),
                html.H2("Optimization Home", className="display-4", style={"textAlign": "center","marginTop":"5px", "marginBottom": "20px"}),
            ], width=12),
        ]),
    ])
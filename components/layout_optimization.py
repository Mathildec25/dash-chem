import dash_bootstrap_components as dbc
from dash import dcc, html

# This function creates the layout for the dashboard page 
def create_optimization_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Coming soon", className="display-6", style={"fontSize":"100px","textAlign": "center", "marginBottom": "35px",  "marginTop": "8px"}),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="bi bi-cone-striped", style={"font-size": "15rem", "color":"orange","textAlign": "center"}),
                    html.I(className="bi bi-cone-striped", style={"font-size": "15rem", "color":"orange","textAlign": "center"}),
                ], style={"display": "flex", "justifyContent": "center"})
            ], width=12),
        ]),
    ])

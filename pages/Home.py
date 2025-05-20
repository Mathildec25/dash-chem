import dash
import dash_bootstrap_components as dbc
from dash import dcc, html


# Include this file as a page in the Dash app
dash.register_page(__name__, name="Home", path="/", order=1)

# Define the layout of the page using the function from layout_display.py
layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Select a sheet", className="display-2", style={"textAlign": "center", "marginTop":"200px"}),
            ], width=12),
        ]),
])
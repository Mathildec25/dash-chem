import dash
import dash_bootstrap_components as dbc
from dash import dcc, html


# Include this file as a page in the Dash app
dash.register_page(__name__, name="Home", path="/", order=1)

# Define the layout of the page using the function from layout_display.py
layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Welcome to MET", className="display-2", style={"textAlign": "center", "marginTop":"5px", "color": "#f96052"}),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="bi bi-arrow-down", 
                        style={"fontSize": "2.5rem", "marginRight": "8px", "marginTop":"5px", "color": "#f96052"}),
                    html.H4("Please select a sheet to work on from the sidebar", 
                        className="display-6", 
                        style={"marginTop": "5px", "color": "#ff9e3d", "display": "inline-block"}),
                    html.I(className="bi bi-arrow-down", 
                        style={"fontSize": "2.5rem", "marginLeft": "8px", "marginTop":"5px", "color": "#f96052"})  
                ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card(
                    color="gray", 
                    inverse=True,
                    style={"height": "480px", "marginTop":"5px"}, 
                    children=[
                        html.Div([
                            html.Video(
                                src="/assets/Select-a-sheet.mp4",
                                autoPlay=True,
                                loop=True,
                                style={"width": "90%", "height": "90%", "objectFit": "contain"} 
                            )
                        ], style={"display": "flex", "justifyContent": "center", "alignItems": "center", "height": "100%"}),
                    ]
                )
            ], width=12),
        ]),
])
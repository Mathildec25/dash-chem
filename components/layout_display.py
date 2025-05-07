import dash_bootstrap_components as dbc
from dash import dcc, html

def create_dashboard_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Display part", className="display-4", style={"textAlign": "center", "marginBottom": "35px"}),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Accordion([
                        dbc.AccordionItem([
                            dcc.Dropdown(
                                id="column-dropdown",
                                options=[],
                                value=[],
                                multi=True,
                                placeholder="Select columns to display",
                                style={"width": "100%"}
                            )
                        ], title="Select columns")
                    ], start_collapsed=True)
                ], style={"marginTop": "0px", "marginBottom": "9px"}),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div(id="main-content")
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Button("Add Row", id="editing-rows-button", n_clicks=0),
                    dbc.Button("Save Changes", id="save-button", n_clicks=0, style={"marginLeft": "10px"}),
                ], style={"padding": "15px"}),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.Hr(),
                html.H2("Visualization part", className="display-4", style={"textAlign": "center", "marginTop": "35px", "marginBottom": "35px"}),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(id="DD-x-axis-scatter", options=[], value=[], placeholder="Select x-axis", style={"width": "100%"}),
            ], width=6),
            dbc.Col([
                dcc.Dropdown(id="DD-y-axis-scatter", options=[], value=[], placeholder="Select y-axis", style={"width": "100%"}),
            ], width=6),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button("Generate Graph", id="generate-graph-button-scatter", n_clicks=0),
                dcc.Graph(id="Scatter_graph")
            ], width=12),
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(id="DD-x-axis-pie", options=[], value=[], placeholder="Select x-axis", style={"width": "100%"}),
            ], width=6),
            dbc.Col([
                dcc.Dropdown(id="DD-y-axis-pie", options=[], value=[], placeholder="Select y-axis", style={"width": "100%"}),
            ], width=6),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button("Generate Graph", id="generate-graph-button-pie", n_clicks=0),
                dcc.Graph(id="Pie_graph")
            ], width=12),
        ]),
    ])
    
    ### Test commit
    
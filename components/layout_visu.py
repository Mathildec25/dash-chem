import dash_bootstrap_components as dbc
from dash import dcc, html

# This function creates the layout for the dashboard page 
def create_visu_layout():
    return dbc.Container([
                dbc.Row([
                            dbc.Col([
                                dcc.Location(id="url"),
                                html.H2("Visualization part", className="display-4", style={"textAlign": "center", "marginTop": "35px", "marginBottom": "35px"}),
                            ], width=12),
                        ]),
                        # Dropdowns for scatter plot
                        dbc.Row([
                            dbc.Col([
                                dcc.Dropdown(id="DD-x-axis-scatter", options=[], placeholder="Select x-axis", style={"width": "100%"}),
                            ], width=4),
                            dbc.Col([
                                dcc.Dropdown(id="DD-y-axis-scatter", options=[], placeholder="Select y-axis", style={"width": "100%"}),
                            ], width=4),
                            dbc.Col([
                                dcc.Dropdown(id="DD-colors-scatter", options=[], placeholder="Select col for colors", style={"width": "100%"}),
                            ], width=4),
                        ]),
                        # Scatter plot
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    dbc.Button("Generate Scatter Graph", id="generate-graph-button-scatter", n_clicks=0),
                                ], style={"padding": "15px"}),
                                dcc.Graph(id="Scatter_graph")
                            ], width=12),
                        ]),
                        html.Hr(),
                        # Dropdowns for boxplots
                        dbc.Row([
                            dbc.Col([
                                dcc.Dropdown(id="DD-x-axis-box", options=[], placeholder="Select x-axis", style={"width": "100%"}),
                            ], width=6),
                            dbc.Col([
                                dcc.Dropdown(id="DD-y-axis-box", options=[], placeholder="Select y-axis", style={"width": "100%"}),
                            ], width=6),
                        ]),
                        # Boxplots
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    dbc.Button("Generate Boxplots", id="generate-graph-button-box", n_clicks=0),
                                ], style={"padding": "15px"}),    
                                dcc.Graph(id="Box_graph")
                            ], width=12),
                        ]),
                        html.Hr(),
                        # Dropdowns for 1D and 2D histograms
                        dbc.Row([   
                            dbc.Col([
                                dcc.Dropdown(id="DD-col-histo", options=[], placeholder="Select column", style={"width": "100%"}),
                            ], width=3,),
                            dbc.Col([
                                dcc.Dropdown(id="DD-col1-2Dhisto", options=[], placeholder="Select columns 1", style={"width": "100%"}),
                            ],width={"size": 3, "offset": 2}),
                            dbc.Col([
                                dcc.Dropdown(id="DD-col2-2Dhisto", options=[], placeholder="Select columns 2", style={"width": "100%"}),
                            ], width=3),
                        ]),
                        # 1D and 2D histograms
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    dbc.Button("Generate Histogram", id="generate-graph-button-histo", n_clicks=0),
                                ], style={"padding": "15px"}),
                                
                                dcc.Graph(id="Histo_graph")
                            ], width=5),
                            dbc.Col([
                                html.Div([
                                    dbc.Button("Generate 2D Histogram", id="generate-graph-button-2Dhisto", n_clicks=0),
                                ], style={"padding": "15px"}),
                                
                                dcc.Graph(id="2DHisto_graph")
                            ], width=7),
                        ]),
])
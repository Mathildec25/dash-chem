import dash_bootstrap_components as dbc
from dash import dcc, html

# This function creates the layout for the dashboard page 
def create_dashboard_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Display part", className="display-4", style={"textAlign": "center", "marginBottom": "35px"}),
            ], width=12),
        ]),
        # Allow to choose which columns to display in the table
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
        # Display the table with the selected columns
        dbc.Row([
            dbc.Col([
                html.Div(id="main-content")
            ], width=12),
        ]),
        # Buttons to add a row and save changes
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
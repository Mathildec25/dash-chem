import dash_bootstrap_components as dbc
from dash import dcc, html

# This function creates the layout for the dashboard page 
def create_visu_layout():
    return dbc.Container([
        # Header Section
        dbc.Row([
            dbc.Col([
                html.H1("Data Visualization Dashboard", 
                       className="text-center mb-2",
                       style={"color": "#2c3e50", "fontWeight": "bold"}),
                html.P("Explore your data through interactive visualizations",
                      className="text-center text-muted mb-4",
                      style={"fontSize": "18px"})
            ], width=12)
        ]),
        
        # Info Alert
        dbc.Alert([
            html.I(className="bi bi-info-circle-fill me-2"),
            html.Strong("How to use this page: "),
            "Select your data columns from the dropdowns and click 'Generate' to create visualizations. "
            "Example plots are shown by default to demonstrate capabilities.",
        ], color="info", className="mb-4"),
        
        # Scatter Plot Section
        dbc.Card([
            dbc.CardHeader([
                html.H4([
                    html.I(className="bi bi-graph-up me-2"),
                    "Scatter Plot"
                ], className="text-primary mb-0"),
                html.P("Visualize relationships between variables with optional color and size dimensions", 
                      className="text-muted mb-0 small mt-1")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("X-Axis *", html_for="DD-x-axis-scatter", className="fw-bold"),
                        dcc.Dropdown(
                            id="DD-x-axis-scatter", 
                            options=[], 
                            placeholder="Select x-axis variable",
                            className="mb-2"
                        ),
                    ], md=2),
                    dbc.Col([
                        dbc.Label("Y-Axis *", html_for="DD-y-axis-scatter", className="fw-bold"),
                        dcc.Dropdown(
                            id="DD-y-axis-scatter", 
                            options=[], 
                            placeholder="Select y-axis variable",
                            className="mb-2"
                        ),
                    ], md=2),
                    dbc.Col([
                        dbc.Label("Color By", html_for="DD-colors-scatter"),
                        dcc.Dropdown(
                            id="DD-colors-scatter", 
                            options=[], 
                            placeholder="Color points by... (optional)",
                            className="mb-2"
                        ),
                    ], md=2),
                    dbc.Col([
                        dbc.Label("Size By", html_for="DD-size-scatter"),
                        dcc.Dropdown(
                            id="DD-size-scatter", 
                            options=[], 
                            placeholder="Size points by... (optional)",
                            className="mb-2"
                        ),
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Hover Info", html_for="DD-hover-scatter"),
                        dcc.Dropdown(
                            id="DD-hover-scatter", 
                            options=[], 
                            placeholder="Show on hover... (optional)",
                            className="mb-2"
                        ),
                    ], md=3),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="bi bi-play-fill me-2"), "Generate Scatter Plot"],
                            id="generate-graph-button-scatter",
                            color="primary",
                            size="lg",
                            n_clicks=0,
                            className="w-100"
                        ),
                    ], md=3),
                    dbc.Col([
                        html.Small("* Required fields", className="text-muted mt-2 d-block")
                    ], md=9)
                ], className="mb-3"),
                dcc.Loading(
                    id="loading-scatter",
                    type="circle",
                    children=[dcc.Graph(id="Scatter_graph")]
                )
            ])
        ], className="mb-4 shadow-sm"),
        
        # Box Plot Section
        dbc.Card([
            dbc.CardHeader([
                html.H4([
                    html.I(className="bi bi-box me-2"),
                    "Box Plot"
                ], className="text-success mb-0"),
                html.P("Compare distributions across categories", 
                      className="text-muted mb-0 small mt-1")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Category (X-Axis) *", html_for="DD-x-axis-box", className="fw-bold"),
                        dcc.Dropdown(
                            id="DD-x-axis-box", 
                            options=[], 
                            placeholder="Select grouping variable",
                            className="mb-2"
                        ),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Values (Y-Axis) *", html_for="DD-y-axis-box", className="fw-bold"),
                        dcc.Dropdown(
                            id="DD-y-axis-box", 
                            options=[], 
                            placeholder="Select numeric variable",
                            className="mb-2"
                        ),
                    ], md=6),
                ], className="mb-3"),
                dbc.Button(
                    [html.I(className="bi bi-play-fill me-2"), "Generate Box Plot"],
                    id="generate-graph-button-box",
                    color="success",
                    size="lg",
                    n_clicks=0,
                    className="mb-3"
                ),
                dcc.Loading(
                    id="loading-box",
                    type="circle",
                    children=[dcc.Graph(id="Box_graph")]
                )
            ])
        ], className="mb-4 shadow-sm"),
        
        # Histograms Section
        dbc.Card([
            dbc.CardHeader([
                html.H4([
                    html.I(className="bi bi-bar-chart me-2"),
                    "Histograms"
                ], className="text-warning mb-0"),
                html.P("Analyze distributions and relationships", 
                      className="text-muted mb-0 small mt-1")
            ]),
            dbc.CardBody([
                dbc.Row([
                    # 1D Histogram
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Single Variable Distribution"),
                            dbc.CardBody([
                                dbc.Label("Select Column *", html_for="DD-col-histo", className="fw-bold"),
                                dcc.Dropdown(
                                    id="DD-col-histo", 
                                    options=[], 
                                    placeholder="Select column",
                                    className="mb-3"
                                ),
                                dbc.Button(
                                    [html.I(className="bi bi-play-fill me-2"), "Generate"],
                                    id="generate-graph-button-histo",
                                    color="warning",
                                    n_clicks=0,
                                    className="w-100 mb-3"
                                ),
                                dcc.Loading(
                                    id="loading-histo",
                                    type="circle",
                                    children=[dcc.Graph(id="Histo_graph")]
                                )
                            ])
                        ])
                    ], md=5),
                    
                  # 2D Histogram
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Two Variable Density"),
                            dbc.CardBody([
                                # Row with two dropdowns side-by-side
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("First Column *", html_for="DD-col1-2Dhisto", className="fw-bold"),
                                        dcc.Dropdown(
                                            id="DD-col1-2Dhisto",
                                            options=[],
                                            placeholder="Select first column",
                                            className="mb-2"
                                        ),
                                    ], md=6, sm=12),

                                    dbc.Col([
                                        dbc.Label("Second Column *", html_for="DD-col2-2Dhisto", className="fw-bold"),
                                        dcc.Dropdown(
                                            id="DD-col2-2Dhisto",
                                            options=[],
                                            placeholder="Select second column",
                                            className="mb-2"
                                        ),
                                    ], md=6, sm=12),
                                ], className="mb-2", align="center"),

                                # Generate button (full width)
                                dbc.Button(
                                    [html.I(className="bi bi-play-fill me-2"), "Generate"],
                                    id="generate-graph-button-2Dhisto",
                                    color="warning",
                                    n_clicks=0,
                                    className="w-100 mb-3"
                                ),

                                # Graph with loading spinner
                                dcc.Loading(
                                    id="loading-2dhisto",
                                    type="circle",
                                    children=[dcc.Graph(id="2DHisto_graph")]
                                )
                            ])
                        ])
                    ], md=7),
                ])
            ])
        ], className="mb-4 shadow-sm"),
        
        # Data Overview Section
        dbc.Card([
            dbc.CardHeader([
                html.H4([
                    html.I(className="bi bi-table me-2"),
                    "Data Overview"
                ], className="text-info mb-0"),
                html.P("Column statistics and unique value counts", 
                      className="text-muted mb-0 small mt-1")
            ]),
            dbc.CardBody([
                dcc.Loading(
                    id="loading-bar",
                    type="circle",
                    children=[dcc.Graph(id="Bar_graph")]
                )
            ])
        ], className="mb-4 shadow-sm"),
        
    ], fluid=True, style={"maxWidth": "1400px"})
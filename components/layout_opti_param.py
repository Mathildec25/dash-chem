import dash_bootstrap_components as dbc
from dash import dcc, html
import uuid

initial_id = str(uuid.uuid4())
initial_objective_id = str(uuid.uuid4())
initial_extra_col_id = str(uuid.uuid4())

def create_opti_param_layout():
    return dbc.Container([
        # Header with back button
        dbc.Row([
            dbc.Col([
                dcc.Link(
                    html.I(className="bi bi-arrow-left", style={"fontSize": "1.5rem", "color": "#6c757d"}),
                    href="/Opt-home",
                    style={"textDecoration": "none"}
                )
            ], width="auto"),
            dbc.Col([
                html.H1("Domain Configuration", 
                       style={
                           "color": "#1a1a1a", 
                           "fontWeight": "600",
                           "fontSize": "2rem",
                           "letterSpacing": "-0.02em",
                           "marginBottom": "0.25rem"
                       }),
                html.P("Define your optimization space parameters and objectives",
                      style={
                          "fontSize": "1rem",
                          "color": "#6c757d",
                          "marginBottom": "0"
                      })
            ], width=True)
        ], className="mb-4 align-items-center"),
        
        # Main card
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # Parameters Section
                    dbc.Col([
                        html.H5("Parameters", className="mb-3", style={"fontWeight": "600"}),
                        
                        # Parameter counter (read-only display)
                        html.Div([
                            html.Label("Number of Parameters", className="form-label text-muted small"),
                            html.Div(
                                id="param-count-display",
                                children="1",
                                style={
                                    "padding": "0.5rem 1rem",
                                    "backgroundColor": "#f8f9fa",
                                    "borderRadius": "8px",
                                    "fontWeight": "500",
                                    "marginBottom": "1rem"
                                }
                            )
                        ]),
                        
                        # Parameters container
                        html.Div(id="parameter-container", children=[
                            # Initial parameter
                            html.Div([
                                dbc.Input(
                                    id={'type': 'parameter-name', 'index': initial_id},
                                    placeholder="Parameter 1",
                                    className="mb-2",
                                    style={"borderRadius": "8px", "fontSize": "1rem"}
                                ),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Input(
                                            id={'type': 'parameter-type-specific-lower', 'index': initial_id},
                                            placeholder="Min",
                                            type="number",
                                            step="any",
                                            style={"borderRadius": "8px"}
                                        )
                                    ], width=6),
                                    dbc.Col([
                                        dbc.Input(
                                            id={'type': 'parameter-type-specific-upper', 'index': initial_id},
                                            placeholder="Max",
                                            type="number",
                                            step="any",
                                            style={"borderRadius": "8px"}
                                        )
                                    ], width=6)
                                ], className="mb-2"),
                                # Hidden type selector set to float by default
                                html.Div([
                                    dcc.Dropdown(
                                        id={'type': 'parameter-type', 'index': initial_id},
                                        options=[
                                            {"label": "Continuous", "value": "float"},
                                            {"label": "Discrete", "value": "int"},
                                            {"label": "Categorical", "value": "cat"},
                                        ],
                                        value="float",
                                        style={"display": "none"}
                                    )
                                ], id={'type': 'parameter-type-container', 'index': initial_id}),
                                html.Div(id={'type': 'parameter-type-specific-container', 'index': initial_id}),
                                html.Div(id={'type': 'parameter-block', 'index': initial_id}, style={"display": "none"})
                            ], className="mb-3", style={
                                "padding": "1rem",
                                "backgroundColor": "#f8f9fa",
                                "borderRadius": "8px"
                            })
                        ]),
                        
                        # Add parameter button
                        dbc.Button([
                            html.I(className="bi bi-plus me-2"),
                            "Add Parameter"
                        ],
                        id="add-para-button",
                        outline=True,
                        color="primary",
                        size="sm",
                        className="mb-3",
                        style={"borderRadius": "8px"}
                        ),
                    ], md=6, className="border-end pe-4"),
                    
                    # Objectives Section
                    dbc.Col([
                        html.H5("Objectives", className="mb-3", style={"fontWeight": "600"}),
                        
                        # Objective counter (read-only display)
                        html.Div([
                            html.Label("Number of Objectives", className="form-label text-muted small"),
                            html.Div(
                                id="objective-count-display",
                                children="1",
                                style={
                                    "padding": "0.5rem 1rem",
                                    "backgroundColor": "#f8f9fa",
                                    "borderRadius": "8px",
                                    "fontWeight": "500",
                                    "marginBottom": "1rem"
                                }
                            )
                        ]),
                        
                        # Objectives container
                        html.Div(id="objective-container", children=[
                            # Initial objective
                            html.Div([
                                dbc.Input(
                                    id={'type': 'objective-name', 'index': initial_objective_id},
                                    placeholder="Objective 1",
                                    className="mb-2",
                                    style={"borderRadius": "8px", "fontSize": "1rem"}
                                ),
                                dcc.Dropdown(
                                    id={'type': 'objective-direction', 'index': initial_objective_id},
                                    options=[
                                        {"label": "Minimize", "value": "min"},
                                        {"label": "Maximize", "value": "max"}
                                    ],
                                    placeholder="Select direction...",
                                    className="mb-2",
                                    style={"borderRadius": "8px"}
                                ),
                                html.Div(id={'type': 'objective-direction-container', 'index': initial_objective_id}, style={"display": "none"}),
                                html.Div(id={'type': 'objective-bounds-container', 'index': initial_objective_id}),
                                html.Div(id={'type': 'objective-block', 'index': initial_objective_id}, style={"display": "none"})
                            ], className="mb-3", style={
                                "padding": "1rem",
                                "backgroundColor": "#f8f9fa",
                                "borderRadius": "8px"
                            })
                        ]),
                        
                        # Add objective button
                        dbc.Button([
                            html.I(className="bi bi-plus me-2"),
                            "Add Objective"
                        ],
                        id="add-objective-button",
                        outline=True,
                        color="success",
                        size="sm",
                        className="mb-3",
                        style={"borderRadius": "8px"}
                        ),
                    ], md=6, className="ps-4"),
                ]),
                
                # Extra columns section (collapsible)
                html.Hr(className="my-4"),
                
                dbc.Collapse([
                    html.H5("Additional Columns (Optional)", className="mb-3", style={"fontWeight": "600"}),
                    html.Div(id="extra-column-container", children=[]),
                    dbc.Button([
                        html.I(className="bi bi-plus me-2"),
                        "Add Extra Column"
                    ],
                    id="add-extra-column-button",
                    outline=True,
                    color="secondary",
                    size="sm",
                    className="mb-3",
                    style={"borderRadius": "8px"}
                    ),
                ], id="extra-columns-collapse", is_open=False),
                
                dbc.Button([
                    html.I(className="bi bi-gear me-2"),
                    "Show Extra Columns"
                ],
                id="toggle-extra-columns",
                outline=True,
                color="secondary",
                size="sm",
                className="mb-3",
                style={"borderRadius": "8px"}
                ),
                
                # Sampling configuration
                html.Hr(className="my-4"),
                html.H5("Initial Sampling", className="mb-3", style={"fontWeight": "600"}),
                
                dbc.Row([
                    dbc.Col([
                        html.Label("Sampling Method", className="form-label"),
                        dcc.Dropdown(
                            id="starting-sampling-DD",
                            options=[
                                {"label": "None", "value": "none"},
                                {"label": "Random", "value": "random"},
                                {"label": "Latin Hypercube", "value": "latin_hypercube"},
                                {"label": "Sobol", "value": "sobol"},
                            ],
                            value="latin_hypercube",
                            style={"borderRadius": "8px"}
                        ),
                    ], md=6),
                    dbc.Col([
                        html.Label("Number of Points", className="form-label"),
                        dbc.Input(
                            id="nb-sampling-points",
                            type="number",
                            value=10,
                            min=1,
                            style={"borderRadius": "8px"}
                        ),
                    ], md=6)
                ], className="mb-4"),
                
                # Continue button
                dbc.Row([
                    dbc.Col([
                        dcc.Link(
                            dbc.Button([
                                "Continue to Experiments"
                            ],
                            id="create-domain-btn",
                            color="primary",
                            size="lg",
                            className="w-100",
                            style={
                                "backgroundColor": "#6366f1",
                                "border": "none",
                                "borderRadius": "8px",
                                "padding": "0.75rem",
                                "fontSize": "1rem",
                                "fontWeight": "500",
                                "boxShadow": "0 2px 8px rgba(99, 102, 241, 0.2)"
                            }
                            ), 
                            href="/Opt-run"
                        )
                    ], md=6, className="mx-auto")
                ])
            ], style={"padding": "2rem"})
        ], style={
            "borderRadius": "16px",
            "border": "1px solid #e0e0e0",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.08)",
            "backgroundColor": "white"
        }),
        
        # Hidden stores
        dcc.Store(id='parameter-store', data=[], storage_type="session"),
        dcc.Store(id='objective-store', data=[], storage_type="session"),
        dcc.Store(id="extra-columns-store", data=[], storage_type="session"),
    ], fluid=True, style={
        "maxWidth": "1200px",
        "backgroundColor": "#f8f9fa",
        "minHeight": "100vh",
        "paddingTop": "2rem",
        "paddingBottom": "4rem"
    })
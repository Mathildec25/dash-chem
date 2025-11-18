import dash_bootstrap_components as dbc
from dash import dcc, html
import uuid

initial_id = str(uuid.uuid4())
initial_objective_id = str(uuid.uuid4())

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
        
        # Alert for validation errors (only shown when clicking Continue)
        dbc.Row([
            dbc.Col([
                dbc.Alert(
                    id="validation-alert",
                    is_open=False,
                    dismissable=True,
                    className="mb-3"
                )
            ], md=12)
        ]),
        
        dbc.Row([
            # Parameters Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5("Parameters", className="mb-0", style={"fontWeight": "600", "display": "inline-block"}),
                            dbc.Button([
                                html.I(className="bi bi-plus-lg")
                            ],
                            id="add-para-button",
                            color="primary",
                            size="sm",
                            className="float-end",
                            style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                            ),
                        ], className="mb-3"),
                        
                        # Parameters container with initial row
                        html.Div(id="parameter-container", children=[
                            html.Div([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Input(
                                            id={'type': 'parameter-name', 'index': initial_id},
                                            placeholder="Parameter name",
                                            size="sm",
                                            style={"borderRadius": "6px"}
                                        )
                                    ], width=3),
                                    dbc.Col([
                                        dcc.Dropdown(
                                            id={'type': 'parameter-type', 'index': initial_id},
                                            options=[
                                                {"label": "Continuous", "value": "float"},
                                                {"label": "Discrete", "value": "int"},
                                                {"label": "Categorical", "value": "cat"},
                                            ],
                                            value="float",
                                            placeholder="Type",
                                            clearable=False,
                                            style={"fontSize": "0.875rem"}
                                        )
                                    ], width=2),
                                    dbc.Col([
                                        html.Div(id={'type': 'parameter-inputs', 'index': initial_id}, children=[
                                            dbc.Row([
                                                dbc.Col([
                                                    dbc.Input(
                                                        id={'type': 'parameter-min', 'index': initial_id},
                                                        placeholder="Min",
                                                        type="number",
                                                        step="any",
                                                        size="sm",
                                                        style={"borderRadius": "6px"}
                                                    )
                                                ], width=6),
                                                dbc.Col([
                                                    dbc.Input(
                                                        id={'type': 'parameter-max', 'index': initial_id},
                                                        placeholder="Max",
                                                        type="number",
                                                        step="any",
                                                        size="sm",
                                                        style={"borderRadius": "6px"}
                                                    )
                                                ], width=6),
                                            ])
                                        ])
                                    ], width=6),
                                    dbc.Col([
                                        dbc.Button(
                                            html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                                            id={'type': 'delete-parameter', 'index': initial_id},
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                                        )
                                    ], width=1),
                                ], className="mb-2 align-items-center"),
                            ], id={'type': 'parameter-row', 'index': initial_id})
                        ]),
                    ], style={"padding": "1.25rem"})
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
                    "backgroundColor": "white",
                    "height": "100%"
                })
            ], md=6, className="mb-3"),
            
            # Objectives Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5("Objectives", className="mb-0", style={"fontWeight": "600", "display": "inline-block"}),
                            dbc.Button([
                                html.I(className="bi bi-plus-lg")
                            ],
                            id="add-objective-button",
                            color="success",
                            size="sm",
                            className="float-end",
                            style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                            ),
                        ], className="mb-3"),
                        
                        # Objectives container with initial row
                        html.Div(id="objective-container", children=[
                            html.Div([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Input(
                                            id={'type': 'objective-name', 'index': initial_objective_id},
                                            placeholder="Objective name",
                                            size="sm",
                                            style={"borderRadius": "6px"}
                                        )
                                    ], width=4),
                                    dbc.Col([
                                        dcc.Dropdown(
                                            id={'type': 'objective-direction', 'index': initial_objective_id},
                                            options=[
                                                {"label": "Minimize", "value": "min"},
                                                {"label": "Maximize", "value": "max"}
                                            ],
                                            placeholder="Direction",
                                            clearable=False,
                                            style={"fontSize": "0.875rem"}
                                        )
                                    ], width=2),
                                    dbc.Col([
                                        dbc.Input(
                                            id={'type': 'objective-lower', 'index': initial_objective_id},
                                            placeholder="Min",
                                            type="number",
                                            step="any",
                                            size="sm",
                                            style={"borderRadius": "6px"}
                                        )
                                    ], width=2),
                                    dbc.Col([
                                        dbc.Input(
                                            id={'type': 'objective-upper', 'index': initial_objective_id},
                                            placeholder="Max",
                                            type="number",
                                            step="any",
                                            size="sm",
                                            style={"borderRadius": "6px"}
                                        )
                                    ], width=2),
                                    dbc.Col([
                                        dbc.Button(
                                            html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                                            id={'type': 'delete-objective', 'index': initial_objective_id},
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                                        )
                                    ], width=1),
                                ], className="mb-2 align-items-center"),
                            ], id={'type': 'objective-row', 'index': initial_objective_id})
                        ]),
                    ], style={"padding": "1.25rem"})
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
                    "backgroundColor": "white",
                    "height": "100%"
                })
            ], md=6, className="mb-3"),
        ]),
        
        # Extra Columns Card (Collapsible)
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className="bi bi-plus-square me-2"),
                    "Add Extra Columns (Optional)"
                ],
                id="toggle-extra-columns",
                outline=True,
                color="secondary",
                size="sm",
                className="mb-3",
                style={"borderRadius": "6px"}
                ),
                
                dbc.Collapse([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Extra Columns", className="mb-3", style={"fontWeight": "600"}),
                            html.Div(id="extra-column-container", children=[]),
                            dbc.Button([
                                html.I(className="bi bi-plus me-2"),
                                "Add Column"
                            ],
                            id="add-extra-column-button",
                            outline=True,
                            color="secondary",
                            size="sm",
                            style={"borderRadius": "6px"}
                            ),
                        ], style={"padding": "1rem"})
                    ], style={
                        "borderRadius": "12px",
                        "border": "1px solid #e0e0e0",
                        "backgroundColor": "white"
                    })
                ], id="extra-columns-collapse", is_open=False),
            ], md=12)
        ]),
        
        # Sampling Configuration Card
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Initial Sampling", className="mb-3", style={"fontWeight": "600"}),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Method", className="form-label small text-muted"),
                                dcc.Dropdown(
                                    id="starting-sampling-DD",
                                    options=[
                                        {"label": "None", "value": "none"},
                                        {"label": "Random", "value": "random"},
                                        {"label": "Latin Hypercube", "value": "latin_hypercube"},
                                        {"label": "Sobol", "value": "sobol"},
                                    ],
                                    value="latin_hypercube",
                                    clearable=False,
                                    style={"fontSize": "0.875rem"}
                                ),
                            ], md=6),
                            dbc.Col([
                                html.Label("Points", className="form-label small text-muted"),
                                dbc.Input(
                                    id="nb-sampling-points",
                                    type="number",
                                    value=10,
                                    min=1,
                                    size="sm",
                                    style={"borderRadius": "6px"}
                                ),
                            ], md=6)
                        ])
                    ], style={"padding": "1.25rem"})
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
                    "backgroundColor": "white"
                })
            ], md=12, className="mb-3")
        ]),
        
        # Continue Button
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className="bi bi-arrow-right-circle me-2"),
                    "Continue to Experiments"
                ],
                id="create-domain-btn",
                color="primary",
                size="lg",
                className="w-100",
                disabled=True,
                style={
                    "backgroundColor": "#6366f1",
                    "border": "none",
                    "borderRadius": "8px",
                    "padding": "0.75rem",
                    "fontSize": "1rem",
                    "fontWeight": "500",
                    "boxShadow": "0 2px 8px rgba(99, 102, 241, 0.2)"
                }
                )
            ], md=6, className="mx-auto")
        ]),
        
        # Hidden stores
        dcc.Store(id='parameter-store', data=[], storage_type="session"),
        dcc.Store(id='objective-store', data=[], storage_type="session"),
        dcc.Store(id="extra-columns-store", data=[], storage_type="session"),
        
    ], fluid=True, style={
        "maxWidth": "1400px",
        "backgroundColor": "#f8f9fa",
        "minHeight": "100vh",
        "paddingTop": "2rem",
        "paddingBottom": "4rem"
    })
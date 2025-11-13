import dash_bootstrap_components as dbc
from dash import dcc, html

def get_bo_tab_content():
    """Return the Bayesian Optimization tab content"""
    return html.Div([
        html.P("Configure and run Bayesian Optimization experiments", className="text-muted small")
    ])

def get_visualization_tab_content():
    """Return the visualization tab content"""
    return html.Div([
        html.P("Visualization content will appear here", className="text-muted small")
    ])
def create_opti_run_layout():
    return dbc.Container([
        # Header with back button
        dbc.Row([
            dbc.Col([
                dcc.Link(
                    html.I(className="bi bi-arrow-left", style={"fontSize": "1.5rem", "color": "#6c757d"}),
                    href="/Opt-param",
                    style={"textDecoration": "none"}
                )
            ], width="auto"),
            dbc.Col([
                html.H1("Run Optimization", 
                       style={
                           "color": "#1a1a1a", 
                           "fontWeight": "600",
                           "fontSize": "2rem",
                           "letterSpacing": "-0.02em",
                           "marginBottom": "0.25rem"
                       }),
                html.P("Configure and execute your optimization experiments",
                      style={
                          "fontSize": "1rem",
                          "color": "#6c757d",
                          "marginBottom": "0"
                      })
            ], width=True)
        ], className="mb-4 align-items-center"),
        
        # Alert/Status messages
        html.Div(id="opti-run-alerts"),
        
        dbc.Row([
            # Left Column - Configuration
            dbc.Col([
                # Experiment Configuration Card
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Experiment Configuration", className="mb-3", style={"fontWeight": "600"}),
                        
                        # Experiment name
                        html.Div([
                            html.Label("Experiment Name", className="form-label small text-muted mb-1"),
                            dbc.Input(
                                id="experiment-name-input",
                                placeholder="e.g., Trial_001, Batch_A...",
                                size="sm",
                                style={"borderRadius": "6px", "marginBottom": "1rem"}
                            )
                        ]),
                        
                        # Acquisition function
                        html.Div([
                            html.Label("Acquisition Function", className="form-label small text-muted mb-1"),
                            dcc.Dropdown(
                                id="acquisition-function-dropdown",
                                options=[
                                    {"label": "Expected Improvement (EI)", "value": "EI"},
                                    {"label": "Upper Confidence Bound (UCB)", "value": "UCB"},
                                    {"label": "Probability of Improvement (PI)", "value": "PI"},
                                    {"label": "qEI (Batch)", "value": "qEI"},
                                ],
                                value="EI",
                                clearable=False,
                                style={"fontSize": "0.875rem", "marginBottom": "1rem"}
                            )
                        ]),
                        
                        # Number of suggestions
                        html.Div([
                            html.Label("Suggestions per Iteration", className="form-label small text-muted mb-1"),
                            dbc.Input(
                                id="num-suggestions-input",
                                type="number",
                                value=1,
                                min=1,
                                max=10,
                                size="sm",
                                style={"borderRadius": "6px", "marginBottom": "1rem"}
                            )
                        ]),
                        
                        # Max iterations
                        html.Div([
                            html.Label("Maximum Iterations", className="form-label small text-muted mb-1"),
                            dbc.Input(
                                id="max-iterations-input",
                                type="number",
                                value=20,
                                min=1,
                                size="sm",
                                style={"borderRadius": "6px", "marginBottom": "1rem"}
                            )
                        ]),
                        
                        html.Hr(className="my-3"),
                        
                        # Action buttons
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-play-fill me-2"),
                                    "Generate Suggestions"
                                ],
                                id="run-optimization-button",
                                color="primary",
                                size="sm",
                                className="w-100",
                                style={
                                    "backgroundColor": "#6366f1",
                                    "border": "none",
                                    "borderRadius": "6px",
                                    "fontWeight": "500"
                                }
                                )
                            ], width=12, className="mb-2"),
                        ]),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-arrow-clockwise me-2"),
                                    "Reset"
                                ],
                                id="reset-optimization-button",
                                color="secondary",
                                outline=True,
                                size="sm",
                                className="w-100",
                                style={"borderRadius": "6px"}
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-download me-2"),
                                    "Export"
                                ],
                                id="export-results-button",
                                color="success",
                                outline=True,
                                size="sm",
                                className="w-100",
                                style={"borderRadius": "6px"}
                                )
                            ], width=6),
                        ])
                    ], style={"padding": "1.25rem"})
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
                    "backgroundColor": "white",
                    "marginBottom": "1rem"
                }),
                
                # Domain Summary Card
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Domain Summary", className="mb-3", style={"fontWeight": "600"}),
                        html.Div(id="domain-summary-display", children=[
                            html.P("No domain configured", className="text-muted small mb-0")
                        ])
                    ], style={"padding": "1rem"})
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "backgroundColor": "#f8f9fa"
                }),
                
            ], md=4),
            
            # Right Column - Results & Suggestions
            dbc.Col([
                # Suggestions Card
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5("Suggested Experiments", 
                                   className="mb-0 d-inline-block", 
                                   style={"fontWeight": "600"}),
                            dbc.Badge("0", 
                                     id="suggestions-count-badge",
                                     color="primary", 
                                     className="ms-2",
                                     style={"fontSize": "0.75rem"})
                        ], className="mb-3"),
                        
                        # Suggestions table container
                        html.Div(id="suggestions-table-container", children=[
                            html.Div([
                                html.I(className="bi bi-lightbulb", style={"fontSize": "3rem", "color": "#e0e0e0"}),
                                html.P("No suggestions yet", className="text-muted mt-2")
                            ], className="text-center py-5")
                        ])
                    ], style={"padding": "1.25rem"})
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
                    "backgroundColor": "white",
                    "marginBottom": "1rem"
                }),
                
                # Results Entry Card
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Enter Results", className="mb-3", style={"fontWeight": "600"}),
                        html.Div(id="results-entry-container", children=[
                            html.P("Run optimization to enter results", className="text-muted small mb-0")
                        ])
                    ], style={"padding": "1.25rem"})
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
                    "backgroundColor": "white"
                }),
                
            ], md=8)
        ]),
        
        # Tabs for additional views
        dbc.Card([
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(label="Optimization History", tab_id="history", label_style={"fontSize": "0.9rem"}),
                    dbc.Tab(label="Convergence Plot", tab_id="convergence", label_style={"fontSize": "0.9rem"}),
                    dbc.Tab(label="Parameter Space", tab_id="space", label_style={"fontSize": "0.9rem"}),
                ], id="results-tabs", active_tab="history", style={"marginBottom": "1rem"}),
                
                html.Div(id="tab-content-container")
            ], style={"padding": "1.25rem"})
        ], style={
            "borderRadius": "12px",
            "border": "1px solid #e0e0e0",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
            "backgroundColor": "white",
            "marginTop": "1rem"
        }),
        
        # Hidden stores
        dcc.Store(id='optimization-state-store', storage_type='session'),
        dcc.Store(id='suggestions-store', storage_type='session'),
        dcc.Store(id='iteration-counter-store', data=0, storage_type='session'),
        
    ], fluid=True, style={
        "maxWidth": "1400px",
        "backgroundColor": "#f8f9fa",
        "minHeight": "100vh",
        "paddingTop": "2rem",
        "paddingBottom": "4rem"
    })
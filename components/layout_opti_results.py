"""
Layout for Optimization Results & Analysis page
Adaptive layout for Single-Objective (SOBO) and Multi-Objective (MOBO) optimization
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_opti_results_layout():
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                dcc.Link(
                    html.I(className="bi bi-arrow-left", style={"fontSize": "1.5rem", "color": "#6c757d"}),
                    href="/Opt-run",
                    style={"textDecoration": "none"}
                )
            ], width="auto"),
            dbc.Col([
                html.H1("Results & Analysis", 
                       style={
                           "color": "#1a1a1a", 
                           "fontWeight": "600",
                           "fontSize": "2rem",
                           "letterSpacing": "-0.02em",
                           "marginBottom": "0.25rem"
                       }),
                html.P("Analyze your optimization results and find the best configurations",
                      style={
                          "fontSize": "1rem",
                          "color": "#6c757d",
                          "marginBottom": "0"
                      })
            ], width=True),
            # Optimization type badge
            dbc.Col([
                html.Div(id="optimization-type-badge", children=[
                    dbc.Badge("Loading...", color="secondary", className="px-3 py-2")
                ])
            ], width="auto", className="text-end")
        ], className="mb-4 align-items-center"),
        
        # Alert for status
        dbc.Row([
            dbc.Col([
                dbc.Alert(
                    id="results-status-alert",
                    is_open=False,
                    dismissable=True,
                    className="mb-3"
                )
            ], md=12)
        ]),
        
        # ===== SUMMARY CARDS ROW =====
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-hash", style={"fontSize": "1.5rem", "color": "#6366f1"}),
                        ], className="mb-2"),
                        html.H3(id="total-experiments", children="0", className="mb-1", style={"fontWeight": "700"}),
                        html.P("Total Experiments", className="text-muted mb-0 small")
                    ], className="text-center")
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-trophy", style={"fontSize": "1.5rem", "color": "#10b981"}),
                        ], className="mb-2"),
                        html.H3(id="best-objective-value", children="-", className="mb-1", style={"fontWeight": "700"}),
                        html.P("Best Objective", className="text-muted mb-0 small")
                    ], className="text-center")
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-lightning-charge", style={"fontSize": "1.5rem", "color": "#f59e0b"}),
                        ], className="mb-2"),
                        html.H3(id="bo-experiments", children="0", className="mb-1", style={"fontWeight": "700"}),
                        html.P("BO Suggestions", className="text-muted mb-0 small")
                    ], className="text-center")
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-graph-up-arrow", style={"fontSize": "1.5rem", "color": "#ef4444"}),
                        ], className="mb-2"),
                        html.H3(id="improvement-percent", children="-", className="mb-1", style={"fontWeight": "700"}),
                        html.P("Improvement", className="text-muted mb-0 small")
                    ], className="text-center")
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=3, className="mb-3"),
        ]),
        
        # ===== MAIN CONVERGENCE SECTION =====
        # This section adapts based on SOBO vs MOBO
        dbc.Row([
            # Primary convergence plot (left side - larger)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5(id="convergence-title", children="Optimization Convergence", 
                                       className="mb-0", style={"fontWeight": "600"})
                            ]),
                            dbc.Col([
                                dbc.Select(
                                    id="convergence-objective-selector",
                                    options=[],
                                    placeholder="Select objective",
                                    size="sm",
                                    style={"width": "150px", "display": "none"}
                                )
                            ], width="auto")
                        ], align="center")
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="convergence-plot", style={"height": "380px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=8, className="mb-3"),
            
            # Secondary metrics (right side - smaller)
            dbc.Col([
                # For SOBO: Regret plot / For MOBO: Hypervolume
                dbc.Card([
                    dbc.CardHeader([
                        html.H5(id="secondary-metric-title", children="Optimization Progress", 
                               className="mb-0", style={"fontWeight": "600"})
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="secondary-metric-plot", style={"height": "160px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"}, className="mb-3"),
                
                # Objective Distribution
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Objective Distribution", className="mb-0", style={"fontWeight": "600"})
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="objective-distribution", style={"height": "160px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=4, className="mb-3"),
        ]),
        
        # ===== MOBO SPECIFIC: PARETO FRONT SECTION =====
        html.Div(id="mobo-section", children=[
            dbc.Row([
                # Pareto Front Plot
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Pareto Front Evolution", className="mb-0", style={"fontWeight": "600"}),
                                    html.Small("Non-dominated solutions over iterations", className="text-muted")
                                ]),
                                dbc.Col([
                                    dbc.ButtonGroup([
                                        dbc.Button("2D", id="pareto-2d-btn", color="primary", size="sm", outline=False),
                                        dbc.Button("3D", id="pareto-3d-btn", color="primary", size="sm", outline=True),
                                    ], size="sm")
                                ], width="auto")
                            ], align="center")
                        ], style={"backgroundColor": "#f8f9fa"}),
                        dbc.CardBody([
                            dcc.Graph(id="pareto-front-plot", style={"height": "400px"})
                        ])
                    ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
                ], md=8, className="mb-3"),
                
                # Hypervolume Evolution
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Hypervolume Indicator", className="mb-0", style={"fontWeight": "600"}),
                            html.Small("Pareto front quality metric", className="text-muted")
                        ], style={"backgroundColor": "#f8f9fa"}),
                        dbc.CardBody([
                            dcc.Graph(id="hypervolume-plot", style={"height": "400px"})
                        ])
                    ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
                ], md=4, className="mb-3"),
            ])
        ], style={"display": "none"}),  # Hidden by default, shown for MOBO
        
        # ===== SOBO SPECIFIC: REGRET & EXPLORATION SECTION =====
        html.Div(id="sobo-section", children=[
            dbc.Row([
                # Cumulative Regret
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Optimization Regret", className="mb-0", style={"fontWeight": "600"}),
                            html.Small("Gap from best found solution", className="text-muted")
                        ], style={"backgroundColor": "#f8f9fa"}),
                        dbc.CardBody([
                            dcc.Graph(id="regret-plot", style={"height": "300px"})
                        ])
                    ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
                ], md=6, className="mb-3"),
                
                # Improvement Rate
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Improvement Rate", className="mb-0", style={"fontWeight": "600"}),
                            html.Small("Rolling improvement over iterations", className="text-muted")
                        ], style={"backgroundColor": "#f8f9fa"}),
                        dbc.CardBody([
                            dcc.Graph(id="improvement-rate-plot", style={"height": "300px"})
                        ])
                    ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
                ], md=6, className="mb-3"),
            ])
        ], style={"display": "none"}),  # Hidden by default, shown for SOBO
        
        # ===== PARAMETER EXPLORATION SECTION =====
        dbc.Row([
            # Parameter Space Exploration
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5("Parameter Space Exploration", className="mb-0", style={"fontWeight": "600"}),
                                html.Small("How parameters were explored during optimization", className="text-muted")
                            ]),
                            dbc.Col([
                                dbc.Select(
                                    id="param-x-selector",
                                    options=[],
                                    placeholder="X-axis",
                                    size="sm",
                                    style={"width": "120px", "display": "inline-block", "marginRight": "8px"}
                                ),
                                dbc.Select(
                                    id="param-y-selector",
                                    options=[],
                                    placeholder="Y-axis",
                                    size="sm",
                                    style={"width": "120px", "display": "inline-block"}
                                )
                            ], width="auto")
                        ], align="center")
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="parameter-exploration-plot", style={"height": "400px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=7, className="mb-3"),
            
            # Parameter Importance
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Parameter Influence", className="mb-0", style={"fontWeight": "600"}),
                        html.Small("Correlation with objective", className="text-muted")
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="parameter-importance-plot", style={"height": "400px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=5, className="mb-3"),
        ]),
        
        # ===== PARALLEL COORDINATES =====
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5("Parallel Coordinates", className="mb-0", style={"fontWeight": "600"}),
                                html.Small("Visualize parameter-objective relationships", className="text-muted")
                            ]),
                            dbc.Col([
                                dbc.Select(
                                    id="parallel-color-selector",
                                    options=[
                                        {"label": "By Iteration", "value": "iteration"},
                                        {"label": "By Objective", "value": "objective"},
                                        {"label": "By Point Type", "value": "point_type"}
                                    ],
                                    value="objective",
                                    size="sm",
                                    style={"width": "140px"}
                                )
                            ], width="auto")
                        ], align="center")
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="parallel-coordinates-plot", style={"height": "420px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=12, className="mb-3"),
        ]),
        
        # ===== CORRELATION HEATMAP =====
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Parameter-Objective Correlations", className="mb-0", style={"fontWeight": "600"})
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="correlation-heatmap", style={"height": "350px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=6, className="mb-3"),
            
            # Slice Plot / 1D Effect
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5("Parameter Effect (1D Slice)", className="mb-0", style={"fontWeight": "600"})
                            ]),
                            dbc.Col([
                                dbc.Select(
                                    id="slice-param-selector",
                                    options=[],
                                    placeholder="Select parameter",
                                    size="sm",
                                    style={"width": "150px"}
                                )
                            ], width="auto")
                        ], align="center")
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="slice-plot", style={"height": "350px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=6, className="mb-3"),
        ]),
        
        # ===== BEST EXPERIMENTS TABLE =====
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5("Top Experiments", className="mb-0", style={"fontWeight": "600"})
                            ]),
                            dbc.Col([
                                dbc.Select(
                                    id="top-n-selector",
                                    options=[
                                        {"label": "Top 5", "value": "5"},
                                        {"label": "Top 10", "value": "10"},
                                        {"label": "Top 20", "value": "20"},
                                        {"label": "All", "value": "all"}
                                    ],
                                    value="10",
                                    size="sm",
                                    style={"width": "120px"}
                                )
                            ], width="auto")
                        ], align="center")
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        html.Div(id="best-experiments-table")
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=12, className="mb-3"),
        ]),
        
        # ===== GENERATE REPORT BUTTON =====
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className="bi bi-file-earmark-text me-2"),
                    "Generate Report"
                ], id="generate-report-btn", color="primary", size="lg"),
            ], className="text-center mb-4")
        ]),
        
        # Download component and status alert for report
        dcc.Download(id='download-report'),

        dbc.Row([
            dbc.Col([
                dbc.Alert(
                    id="generate-report-status",
                    is_open=False,
                    dismissable=True,
                    duration=5000,
                    className="mb-3"
                )
            ], md=12)
        ]),
        
        # Store for optimization type
        dcc.Store(id='optimization-type-store', data='SOBO'),
        
    ], fluid=True, style={
        "maxWidth": "1400px",
        "backgroundColor": "#f8f9fa",
        "minHeight": "100vh",
        "paddingTop": "2rem",
        "paddingBottom": "4rem"
    })
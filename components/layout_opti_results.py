"""
Results Layout for Optimization Analysis
Adaptive layout for SOBO and MOBO optimization results

CHANGES:
- Removed: SHAP Dependence Plot, Parameter-Objective Correlations, Parameter Effect (1D Slice)
- Removed: Cumulative Best (secondary-metric), Objective Distribution, Improvement Rate
- Convergence plot now full width (md=12)
- MOBO: objective selector always visible for convergence
- Parameter Influence + SHAP Beeswarm on same row
- SOBO section: Regret only (full width)
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_opti_results_layout():
    """Create the optimization results analysis page layout"""
    
    return html.Div([
        # Status alert
        dbc.Alert(
            id="results-status-alert",
            children="Loading...",
            color="info",
            is_open=False,
            dismissable=True,
            className="mb-3"
        ),
        
        # ===== OPTIMIZATION TYPE BADGE =====
        dbc.Row([
            dbc.Col([
                html.Div(id="optimization-type-badge", className="mb-3")
            ])
        ]),
        
        # Store for optimization type
        dcc.Store(id="optimization-type-store", data="SOBO"),
        
        # ===== KPI CARDS =====
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-clipboard-data", style={"fontSize": "1.5rem", "color": "#6366f1"}),
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
        
        # ===== CONVERGENCE SECTION (full width) =====
        dbc.Row([
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
            ], md=12, className="mb-3"),
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
        
        # ===== SOBO SPECIFIC: REGRET SECTION =====
        html.Div(id="sobo-section", children=[
            dbc.Row([
                # Optimization Regret (full width)
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
                ], md=12, className="mb-3"),
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
            ], md=12, className="mb-3"),
        ]),
        
         # ===== PARAMETER INFLUENCE + SHAP BEESWARM (same row) =====
        dbc.Row([
            # Parameter Influence (bar plot) - AVEC SÉLECTEUR D'OBJECTIF
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5("Parameter Influence", className="mb-0", style={"fontWeight": "600"}),
                                html.Small("Mean |SHAP| value", className="text-muted")
                            ]),
                            dbc.Col([
                                # NOUVEAU: Sélecteur d'objectif
                                dbc.Select(
                                    id="shap-objective-selector",
                                    options=[],
                                    placeholder="Select objective",
                                    size="sm",
                                    style={"width": "150px", "display": "none"}
                                )
                            ], width="auto")
                        ], align="center")
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="parameter-importance-plot", style={"height": "450px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=5, className="mb-3"),
            
            # SHAP Beeswarm - MÊME SÉLECTEUR PARTAGÉ
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("SHAP Summary (Beeswarm)", className="mb-0", style={"fontWeight": "600"}),
                        html.Small("Distribution of feature effects - each dot is one experiment", className="text-muted")
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="shap-beeswarm-plot", style={"height": "450px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=7, className="mb-3"),
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
                        # MODIFICATION: Hauteur augmentée de 420px à 500px pour voir les noms de colonnes
                        dcc.Graph(id="parallel-coordinates-plot", style={"height": "500px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=12, className="mb-3"),
        ]),
        
        # ===== BEST EXPERIMENTS TABLE =====
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5("Best Experiments", className="mb-0", style={"fontWeight": "600"})
                            ]),
                            dbc.Col([
                                html.Label("Show top:", className="small me-2"),
                                dbc.Select(
                                    id="top-n-selector",
                                    options=[
                                        {"label": "5", "value": 5},
                                        {"label": "10", "value": 10},
                                        {"label": "20", "value": 20},
                                        {"label": "All", "value": 999}
                                    ],
                                    value=10,
                                    size="sm",
                                    style={"width": "80px", "display": "inline-block"}
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
                    html.I(className="bi bi-file-earmark-word me-2"),
                    "Generate Report"
                ],
                id="generate-report-btn",
                color="primary",
                size="lg",
                className="w-100",
                style={"borderRadius": "8px"}
                ),
                dcc.Download(id="download-report"),
                dbc.Alert(
                    id="report-status-alert",
                    children="",
                    color="info",
                    is_open=False,
                    dismissable=True,
                    className="mt-2"
                )
            ], md=4, className="mb-3 mx-auto"),
        ]),
        
    ], className="p-3")
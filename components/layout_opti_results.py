"""
Layout for Optimization Results & Analysis page
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
            ], width=True)
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
        
        # Summary Cards Row
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
        
        # Convergence Plot
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Optimization Convergence", className="mb-0", style={"fontWeight": "600"})
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="convergence-plot", style={"height": "350px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=8, className="mb-3"),
            
            # Objective Distribution
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Objective Distribution", className="mb-0", style={"fontWeight": "600"})
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="objective-distribution", style={"height": "350px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=4, className="mb-3"),
        ]),
        
        # Parallel Coordinates Plot
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Parallel Coordinates", className="mb-0", style={"fontWeight": "600"}),
                        html.Small("Visualize parameter-objective relationships", className="text-muted")
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="parallel-coordinates-plot", style={"height": "400px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=12, className="mb-3"),
        ]),
        
        # Parameter Importance & Pareto Front (for multi-objective)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Parameter Influence", className="mb-0", style={"fontWeight": "600"})
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="parameter-importance-plot", style={"height": "300px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=6, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Pareto Front", className="mb-0", style={"fontWeight": "600"}),
                        html.Small("Multi-objective trade-offs", className="text-muted")
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="pareto-front-plot", style={"height": "300px"})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=6, className="mb-3"),
        ]),
        
        # Best Experiments Table
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
        
# Generate Report button
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
        
        
    ], fluid=True, style={
        "maxWidth": "1400px",
        "backgroundColor": "#f8f9fa",
        "minHeight": "100vh",
        "paddingTop": "2rem",
        "paddingBottom": "4rem"
    })
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
            
            # Right Column - Sampling / BO Results
            dbc.Col([
                # Sampling / BO results card
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5(
                                "Sampling (Bayesian Optimization)",
                                className="mb-0 d-inline-block",
                                style={"fontWeight": "600"}
                            ),
                            # Tu peux garder ou supprimer ce badge selon si tu le mets à jour
                            dbc.Badge(
                                "0",
                                id="suggestions-count-badge",
                                color="primary",
                                className="ms-2",
                                style={"fontSize": "0.75rem"}
                            )
                        ], className="mb-3"),
                        
                        # ICI : affichage des résultats du BO
                        html.Div(
                            id="optimization-results",
                            children=[
                                html.Div([
                                    html.I(
                                        className="bi bi-lightbulb",
                                        style={"fontSize": "3rem", "color": "#e0e0e0"}
                                    ),
                                    html.P("No sampling yet", className="text-muted mt-2")
                                ], className="text-center py-5")
                            ]
                        )
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

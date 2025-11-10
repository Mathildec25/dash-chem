import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
import os
from excel_storage import EXCEL_FOLDER, TRACKING_FILE, TRACKING_FILENAME

def load_tracked_files():
    if os.path.exists(TRACKING_FILE):
        df = pd.read_excel(TRACKING_FILE)
        return [{'label': fname, 'value': fname} for fname in df['filename'].dropna()]
    return []

def create_opti_home_layout():
    return dbc.Container([
        # Header Section - Clean and minimal
        dbc.Row([
            dbc.Col([
                html.H1("Bayesian Optimization Platform", 
                       className="text-center mb-2",
                       style={
                           "color": "#1a1a1a", 
                           "fontWeight": "600",
                           "fontSize": "2.5rem",
                           "letterSpacing": "-0.02em"
                       }),
                html.P("Choose your optimization approach",
                      className="text-center mb-5",
                      style={
                          "fontSize": "1.1rem",
                          "color": "#6c757d",
                          "fontWeight": "400"
                      })
            ], width=12)
        ], className="mt-5 mb-4"),
        
        # Main Cards Section - Side by side
        dbc.Row([
            # New Project Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        # Icon circle
                        html.Div([
                            html.Div([
                                html.I(className="bi bi-plus-lg",
                                      style={"fontSize": "2rem", "color": "white"})
                            ], style={
                                "width": "80px",
                                "height": "80px",
                                "borderRadius": "50%",
                                "backgroundColor": "#a8a8a8",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "margin": "0 auto 1.5rem auto",
                            })
                        ]),
                        
                        # Title
                        html.H4("New Project", 
                               className="text-center mb-3",
                               style={
                                   "fontWeight": "600",
                                   "color": "#1a1a1a",
                                   "fontSize": "1.5rem"
                               }),
                        
                        # Description
                        html.P("Start a fresh optimization project with custom parameters and objectives",
                              className="text-center mb-4",
                              style={
                                  "color": "#6c757d",
                                  "fontSize": "0.95rem",
                                  "lineHeight": "1.6"
                              }),
                        
                        # Input for project name
                        html.Div([
                            dbc.Input(
                                id="new-proj",
                                type="text",
                                placeholder="Enter project name...",
                                className="mb-3",
                                style={
                                    "fontSize": "1rem",
                                    "padding": "0.75rem",
                                    "borderRadius": "8px",
                                    "border": "1px solid #e0e0e0",
                                    "transition": "all 0.2s"
                                }
                            ),
                        ], style={"marginBottom": "1.5rem"}),
                        
                        # Button
                        html.Div([
                            dcc.Link(
                                dbc.Button([
                                    "Create New Project"
                                ],
                                id="start-opti-button",
                                style={
                                    "backgroundColor": "#fb8500",
                                    "border": "none",
                                    "padding": "0.75rem 2rem",
                                    "fontSize": "1rem",
                                    "fontWeight": "500",
                                    "borderRadius": "8px",
                                    "width": "100%",
                                    "transition": "all 0.3s",
                                    "boxShadow": "0 2px 8px rgba(99, 102, 241, 0.2)",
                                    "display": "none"
                                },
                                className="hover-lift"
                                ), 
                                href="/Opt-param"
                            )
                        ], id="start-opti-button-container"),
                    ], style={"padding": "2.5rem 2rem"})
                ], style={
                    "borderRadius": "16px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.08)",
                    "transition": "all 0.3s",
                    "height": "100%",
                    "backgroundColor": "white"
                }, className="h-100 hover-card-modern")
            ], md=6, className="mb-4"),
            
            # Existing Project Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        # Icon circle
                        html.Div([
                            html.Div([
                                html.I(className="bi bi-folder2-open",
                                      style={"fontSize": "2rem", "color": "white"})
                            ], style={
                                "width": "80px",
                                "height": "80px",
                                "borderRadius": "50%",
                                "backgroundColor": "#a8a8a8",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "margin": "0 auto 1.5rem auto",
                            })
                        ]),
                        
                        # Title
                        html.H4("Load Existing Project", 
                               className="text-center mb-3",
                               style={
                                   "fontWeight": "600",
                                   "color": "#1a1a1a",
                                   "fontSize": "1.5rem"
                               }),
                        
                        # Description
                        html.P("Continue working on a previously saved optimization project",
                              className="text-center mb-4",
                              style={
                                  "color": "#6c757d",
                                  "fontSize": "0.95rem",
                                  "lineHeight": "1.6"
                              }),
                        
                        # Dropdown for file selection
                        html.Div([
                            dcc.Dropdown(
                                id="excels-DD-opti",
                                options=load_tracked_files(),
                                placeholder="Select a project...",
                                className="mb-2",
                                style={
                                    "fontSize": "1rem",
                                    "borderRadius": "8px"
                                }
                            ),
                            html.Div(id='domain-status-display', className="mb-2"),
                        ], style={"marginBottom": "1rem"}),
                        
                        # Sheet selector (hidden by default)
                        html.Div([
                            html.Div(id='sheets-DD-opti', className="mb-3"),
                        ]),
                        
                        # Action buttons
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    dcc.Link(
                                        dbc.Button([
                                            "Load Project"
                                        ],
                                        id="restart-opti-button",
                                        style={
                                            "backgroundColor": "#fb8500",
                                            "border": "none",
                                            "padding": "0.75rem 2rem",
                                            "fontSize": "1rem",
                                            "fontWeight": "500",
                                            "borderRadius": "8px",
                                            "width": "100%",
                                            "transition": "all 0.3s",
                                            "boxShadow": "0 2px 8px rgba(16, 185, 129, 0.2)",
                                            "display": "none"
                                        },
                                        className="hover-lift"
                                        ), 
                                        href="/Opt-run"
                                    )
                                ])
                            ], md=8),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-trash")
                                ],
                                id="delete-excel-button-opti",
                                outline=True,
                                color="danger",
                                style={
                                    "padding": "0.75rem",
                                    "borderRadius": "8px",
                                    "width": "100%",
                                    "display": "none",
                                    "transition": "all 0.3s"
                                }
                                )
                            ], md=4)
                        ])
                    ], style={"padding": "2.5rem 2rem"})
                ], style={
                    "borderRadius": "16px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.08)",
                    "transition": "all 0.3s",
                    "height": "100%",
                    "backgroundColor": "white"
                }, className="h-100 hover-card-modern")
            ], md=6, className="mb-4"),
        ], justify="center", style={"maxWidth": "1000px", "margin": "0 auto"}),
        
])
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
        # Header Section
        dbc.Row([
            dbc.Col([
                html.H1("Bayesian Optimization Hub", 
                       className="text-center mb-2",
                       style={"color": "#2c3e50", "fontWeight": "bold"}),
                html.P("AI-powered experimental design and optimization using BoFire",
                      className="text-center text-muted mb-4",
                      style={"fontSize": "18px"})
            ], width=12)
        ], className="mt-4"),
        
        # Info Alert
 #       dbc.Alert([
 #           html.I(className="bi bi-robot me-2"),
 #           html.Strong("What is Bayesian Optimization? "),
 #           "An intelligent approach to experimental design that uses machine learning to suggest the most promising "
 #           "experiments, with aim to reduce the number of trials needed to find optimal conditions.",
 #       ], color="info", className="mb-4"),
        
        # Process Overview
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-1-circle", 
                                  style={"fontSize": "32px", "color": "#3498db"}),
                            html.H6("Define Domain", className="mt-2 mb-1"),
                            html.Small("Set parameters, objectives & constraints",
                                      className="text-muted")
                        ], className="text-center")
                    ])
                ], className="h-100 shadow border-0")
            ], md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-2-circle", 
                                  style={"fontSize": "32px", "color": "#2ecc71"}),
                            html.H6("Initial Sampling", className="mt-2 mb-1"),
                            html.Small("Generate first experiments points",
                                      className="text-muted")
                        ], className="text-center")
                    ])
                ], className="h-100 shadow border-0")
            ], md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-3-circle", 
                                  style={"fontSize": "32px", "color": "#9b59b6"}),
                            html.H6("Run Experiments", className="mt-2 mb-1"),
                            html.Small("Execute suggested experiments & record results",
                                      className="text-muted")
                        ], className="text-center")
                    ])
                ], className="h-100 shadow border-0")
            ], md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-4-circle", 
                                  style={"fontSize": "32px", "color": "#e74c3c"}),
                            html.H6("AI Suggestions", className="mt-2 mb-1"),
                            html.Small("BO for next experiment recommendations",
                                      className="text-muted")
                        ], className="text-center")
                    ])
                ], className="h-100 shadow border-0")
            ], md=3, className="mb-3"),
        ], className="mb-4"),
        
        # Main Action Options
        dbc.Row([
            # New Project Card
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H4([
                                html.I(className="bi bi-plus-circle me-2"),
                                "Start New Project"
                            ], className="text-success mb-0"),
                        ])
                    ], style={"backgroundColor": "#e8f5e8"}),
                    dbc.CardBody([
                        html.P("Create a new optimization project from scratch",
                              className="text-muted mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Project Name", className="fw-bold mb-2"),
                                dbc.Input(
                                    id="new-proj",
                                    type="text",
                                    placeholder="🔬 Enter your project name...",
                                    className="mb-3",
                                    style={"fontSize": "16px"}
                                ),
                            ], width=12)
                        ]),
                        
                        html.Div([
                            dcc.Link(
                                dbc.Button([
                                    html.I(className="bi bi-rocket-takeoff me-2"),
                                    "Create Project & Configure Domain"
                                ],
                                id="start-opti-button",
                                color="success",
                                size="lg",
                                className="w-100",
                                style={"marginTop": "12px", "display": "none"}
                                ), 
                                href="/Opt-param"
                            )
                        ], id="start-opti-button-container"),
                        
                        # Process Flow
#                        dbc.Alert([
#                            html.Strong("Next Steps: "),
#                            "Parameter Definition → Objective Setting → Initial Sampling → Domain Creation"
#                        ], color="light", className="mt-3 mb-0", style={"border": "1px solid #28a745"})
                    ])
                ], className="h-100 shadow")
            ], md=6, className="mb-4"),
            
            # Existing Project Card
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H4([
                                html.I(className="bi bi-folder-open me-2"),
                                "Continue Existing Project"
                            ], className="text-primary mb-0"),
                        ])
                    ], style={"backgroundColor": "#e7f3ff"}),
                    dbc.CardBody([
                        html.P("Select an existing project that already has a configured domain",
                              className="text-muted mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Select Project File", className="fw-bold mb-2"),
                                dcc.Dropdown(
                                    id="excels-DD-opti",
                                    options=load_tracked_files(),
                                    placeholder="📁 Choose an existing optimization project...",
                                    className="mb-2",
                                    style={"fontSize": "16px"}
                                ),
                                html.Div(id='domain-status-display', className="mb-2"),
                            ], width=12)
                        ]),
                        
                        html.Div([
                            dbc.Label("Select Data Sheet", className="fw-bold mb-2", id="text-DD-2-opti", style={"display":"none"}),
                            html.Div(id='sheets-DD-opti', className="mb-2"),
                        ]),
                        
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    dcc.Link(
                                        dbc.Button([
                                            html.I(className="bi bi-play-fill me-2"),
                                            "Continue Optimization"
                                        ],
                                        id="restart-opti-button",
                                        color="primary",
                                        size="lg",
                                        className="w-100",
                                        style={"marginTop": "12px", "display": "none"}
                                        ), 
                                        href="/Opt-run"
                                    )
                                ], id="restart-opti-button-container"),
                            ], md=8),
                            dbc.Col([
                                html.Div([
                                    dbc.Button([
                                        html.I(className="bi bi-trash me-2"),
                                        "Delete"
                                    ],
                                    id="delete-excel-button-opti",
                                    color="outline-danger",
                                    size="lg",
                                    className="w-100",
                                    style={"marginTop": "12px", "display": "none"}
                                    )
                                ], id="delete-button-container"),
                            ], md=4)
                        ]),
                        
                        # Process Flow
 #                       dbc.Alert([
 #                           html.Strong("Next Steps: "),
 #                           "Review Results → Add New Experiments → Get AI Recommendations → Analyze Performance"
 #                       ], color="light", className="mt-3 mb-0", style={"border": "1px solid #007bff"})
                    ])
                ], className="h-100 shadow")
            ], md=6, className="mb-4"),
        ]),
        
# Help and Information Section
        # dbc.Row([
        #     dbc.Col([
        #         dbc.Alert([
        #             html.H6([
        #                 html.I(className="bi bi-question-circle me-2"),
        #                 "Understanding Bayesian Optimization"
        #             ], className="alert-heading"),
        #             html.Hr(),
        #             html.P([
        #                 html.Strong("Why use BO? "),
        #                 "Traditional experimental approaches often require many trials. Bayesian Optimization uses "
        #                 "machine learning to intelligently suggest which experiments to run next, "
        #                 "reducing the time and resources needed to find optimal conditions."
        #             ], className="mb-2"),
        #             html.P([
        #                 html.Strong("Key Benefits: "),
        #                 "• Fewer experiments needed • Handles complex parameter interactions • "
        #                 "Provides uncertainty estimates • Works with expensive/time-consuming experiments"
        #             ], className="mb-2"),
        #             html.P([
        #                 html.Strong("Best For: "),
        #                 "Process optimization, material discovery, reaction condition screening, "
        #                 "and any scenario where experiments are costly or time-consuming."
        #             ], className="mb-0"),
        #         ], color="light", className="border")
        #     ], width=12)
        # ], className="mt-4"),
        
    ], fluid=True, style={"maxWidth": "1400px"})
"""
Layout for Optimization Home page
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
import os
import pandas as pd
from config_path import EXCEL_FOLDER, TRACKING_FILE


def get_existing_projects():
    """Get list of existing project files"""
    projects = []
    
    # Check tracking file
    if os.path.exists(TRACKING_FILE):
        try:
            df = pd.read_excel(TRACKING_FILE, engine='openpyxl')
            if 'filename' in df.columns:
                for fname in df['filename'].values:
                    if fname and os.path.exists(os.path.join(EXCEL_FOLDER, fname)):
                        projects.append({'label': fname.replace('.xlsx', ''), 'value': fname})
        except:
            pass
    
    # Also check folder directly
    if os.path.exists(EXCEL_FOLDER):
        for f in os.listdir(EXCEL_FOLDER):
            if f.endswith('.xlsx'):
                entry = {'label': f.replace('.xlsx', ''), 'value': f}
                if entry not in projects:
                    projects.append(entry)
    
    return projects


def create_opti_home_layout():
    projects = get_existing_projects()
    
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("Bayesian Optimization", 
                       style={
                           "color": "#1a1a1a", 
                           "fontWeight": "700",
                           "fontSize": "2.5rem",
                           "letterSpacing": "-0.02em",
                           "textAlign": "center"
                       }),
                html.P("Design and optimize your experiments with AI-powered suggestions",
                      style={
                          "fontSize": "1.1rem",
                          "color": "#6c757d",
                          "textAlign": "center",
                          "marginBottom": "2rem"
                      })
            ], md=12)
        ], className="mb-4"),
        
        dbc.Row([
            # New Project Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-plus-circle", 
                                  style={"fontSize": "3rem", "color": "#6366f1"}),
                        ], className="text-center mb-3"),
                        
                        html.H4("New Project", 
                               className="text-center mb-3",
                               style={"fontWeight": "600"}),
                        
                        dbc.Input(
                            id="new-proj",
                            placeholder="Enter project name...",
                            type="text",
                            className="mb-3",
                            style={"borderRadius": "8px"}
                        ),
                        
                        dbc.Button([
                            html.I(className="bi bi-arrow-right me-2"),
                            "Create Project"
                        ],
                        id="start-opti-button",
                        color="primary",
                        className="w-100",
                        style={
                            "backgroundColor": "#6366f1",
                            "border": "none",
                            "borderRadius": "8px",
                            "fontWeight": "500",
                            "display": "none"
                        }
                        )
                    ], style={"padding": "2rem"})
                ], style={
                    "borderRadius": "16px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.08)",
                    "height": "100%"
                })
            ], md=6, className="mb-4"),
            
            # Existing Projects Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-folder2-open", 
                                  style={"fontSize": "3rem", "color": "#10b981"}),
                        ], className="text-center mb-3"),
                        
                        html.H4("Open Project", 
                               className="text-center mb-3",
                               style={"fontWeight": "600"}),
                        
                        dcc.Dropdown(
                            id="existing-projects-list",
                            options=projects,
                            placeholder="Select a project...",
                            style={"borderRadius": "8px"},
                            className="mb-3"
                        ) if projects else html.P(
                            "No existing projects",
                            className="text-muted text-center mb-3"
                        ),
                        
                        dbc.Button([
                            html.I(className="bi bi-folder2-open me-2"),
                            "Open Project"
                        ],
                        id="open-existing-project-btn",
                        color="success",
                        className="w-100",
                        style={
                            "borderRadius": "8px",
                            "fontWeight": "500",
                            "display": "none"
                        }
                        ) if projects else None,
                        
                        html.Div([
                            html.Small(f"{len(projects)} project(s) available", 
                                      className="text-muted")
                        ], className="text-center mt-2")
                    ], style={"padding": "2rem"})
                ], style={
                    "borderRadius": "16px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.08)",
                    "height": "100%"
                })
            ], md=6, className="mb-4"),
        ]),
        
        # Info section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("How it works", className="mb-3", style={"fontWeight": "600"}),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Span("1", className="badge bg-primary me-2", 
                                             style={"borderRadius": "50%", "padding": "0.5rem 0.75rem"}),
                                    html.Strong("Define Domain"),
                                    html.P("Set your parameters and objectives", 
                                          className="text-muted small mb-0 mt-1")
                                ])
                            ], md=3),
                            dbc.Col([
                                html.Div([
                                    html.Span("2", className="badge bg-primary me-2",
                                             style={"borderRadius": "50%", "padding": "0.5rem 0.75rem"}),
                                    html.Strong("Initial Sampling"),
                                    html.P("Generate starting experiments", 
                                          className="text-muted small mb-0 mt-1")
                                ])
                            ], md=3),
                            dbc.Col([
                                html.Div([
                                    html.Span("3", className="badge bg-primary me-2",
                                             style={"borderRadius": "50%", "padding": "0.5rem 0.75rem"}),
                                    html.Strong("Run & Record"),
                                    html.P("Execute experiments and enter results", 
                                          className="text-muted small mb-0 mt-1")
                                ])
                            ], md=3),
                            dbc.Col([
                                html.Div([
                                    html.Span("4", className="badge bg-success me-2",
                                             style={"borderRadius": "50%", "padding": "0.5rem 0.75rem"}),
                                    html.Strong("Optimize"),
                                    html.P("Get AI-suggested next experiments", 
                                          className="text-muted small mb-0 mt-1")
                                ])
                            ], md=3),
                        ])
                    ], style={"padding": "1.5rem"})
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "backgroundColor": "#f8f9fa"
                })
            ], md=12)
        ])
        
    ], fluid=True, style={
        "maxWidth": "1000px",
        "marginTop": "3rem",
        "paddingBottom": "3rem"
    })
"""
Layout for Optimization Home page - COMPACT & CLEAN VERSION
Changes:
- Logo 220px (bon compromis)
- Cartes et textes plus compacts
- PAS d'attribut color= pour éviter le rouge Bootstrap
- Design épuré et professionnel
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
        # Header - Compact
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Img(
                        src="/assets/REACTO_logo.png",
                        style={
                            "maxWidth": "220px",
                            "height": "auto",
                            "display": "block",
                            "margin": "0 auto 0.5rem auto"
                        }
                    ),
                    html.P("Start or continue your optimization project",
                          className="text-center text-muted mb-0",
                          style={"fontSize": "0.875rem"})  # Plus petit
                ], style={"marginBottom": "2rem"})  # Réduit de 2.5rem
            ], md=12)
        ]),
        
        # Main action cards - COMPACT
        dbc.Row([
            # New Project Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        # Icon - Plus petit
                        html.Div([
                            html.I(className="bi bi-plus-circle", 
                                  style={"fontSize": "2.25rem", "color": "#6366f1"}),  # Réduit de 3rem
                        ], className="text-center mb-2"),  # Réduit de mb-3
                        
                        # Title - Plus petit
                        html.H4("New Project",  # H4 au lieu de H3
                               className="text-center mb-2",
                               style={"fontWeight": "600", "fontSize": "1.35rem"}),  # Réduit de 1.75rem
                        
                        # Description - Plus compacte
                        html.P("Create a new optimization campaign",
                              className="text-center text-muted mb-3",
                              style={"fontSize": "0.85rem"}),  # Réduit de 0.9rem
                        
                        # Input
                        dbc.Input(
                            id="new-proj",
                            placeholder="Project name...",  # Texte plus court
                            type="text",
                            className="mb-3",
                            style={
                                "borderRadius": "8px",
                                "fontSize": "0.9rem",  # Réduit de 1rem
                                "padding": "0.6rem"  # Réduit de 0.75rem
                            }
                        ),
                        
                        # Button 
                        dbc.Button([
                            html.I(className="bi bi-arrow-right me-2"),
                            "Create Project"
                        ],
                        id="start-opti-button",
                        className="w-100",
                        style={
                            "backgroundColor": "#6366f1",
                            "color": "white",
                            "border": "none",
                            "borderRadius": "8px",
                            "fontWeight": "500",
                            "fontSize": "0.95rem",  
                            "padding": "0.6rem",  
                            "display": "none"
                        }
                        )
                    ], style={"padding": "1.75rem"})  
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.08)",
                    "height": "100%",
                    "transition": "all 0.2s ease"
                }, className="hover-card")
            ], md=6, className="mb-3"),  # Réduit de mb-4
            
            # Existing Projects Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        # Icon - Plus petit
                        html.Div([
                            html.I(className="bi bi-folder2-open", 
                                  style={"fontSize": "2.25rem", "color": "#10b981"}),  # Réduit de 3rem
                        ], className="text-center mb-2"),
                        
                        # Title - Plus petit
                        html.H4("Open Project",  # H4 au lieu de H3
                               className="text-center mb-2",
                               style={"fontWeight": "600", "fontSize": "1.35rem"}),  # Réduit de 1.75rem
                        
                        # Description
                        html.P("Resume an existing optimization",
                              className="text-center text-muted mb-3",
                              style={"fontSize": "0.85rem"}),  # Réduit de 0.9rem
                        
                        # Dropdown
                        dcc.Dropdown(
                            id="existing-projects-list",
                            options=projects,
                            placeholder="Select a project...",
                            style={
                                "borderRadius": "8px",
                                "fontSize": "0.9rem"  # Réduit de 1rem
                            },
                            className="mb-3"
                        ) if projects else html.Div([
                            html.P(
                                "No existing projects yet",
                                className="text-muted text-center mb-1",
                                style={"fontSize": "0.9rem"}
                            ),
                            html.P(
                                "Create your first project to get started!",
                                className="text-muted text-center mb-0",
                                style={"fontSize": "0.8rem"}
                            )
                        ], className="mb-3"),
                        
                        # Button - PAS de color=
                        dbc.Button([
                            html.I(className="bi bi-folder2-open me-2"),
                            "Open Project"
                        ],
                        id="open-existing-project-btn",
                        className="w-100",
                        style={
                            "backgroundColor": "#10b981",
                            "color": "white",
                            "border": "none",
                            "borderRadius": "8px",
                            "fontWeight": "500",
                            "fontSize": "0.95rem",  # Ajouté
                            "padding": "0.6rem",  # Réduit de 0.75rem
                            "display": "none"
                        }
                        ) if projects else None,
                        
                        # Project count
                        html.Div([
                            html.Small(
                                f"📊 {len(projects)} project{'s' if len(projects) != 1 else ''}", 
                                className="text-muted"
                            )
                        ], className="text-center mt-2", style={"fontSize": "0.85rem"})
                    ], style={"padding": "1.75rem"})  # Réduit de 2.5rem
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.08)",
                    "height": "100%",
                    "transition": "all 0.2s ease"
                }, className="hover-card")
            ], md=6, className="mb-3"),
        ]),
        
        # Workflow - Compact
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-info-circle me-2", 
                                  style={"fontSize": "1rem", "color": "#6366f1"}),  # Réduit
                            html.Span("Workflow", 
                                     style={"fontWeight": "600", "fontSize": "0.95rem"})  # Réduit
                        ], className="mb-2"),  # Réduit de mb-3
                        
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Span("1", 
                                             style={
                                                 "display": "inline-block",
                                                 "backgroundColor": "#6366f1",
                                                 "color": "white",
                                                 "borderRadius": "50%",
                                                 "width": "22px",
                                                 "height": "22px",
                                                 "lineHeight": "22px",
                                                 "textAlign": "center",
                                                 "fontSize": "0.75rem",
                                                 "fontWeight": "600",
                                                 "marginRight": "0.4rem"
                                             }),
                                    html.Span("Define Domain", 
                                             style={"fontWeight": "500", "fontSize": "0.85rem"})
                                ])
                            ], md=3, className="mb-2 mb-md-0"),
                            dbc.Col([
                                html.Div([
                                    html.Span("2",
                                             style={
                                                 "display": "inline-block",
                                                 "backgroundColor": "#6366f1",
                                                 "color": "white",
                                                 "borderRadius": "50%",
                                                 "width": "22px",
                                                 "height": "22px",
                                                 "lineHeight": "22px",
                                                 "textAlign": "center",
                                                 "fontSize": "0.75rem",
                                                 "fontWeight": "600",
                                                 "marginRight": "0.4rem"
                                             }),
                                    html.Span("Initial Sampling", 
                                             style={"fontWeight": "500", "fontSize": "0.85rem"})
                                ])
                            ], md=3, className="mb-2 mb-md-0"),
                            dbc.Col([
                                html.Div([
                                    html.Span("3",
                                             style={
                                                 "display": "inline-block",
                                                 "backgroundColor": "#6366f1",
                                                 "color": "white",
                                                 "borderRadius": "50%",
                                                 "width": "22px",
                                                 "height": "22px",
                                                 "lineHeight": "22px",
                                                 "textAlign": "center",
                                                 "fontSize": "0.75rem",
                                                 "fontWeight": "600",
                                                 "marginRight": "0.4rem"
                                             }),
                                    html.Span("Run & Record", 
                                             style={"fontWeight": "500", "fontSize": "0.85rem"})
                                ])
                            ], md=3, className="mb-2 mb-md-0"),
                            dbc.Col([
                                html.Div([
                                    html.Span("4",
                                             style={
                                                 "display": "inline-block",
                                                 "backgroundColor": "#10b981",
                                                 "color": "white",
                                                 "borderRadius": "50%",
                                                 "width": "22px",
                                                 "height": "22px",
                                                 "lineHeight": "22px",
                                                 "textAlign": "center",
                                                 "fontSize": "0.75rem",
                                                 "fontWeight": "600",
                                                 "marginRight": "0.4rem"
                                             }),
                                    html.Span("Optimize", 
                                             style={"fontWeight": "500", "fontSize": "0.85rem"})
                                ])
                            ], md=3),
                        ])
                    ], style={"padding": "1rem"})  # Réduit de 1.25rem
                ], style={
                    "borderRadius": "10px",
                    "border": "1px solid #e0e0e0",
                    "backgroundColor": "#f8f9fa"
                })
            ], md=12)
        ])
        
    ], fluid=True, style={
        "maxWidth": "1050px",  # Réduit de 1100px
        "marginTop": "1.5rem",  # Réduit de 2rem
        "paddingBottom": "2.5rem"  # Réduit de 3rem
    })
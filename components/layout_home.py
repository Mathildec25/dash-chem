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

def create_home_layout():
    return dbc.Container([
        # Welcome Header
        dbc.Row([
            dbc.Col([
                html.H1("Data Analysis & Optimization Platform", 
                       className="text-center mb-2",
                       style={"color": "#2c3e50", "fontWeight": "bold"}),
                html.P("Welcome to MET !!",
                      className="text-center text-muted mb-2",
                      style={"fontSize": "25px"})
            ], width=12)
        ], className="mt-4"),
        
        # Feature Cards Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-table", 
                                  style={"fontSize": "48px", "color": "#3498db"}),
                            html.H4("Dashboard", className="mt-3 mb-2"),
                            html.P("View and edit your data in a familiar spreadsheet format.",
                                  className="text-muted",
                                  style={"fontSize": "16px"})
                        ], className="text-center")
                    ])
                ], className="h-100 shadow hover-card")
            ], md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-graph-up", 
                                  style={"fontSize": "48px", "color": "#2ecc71"}),
                            html.H4("Visualization", className="mt-3 mb-2"),
                            html.P("Create interactive charts and explore your data.",
                                  className="text-muted",
                                  style={"fontSize": "16px"})
                        ], className="text-center")
                    ])
                ], className="h-100 shadow hover-card")
            ], md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-gear", 
                                  style={"fontSize": "48px", "color": "#95a5a6"}),
                            html.H4("Caracterization", className="mt-3 mb-2"),
                            html.P("Manage and track your experimental analysis.",
                                  className="text-muted",
                                  style={"fontSize": "16px"})
                        ], className="text-center")
                    ])
                ], className="h-100 shadow hover-card")
            ], md=3, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-calculator", 
                                  style={"fontSize": "48px", "color": "#e74c3c"}),
                            html.H4("Optimization", className="mt-3 mb-2"),
                            html.P("AI-powered recommendations for experiments.",
                                  className="text-muted",
                                  style={"fontSize": "16px"})
                        ], className="text-center")
                    ])
                ], className="h-100 shadow hover-card")
            ], md=3, className="mb-3"),
        ], className="mb-4"),
        
        # Main Action Section
        dbc.Card([
            dbc.CardBody([
                # Getting Started Section
                dbc.Row([
                    dbc.Col([
                        html.H3([
                            html.I(className="bi bi-rocket-takeoff me-2"),
                            "Getting Started"
                        ], className="mb-4", style={"color": "#34495e"}),
                    ], width=12)
                ]),
                
                # Step 1: Load Data
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.Span("Step 1: ", className="text-primary"),
                                    "Load or Select Data"
                                ], className="mb-0")
                            ], style={"backgroundColor": "#f8f9fa"}),
                            dbc.CardBody([
                                dbc.Tabs([
                                    dbc.Tab(label="📤 Upload", tab_id="upload-tab"),
                                    dbc.Tab(label="📂 Existing", tab_id="select-tab"),
                                    dbc.Tab(label="✨ New", tab_id="create-tab"),
                                ], id="file-tabs", active_tab="upload-tab", className="mb-3"),
                                
                                html.Div(id="tab-content", children=[
                                    # This will be populated by callback
                                ])
                            ])
                        ], className="mb-3")
                    ], width=12)
                ]),
                
                # File Selection Results
                html.Div(id='output-data-upload', className="mb-3"),
                
                # Step 2: Choose Action (Initially Hidden)
                html.Div(id="step-2-container", style={"display": "none"}, children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5([
                                        html.Span("Step 2: ", className="text-primary"),
                                        "Choose Your Action"
                                    ], className="mb-0")
                                ], style={"backgroundColor": "#f8f9fa"}),
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            dcc.Link(
                                                dbc.Button([
                                                    html.I(className="bi bi-table me-2"),
                                                    "Dashboard"
                                                ], 
                                                color="primary",
                                                size="lg",
                                                className="w-100 mb-2"
                                                ), 
                                                href="/table"
                                            ),
                                            html.Small("View and edit",
                                                      className="text-muted d-block text-center")
                                        ], md=6, lg=3, className="mb-3"),
                                        
                                        dbc.Col([
                                            dcc.Link(
                                                dbc.Button([
                                                    html.I(className="bi bi-graph-up me-2"),
                                                    "Visualization"
                                                ], 
                                                color="success",
                                                size="lg",
                                                className="w-100 mb-2"
                                                ), 
                                                href="/visu"
                                            ),
                                            html.Small("Charts & graphs",
                                                      className="text-muted d-block text-center")
                                        ], md=6, lg=3, className="mb-3"),
                                        
                                        dbc.Col([
                                            dcc.Link(
                                                dbc.Button([
                                                    html.I(className="bi bi-gear me-2"),
                                                    "Caracterization"
                                                ], 
                                                color="info",
                                                size="lg",
                                                className="w-100 mb-2"
                                                ), 
                                                href="/carac"
                                            ),
                                            html.Small("Analysis",
                                                      className="text-muted d-block text-center")
                                        ], md=6, lg=3, className="mb-3"),
                                        
                                        dbc.Col([
                                            dcc.Link(
                                                dbc.Button([
                                                    html.I(className="bi bi-calculator me-2"),
                                                    "Optimization"
                                                ], 
                                                color="warning",
                                                size="lg",
                                                className="w-100 mb-2"
                                                ), 
                                                href="/Opt-home"
                                            ),
                                            html.Small("AI optimization",
                                                      className="text-muted d-block text-center")
                                        ], md=6, lg=3, className="mb-3"),
                                    ], justify="center")
                                ])
                            ])
                        ], width=12)
                    ])
                ]),
                
                # Hidden components for file handling
                html.Div(style={"display": "none"}, children=[
                    dcc.Dropdown(id="excels-DD", options=[], value=None),
                    html.Div(id='sheets-DD'),
                    html.H5(id="text-DD-1"),
                    html.H5(id="text-DD-2"),
                    html.Div(id="redirec-button"),
                    dbc.Button(id="delete-excel-button")
                ])
            ])
        ], className="shadow"),
        
    ], fluid=True, style={"maxWidth": "1400px"})
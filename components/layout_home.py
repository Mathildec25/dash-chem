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
                            html.P("View and edit your data in a familiar spreadsheet format. "
                                  "Filter, sort, and manage your experimental data with ease.",
                                  className="text-muted",
                                  style={"fontSize": "16px"})
                        ], className="text-center")
                    ])
                ], className="h-100 shadow-sm hover-card")
            ], md=4, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-graph-up", 
                                  style={"fontSize": "48px", "color": "#2ecc71"}),
                            html.H4("Visualization", className="mt-3 mb-2"),
                            html.P("Create interactive charts and graphs. Explore your data with "
                                  "histograms, scatter plots, and other visualization tools.",
                                  className="text-muted",
                                  style={"fontSize": "16px"})
                        ], className="text-center")
                    ])
                ], className="h-100 shadow-sm hover-card")
            ], md=4, className="mb-3"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-calculator", 
                                  style={"fontSize": "48px", "color": "#e74c3c"}),
                            html.H4("Optimization", className="mt-3 mb-2"),
                            html.P("Use Bayesian Optimization to find optimal experimental conditions. "
                                  "AI-powered recommendations for your next experiments.",
                                  className="text-muted",
                                  style={"fontSize": "16px"})
                        ], className="text-center")
                    ])
                ], className="h-100 shadow-sm hover-card")
            ], md=4, className="mb-3"),
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
                
                # Step 1: Upload or Select File
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
                                    dbc.Tab(label="Upload New File", tab_id="upload-tab"),
                                    dbc.Tab(label="Select Existing File", tab_id="select-tab"),
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
                                    html.P("Great! Your data is ready. Now choose what you want to do:",
                                          className="text-muted mb-3"),
                                    
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
                                            html.Small("View and edit your data",
                                                      className="text-muted")
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
                                            html.Small("Create charts and graphs",
                                                      className="text-muted")
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
                                            html.Small("Manage analysis",
                                                      className="text-muted")
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
                                            html.Small("Start Bayesian Optimization",
                                                      className="text-muted")
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
        
        # Help Section
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H6([
                        html.I(className="bi bi-info-circle me-2"),
                        "Need Help?"
                    ], className="alert-heading"),
                    html.Hr(),
                    html.P([
                        html.Strong("Dashboard: "),
                        "Perfect for data entry and quick edits. Works like Excel."
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Visualization: "),
                        "Best for understanding trends and patterns in your data."
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Caracterization: "),
                        "Need to be updated"
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Optimization: "),
                        "Use when you want AI to suggest your next experiments."
                    ], className="mb-0"),
                ], color="info", className="mt-4")
            ], width=12)
        ])
    ], fluid=True, style={"maxWidth": "1400px"})
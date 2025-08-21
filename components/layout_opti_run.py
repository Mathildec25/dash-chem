import dash
from dash import html, dcc, dash_table, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import os
from excel_storage import EXCEL_FOLDER


## MAIN LAYOUT ##
def create_opti_run_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Optimization Run Part", className="display-4",
                        style={"textAlign": "center","marginTop":"5px", "marginBottom": "20px"}),
            ], width=12),
        ]),

        dbc.Tabs([
            dbc.Tab(label="Optimization & Data", tab_id="bo-tab"),
            dbc.Tab(label="Visualization", tab_id="viz-tab"),
        ], id="opti-run-tabs", active_tab="bo-tab", className="mb-3"),

        html.Div(id="opti-run-tab-content")
    ], fluid=True)


## TABS LAYOUT ##

# Tab 1 content = current workflow
def get_bo_tab_content():
    return html.Div([
        # Dynamic table container
        html.Div(id="excel-table-container"),

        html.Br(),

        # Action buttons
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    " Add Row", 
                    id="add-row-btn", 
                    color="secondary", 
                    size="lg",
                    className="me-2 bi bi-plus-square"
                )
            ], width="auto"),
            dbc.Col([
                dbc.Button(
                    " Save Excel", 
                    id="save-excel-btn-opti", 
                    color="primary", 
                    size="lg",
                    className="me-2 bi bi-save"
                )
            ], width="auto"),
            dbc.Col([
                dbc.Button(
                    " Run BO",  
                    id="run-BO-btn",
                    n_clicks=0, 
                    color="success", 
                    size="lg",
                    className="me-2 bi bi-play-circle"
                )
            ], width="auto"),
        ], justify="center"),

        html.Br(),

        # Status messages (including experiment counter, BO status, etc.)
        html.Div(id="save-status", className="text-center mb-3"),
        html.Div(id="experiment-counter", className="text-center fw-bold text-primary mb-3"),

        dcc.Store(id="optimization-store", data={}),

        # Optimization modal
        dbc.Modal([
            dbc.ModalBody([
                html.Div([
                    dbc.Spinner(
                        color="primary",
                        size="lg",
                        spinner_style={"width": "3rem", "height": "3rem"}
                    ),
                    html.H4("Running Bayesian Optimization", className="mt-3"),
                    html.P("Please wait while we calculate the next optimal experiment...", className="text-muted"),
                    html.P([
                        html.I(className="bi bi-info-circle me-2"),
                        "This may take a few moments depending on your data complexity."
                    ], className="small text-info")
                ], className="text-center")
            ])
        ], id="loading-modal", is_open=False, centered=True, backdrop="static", keyboard=False),

        # Optimization results
        dcc.Loading(
            id="loading-optimization",
            type="circle",
            children=[
                html.Div(id="optimization-results", className="mt-4"),
            ],
            color="#007bff",
            style={"marginTop": "20px"}
        ),
    ])


# Tab 2 content = visualization placeholder
# ============================================
# UPDATED VISUALIZATION TAB CONTENT
# ============================================

def get_visualization_tab_content():
    """Create the visualization tab layout with parallel coordinates and iteration plot"""
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H4([
                    html.I(className="bi bi-graph-up me-2"),
                    "Optimization Visualization Dashboard"
                ], className="text-primary mb-0")
            ]),
            dbc.CardBody([
                # Info section
                dbc.Alert([
                    html.H6("📊 Visualization Tools", className="alert-heading"),
                    html.Hr(),
                    html.P([
                        "Multiple views of your optimization data:",
                        html.Br(),
                        html.Strong("Parallel Coordinates: "), "Shows relationships between all parameters and objectives.",
                        html.Br(),
                        html.Strong("Objectives Scatter: "), "2D/3D scatter plot of objectives.",
                        html.Br(),
                        html.Strong("Iteration Plot: "), "Track how objectives change over experiment iterations."
                    ], className="mb-2"),
                ], color="info", className="mb-3"),
                
                # Plot container for parallel coordinates
                dcc.Loading(
                    id="loading-viz",
                    type="circle",
                    children=[
                        dcc.Graph(
                            id="parallel-coordinates-plot",
                        ),
                    ]
                ),
                
                # NEW SECTION: Interactive Objectives Scatter with Controls
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="bi bi-scatter-chart me-2"),
                            "Interactive Objectives Scatter Plot"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        # Controls row
                        dbc.Row([
                            dbc.Col([
                                html.Label("X-Axis:", className="form-label"),
                                dcc.Dropdown(
                                    id="scatter-x-dropdown",
                                    placeholder="Select X axis...",
                                    className="mb-2"
                                )
                            ], width=4),
                            dbc.Col([
                                html.Label("Y-Axis:", className="form-label"),
                                dcc.Dropdown(
                                    id="scatter-y-dropdown",
                                    placeholder="Select Y axis...",
                                    className="mb-2"
                                )
                            ], width=4),
                            dbc.Col([
                                html.Label("Z-Axis (3D):", className="form-label"),
                                dcc.Dropdown(
                                    id="scatter-z-dropdown",
                                    placeholder="Select Z axis (optional)...",
                                    className="mb-2"
                                )
                            ], width=4),
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                html.Label("Color By:", className="form-label"),
                                dcc.Dropdown(
                                    id="scatter-color-dropdown",
                                    placeholder="Select color column (optional)...",
                                    className="mb-2"
                                )
                            ], width=4),
                            dbc.Col([
                                html.Label("Size By:", className="form-label"),
                                dcc.Dropdown(
                                    id="scatter-size-dropdown",
                                    placeholder="Select size column (optional)...",
                                    className="mb-2"
                                )
                            ], width=4),
                            dbc.Col([
                                dbc.Button(
                                    "Generate Scatter Plot",
                                    id="generate-scatter-btn",
                                    color="primary",
                                    size="lg",
                                    className="mt-4"
                                )
                            ], width=4),
                        ], className="mb-3"),
                        
                        # Plot container for objectives scatter
                        dcc.Loading(
                            id="loading-scatter",
                            type="circle",
                            children=[
                                dcc.Graph(
                                    id="objectives-scatter",
                                    style={"height": "600px"}
                                ),
                            ]
                        ),
                    ])
                ], className="mb-3"),
                
                html.Hr(),
                
                # NEW SECTION: Iteration Plot with Controls
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="bi bi-graph-up-arrow me-2"),
                            "Iteration Progress Plot"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        # Controls row
                        dbc.Row([
                            dbc.Col([
                                html.Label("Y-Axis (Objective):", className="form-label"),
                                dcc.Dropdown(
                                    id="iteration-y-dropdown",
                                    placeholder="Select objective to plot...",
                                    className="mb-3"
                                )
                            ], width=6),
                        ], className="mb-3"),
                        
                        # Plot container for iteration plot
                        dcc.Loading(
                            id="loading-iteration",
                            type="circle",
                            children=[
                                dcc.Graph(
                                    id="iteration-plot",
                                    style={"height": "500px"}
                                ),
                            ]
                        ),
                    ])
                ], className="mt-3")
            ])
        ])
    ])
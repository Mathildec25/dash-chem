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
    """Create the visualization tab layout with parallel coordinates"""
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
                    html.H6("📊 Parallel Coordinates Plot", className="alert-heading"),
                    html.Hr(),
                    html.P([
                        "This plot shows the relationships between all parameters and objectives in your experiments.",
                        html.Br(),
                        html.Strong("How to read: "),
                        "Each line represents one experiment. Follow the lines across to see how parameter values relate to objective outcomes."
                    ], className="mb-2"),
                ], color="info", className="mb-3"),
                
                # Plot container
                dcc.Loading(
                    id="loading-viz",
                    type="circle",
                    children=[
                        dcc.Graph(
                            id="parallel-coordinates-plot",
                        ),
                    ]
                ),
                
                dcc.Loading(
                    id="loading-scatter",
                    type="circle",
                    children=[
                        dcc.Graph(
                            id="objectives-scatter",
                        ),
                    ]
                ),
            ])
        ])
    ])
import dash
from dash import html, dcc, dash_table, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import os
from excel_storage import EXCEL_FOLDER


# This function creates the layout for the dashboard page 
def create_opti_run_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Optimization Run part", className="display-4", style={"textAlign": "center","marginTop":"5px", "marginBottom": "20px"}),
            ], width=12),
        ]),
        html.Div([
            
            # Dynamic table container - will be populated by callback
            html.Div(id="excel-table-container"),
            
            html.Br(),
            
            # Action buttons
            html.Div([
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
                ], justify="center")
            ]),
            
            html.Br(),
            
            # Status messages
            html.Div(id="save-status", className="text-center"),

            dcc.Store(id="optimization-store", data={}),
            
            # Optimization results area
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
            
            # Optimization results area with loading wrapper
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
    ])
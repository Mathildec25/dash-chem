import dash
from dash import html, dcc, dash_table, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import os
from excel_storage import SAVE_FOLDER


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
                            " Start BO",  # Fixed typo: was "Strat BO"
                            id="run-BO-btn", 
                            color="success", 
                            size="lg",
                            className="me-2 bi bi-play-circle"
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
                            " Add Row", 
                            id="add-row-btn", 
                            color="secondary", 
                            size="lg",
                            className="me-2 bi bi-plus-square"
                        )
                    ], width="auto"),
                ], justify="center")
            ]),
            
            html.Br(),
            
            # Status messages
            html.Div(id="save-status", className="text-center"),
            
            # Optimization results area
            html.Div(id="optimization-results", className="mt-4"),
            
        ])
    ])
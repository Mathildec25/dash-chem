import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
import os
from excel_storage import SAVE_FOLDER, TRACKING_FILE, TRACKING_FILENAME

def load_tracked_files():
    if os.path.exists(TRACKING_FILE):
        df = pd.read_excel(TRACKING_FILE)
        return [{'label': fname, 'value': fname} for fname in df['filename'].dropna()]
    return []

# This function creates the layout for the dashboard page 
def create_opti_home_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Optimization Home", className="display-4", style={"textAlign": "center","marginTop":"5px", "marginBottom": "20px"}),
            ], width=12),
        ]),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H5(
                                id="text-DD-1",
                                children=[
                                    "Create a New Project Here"
                                ], 
                                style={"fontSize":"20px", "textAlign":"left"}
                            ),
                            dbc.Input(
                                id="new-proj",
                                type="text",
                                placeholder="Enter the Name...",
                            ),
                            html.Div(
                                dcc.Link(
                                    dbc.Button(
                                        " GO",
                                        id="start-opti-button",
                                        color="success",
                                        className="bi bi-rocket-takeoff",
                                        style={"marginTop": "12px", "display": "none"}
                                    ), href="/Opt-param"),
                                id="start-opti-button-container"
                            ),
                        ]),
                    ], width=12),
                ]),
                ])
        ], 
        color="#ff9e3d",
        outline=False,
        style={"margin": "20px", "minHeight": "200px", "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)", "borderRadius": "10px" }, className="h-auto"),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H5(
                                id="text-DD-1-existing",
                                children=[
                                    "Select the excel file here"
                                ], 
                                style={"fontSize":"20px", "textAlign":"left"}
                            ),
                            dcc.Dropdown(
                                id="excels-DD-opti",
                                options=load_tracked_files(),
                                placeholder="Select an excel file...",
                            ),
                            html.Div(id='domain-status-display'),
                            html.Div(
                                dbc.Button(
                                    " Delete selected Excel",
                                    id="delete-excel-button-opti",
                                    color="danger",
                                    className="bi bi-trash",
                                    style={"marginTop": "12px", "display": "none"}
                                ),
                                id="delete-button-container"
                            ),
                            html.H5(
                                id="text-DD-2-opti",
                                children=[
                                    "Select the sheet here"
                                ], 
                                style={"display":"none"}
                            ),
                            html.Div(id='sheets-DD-opti'),
                            html.Div(
                                dcc.Link(
                                    dbc.Button(
                                        " GO",
                                        id="restart-opti-button",  # Fixed: removed extra space
                                        color="success",
                                        className="bi bi-rocket-takeoff",
                                        style={"marginTop": "12px", "display": "none"}
                                    ), href="/Opt-run"),
                                id="restart-opti-button-container"
                            ),
                        ]),
                    ], width=12),
                ]),
                ])
        ], 
        color="#ff9e3d",
        outline=False,
        style={"margin": "20px", "minHeight": "200px", "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)", "borderRadius": "10px" }, className="h-auto"),
    ])
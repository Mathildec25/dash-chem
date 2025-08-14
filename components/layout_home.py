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

def create_home_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div([
                            dbc.Button(
                            ' Upload your Excel file here',
                            className="bi bi-upload",
                            style={"fontSize": "30px"},
                            color="primary"
                            )
                        ]),
                        multiple=True,    
                    ),
                    html.Div(id='output-data-upload'),
                ])
            ], width="auto"),
            # Add excel part id needed
            # dbc.Col([
            #     html.Div([
            #         dbc.Button(
            #             " New Excel file",
            #             id="create-excel-button",
            #             className="bbi bi-file-earmark-plus",
            #             style={"fontSize": "30px", "marginLeft": "10px"},
            #             color="primary"
            #         ),
            #         dbc.Modal([
            #             dbc.ModalHeader("Create a new Excel file"),
            #             dbc.ModalBody([
            #                 dcc.Input(
            #                     id='new-excel-name',
            #                     type='text',
            #                     placeholder='Enter a name (without extension)',
            #                     style={'width': '100%'}
            #                 ),
            #             ]),
            #             dbc.ModalFooter([
            #                 dbc.Button("Create", id="confirm-create-excel", color="success"),
            #                 dbc.Button("Cancel", id="cancel-create-excel", color="secondary"),
            #             ]),
            #         ],
            #         id="excel-modal",
            #         is_open=False),
            #     ]),
            # ], width="auto"),
        ], justify="center", align="center", className="mt-4"),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H5(
                                id="text-DD-1",
                                children=[
                                    "Select the excel file here"
                                ], 
                                style={"fontSize":"20px", "textAlign":"left"}
                            ),
                            dcc.Dropdown(
                                id="excels-DD",
                                options=load_tracked_files(),
                                placeholder="Select an excel file...",
                            ),
                            html.Div(
                                dbc.Button(
                                    " Delete selected Excel",
                                    id="delete-excel-button",
                                    color="danger",
                                    className="bi bi-trash",
                                    style={"marginTop": "12px", "display": "none"}
                                ),
                                id="delete-button-container"
                            ),
                            html.H5(
                                id="text-DD-2",
                                children=[
                                    "Select the sheet here"
                                ], 
                                style={"display":"none"}
                            ),
                            html.Div(id='sheets-DD'),
                        ]),
                    ], width=12),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            id="redirec-button",
                            children=[
                                dcc.Link(dbc.Button(children=["Dashboard"], className="bi-table", style={"fontSize": "28px"}), href="/table"),
                                dcc.Link(dbc.Button(children=["Visualization"],className="bi-graph-up", style={"fontSize": "28px", "marginLeft": "25px"}), href="/visu"),
                                dcc.Link(dbc.Button(children=["Caracterization"],className="bi-gear", style={"fontSize": "28px", "marginLeft": "25px"}), href="/carac"),
                                dcc.Link(dbc.Button(children=["Optimization"],className="bi-calculator", style={"fontSize": "28px", "marginLeft": "25px"}), href="/Bay-Opt"),
                            ],
                            style={"display": "none", "alignItems": "center", "justifyContent": "center", "padding": "80px"}
                        ),
                    ], width=12),
                ]),
            ])
        ], 
        color="#ff9e3d",
        outline=False,
        style={"margin": "20px", "minHeight": "200px", "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)", "borderRadius": "10px" }, className="h-auto"),
        ## If video is needed
        # dbc.Row([
        #     dbc.Col([
        #         dbc.Card(
        #             color="gray", 
        #             inverse=True,
        #             style={"height": "480px", "marginTop":"5px"}, 
        #             children=[
        #                 html.Div([
        #                     html.Video(
        #                         src="/assets/Select-a-sheet.mp4",
        #                         autoPlay=True,
        #                         loop=True,
        #                         style={"width": "90%", "height": "90%", "objectFit": "contain"} 
        #                     )
        #                 ], style={"display": "flex", "justifyContent": "center", "alignItems": "center", "height": "100%"}),
        #             ]
        #         )
        #     ], width=12),
        # ]),
])
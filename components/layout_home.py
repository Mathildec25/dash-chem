import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd

excel_files = ["results.xlsx","Test-1.xlsx","Test-2.xlsx"]
all_names=[]
for i in range(len(excel_files)):
    names = pd.ExcelFile(excel_files[i]).sheet_names
    all_names.append(names)

def create_home_layout():
    return dbc.Container([
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
                                options=[{"label": f"{name}"[:-5],"value": name} for name in excel_files],
                                placeholder="Select an excel file...",
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
        style={"margin": "20px", "minHeight": "200px", "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)", "borderRadius": "10px" }, className="h-auto")
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
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
        dbc.Row([
            dbc.Col([
                html.H2("Welcome to MET", className="display-2", style={"textAlign": "center", "marginTop":"5px", "color": "#f96052"}),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="bi bi-arrow-down", 
                        style={"fontSize": "3rem", "marginRight": "8px", "marginTop":"5px", "color": "#f96052"}),
                    html.H4("Please select a sheet to work on", 
                        className="display-5", 
                        style={"marginTop": "5px", "color": "#ff9e3d", "display": "inline-block"}),
                    html.I(className="bi bi-arrow-down", 
                        style={"fontSize": "3rem", "marginLeft": "8px", "marginTop":"5px", "color": "#f96052"})  
                ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
            ])
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Dropdown(
                        id = "excels-DD",
                        options=[{"label": f"{name}"[:-5],"value": name} for name in excel_files],
                        placeholder="Select an excel file...",
                    ),
                    html.Div(id='sheets-DD'),
                ]),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Link(dbc.Button(className="bi-table", style={"fontSize": "85px"}), href="/table"),
                    dcc.Link(dbc.Button(className="bi-graph-up", style={"fontSize": "85px", "marginLeft": "50px"}), href="/visu"),
                    dcc.Link(dbc.Button(className="bi-gear", style={"fontSize": "85px", "marginLeft": "50px"}), href="/carac"),
                    dcc.Link(dbc.Button(className="bi-calculator", style={"fontSize": "85px", "marginLeft": "50px"}), href="/Bay-Opt"),
                ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "padding": "80px"}),
            ], width=12),
        ]),
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
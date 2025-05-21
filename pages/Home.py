import dash
from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update
import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd


# Include this file as a page in the Dash app
dash.register_page(__name__, name="Home", path="/", order=1)

excel_files = ["results.xlsx","Test-1.xlsx","Test-2.xlsx"]
all_names=[]
for i in range(len(excel_files)):
    names = pd.ExcelFile(excel_files[i]).sheet_names
    all_names.append(names)

# Define the layout of the page using the function from layout_display.py
layout = dbc.Container([
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
                dbc.Card(
                    color="gray", 
                    inverse=True,
                    style={"height": "480px", "marginTop":"5px"}, 
                    children=[
                        html.Div([
                            html.Video(
                                src="/assets/Select-a-sheet.mp4",
                                autoPlay=True,
                                loop=True,
                                style={"width": "90%", "height": "90%", "objectFit": "contain"} 
                            )
                        ], style={"display": "flex", "justifyContent": "center", "alignItems": "center", "height": "100%"}),
                    ]
                )
            ], width=12),
        ]),
])

@callback(
    Output('sheets-DD', 'children'),
    Input('excels-DD', 'value')
)
def update_sub_dropdown(selected_excel):
    if selected_excel == 'results.xlsx':
        return dcc.Dropdown(
            id='results-DD',
            options=[
               {"label": name,"value": name} for name in all_names[0] 
            ],
            placeholder="Select a sheet..."
        )
    elif selected_excel == 'Test-1.xlsx':
        return dcc.Dropdown(
            id='Test-1-DD',
            options=[
               {"label": name,"value": name} for name in all_names[1]
            ],
            placeholder="Select a sheet..."
        )
    elif selected_excel == 'Test-2.xlsx':
        return dcc.Dropdown(
            id='Test-2-DD',
            options=[
               {"label": name,"value": name} for name in all_names[2]
            ],
            placeholder="Select a sheet..."
        )
    return None
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State, dcc, MATCH, ALL, dash_table, html, no_update
import pandas as pd
from utils.data_handling import load_filtered_df, get_columns_carac, get_column_dropdown_options


dff = pd.read_excel("Test-caracterization.xlsx")
df = dff.copy()
columns = get_columns_carac(df)

# This function creates the layout for the caracterization page 
def create_carac_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Caracterization Table", className="display-4", style={"textAlign": "center", "marginBottom": "20px", "marginTop": "8px"}),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                dash_table.DataTable(
                    id="carac-table",
                    data=df.to_dict('records'),
                    columns=columns,
                    dropdown={
                        col: {
                            'options': [
                                {'label': '✅', 'value': 'Yes'},
                                {'label': '❌', 'value': 'No'}
                            ]
                        } for col in df.columns if col in ["NMR H", "NMR C", "GC", "LC"]
                    },
                    css=[
                        {"selector": ".dash-spreadsheet-container", "rule": "max-height: 100vh !important; height: 75vh !important;"},
                        {"selector": ".dash-spreadsheet-inner", "rule": "max-height: 100vh !important; height: 75vh !important;"},
                        {"selector": ".dash-table-container", "rule": "max-height: 100vh !important; height: 75vh !important;"}
                    ],
                    editable=True,
                    style_header={
                        'backgroundColor': 'white', 'textAlign': 'center', 'fontSize': '14px',
                        'fontWeight': 'bold', 'border': '1px solid black'
                    },
                    fixed_rows={'headers': True},
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
                    ],    
                    style_as_list_view=True,
                    style_cell={'padding': '8px','textAlign': 'center'},
                    page_action='none',
                    style_table={'width': '99.5%', 'overflowY': 'auto', 'overflowX': 'auto'},
                    filter_action='native',
                    sort_action='native',
                    sort_mode='single',
                    filter_options={"placeholder_text": "Filter.."},
                )
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Button("Add Row", id="editing-rows-button-carac", n_clicks=0),
                    dbc.Button("Save Changes", id="save-button-carac", n_clicks=0, style={"marginLeft": "10px"}),
                ], style={"padding": "15px"}),
            ], width=12),
        ]),
    ])
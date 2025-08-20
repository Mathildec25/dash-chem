import dash_bootstrap_components as dbc
from dash import dcc, html

# This function creates the layout for the dashboard page 
def create_dashboard_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Display part", className="display-4", style={"textAlign": "center", "marginBottom": "35px"}),
            ], width=12),
        ]),
        # Allow to choose which columns to display in the table
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Accordion([
                        dbc.AccordionItem([
                            dcc.Dropdown(
                                id="column-dropdown",
                                options=[],
                                value=[],
                                multi=True,
                                placeholder="Select columns to display",
                                style={"width": "100%"}
                            )
                        ], title="Select columns")
                    ], start_collapsed=True)
                ], style={"marginTop": "0px", "marginBottom": "9px"}),
            ], width=12),
        ]),
        # Display the table with the selected columns
        dbc.Row([
            dbc.Col([
                html.Div(id="main-content")
            ], width=12),
        ]),
        # Buttons to add a row and save changes
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Button("Add Row", id="editing-rows-button", n_clicks=0),
                    dbc.Button("Save Changes", id="save-button", n_clicks=0, style={"marginLeft": "10px"}),
                ], style={"padding": "15px"}),
            ], width=12),
        ]),
    ])
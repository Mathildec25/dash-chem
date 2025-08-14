import dash
from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update, dcc, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from utils.data_handling import load_filtered_df, get_columns, get_column_dropdown_options
import pandas as pd
import uuid
import json
import os

## OBJECTIVES PART ##

# Add a new objective block
@callback(
    Output("objective-container", "children", allow_duplicate=True),
    Input("add-objective-button", "n_clicks"),
    State("objective-container", "children"),
    prevent_initial_call="initial_duplicate"
)
def add_new_objective(n_clicks, current_children):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    new_id = str(uuid.uuid4())

    new_block = html.Div(
        id={'type': 'objective-block', 'index': new_id},
        children=[
            dbc.Row(
                children=[
                    dbc.Col([
                        dbc.Label("Name of the objective"),
                        dbc.Input(
                            id={'type': 'objective-name', 'index': new_id},
                            placeholder="Type here...",
                            type="text",
                            size="sm",
                            style={"fontSize": "18px"}
                        ),
                    ], width=3),
                    dbc.Col([
                        html.Div(id={'type': 'objective-direction-container', 'index': new_id})
                    ], width=3),
                    dbc.Col([
                        html.Div(id={'type': 'objective-bounds-container', 'index': new_id})
                    ], width=4),
                    dbc.Col([
                        dbc.Button(
                            "✕",
                            id={'type': 'delete-objective-btn', 'index': new_id},
                            color="danger",
                            size="sm",
                        )
                    ], width=2),
                ],
                style={"marginBottom": "10px"}
            )
        ]
    )

    return current_children + [new_block]

# Display the dropdown to choose Min/Max
@callback(
    Output({'type': 'objective-direction-container', 'index': MATCH}, 'children'),
    Input({'type': 'objective-name', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def show_objective_direction(name):
    if not name:
        return ""

    return html.Div([
        dbc.Label("Select direction"),
        dcc.Dropdown(
            id={'type': 'objective-direction', 'index': ctx.triggered_id['index']},
            options=[
                {"label": "Minimize", "value": "min"},
                {"label": "Maximize", "value": "max"},
            ],
            placeholder="Choose direction",
        )
    ])

# Delete objective block and saved information
@callback(
    Output("objective-container", "children", allow_duplicate=True),
    Output("objective-store", "data", allow_duplicate=True),
    Input({'type': 'delete-objective-btn', 'index': ALL}, 'n_clicks'),
    State("objective-container", "children"),
    State("objective-store", "data"),
    prevent_initial_call=True
)
def delete_objective(n_clicks_list, current_children, stored_data):
    ctx_trigger = ctx.triggered_id
    if not ctx_trigger:
        raise dash.exceptions.PreventUpdate
    
    # Check if any delete button was actually clicked
    if not any(n_clicks_list) or all(clicks is None for clicks in n_clicks_list):
        raise dash.exceptions.PreventUpdate

    delete_index = ctx_trigger['index']

    # Remove the block from the layout
    new_children = [
        child for child in current_children
        if child['props']['id']['index'] != delete_index
    ]

    # Remove the corresponding objective from the store
    new_store = [
        obj for obj in stored_data
        if obj.get('id') != delete_index  # Assuming you store the ID
    ]

    return new_children, new_store

# Save objectives part information described by the user
@callback(
    Output("objective-store", "data"),
    Output("objective-display", "children"),
    Input("save-objectives-btn", "n_clicks"),
    Input({"type": "objective-name", "index": ALL}, "value"),
    Input({"type": "objective-direction", "index": ALL}, "value"),
    Input({"type": "objective-lower-bound", "index": ALL}, "value"),
    Input({"type": "objective-upper-bound", "index": ALL}, "value"),
    State("objective-store", "data"),
    prevent_initial_call=False
)
def update_objectives(n_clicks, names, directions, lowers, uppers, current_store):
    triggered_id = ctx.triggered_id

    objectives = []
    for name, direction, lower, upper in zip(names, directions, lowers, uppers):
        if name and direction:
            objectives.append({
                "name": name,
                "direction": direction,
                "lower_bound": lower,
                "upper_bound": upper
            })

    display = html.Pre(
        json.dumps(objectives, indent=2),
        style={"whiteSpace": "pre-wrap", "fontSize": "14px"}
    )

    if triggered_id == "save-objectives-btn" and n_clicks:
        return objectives, display
    else:
        return dash.no_update, display
    
# Display lower and upper bounds inputs
@callback(
    Output({'type': 'objective-bounds-container', 'index': MATCH}, 'children'),
    Input({'type': 'objective-name', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def show_objective_bounds(name):
    if not name:
        return ""
    
    return html.Div([
        dbc.Label("Bounds (Lower / Upper)"),
        dbc.Row([
            dbc.Col(
                dbc.Input(
                    id={'type': 'objective-lower-bound', 'index': ctx.triggered_id['index']},
                    type="number",
                    placeholder="Lower bound",
                    size="sm"
                ), width=6
            ),
            dbc.Col(
                dbc.Input(
                    id={'type': 'objective-upper-bound', 'index': ctx.triggered_id['index']},
                    type="number",
                    placeholder="Upper bound",
                    size="sm"
                ), width=6
            )
        ])
    ])
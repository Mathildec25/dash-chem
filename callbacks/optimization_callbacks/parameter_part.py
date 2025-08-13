import dash
from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update, dcc, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from utils.data_handling import load_filtered_df, get_columns, get_column_dropdown_options
import pandas as pd
import uuid
import json
import os

## PARAMETERS PART ##

# Update layout dynamically
@callback(
    Output({'type': 'parameter-type-container', 'index': MATCH}, 'children'),
    Input({'type': 'parameter-name', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def show_type_dropdown(name):
    if not name:
        return ""

    return html.Div([
        dbc.Label("Select the type"),
        dcc.Dropdown(
            id={'type': 'parameter-type', 'index': ctx.triggered_id['index']},
            options=[
                {"label": "Integer", "value": "int"},
                {"label": "Continuous", "value": "float"},
                {"label": "Categorical", "value": "cat"},
                {"label": "Ordinal", "value": "ord"},
                {"label": "Chemical", "value": "chem"},
            ],
            placeholder="Select type",
            style={"fontSize": "18px"},
        )
    ])

# Add a new parameter block
@callback(
    Output("parameter-container", "children", allow_duplicate=True),
    Input("add-para-button", "n_clicks"),
    State("parameter-container", "children"),
    prevent_initial_call="initial_duplicate"
)
def add_new_parameter(n_clicks, current_children):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    new_id = str(uuid.uuid4())

    new_block = html.Div(
        id={'type': 'parameter-block', 'index': new_id},
        children=[
            dbc.Row(
                children=[
                    dbc.Col([
                        dbc.Label("Name of the parameter"),
                        dbc.Input(
                            id={'type': 'parameter-name', 'index': new_id},
                            placeholder="Type here...",
                            type="text",
                            size="sm",
                            style={"fontSize": "18px"}
                        ),
                    ], width=5),
                    dbc.Col([
                        html.Div(id={'type': 'parameter-type-container', 'index': new_id})
                    ], width=5),
                    dbc.Col([
                        dbc.Button(
                            "✕",
                            id={'type': 'delete-parameter', 'index': new_id},
                            color="danger",
                            size="sm"
                        )
                    ], width=2)
                ],
                style={"marginBottom": "10px"}
            ),
            html.Div(id={'type': 'parameter-type-specific-container', 'index': new_id})
        ]
    )

    return current_children + [new_block]

# Add the component according to the type selected
@callback(
    Output({'type': 'parameter-type-specific-container', 'index': MATCH}, 'children'),
    Input({'type': 'parameter-type', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def render_type_specific_component(selected_type):
    if not selected_type:
        return ""

    if selected_type in ['int', 'float']:
        # RangeSlider with reasonable default min/max and marks
        return dbc.Row([
            dbc.Label("Select range:", style={"marginBottom": "5px"}),
            dcc.RangeSlider(
                min=-200, max=200, step=1 if selected_type=='int' else 0.1,
                marks={i: str(i) for i in range(-200, 200, 20)},
                tooltip={"placement": "bottom", "always_visible": True},
                id={'type': 'parameter-type-specific', 'index': ctx.triggered_id['index']}
            )
        ], style={"marginBottom": "15px"})

    elif selected_type in ['cat', 'chem']:
        # Upload component
        return dbc.Row([
            dbc.Label("Upload values:", style={"marginBottom": "5px"}),
            dcc.Upload(
                id={'type': 'parameter-type-specific', 'index': ctx.triggered_id['index']},
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'marginBottom': '15px'
                },
                multiple=True
            )
        ])

    elif selected_type == 'ord':
        # Input box for ordinal values
        return dbc.Row([
            dbc.Label("Enter ordinal values:", style={"marginBottom": "5px"}),
            dbc.Input(
                id={'type': 'parameter-type-specific', 'index': ctx.triggered_id['index']},
                placeholder="Enter values separated by commas",
                type="text",
                style={"marginBottom": "15px"}
            )
        ])

    else:
        return ""
    
# Save parameters part information described by the user / auto-update display if one is removed
@callback(
    Output("parameter-store", "data"),
    Output("parameter-display", "children"),
    Input("save-parameters-btn", "n_clicks"),
    Input({"type": "parameter-name", "index": ALL}, "value"),
    Input({"type": "parameter-type", "index": ALL}, "value"),
    Input({"type": "parameter-type-specific", "index": ALL}, "value"),
    State("parameter-store", "data"),
    prevent_initial_call=False
)
def update_parameters(n_clicks, names, types, type_values, current_store):
    triggered_id = ctx.triggered_id

    # Build the parameters list from current inputs
    parameters = []
    for name, typ, typ_val in zip(names, types, type_values):
        if name and typ:
            parameters.append({
                "name": name,
                "type": typ,
                "type_info": typ_val
            })

    # Prepare the display (always update)
    display = html.Pre(
        json.dumps(parameters, indent=2),
        style={"whiteSpace": "pre-wrap", "fontSize": "14px"}
    )

    # Update store data only if Save button triggered this callback
    if triggered_id == "save-parameters-btn" and n_clicks:
        return parameters, display
    else:
        # If triggered by other inputs (e.g., parameter changes), update display but keep store as-is
        return dash.no_update, display

# Delete parametre block and saved information
@callback(
    Output("parameter-container", "children", allow_duplicate=True),
    Output("parameter-store", "data", allow_duplicate=True),
    Input({'type': 'delete-parameter', 'index': ALL}, 'n_clicks'),
    State("parameter-container", "children"),
    State("parameter-store", "data"),
    prevent_initial_call=True
)
def delete_parameter(n_clicks_list, container_children, stored_data):
    if not any(n_clicks_list):
        raise PreventUpdate

    # Find which delete button was clicked
    triggered_id = ctx.triggered_id
    if not triggered_id:
        raise PreventUpdate

    index_to_delete = triggered_id['index']

    # Remove the block with that index from container children
    new_children = []
    for child in container_children:
        if child['props']['id'].get('index') != index_to_delete:
            new_children.append(child)

    # Also update the store data
    new_store = []
    for param in stored_data:
        if not param['name'].endswith(str(index_to_delete)):
            new_store.append(param)

    return new_children, new_store
import dash
from dash import callback, Input, Output, State, MATCH, ALL, html, dcc, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid
import json

## PARAMETERS PART ##

# Show type dropdown when name is entered
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
                {"label": "Continuous", "value": "float"},
                {"label": "Discrete", "value": "int"},
                {"label": "Categorical", "value": "cat"},
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
        raise PreventUpdate

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

# Render type-specific component
@callback(
    Output({'type': 'parameter-type-specific-container', 'index': MATCH}, 'children'),
    Input({'type': 'parameter-type', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def render_type_specific_component(selected_type):
    if not selected_type:
        return ""

    # Continuous: two numeric inputs for bounds
    if selected_type == "float":
        return dbc.Row([
            dbc.Col([
                dbc.Label("Lower bound"),
                dbc.Input(
                    type="number",
                    id={'type': 'parameter-type-specific-lower', 'index': ctx.triggered_id['index']},
                    placeholder="Lower bound"
                )
            ], width=6),
            dbc.Col([
                dbc.Label("Upper bound"),
                dbc.Input(
                    type="number",
                    id={'type': 'parameter-type-specific-upper', 'index': ctx.triggered_id['index']},
                    placeholder="Upper bound"
                )
            ], width=6),
        ], style={"marginBottom": "15px"})

    # Discrete & Categorical: textarea for values
    elif selected_type in ["int", "cat"]:
        return html.Div([
            html.H5("Enter several values (space or comma separated)"),
            dcc.Textarea(
                id={'type': 'parameter-type-specific', 'index': ctx.triggered_id['index']},
                value="",
                style={"width": "100%", "height": "80px"}
            ),
            html.Small("Example: 1, 2, 3 or red, blue, green")
        ])

    return ""

# Save parameters part information / auto-update display
@callback(
    Output("parameter-store", "data"),
    Output("parameter-display", "children"),
    Input("save-parameters-btn", "n_clicks"),
    State({"type": "parameter-name", "index": ALL}, "id"),
    State({"type": "parameter-name", "index": ALL}, "value"),
    State({"type": "parameter-type", "index": ALL}, "id"),
    State({"type": "parameter-type", "index": ALL}, "value"),
    # Float-specific inputs
    State({'type': 'parameter-type-specific-lower', 'index': ALL}, 'id'),
    State({'type': 'parameter-type-specific-lower', 'index': ALL}, 'value'),
    State({'type': 'parameter-type-specific-upper', 'index': ALL}, 'id'),
    State({'type': 'parameter-type-specific-upper', 'index': ALL}, 'value'),
    # Textarea for int and cat
    State({"type": "parameter-type-specific", "index": ALL}, "id"),
    State({"type": "parameter-type-specific", "index": ALL}, "value"),
    prevent_initial_call=False
)
def update_parameters(n_clicks, name_ids, names, type_ids, types,
                      lower_ids, lower_values, upper_ids, upper_values,
                      text_ids, text_values):

    # Map IDs to values
    name_dict = {nid['index']: val for nid, val in zip(name_ids, names)}
    type_dict = {tid['index']: val for tid, val in zip(type_ids, types)}
    lower_dict = {d['index']: val for d, val in zip(lower_ids, lower_values)}
    upper_dict = {d['index']: val for d, val in zip(upper_ids, upper_values)}
    text_dict = {d['index']: val for d, val in zip(text_ids, text_values)}

    parameters = []
    for idx, name in name_dict.items():
        if not name or idx not in type_dict or not type_dict[idx]:
            continue

        typ = type_dict[idx]

        if typ == "float":
            # Float: store as [lower, upper] floats
            try:
                lower = float(lower_dict.get(idx, None))
            except (TypeError, ValueError):
                lower = None
            try:
                upper = float(upper_dict.get(idx, None))
            except (TypeError, ValueError):
                upper = None
            type_info = {"range": [lower, upper]}

        elif typ == "int":
            # Discrete (but allow decimal values like 0.5, 1.5)
            raw_val = text_dict.get(idx, "")
            parsed_vals = []
            for v in str(raw_val).replace(",", " ").split():
                try:
                    parsed_vals.append(float(v))  # accept decimals
                except ValueError:
                    continue
            type_info = {"range": parsed_vals}

        else:  # "cat"
            raw_val = text_dict.get(idx, "")
            parsed_vals = [v.strip() for v in str(raw_val).replace(",", " ").split() if v.strip()]
            type_info = {"values": parsed_vals}

        parameters.append({
            "id": idx,
            "name": name,
            "type": typ,
            "type_info": type_info
        })

    display = html.Pre(
        json.dumps(parameters, indent=2),
        style={"whiteSpace": "pre-wrap", "fontSize": "14px"}
    )

    if n_clicks:
        return parameters, display
    return dash.no_update, display

# Delete parameter block and update store
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

    triggered_id = ctx.triggered_id
    if not triggered_id:
        raise PreventUpdate

    index_to_delete = triggered_id['index']

    # Remove block from layout
    new_children = [
        child for child in container_children
        if child['props']['id'].get('index') != index_to_delete
    ]

    # Remove from store
    new_store = [
        param for param in stored_data or []
        if param.get("id") != index_to_delete
    ]

    return new_children, new_store

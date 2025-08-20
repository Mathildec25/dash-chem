import dash
from dash import callback, Input, Output, State, MATCH, ALL, html, dcc, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid
import json

from utils.data_handling import find_component_id_in_structure

## FIXED PARAMETERS CALLBACKS ##

# Show type dropdown when name is entered
@callback(
    Output({'type': 'parameter-type-container', 'index': MATCH}, 'children'),
    Input({'type': 'parameter-name', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def show_type_dropdown(name):
    if not name:
        return ""

    return dcc.Dropdown(
        id={'type': 'parameter-type', 'index': ctx.triggered_id['index']},
        options=[
            {"label": "Continuous", "value": "float"},
            {"label": "Discrete", "value": "int"},
            {"label": "Categorical", "value": "cat"},
        ],
        placeholder="Select parameter type...",
        style={"fontSize": "16px"},
    )

# Add a new parameter block within the same card structure
@callback(
    Output("parameter-container", "children", allow_duplicate=True),
    Input("add-para-button", "n_clicks"),
    State("parameter-container", "children"),
    prevent_initial_call="initial_duplicate"  # FIXED: Use initial_duplicate
)
def add_new_parameter(n_clicks, current_children):
    if not n_clicks:
        raise PreventUpdate

    new_id = str(uuid.uuid4())

    # Create new parameter block that matches the layout structure
    new_block = dbc.Card([
        dbc.CardBody([
            dbc.Row(
                id={'type': 'parameter-block', 'index': new_id},
                children=[
                    dbc.Col([
                        dbc.Label("Parameter Name", className="fw-bold"),
                        dbc.Input(
                            id={'type': 'parameter-name', 'index': new_id},
                            placeholder="e.g., Temperature, Concentration...",
                            type="text",
                            size="md",
                            style={"fontSize": "16px"}
                        ),
                    ], width=5),
                    dbc.Col([
                        dbc.Label("Parameter Type", className="fw-bold"),
                        html.Div(id={'type': 'parameter-type-container', 'index': new_id})
                    ], width=5),
                    dbc.Col([
                        dbc.Label("Delete", className="fw-bold"),
                        dbc.Button(
                            "✕",
                            id={'type': 'delete-parameter', 'index': new_id},
                            color="outline-danger",
                            size="sm",
                            className="w-100"
                        ),
                    ], width=2)
                ],
                className="align-items-end mb-3"
            ),
            # Type-specific configuration area
            html.Div(id={'type': 'parameter-type-specific-container', 'index': new_id}),
        ])
    ], className="mb-3 shadow-sm")

    return current_children + [new_block]

# Render type-specific component with better styling
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
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Lower Bound", className="fw-bold"),
                        dbc.Input(
                            type="number",
                            id={'type': 'parameter-type-specific-lower', 'index': ctx.triggered_id['index']},
                            step="any"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Upper Bound", className="fw-bold"),
                        dbc.Input(
                            type="number",
                            id={'type': 'parameter-type-specific-upper', 'index': ctx.triggered_id['index']},
                            step="any"
                        )
                    ], width=6),
                ]),
            ])
        ], className="mt-2", style={"backgroundColor": "#f8f9fa"})

    # Discrete & Categorical: textarea for values
    elif selected_type in ["int", "cat"]:
        example = "1 2 3" if selected_type == "int" else "red,blue,green,yellow"
        help_text = "Enter specific numeric values" if selected_type == "int" else "Enter text options"
        
        return dbc.Card([
            dbc.CardBody([
                dbc.Label(f"{help_text} (comma or space separated)", className="fw-bold"),
                dcc.Textarea(
                    id={'type': 'parameter-type-specific', 'index': ctx.triggered_id['index']},
                    placeholder=f"Example: {example}",
                    style={"width": "100%", "height": "80px", "fontSize": "16px"},
                    className="form-control"
                ),
                html.Small([
                    html.I(className="bi bi-info-circle text-info me-1"),
                    f"Each value will be a separate option for this parameter"
                ], className="text-muted mt-2")
            ])
        ], className="mt-2", style={"backgroundColor": "#f8f9fa"})

    return ""

# Enhanced parameter saving with better display
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
    name_dict = {nid['index']: val for nid, val in zip(name_ids, names) if val}
    type_dict = {tid['index']: val for tid, val in zip(type_ids, types) if val}
    lower_dict = {d['index']: val for d, val in zip(lower_ids, lower_values) if val is not None}
    upper_dict = {d['index']: val for d, val in zip(upper_ids, upper_values) if val is not None}
    text_dict = {d['index']: val for d, val in zip(text_ids, text_values) if val}

    parameters = []
    for idx, name in name_dict.items():
        if not name or idx not in type_dict or not type_dict[idx]:
            continue

        typ = type_dict[idx]

        if typ == "float":
            # Float: store as [lower, upper] floats
            try:
                lower = float(lower_dict.get(idx, 0))
                upper = float(upper_dict.get(idx, 1))
                if lower >= upper:
                    continue  # Skip invalid ranges
            except (TypeError, ValueError):
                continue
            type_info = {"range": [lower, upper]}

        elif typ == "int":
            # Discrete (numeric values)
            raw_val = text_dict.get(idx, "")
            parsed_vals = []
            for v in str(raw_val).replace(",", " ").split():
                try:
                    parsed_vals.append(float(v))
                except ValueError:
                    continue
            if not parsed_vals:
                continue
            type_info = {"range": parsed_vals}

        else:  # "cat"
            raw_val = text_dict.get(idx, "")
            parsed_vals = [v.strip() for v in str(raw_val).replace(",", " ").split() if v.strip()]
            if not parsed_vals:
                continue
            type_info = {"values": parsed_vals}

        parameters.append({
            "id": idx,
            "name": name,
            "type": typ,
            "type_info": type_info
        })

    # Create enhanced display
    if parameters:
        display_items = []
        for i, param in enumerate(parameters, 1):
            if param["type"] == "float":
                range_str = f"[{param['type_info']['range'][0]} - {param['type_info']['range'][1]}]"
            elif param["type"] == "int":
                range_str = f"Values: {param['type_info']['range']}"
            else:
                range_str = f"Options: {param['type_info']['values']}"
            
            display_items.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"{i}. {param['name']}", className="mb-1"),
                        dbc.Badge(param["type"].upper(), color="primary", className="me-2"),
                        html.Small(range_str, className="text-muted")
                    ])
                ], className="mb-2")
            )
        display = html.Div(display_items)
    else:
        display = html.P("No parameters defined yet", className="text-muted")

    if n_clicks:
        return parameters, display
    return dash.no_update, display

# FIXED: Delete parameter block with correct card structure navigation
@callback(
    Output("parameter-container", "children", allow_duplicate=True),
    Output("parameter-store", "data", allow_duplicate=True),
    Input({'type': 'delete-parameter', 'index': ALL}, 'n_clicks'),
    State("parameter-container", "children"),
    State("parameter-store", "data"),
    prevent_initial_call="initial_duplicate"
)
def delete_parameter(n_clicks_list, container_children, stored_data):
    if not any(n_clicks_list):
        raise PreventUpdate

    triggered_id = ctx.triggered_id
    if not triggered_id:
        raise PreventUpdate

    index_to_delete = triggered_id['index']
    print(f"🗑️ Attempting to delete parameter with index: {index_to_delete}")

    # ROBUST: Find and remove the card containing our parameter
    new_children = []
    for i, child in enumerate(container_children):
        try:
            # Search for parameter-block with our index in this card
            found_id = find_component_id_in_structure(child, 'parameter-block')
            
            if found_id != index_to_delete:
                new_children.append(child)
            else:
                print(f"✅ Found and removing parameter card #{i}: {index_to_delete}")
                
        except Exception as e:
            print(f"⚠️ Error processing child #{i}: {e}")
            # Keep the child if we can't determine its ID
            new_children.append(child)

    # Remove from store
    new_store = [
        param for param in stored_data or []
        if param.get("id") != index_to_delete
    ]

    return new_children, new_store
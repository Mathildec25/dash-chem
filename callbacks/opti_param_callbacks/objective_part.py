import dash
from dash import callback, Input, Output, State, MATCH, ALL, html, dcc, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid
import json

from utils.data_handling import find_component_id_in_structure

## FIXED OBJECTIVES CALLBACKS ##

# Add a new objective block within the same card structure
@callback(
    Output("objective-container", "children", allow_duplicate=True),
    Input("add-objective-button", "n_clicks"),
    State("objective-container", "children"),
    prevent_initial_call="initial_duplicate"  # FIXED: Use initial_duplicate
)
def add_new_objective(n_clicks, current_children):
    if not n_clicks:
        raise PreventUpdate

    new_id = str(uuid.uuid4())

    # Create new objective block that matches the layout structure
    new_block = dbc.Card([
        dbc.CardBody([
            dbc.Row(
                id={'type': 'objective-block', 'index': new_id},
                children=[
                    dbc.Col([
                        dbc.Label("Objective Name", className="fw-bold"),
                        dbc.Input(
                            id={'type': 'objective-name', 'index': new_id},
                            placeholder="e.g., Yield, Purity, Cost...",
                            type="text",
                            size="md",
                            style={"fontSize": "16px"}
                        ),
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Optimization Direction", className="fw-bold"),
                        html.Div(id={'type': 'objective-direction-container', 'index': new_id})
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Bounds", className="fw-bold"),
                        html.Div(id={'type': 'objective-bounds-container', 'index': new_id})
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Delete", className="fw-bold"),
                        dbc.Button(
                            "✕",
                            id={'type': 'delete-objective-btn', 'index': new_id},
                            color="outline-danger",
                            size="sm",
                            className="w-100"
                        )
                    ], width=2),
                ],
                className="align-items-end mb-3"
            )
        ])
    ], className="mb-3 shadow-sm")

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

    return dcc.Dropdown(
        id={'type': 'objective-direction', 'index': ctx.triggered_id['index']},
        options=[
            {"label": "Minimize", "value": "min"},
            {"label": "Maximize", "value": "max"},
        ],
        placeholder="Choose optimization goal...",
        style={"fontSize": "16px"}
    )

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
        dbc.Row([
            dbc.Col([
                dbc.Input(
                    id={'type': 'objective-lower-bound', 'index': ctx.triggered_id['index']},
                    type="number",
                    size="md",
                    step="any"
                )
            ], width=6),
            dbc.Col([
                dbc.Input(
                    id={'type': 'objective-upper-bound', 'index': ctx.triggered_id['index']},
                    type="number",
                    size="md",
                    step="any"
                )
            ], width=6)
        ]),
    ])

# Enhanced objectives saving with better display
@callback(
    Output("objective-store", "data"),
    Output("objective-display", "children"),
    Input("save-objectives-btn", "n_clicks"),
    State({"type": "objective-name", "index": ALL}, "id"),
    State({"type": "objective-name", "index": ALL}, "value"),
    State({"type": "objective-direction", "index": ALL}, "id"),
    State({"type": "objective-direction", "index": ALL}, "value"),
    State({"type": "objective-lower-bound", "index": ALL}, "id"),
    State({"type": "objective-lower-bound", "index": ALL}, "value"),
    State({"type": "objective-upper-bound", "index": ALL}, "id"),
    State({"type": "objective-upper-bound", "index": ALL}, "value"),
    prevent_initial_call=False
)
def update_objectives(n_clicks, name_ids, names, direction_ids, directions, 
                     lower_ids, lowers, upper_ids, uppers):
    
    # Create mapping dictionaries
    name_dict = {nid['index']: val for nid, val in zip(name_ids, names) if val}
    direction_dict = {did['index']: val for did, val in zip(direction_ids, directions) if val}
    lower_dict = {lid['index']: val for lid, val in zip(lower_ids, lowers) if val is not None}
    upper_dict = {uid['index']: val for uid, val in zip(upper_ids, uppers) if val is not None}

    objectives = []
    for idx, name in name_dict.items():
        if not name or idx not in direction_dict or not direction_dict[idx]:
            continue
            
        objectives.append({
            "id": idx,
            "name": name,
            "direction": direction_dict[idx],
            "lower_bound": lower_dict.get(idx),
            "upper_bound": upper_dict.get(idx)
        })

    # Create enhanced display
    if objectives:
        display_items = []
        for i, obj in enumerate(objectives, 1):
            direction_icon = "🔻" if obj["direction"] == "min" else "🔺"
            direction_text = "Minimize" if obj["direction"] == "min" else "Maximize"
            
            bounds_info = ""
            if obj.get("lower_bound") is not None and obj.get("upper_bound") is not None:
                bounds_info = f" (Bounds: {obj['lower_bound']} - {obj['upper_bound']})"
            
            display_items.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"{i}. {obj['name']}", className="mb-1"),
                        html.Div([
                            dbc.Badge(f"{direction_icon} {direction_text}", 
                                     color="success" if obj["direction"] == "max" else "warning", 
                                     className="me-2"),
                            html.Small(bounds_info, className="text-muted")
                        ])
                    ])
                ], className="mb-2")
            )
        display = html.Div(display_items)
    else:
        display = html.P("No objectives defined yet", className="text-muted")

    if n_clicks:
        return objectives, display
    return dash.no_update, display

# FIXED OBJECTIVE DELETE
@callback(
    Output("objective-container", "children", allow_duplicate=True),
    Output("objective-store", "data", allow_duplicate=True),
    Input({'type': 'delete-objective-btn', 'index': ALL}, 'n_clicks'),
    State("objective-container", "children"),
    State("objective-store", "data"),
    prevent_initial_call="initial_duplicate"
)
def delete_objective(n_clicks_list, current_children, stored_data):
    if not any(n_clicks_list):
        raise PreventUpdate
    
    triggered_id = ctx.triggered_id
    if not triggered_id:
        raise PreventUpdate

    index_to_delete = triggered_id['index']
    print(f"🗑️ Attempting to delete objective with index: {index_to_delete}")

    # ROBUST: Find and remove the card containing our objective
    new_children = []
    for i, child in enumerate(current_children):
        try:
            # Search for objective-block with our index in this card
            found_id = find_component_id_in_structure(child, 'objective-block')
            
            if found_id != index_to_delete:
                new_children.append(child)
            else:
                print(f"✅ Found and removing objective card #{i}: {index_to_delete}")
                
        except Exception as e:
            print(f"⚠️ Error processing child #{i}: {e}")
            # Keep the child if we can't determine its ID
            new_children.append(child)

    # Remove from store
    new_store = [
        obj for obj in stored_data or []
        if obj.get("id") != index_to_delete
    ]

    return new_children, new_store
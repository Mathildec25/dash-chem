import dash
from dash import callback, Input, Output, State, MATCH, ALL, html, dcc, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid
import json

from utils.data_handling import find_component_id_in_structure

## FIXED EXTRA COLUMNS CALLBACKS ##

# Add a new extra column block within the same card structure
@callback(
    Output("extra-column-container", "children", allow_duplicate=True),
    Input("add-extra-column-button", "n_clicks"),
    State("extra-column-container", "children"),
    prevent_initial_call="initial_duplicate"  # FIXED: Use initial_duplicate
)
def add_extra_column(n_clicks, current_children):
    if not n_clicks:
        raise PreventUpdate

    new_id = str(uuid.uuid4())

    # Create new extra column block that matches the layout structure
    new_block = dbc.Card([
        dbc.CardBody([
            dbc.Row(
                id={'type': 'extra-column-block', 'index': new_id},
                children=[
                    dbc.Col([
                        dbc.Label("Column Name", className="fw-bold"),
                        dbc.Input(
                            id={'type': 'extra-column-name', 'index': new_id},
                            placeholder="e.g., Batch_ID, Operator, Notes...",
                            type="text",
                            size="md",
                            style={"fontSize": "16px"}
                        ),
                    ], width=10),
                    dbc.Col([
                        dbc.Label("Delete", className="fw-bold"),  # FIXED: Changed from "Action"
                        dbc.Button(
                            "✕",
                            id={'type': 'delete-extra-column-btn', 'index': new_id},
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

# FIXED EXTRA COLUMN DELETE  
@callback(
    Output("extra-column-container", "children", allow_duplicate=True),
    Output("extra-columns-store", "data", allow_duplicate=True),
    Input({'type': 'delete-extra-column-btn', 'index': ALL}, 'n_clicks'),
    State("extra-column-container", "children"),
    State("extra-columns-store", "data"),
    prevent_initial_call="initial_duplicate"
)
def delete_extra_column(n_clicks_list, current_children, stored_data):
    if not any(n_clicks_list):
        raise PreventUpdate
    
    triggered_id = ctx.triggered_id
    if not triggered_id:
        raise PreventUpdate

    index_to_delete = triggered_id['index']
    print(f"🗑️ Attempting to delete extra column with index: {index_to_delete}")

    # ROBUST: Find and remove the card containing our extra column
    new_children = []
    for i, child in enumerate(current_children):
        try:
            # Search for extra-column-block with our index in this card
            found_id = find_component_id_in_structure(child, 'extra-column-block')
            
            if found_id != index_to_delete:
                new_children.append(child)
            else:
                print(f"✅ Found and removing extra column card #{i}: {index_to_delete}")
                
        except Exception as e:
            print(f"⚠️ Error processing child #{i}: {e}")
            # Keep the child if we can't determine its ID
            new_children.append(child)

    # Remove from store
    new_store = [
        col for col in stored_data or []
        if col.get("id") != index_to_delete
    ]

    return new_children, new_store

# Enhanced extra columns saving with better display
@callback(
    Output("extra-columns-store", "data", allow_duplicate=True),
    Output("extra-columns-display", "children", allow_duplicate=True),
    Input("save-extra-columns-btn", "n_clicks"),
    State({"type": "extra-column-name", "index": ALL}, "id"),
    State({"type": "extra-column-name", "index": ALL}, "value"),
    prevent_initial_call="initial_duplicate"  # FIXED: Use initial_duplicate for consistency
)
def save_extra_columns(n_clicks, column_ids, column_names):
    
    # Create mapping dictionary
    name_dict = {cid['index']: val for cid, val in zip(column_ids, column_names) if val and val.strip()}

    columns = []
    for idx, name in name_dict.items():
        columns.append({
            "id": idx,
            "name": name.strip()
        })

    # Create enhanced display
    if columns:
        display_items = []
        for i, col in enumerate(columns, 1):
            display_items.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"{i}. {col['name']}", className="mb-1"),
                        dbc.Badge("Extra Column", color="secondary", className="me-2"),
                        html.Small("For additional data tracking", className="text-muted")
                    ])
                ], className="mb-2")
            )
        display = html.Div(display_items)
    else:
        display = html.P("No additional columns defined", className="text-muted")

    if n_clicks:
        return columns, display
    return dash.no_update, display
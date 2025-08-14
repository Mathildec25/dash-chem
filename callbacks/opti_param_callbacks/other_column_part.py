import dash
from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update, dcc, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from utils.data_handling import load_filtered_df, get_columns, get_column_dropdown_options
import pandas as pd
import uuid
import json
import os
from excel_storage import SAVE_FOLDER, TRACKING_FILE, TRACKING_FILENAME

## EXTRA COLUMNS PART ##

# Add a new other column block
@callback(
    Output("extra-column-container", "children", allow_duplicate=True),
    Input("add-extra-column-button", "n_clicks"),
    State("extra-column-container", "children"),
    prevent_initial_call="initial_duplicate"
)
def add_extra_column(n_clicks, current_children):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    new_id = str(uuid.uuid4())

    new_row = dbc.Row([
        dbc.Col([
            dbc.Input(
                id={'type': 'extra-column-name', 'index': new_id},
                placeholder="Enter column name...",
                type="text",
                style={"marginBottom": "8px"}
            )
        ], width=10),
        dbc.Col([
            dbc.Button(
                "✕",
                id={'type': 'delete-extra-column-btn', 'index': new_id},
                color="danger",
                size="sm",
                style={"marginBottom": "8px"}
            )
        ], width=2),
    ], style={"marginBottom": "5px"})

    return current_children + [new_row]

@callback(
    Output("extra-column-container", "children", allow_duplicate=True),
    Output("extra-columns-store", "data", allow_duplicate=True),
    Input({'type': 'delete-extra-column-btn', 'index': ALL}, 'n_clicks'),
    State("extra-column-container", "children"),
    State("extra-columns-store", "data"),
    prevent_initial_call=True
)
def delete_extra_column(n_clicks_list, current_children, stored_data):
    ctx_trigger = ctx.triggered_id
    if not ctx_trigger:
        raise dash.exceptions.PreventUpdate
    
    # Check if any delete button was clicked
    if not any(n_clicks_list) or all(click is None for click in n_clicks_list):
        raise dash.exceptions.PreventUpdate

    delete_index = ctx_trigger["index"]
    new_children = []

    for child in current_children:
        try:
            # Loop through Cols inside the Row
            row_cols = child["props"]["children"]
            found = False

            for col in row_cols:
                col_children = col["props"].get("children", [])
                # Force into list if it's a single component
                if isinstance(col_children, dict):
                    col_children = [col_children]

                for comp in col_children:
                    comp_id = comp["props"].get("id")
                    if isinstance(comp_id, dict) and comp_id.get("type") == "delete-extra-column-btn" and comp_id.get("index") == delete_index:
                        found = True
                        break

                if found:
                    break

            if not found:
                new_children.append(child)
        except Exception as e:
            print("Skipping a child due to error:", e)
            new_children.append(child)

    # Store remains untouched (will be saved again on save button)
    return new_children, stored_data

# Save extra columns part information described by the user
@callback(
    Output("extra-columns-store", "data", allow_duplicate=True),
    Output("extra-columns-display", "children", allow_duplicate=True),
    Input("save-extra-columns-btn", "n_clicks"),
    Input({"type": "extra-column-name", "index": ALL}, "value"),
    State("extra-columns-store", "data"),
    prevent_initial_call=True
)
def save_extra_columns(n_clicks, column_names, current_store):
    triggered_id = ctx.triggered_id

    columns = []
    for name in column_names:
        if name:
            columns.append({
                "name": name
            })

    display = html.Pre(
        json.dumps(columns, indent=2),
        style={"whiteSpace": "pre-wrap", "fontSize": "14px"}
    )

    # Only update store if Save button clicked
    if triggered_id == "save-extra-columns-btn" and n_clicks:
        return columns, display
    else:
        # Update display only
        return dash.no_update, display
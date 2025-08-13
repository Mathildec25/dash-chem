import dash
from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update, dcc, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from utils.data_handling import load_filtered_df, get_columns, get_column_dropdown_options
import pandas as pd
import uuid
import json
import os

### NEED CHANGEMENT BEFORE DEPLOY IT ###
SAVE_FOLDER = r"C:\Users\ThBrHu\Dev\dash-chem"
TRACKING_FILE = os.path.join(SAVE_FOLDER, "Excel_names.xlsx")

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

# Save Excel name 
@callback(
    Output("excel-name-store", "data"),
    Output("excel-confirmation", "children"),
    Input("save-excel-name-btn", "n_clicks"),
    State("excel-name-input", "value"),
    prevent_initial_call=True
)
def save_excel_name(n_clicks, filename):
    if not filename:
        raise dash.exceptions.PreventUpdate

    return filename, f"✔️ Saved: '{filename}'"

# Display the create excel button when the name is saved
@callback(
    Output("create-excel-btn-container", "style"),
    Input("excel-name-store", "data"),
    prevent_initial_call=True
)
def show_create_excel_button(excel_name):
    if excel_name:
        return {"display": "block"}
    return {"display": "none"}

# Create the Excel from all store components 
@callback(
    Output("excel-create-message", "children"),
    Input("create-excel-btn", "n_clicks"),
    State("extra-columns-store", "data"),
    State("parameter-store", "data"),
    State("objective-store", "data"),
    State("excel-name-store", "data"),
    prevent_initial_call=True
)
def create_excel_file(n_clicks, extra_cols, parameters, objectives, excel_name):
    if not excel_name:
        return "❌ Please provide a valid Excel file name."

    # Ensure .xlsx extension
    if not excel_name.endswith(".xlsx"):
        excel_name += ".xlsx"

    file_path = os.path.join(SAVE_FOLDER, excel_name)

    headers = []

    # 1. Extra columns: expect a list of strings
    if extra_cols :
        headers.extend([col.get("name") for col in extra_cols])

    # 2. Parameters: expect list of dicts with "name"
    if parameters:
        headers.extend([param.get("name") for param in parameters])

    # 3. Objectives: expect list of dicts with "name"
    if objectives:
        headers.extend([obj.get("name") for obj in objectives])

    if not headers:
        return "⚠️ No columns to write into Excel."

    df = pd.DataFrame(columns=headers)

    try:
        # Save Excel file
        df.to_excel(file_path, index=False, engine='openpyxl')

        # Update tracking file if needed
        if os.path.exists(TRACKING_FILE):
            df_tracking = pd.read_excel(TRACKING_FILE)
        else:
            df_tracking = pd.DataFrame(columns=["filename"])

        if excel_name not in df_tracking["filename"].values:
            df_tracking.loc[len(df_tracking)] = [excel_name]
            df_tracking.to_excel(TRACKING_FILE, index=False)

        return f"✅ Excel file '{excel_name}' created successfully with {len(headers)} columns."

    except Exception as e:
        return f"❌ Failed to create Excel file: {str(e)}"
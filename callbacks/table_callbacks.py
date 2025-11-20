import dash
from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update
from dash.exceptions import PreventUpdate
from utils.data_handling import load_filtered_df, get_columns, get_column_dropdown_options
import pandas as pd
import os

from config_path import EXCEL_FOLDER

### CALLBACKS TO GENERATE THE TABLE PARTS###

# Load and return the table for the selected sheet and return the column dropdown options and values
@callback(
    [Output("main-content-dashboard", "children"),
    Output("column-dropdown", "options"),
    Output("column-dropdown", "value")],
    Input("url", "pathname"),
    State("selected-sheet-store", "data"),
    State("selected-excel-store", "data"),
    suppress_callback_exceptions=True
)
def load_table_for_sheet(pathname, sheet, excel):
    # Only trigger when on /table page
    if pathname != "/table": 
        raise PreventUpdate
    
    # Basic validation
    if not sheet or not excel:
        return html.Div("No sheet selected"), [], []

    if not excel.endswith(".xlsx"):
        excel += ".xlsx"

    file_path = os.path.join(EXCEL_FOLDER, excel)
    if not os.path.exists(file_path):
        return html.Div(f"❌ File not found: {file_path}"), [], []

    # Load data
    try:
        df = pd.read_excel(file_path, sheet_name=sheet, engine="openpyxl")
    except Exception as e:
        return html.Div(f"❌ Error loading Excel file: {str(e)}"), [], []

    # Build dropdown options
    columns = get_columns(df)
    options = get_column_dropdown_options(df)
    
    try:
        # MODIFICATION: Rendre les colonnes éditables
        table = dash_table.DataTable(
            id={"type": "editable-table", "sheet": sheet},
            data=df.to_dict('records'),
            columns=columns,
            css=[
                {"selector": ".dash-spreadsheet-container", "rule": "max-height: 100vh !important; height: 75vh !important;"},
                {"selector": ".dash-spreadsheet-inner", "rule": "max-height: 100vh !important; height: 75vh !important;"},
                {"selector": ".dash-table-container", "rule": "max-height: 100vh !important; height: 75vh !important;"}
            ],
            tooltip_data=[
                {column: {'value': str(value), 'type': 'markdown'} for column, value in row.items()}
                for row in df.to_dict('records')
            ],
            tooltip_delay=0,
            tooltip_duration=None,
            editable=True,
            row_deletable=True,  # Permettre suppression de lignes
            style_header={
                'backgroundColor': 'white', 'textAlign': 'center', 'fontSize': '14px',
                'whiteSpace': 'normal', 'maxWidth': '200px', 'fontWeight': 'bold', 'border': '1px solid black'
            },
            fixed_rows={'headers': True},
            style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}],    
            style_as_list_view=True,
            style_cell={'padding': '8px', 'textAlign':'center'},
            page_action='none',
            style_table={'width': '99.5%', 'overflowY': 'auto', 'overflowX': 'auto'},
            style_data={'width': '125px', 'minWidth': '125px', 'maxWidth': '125px', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},
            filter_action='native',
            sort_action='native',
            sort_mode='single',
            filter_options={"placeholder_text": "Filter.."}
        )
        return html.Div(table, style={"padding": "4px"}), options, [opt["value"] for opt in options]
    except Exception as e:
        return html.Div(f"Error creating table: {str(e)}"), [], []


# Update the columns of the table based on the selected columns in the dropdown
@callback(
    Output({"type": "editable-table", "sheet": MATCH}, "columns"),
    Input("column-dropdown", "value"),
    State("selected-excel-store", "data"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def update_columns(selected_columns, selected_excel, selected_sheet):
    if not selected_sheet or not selected_columns:
        raise PreventUpdate
    
    try:
        df = load_filtered_df(selected_excel, selected_sheet)
        full_columns = get_columns(df)
        return [col for col in full_columns if col["id"] in selected_columns]
    except Exception as e:
        raise PreventUpdate


@callback(
    Output({"type": "editable-table", "sheet": MATCH}, "data", allow_duplicate=True),
    Input("editing-rows-button", "n_clicks"),
    State({"type": "editable-table", "sheet": MATCH}, "data"),
    State({"type": "editable-table", "sheet": MATCH}, "columns"),
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def add_row_to_table(n_clicks, rows, columns):
    if not n_clicks or not columns:
        raise PreventUpdate
    new_row = {c['id']: '' for c in columns}
    rows.insert(0, new_row)
    return rows


# FIXED: Callback pour ajouter une colonne via modal
@callback(
    Output("add-column-modal", "is_open"),
    [Input("quick-add-column-btn", "n_clicks"),
     Input("cancel-add-column", "n_clicks"),
     Input("confirm-add-column", "n_clicks")],
    State("add-column-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_add_column_modal(open_clicks, cancel_clicks, confirm_clicks, is_open):
    """Toggle modal pour ajouter une colonne"""
    return not is_open

@callback(
    [Output("new-column-name-modal", "value"),
     Output("column-dropdown", "options", allow_duplicate=True),
     Output("column-dropdown", "value", allow_duplicate=True),
     Output("save-status-inline", "children", allow_duplicate=True)],
    Input("confirm-add-column", "n_clicks"),
    [State("new-column-name-modal", "value"),
     State("column-dropdown", "options"),
     State("selected-excel-store", "data"),
     State("selected-sheet-store", "data")],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def update_dropdown_and_status(n_clicks, new_col_name, current_options, excel, sheet):
    if not n_clicks or not new_col_name or not new_col_name.strip():
        raise PreventUpdate

    new_col_name = new_col_name.strip()

    if not excel.endswith(".xlsx"):
        excel += ".xlsx"

    file_path = os.path.join(EXCEL_FOLDER, excel)

    try:
        new_options = current_options + [{"label": new_col_name, "value": new_col_name}]
        new_values = [opt["value"] for opt in new_options]

        # Save updated structure to Excel
        df = pd.read_excel(file_path, sheet_name=sheet, engine="openpyxl")
        if new_col_name not in df.columns:
            df[new_col_name] = ''
            with pd.ExcelWriter(file_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                df.to_excel(writer, sheet_name=sheet, index=False)

        return "", new_options, new_values, html.Small(f"✅ Column '{new_col_name}' added", className="text-success")
    except Exception as e:
        return "", no_update, no_update, html.Small(f"❌ Error: {str(e)}", className="text-danger")

def add_column_via_modal(n_clicks, new_col_name, current_columns, current_data, excel, sheet, current_options):
    """Add a new column to the table"""
    if not n_clicks or not new_col_name or not new_col_name.strip():
        raise PreventUpdate
    
    if not excel or not sheet:
        raise PreventUpdate
    
    try:
        new_col_name = new_col_name.strip()
        
        # Ensure extension
        if not excel.endswith(".xlsx"):
            excel += ".xlsx"
        
        file_path = os.path.join(EXCEL_FOLDER, excel)
        
        # Check if column name already exists
        if any(col['id'] == new_col_name for col in current_columns):
            return (no_update, no_update, "", no_update, no_update, 
                    html.Small(f"❌ Column '{new_col_name}' already exists", className="text-danger"))
        
        # Add new column to columns definition
        new_columns = current_columns + [{
            'name': new_col_name,
            'id': new_col_name,
            'editable': True
        }]
        
        # Add new column to data with empty values
        updated_data = []
        for row in current_data:
            row[new_col_name] = ''
            updated_data.append(row)
        
        # Save to Excel
        df = pd.DataFrame(updated_data)
        with pd.ExcelWriter(file_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet, index=False)
        
        # Update dropdown options
        new_options = current_options + [{"label": new_col_name, "value": new_col_name}]
        new_values = [opt["value"] for opt in new_options]
        
        return (new_columns, updated_data, "", new_options, new_values,
                html.Small(f"✅ Column '{new_col_name}' added", className="text-success"))
        
    except Exception as e:
        print(f"Error adding column: {e}")
        return (no_update, no_update, "", no_update, no_update,
                html.Small(f"❌ Error: {str(e)}", className="text-danger"))


# NOUVEAU: Callback pour renommer les colonnes
@callback(
    Output({"type": "editable-table", "sheet": MATCH}, "columns", allow_duplicate=True),
    Input("rename-column-btn", "n_clicks"),
    [State("old-column-name", "value"),
     State("new-column-name", "value"),
     State({"type": "editable-table", "sheet": MATCH}, "columns"),
     State("selected-excel-store", "data"),
     State("selected-sheet-store", "data")],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def rename_column(n_clicks, old_name, new_name, current_columns, excel, sheet):
    """Rename a column in the table"""
    if not n_clicks or not old_name or not new_name:
        raise PreventUpdate
    
    if not excel or not sheet:
        raise PreventUpdate
    
    try:
        # Ensure extension
        if not excel.endswith(".xlsx"):
            excel += ".xlsx"
        
        file_path = os.path.join(EXCEL_FOLDER, excel)
        
        # Load the Excel file
        df = pd.read_excel(file_path, sheet_name=sheet, engine="openpyxl")
        
        # Check if old column exists
        if old_name not in df.columns:
            raise PreventUpdate
        
        # Check if new name already exists
        if new_name in df.columns and new_name != old_name:
            raise PreventUpdate
        
        # Rename the column
        df = df.rename(columns={old_name: new_name})
        
        # Save back to Excel
        with pd.ExcelWriter(file_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet, index=False)
        
        # Update column definitions
        updated_columns = []
        for col in current_columns:
            if col['id'] == old_name:
                updated_columns.append({
                    'name': new_name,
                    'id': new_name,
                    'editable': True
                })
            else:
                updated_columns.append(col)
        
        return updated_columns
        
    except Exception as e:
        print(f"Error renaming column: {e}")
        raise PreventUpdate


# Save changes to the Excel file when the button is clicked
@callback(
    [Output("save-button", "children"),
     Output("save-status-inline", "children")],
    Input("save-button", "n_clicks"),
    State({"type": "editable-table", "sheet": ALL}, "data"),
    State({"type": "editable-table", "sheet": ALL}, "columns"),
    State("selected-excel-store", "data"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def save_changes(n_clicks, all_tables_data, all_tables_columns, excel, sheet):
    if not n_clicks or n_clicks == 0:
        raise PreventUpdate
        
    if not all_tables_data or not all_tables_columns or not sheet or not excel:
        return "Save Changes", html.Small("❌ No data to save", className="text-danger")
    
    try:
        if not excel.endswith(".xlsx"):
            excel += ".xlsx"
        file_path = os.path.join(EXCEL_FOLDER, excel)

        df = pd.DataFrame(all_tables_data[0], columns=[c["id"] for c in all_tables_columns[0]])
        with pd.ExcelWriter(file_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet, index=False)
        return "Save Changes", html.Small("✅ Saved successfully", className="text-success")
    except Exception as e:
        return "Save Changes", html.Small(f"❌ Error: {str(e)}", className="text-danger")
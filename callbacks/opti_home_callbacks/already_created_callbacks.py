import dash
from dash import dcc, html, Input, Output, State, callback, ALL
import dash_bootstrap_components as dbc
import os
import pandas as pd
import base64
import io

from excel_storage import (
    EXCEL_FOLDER, 
    TRACKING_FILE, 
    get_uploaded_excel_files,
    get_excel_dropdown_options
)
from domain_storage import DomainStorage, check_domain_availability

# ============================================
# EXISTING PROJECT SECTION
# ============================================

@callback(
        [Output('excels-DD-opti', 'options'),
         Output('domain-status-display', 'children')],
        [Input('excels-DD-opti', 'value'),
         Input('url', 'pathname')]
    )
def update_excel_dropdown_with_domain_status(selected_excel, pathname):
    """Update Excel dropdown showing which files have domains"""

    if pathname != "/Opt-home":
        return dash.no_update
    
    excel_files = get_uploaded_excel_files()
    domain_availability = check_domain_availability()
    
    options = []
    status_info = html.Div()
    
    if not excel_files:
        options = [{"label": "No Excel files available", "value": None, "disabled": True}]
    else:
        for file in excel_files:
            has_domain = domain_availability.get(file, False)
            if has_domain:
                label = f"✅ {file}"
                options.append({"label": label, "value": file})
            else:
                label = f"⚠️ {file} (No Domain)"
                options.append({"label": label, "value": file, "disabled": True})
        
        # Create status info if file is selected
        if selected_excel and domain_availability.get(selected_excel, False):
            success, domain, metadata = DomainStorage.load_domain(selected_excel)
            if success and metadata:
                status_info = dbc.Alert([
                    html.Strong("✅ Domain Ready | "),
                    f"Parameters: {len(metadata.get('parameters', []))} | ",
                    f"Objectives: {len(metadata.get('objectives', []))}"
                ], color="success", className="mt-2")
    
    return options, status_info


@callback(
    [Output('sheets-DD-opti', 'children'),
     Output('restart-opti-button', 'style', allow_duplicate=True),
     Output('delete-excel-button-opti', 'style')],
    Input('excels-DD-opti', 'value'),
    prevent_initial_call=True
)
def update_sheet_dropdown_and_buttons(selected_excel):
    restart_button_style = {"display": "none", "marginTop": "12px"}
    delete_button_style = {"display": "none", "marginTop": "12px"}
    sheet_dropdown = html.Div()

    if not selected_excel:
        return sheet_dropdown, restart_button_style, delete_button_style

    try:
        if not DomainStorage.domain_exists(selected_excel):
            return html.Div([
                dbc.Alert(
                    "This Excel file doesn't have a domain configuration. Create a new project instead.",
                    color="warning"
                )
            ]), restart_button_style, delete_button_style

        excel_path = os.path.join(EXCEL_FOLDER, selected_excel)

        if selected_excel.endswith(('.xls', '.xlsx')):
            with pd.ExcelFile(excel_path) as xls:
                sheet_names = xls.sheet_names
        elif selected_excel.endswith('.csv'):
            sheet_names = ['CSV Data']
        else:
            return dbc.Alert(
                f"Unsupported file type: {selected_excel}",
                color="danger"
            ), restart_button_style, delete_button_style

        sheet_dropdown = dcc.Dropdown(
            id={'type': 'sheet-dropdown', 'index': selected_excel},
            options=[{"label": name, "value": name} for name in sheet_names],
            value=sheet_names[0] if len(sheet_names) == 1 else None,
            placeholder="Select a sheet..." if len(sheet_names) > 1 else None,
            className="mb-2"
        )

        restart_button_style = {"marginTop": "12px", "display": "inline-block"}
        delete_button_style = {"marginTop": "12px", "display": "inline-block", "marginLeft": "10px"}

        return sheet_dropdown, restart_button_style, delete_button_style

    except Exception as e:
        return dbc.Alert(
            f"Error reading file: {e}",
            color="danger"
        ), restart_button_style, delete_button_style

    
@callback(
        Output('restart-opti-button', 'style'),
        Input({'type': 'sheet-dropdown', 'index': ALL}, 'value'),
        prevent_initial_call=True
    )
def toggle_restart_button_on_sheet_select(sheet_values):
    """Show the restart GO button when a sheet is selected"""
    if sheet_values and any(value for value in sheet_values if value):
        return {"marginTop": "12px", "display": "inline-block"}
    else:
        return {"marginTop": "12px", "display": "none"}


@callback(
        Output('selected-file-store', 'data'),
        Input('restart-opti-button', 'n_clicks'),
        State('excels-DD-opti', 'value'),
        State({'type': 'sheet-dropdown', 'index': ALL}, 'value'),
        prevent_initial_call=True
    )
def handle_restart_button_click(n_clicks, selected_excel, sheet_values):
    """Handle restart button click - save selected file/sheet info"""
    if n_clicks and selected_excel:
        selected_sheet = next((v for v in sheet_values if v), None) if sheet_values else 'Experiments'
        
        # Store the selected file and sheet information
        return {
            'excel_file': selected_excel,
            'selected_sheet': selected_sheet
        }
    
    return dash.no_update

@callback(
        [Output('excels-DD-opti', 'value', allow_duplicate=True),
         Output('excels-DD-opti', 'options', allow_duplicate=True)],
        Input('delete-excel-button-opti', 'n_clicks'),
        State('excels-DD-opti', 'value'),
        prevent_initial_call=True
    )
def delete_excel_file_with_domain(n_clicks, selected_file):
    """Delete Excel file and associated domain"""
    if not n_clicks or not selected_file:
        return dash.no_update, dash.no_update
    
    file_path = os.path.join(EXCEL_FOLDER, selected_file)
    
    try:
        # Delete the Excel file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete associated domain
        if DomainStorage.domain_exists(selected_file):
            DomainStorage.delete_domain(selected_file)
        
        # Remove from Excel tracking file
        if os.path.exists(TRACKING_FILE):
            df = pd.read_excel(TRACKING_FILE, engine='openpyxl')
            df = df[df["filename"] != selected_file]
            df.to_excel(TRACKING_FILE, index=False, engine='openpyxl')
        
        # Update dropdown options
        excel_files = get_uploaded_excel_files()
        domain_availability = check_domain_availability()
        
        new_options = []
        for file in excel_files:
            has_domain = domain_availability.get(file, False)
            if has_domain:
                label = f"✅ {file}"
                new_options.append({"label": label, "value": file})
            else:
                label = f"⚠️ {file} (No Domain)"
                new_options.append({"label": label, "value": file, "disabled": True})
        
        return None, new_options
        
    except Exception as e:
        print(f"Error deleting file: {e}")
        return dash.no_update, dash.no_update
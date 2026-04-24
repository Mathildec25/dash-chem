"""Callbacks for opening / managing existing projects on the home page."""

import os

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Input, Output, State, callback, dcc, html, no_update

from config_path import EXCEL_FOLDER, TRACKING_FILE
from domain_storage import DomainStorage, check_domain_availability
from excel_storage import get_uploaded_excel_files
from utils.safe_excel import safe_excel_read, safe_excel_save


def _build_excel_options(excel_files):
    """Build dropdown options annotated with domain availability."""
    options = []
    for file in excel_files:
        has_domain = check_domain_availability(file)
        if has_domain:
            options.append({"label": f"✅ {file}", "value": file})
        else:
            options.append({"label": f"⚠️ {file} (No Domain)", "value": file, "disabled": True})
    return options


@callback(
    [Output("excels-DD-opti", "options"),
     Output("domain-status-display", "children")],
    [Input("excels-DD-opti", "value"),
     Input("url", "pathname")],
)
def update_excel_dropdown_with_domain_status(selected_excel, pathname):
    """Populate the Excel dropdown and a summary of the selected project's domain."""
    if pathname != "/Opt-home":
        return dash.no_update, dash.no_update

    excel_files = get_uploaded_excel_files()
    if not excel_files:
        return [{"label": "No Excel files available", "value": None, "disabled": True}], html.Div()

    options = _build_excel_options(excel_files)
    status_info = html.Div()

    if selected_excel and check_domain_availability(selected_excel):
        data = DomainStorage.load_domain(selected_excel)
        if data:
            status_info = dbc.Alert(
                [
                    html.Strong("✅ Domain Ready | "),
                    f"Parameters: {len(data.get('parameters', []))} | ",
                    f"Objectives: {len(data.get('objectives', []))}",
                ],
                color="success",
                className="mt-2",
            )

    return options, status_info


@callback(
    [Output("sheets-DD-opti", "children"),
     Output("restart-opti-button", "style", allow_duplicate=True),
     Output("delete-excel-button-opti", "style")],
    Input("excels-DD-opti", "value"),
    prevent_initial_call=True,
)
def update_sheet_dropdown_and_buttons(selected_excel):
    """Build the sheet dropdown and toggle the restart / delete buttons."""
    hidden = {"display": "none", "marginTop": "12px"}
    sheet_dropdown = html.Div()

    if not selected_excel:
        return sheet_dropdown, hidden, hidden

    try:
        if not check_domain_availability(selected_excel):
            return (
                html.Div([
                    dbc.Alert(
                        "This Excel file doesn't have a domain configuration. "
                        "Create a new project instead.",
                        color="warning",
                    ),
                ]),
                hidden,
                hidden,
            )

        excel_path = os.path.join(EXCEL_FOLDER, selected_excel)

        if selected_excel.endswith((".xls", ".xlsx")):
            with pd.ExcelFile(excel_path) as xls:
                sheet_names = xls.sheet_names
        elif selected_excel.endswith(".csv"):
            sheet_names = ["CSV Data"]
        else:
            return (
                dbc.Alert(f"Unsupported file type: {selected_excel}", color="danger"),
                hidden,
                hidden,
            )

        sheet_dropdown = dcc.Dropdown(
            id={"type": "sheet-dropdown", "index": selected_excel},
            options=[{"label": name, "value": name} for name in sheet_names],
            value=sheet_names[0] if len(sheet_names) == 1 else None,
            placeholder="Select a sheet..." if len(sheet_names) > 1 else None,
            className="mb-2",
        )

        restart_style = {"marginTop": "12px", "display": "inline-block"}
        delete_style = {"marginTop": "12px", "display": "inline-block", "marginLeft": "10px"}
        return sheet_dropdown, restart_style, delete_style

    except Exception as e:
        return dbc.Alert(f"Error reading file: {e}", color="danger"), hidden, hidden


@callback(
    Output("restart-opti-button", "style"),
    Input({"type": "sheet-dropdown", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def toggle_restart_button_on_sheet_select(sheet_values):
    """Reveal the restart button as soon as a sheet is selected."""
    has_selection = bool(sheet_values) and any(sheet_values)
    return {"marginTop": "12px", "display": "inline-block" if has_selection else "none"}


@callback(
    Output("selected-file-store", "data"),
    Input("restart-opti-button", "n_clicks"),
    State("excels-DD-opti", "value"),
    State({"type": "sheet-dropdown", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def handle_restart_button_click(n_clicks, selected_excel, sheet_values):
    """Persist the selected (file, sheet) to the session store."""
    if not n_clicks or not selected_excel:
        return dash.no_update

    selected_sheet = next((v for v in sheet_values if v), None) if sheet_values else "Experiments"
    return {"excel_file": selected_excel, "selected_sheet": selected_sheet}


@callback(
    [Output("excels-DD-opti", "value", allow_duplicate=True),
     Output("excels-DD-opti", "options", allow_duplicate=True)],
    Input("delete-excel-button-opti", "n_clicks"),
    State("excels-DD-opti", "value"),
    prevent_initial_call=True,
)
def delete_excel_file_with_domain(n_clicks, selected_file):
    """Delete the selected Excel file, its domain, and its tracking entry."""
    if not n_clicks or not selected_file:
        return dash.no_update, dash.no_update

    file_path = os.path.join(EXCEL_FOLDER, selected_file)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)

        if check_domain_availability(selected_file):
            DomainStorage.delete_domain(selected_file)

        if os.path.exists(TRACKING_FILE):
            df, _ = safe_excel_read(TRACKING_FILE)
            if df is not None:
                df = df[df["filename"] != selected_file]
                safe_excel_save(
                    TRACKING_FILE,
                    lambda p: df.to_excel(p, index=False, engine="openpyxl"),
                )

        return None, _build_excel_options(get_uploaded_excel_files())
    except Exception as e:
        print(f"Error deleting file: {e}")
        return dash.no_update, dash.no_update


@callback(
    Output("open-existing-project-btn", "style"),
    Input("existing-projects-list", "value"),
    prevent_initial_call=True,
)
def show_open_button(selected_file):
    """Show the Open button once the user has picked an existing project."""
    base = {"borderRadius": "8px", "fontWeight": "500"}
    return {**base, "display": "block" if selected_file else "none"}


@callback(
    [Output("current-excel-file", "data", allow_duplicate=True),
     Output("url", "pathname", allow_duplicate=True)],
    Input("open-existing-project-btn", "n_clicks"),
    State("existing-projects-list", "value"),
    prevent_initial_call=True,
)
def open_existing_project(n_clicks, selected_file):
    """Open the selected project and navigate to the Run page."""
    if n_clicks and selected_file:
        return selected_file, "/Opt-run"
    return no_update, no_update

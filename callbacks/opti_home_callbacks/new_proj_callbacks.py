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
    TRACKING_FILENAME,
    get_uploaded_excel_files,
    get_excel_dropdown_options
)
from domain_storage import DomainStorage, check_domain_availability

# ============================================
# RESET STORES ON PAGE LOAD
# ============================================

@callback(
    [Output('selected-file-store', 'data', allow_duplicate=True),
        Output('current-excel-file', 'data', allow_duplicate=True),
        Output('current-domain', 'data', allow_duplicate=True),
        Output('parameter-store', 'data', allow_duplicate=True),
        Output('objective-store', 'data', allow_duplicate=True),
        Output("extra-columns-store", 'data', allow_duplicate=True)],
    Input('url', 'pathname'),
    prevent_initial_call=True
)
def reset_stores_on_home(pathname):
    """Reset all stores when navigating to home page"""
    if pathname == "/" or pathname == "/Opt-home":
        # Clear all stores
        return None, None, None, None, None, None
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# ============================================
# NEW PROJECT SECTION
# ============================================

@callback(
    Output('start-opti-button', 'style'),
    Input('new-proj', 'value'),
    prevent_initial_call=True
)
def toggle_go_button(project_name):
    """Show the GO button when text is entered in the input field"""
    if project_name and project_name.strip():
        return {"marginTop": "12px", "display": "inline-block"}
    else:
        return {"marginTop": "12px", "display": "none"}


@callback(
    Output('project-name-store', 'data'),
    Output('url', 'pathname'),
    Input('start-opti-button', 'n_clicks'),
    State('new-proj', 'value'),
    prevent_initial_call=True
)
def handle_go_button_click(n_clicks, project_name):
    """Save project name to store and redirect to parameter page"""
    if n_clicks and project_name and project_name.strip():
        # Save the project name to store and redirect to parameter page
        return project_name.strip(), '/param'
    return dash.no_update, dash.no_update

import dash
from dash import dcc, html, Input, Output, State, callback, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import os
import base64
import io

# Import all functions from excel_storage instead of redefining
from excel_storage import (
    EXCEL_FOLDER, 
    TRACKING_FILE,
    get_uploaded_excel_files,
    get_existing_files,
    update_tracking_file,
    parse_contents,
    get_excel_dropdown_options,
    get_excel_dropdown_options_with_domain_status,
    cleanup_orphaned_domains,
    validate_excel_structure,
    get_file_info,
    create_file_summary_card
)
from domain_storage import DomainStorage

# ============================================
# TAB CONTENT CALLBACK - REMPLACE L'ANCIEN
# ============================================

@callback(
    Output('tab-content', 'children'),
    Input('file-tabs', 'active_tab')
)
def render_tab_content(active_tab):
    """Render content based on selected tab - AVEC 3 TABS"""
    if active_tab == "upload-tab":
        return html.Div([
            dcc.Upload(
                id="upload-data",
                children=html.Div([
                    html.Div([
                        html.I(className="bi bi-cloud-upload", 
                              style={"fontSize": "48px", "color": "#3498db"}),
                        html.H5("Drop files here or click", className="mt-3 mb-2"),
                        html.P("Excel (.xlsx, .xls)",
                              className="text-muted")
                    ], className="text-center p-4")
                ]),
                style={
                    'width': '100%',
                    'minHeight': '200px',
                    'borderWidth': '2px',
                    'borderStyle': 'dashed',
                    'borderRadius': '10px',
                    'borderColor': '#dee2e6',
                    'backgroundColor': '#f8f9fa',
                    'cursor': 'pointer'
                },
                className="upload-area",
                multiple=True,
            )
        ])
    
    elif active_tab == "select-tab":
        files = get_uploaded_excel_files()
        if not files:
            return dbc.Alert([
                html.I(className="bi bi-folder-x me-2"),
                "No files available. Please upload or create a file first."
            ], color="warning")
        
        return html.Div([
            dcc.Dropdown(
                id="excels-DD-visible",
                options=[{"label": f, "value": f} for f in files],
                placeholder="Choose a file...",
                className="mb-3"
            ),
            html.Div(id="sheet-selector-container"),
            html.Div(id="file-actions-container")
        ])
    
    elif active_tab == "create-tab":
        return html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.H5([
                        html.I(className="bi bi-file-earmark-plus me-2"),
                        "Create New Excel File"
                    ], className="mb-3"),
                    
                    html.P("Create a blank Excel file and customize it in the Dashboard", 
                           className="text-muted mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("File Name", className="fw-bold"),
                            dbc.Input(
                                id="new-excel-name",
                                placeholder="e.g., My_Experiments",
                                type="text",
                                className="mb-2"
                            ),
                            html.Small("Extension .xlsx will be added automatically", 
                                      className="text-muted d-block mb-3")
                        ], width=12),
                    ]),
                    
                    dbc.Button([
                        html.I(className="bi bi-arrow-right-circle me-2"),
                        "Create & Open in Dashboard"
                    ],
                    id="create-excel-btn",
                    color="success",
                    size="lg",
                    className="w-100"
                    ),
                    
                    html.Hr(className="my-3"),
                    
                    dbc.Alert([
                        html.I(className="bi bi-info-circle me-2"),
                        html.Strong("In Dashboard you can:"),
                        html.Ul([
                            html.Li("Rename columns by clicking on headers"),
                            html.Li("Add/delete rows and columns"),
                            html.Li("Edit all cell values"),
                            html.Li("Filter and sort data"),
                            html.Li("Save changes anytime")
                        ], className="mb-0 mt-2")
                    ], color="light", className="border border-success")
                ])
            ], className="shadow-sm")
        ])


# ============================================
# FILE SELECTION CALLBACKS
# ============================================

@callback(
    [Output('sheet-selector-container', 'children'),
     Output('file-actions-container', 'children')],
    Input('excels-DD-visible', 'value'),
    prevent_initial_call=True
)
def handle_file_selection(selected_file):
    """Handle file selection from dropdown"""
    if not selected_file:
        return html.Div(), html.Div()
    
    excel_path = os.path.join(EXCEL_FOLDER, selected_file)
    
    try:
        # Get sheet names
        if selected_file.endswith(('.xls', '.xlsx')):
            with pd.ExcelFile(excel_path) as xls:
                sheet_names = xls.sheet_names
        elif selected_file.endswith('.csv'):
            sheet_names = ["CSV Data"]
        else:
            return dbc.Alert("Unsupported file type", color="danger"), html.Div()
        
        sheet_selector = html.Div([
            dcc.Dropdown(
                id={'type': 'sheet-dropdown-visible', 'index': selected_file},
                options=[{"label": name, "value": name} for name in sheet_names],
                value=sheet_names[0] if len(sheet_names) == 1 else None,
                placeholder="Choose a sheet..." if len(sheet_names) > 1 else None,
                className="mb-3"
            )
        ])
        
        actions = html.Div([
            dbc.ButtonGroup([
                dbc.Button([
                    html.I(className="bi bi-check-circle me-2"),
                    "Use This File"
                ], id="confirm-file-btn", color="success", className="me-2"),
                dbc.Button([
                    html.I(className="bi bi-trash me-2"),
                    "Delete"
                ], id="delete-file-btn", color="danger", outline=True)
            ], className="mt-2")
        ])
        
        return sheet_selector, actions
        
    except Exception as e:
        return dbc.Alert(f"Error reading file: {e}", color="danger"), html.Div()


# ============================================
# CONFIRM FILE SELECTION - UPDATE BOTH STORES
# ============================================

@callback(
    [Output('excels-DD', 'value', allow_duplicate=True),
     Output('selected-excel-store', 'data', allow_duplicate=True),
     Output('selected-sheet-store', 'data', allow_duplicate=True),
     Output('step-2-container', 'style'),
     Output('output-data-upload', 'children', allow_duplicate=True)],
    Input('confirm-file-btn', 'n_clicks'),
    [State('excels-DD-visible', 'value'),
     State({'type': 'sheet-dropdown-visible', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def confirm_file_selection(n_clicks, selected_file, sheet_values):
    """Confirm file selection and update stores"""
    if not n_clicks or not selected_file:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    selected_sheet = sheet_values[0] if sheet_values else None
    
    # If no sheet selected for multi-sheet file, don't proceed
    if not selected_sheet:
        excel_path = os.path.join(EXCEL_FOLDER, selected_file)
        if selected_file.endswith(('.xls', '.xlsx')):
            try:
                with pd.ExcelFile(excel_path) as xls:
                    if len(xls.sheet_names) > 1:
                        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                               dbc.Alert("Please select a sheet first", color="warning", dismissable=True))
                    else:
                        selected_sheet = xls.sheet_names[0]
            except:
                pass
        elif selected_file.endswith('.csv'):
            selected_sheet = "CSV Data"
    
    # Update all stores and UI
    success_alert = dbc.Alert([
        html.I(className="bi bi-check-circle-fill me-2"),
        f"File '{selected_file}' is ready to use!",
        html.Br(),
        html.Small(f"Sheet: {selected_sheet}")
    ], color="success", dismissable=True)
    
    return (
        selected_file,           # Update hidden dropdown
        selected_file,           # Update selected-excel-store
        selected_sheet,          # Update selected-sheet-store
        {"display": "block"},    # Show step 2
        success_alert           # Show success message
    )


# ============================================
# UPLOAD FILE CALLBACK - UPDATE STORES AFTER UPLOAD
# ============================================

@callback(
    [Output('output-data-upload', 'children', allow_duplicate=True),
     Output('excels-DD', 'options', allow_duplicate=True),
     Output('selected-excel-store', 'data', allow_duplicate=True),
     Output('selected-sheet-store', 'data', allow_duplicate=True),
     Output('step-2-container', 'style', allow_duplicate=True)],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def handle_file_upload(list_of_contents, list_of_names):
    """Handle file upload and update stores"""
    if not list_of_contents:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    if isinstance(list_of_names, str):
        list_of_names = [list_of_names]
    
    messages = []
    success = False
    last_successful_file = None
    last_successful_sheet = None
    
    for contents, name in zip(list_of_contents, list_of_names):
        if contents and ',' in contents:
            # Use the parse_contents from excel_storage
            result = parse_contents(contents, name)
            messages.append(result)
            
            # Check if upload was successful
            if hasattr(result, 'children'):
                children_str = str(result.children)
                if "Successfully uploaded" in children_str:
                    success = True
                    last_successful_file = name
                    
                    # Determine sheet name
                    if name.endswith('.csv'):
                        last_successful_sheet = "CSV Data"
                    else:
                        # For Excel files, get the first sheet
                        try:
                            excel_path = os.path.join(EXCEL_FOLDER, name)
                            with pd.ExcelFile(excel_path) as xls:
                                last_successful_sheet = xls.sheet_names[0]
                        except:
                            last_successful_sheet = "Sheet1"
    
    # Refresh dropdown options
    files = get_uploaded_excel_files()
    options = [{"label": f, "value": f} for f in files]
    
    # If upload was successful, update stores and show step 2
    if success and last_successful_file:
        return (
            html.Div(messages),
            options,
            last_successful_file,    # Update selected-excel-store
            last_successful_sheet,    # Update selected-sheet-store
            {"display": "block"}      # Show step 2
        )
    else:
        return (
            html.Div(messages),
            options,
            dash.no_update,
            dash.no_update,
            {"display": "none"}
        )


# ============================================
# CREATE EXCEL FROM SCRATCH - REDIRECT TO DASHBOARD
# ============================================

@callback(
    [Output('output-data-upload', 'children', allow_duplicate=True),
     Output('excels-DD', 'options', allow_duplicate=True),
     Output('excels-DD', 'value', allow_duplicate=True),
     Output('selected-excel-store', 'data', allow_duplicate=True),
     Output('selected-sheet-store', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],  # CHANGEMENT: Redirect vers Dashboard
    Input('create-excel-btn', 'n_clicks'),
    [State('new-excel-name', 'value')],  # CHANGEMENT: Plus besoin de cols/rows
    prevent_initial_call=True
)
def create_excel_from_scratch(n_clicks, filename):
    """Create a minimal Excel file and redirect to Dashboard for editing"""
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Validate inputs
    if not filename or not filename.strip():
        error_alert = dbc.Alert("Please enter a file name", color="danger", dismissable=True)
        return error_alert, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    try:
        # Ensure filename has extension
        filename = filename.strip()
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        file_path = os.path.join(EXCEL_FOLDER, filename)
        
        # Check if file already exists
        if os.path.exists(file_path):
            error_alert = dbc.Alert(
                f"A file named '{filename}' already exists. Please choose a different name.",
                color="warning", 
                dismissable=True
            )
            return error_alert, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # NOUVEAU: Créer un fichier minimal (3 colonnes, 10 lignes)
        # L'utilisateur pourra tout modifier dans Dashboard
        columns = ["Column_1", "Column_2", "Column_3"]
        df = pd.DataFrame(index=range(10), columns=columns)
        df = df.fillna("")
        
        # Save to Excel with formatting
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            # Apply formatting
            worksheet = writer.sheets['Sheet1']
            from openpyxl.styles import Font, PatternFill, Alignment
            
            # Format headers
            for cell in worksheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="343A40", end_color="343A40", fill_type="solid")
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max(max_length + 2, 15), 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Update tracking file
        if os.path.exists(TRACKING_FILE):
            df_tracking = pd.read_excel(TRACKING_FILE, engine='openpyxl')
        else:
            df_tracking = pd.DataFrame(columns=["filename"])
        
        if filename not in df_tracking["filename"].values:
            new_row = pd.DataFrame([{"filename": filename}])
            df_tracking = pd.concat([df_tracking, new_row], ignore_index=True)
            df_tracking.to_excel(TRACKING_FILE, index=False, engine='openpyxl')
        
        # Refresh dropdown options
        files = get_uploaded_excel_files()
        options = [{"label": f, "value": f} for f in files]
        
        # Create success message (will be shown briefly before redirect)
        success_alert = dbc.Alert([
            html.I(className="bi bi-check-circle-fill me-2"),
            f"Successfully created '{filename}'! Redirecting to Dashboard...",
        ], color="success")
        
        # NOUVEAU: Redirect to Dashboard au lieu de rester sur Home
        return (
            success_alert,
            options,
            filename,              # Update excels-DD value
            filename,              # Update selected-excel-store
            "Sheet1",             # Update selected-sheet-store
            "/table"              # REDIRECT TO DASHBOARD
        )
        
    except Exception as e:
        error_alert = dbc.Alert(
            f"Failed to create file: {str(e)}", 
            color="danger", 
            dismissable=True
        )
        return error_alert, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


# ============================================
# DELETE FILE CALLBACK
# ============================================

@callback(
    [Output('excels-DD-visible', 'value'),
     Output('excels-DD-visible', 'options'),
     Output('selected-excel-store', 'data', allow_duplicate=True),
     Output('selected-sheet-store', 'data', allow_duplicate=True),
     Output('output-data-upload', 'children', allow_duplicate=True)],
    Input('delete-file-btn', 'n_clicks'),
    State('excels-DD-visible', 'value'),
    prevent_initial_call=True
)
def delete_file(n_clicks, selected_file):
    """Delete selected file and clear stores"""
    if not n_clicks or not selected_file:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    file_path = os.path.join(EXCEL_FOLDER, selected_file)
    messages = []
    
    try:
        # Delete file
        if os.path.exists(file_path):
            os.remove(file_path)
            messages.append(f"File deleted: {selected_file}")
        
        # Delete domain if exists
        domain_success, domain_message = DomainStorage.delete_domain(selected_file)
        if domain_success and "No domain found" not in domain_message:
            messages.append("Associated domain cleaned up")
        
        # Update tracking
        if os.path.exists(TRACKING_FILE):
            df = pd.read_excel(TRACKING_FILE)
            df = df[df["filename"] != selected_file]
            df.to_excel(TRACKING_FILE, index=False)
        
        # Refresh options
        files = get_uploaded_excel_files()
        new_options = [{"label": f, "value": f} for f in files]
        
        alert = dbc.Alert([
            html.I(className="bi bi-trash me-2"),
            " | ".join(messages)
        ], color="info", dismissable=True)
        
        # Clear stores since file was deleted
        return None, new_options, None, None, alert
        
    except Exception as e:
        error_alert = dbc.Alert([
            html.I(className="bi bi-x-circle me-2"),
            f"Delete failed: {e}"
        ], color="danger", dismissable=True)
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, error_alert


# ============================================
# MAINTAIN COMPATIBILITY WITH OLD CALLBACKS
# ============================================

@callback(
    [Output('sheets-DD', 'children'),
     Output('text-DD-2', 'style'),
     Output('redirec-button', 'style'),
     Output('delete-excel-button', 'style'),],
    [Input('excels-DD', 'value'),
     Input({'type': 'sheet-dropdown', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def update_dropdown_and_buttons(selected_excel, sheet_values):
    """Maintain compatibility with existing callbacks and update stores"""
    text_dd2_style = {"display": "none"}
    button_style = {"display": "none"}
    delete_button_style = {"display": "none"}
    
    if not selected_excel:
        return None, text_dd2_style, button_style, delete_button_style
    
    excel_path = os.path.join(EXCEL_FOLDER, selected_excel)
    
    try:
        if selected_excel.endswith(('.xls', '.xlsx')):
            with pd.ExcelFile(excel_path) as xls:
                sheet_names = xls.sheet_names
        elif selected_excel.endswith('.csv'):
            sheet_names = ["CSV Data"]
        else:
            return None, text_dd2_style, button_style, delete_button_style
    except:
        return None, text_dd2_style, button_style, delete_button_style
    
    current_sheet_value = sheet_values[0] if sheet_values else None
    
    # If only one sheet, auto-select it
    if len(sheet_names) == 1 and not current_sheet_value:
        current_sheet_value = sheet_names[0]
    
    sheet_dropdown = dcc.Dropdown(
        id={'type': 'sheet-dropdown', 'index': selected_excel},
        options=[{"label": name, "value": name} for name in sheet_names],
        value=current_sheet_value or (sheet_names[0] if len(sheet_names) == 1 else None),
    )
    
    # Show buttons if a sheet is selected
    if current_sheet_value:
        button_style = {"display": "flex", "alignItems": "center", "justifyContent": "center", "padding": "80px"}
        text_dd2_style = {"display": "block", "fontSize": "20px", "textAlign": "left", "marginTop": "12px"}
    
    # Show delete button whenever a file is selected
    delete_button_style = {"display": "inline-block", "marginTop": "12px"}
    
    return (
        sheet_dropdown, 
        text_dd2_style, 
        button_style, 
        delete_button_style,
    )


# ============================================
# REFRESH DROPDOWN AFTER UPLOAD
# ============================================

@callback(
    Output('excels-DD', 'options', allow_duplicate=True),
    Input('output-data-upload', 'children'),
    prevent_initial_call=True
)
def refresh_excel_dropdown(upload_children):
    """Refresh the hidden dropdown options after upload"""
    files = get_uploaded_excel_files()
    return [{"label": f, "value": f} for f in files]
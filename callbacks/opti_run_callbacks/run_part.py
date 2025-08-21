import dash
from dash import Input, Output, State, callback, html, dash_table, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
from config_path import EXCEL_FOLDER, COLUMN_COLORS
from domain_storage import (
    DomainStorage,
    load_experiments_from_excel_file,
    prepare_experiments_from_excel_data
)
from utils.BoFire import optimization
from components.layout_opti_run import get_bo_tab_content, get_visualization_tab_content

# ============================================
# CALLBACK: switch between tab contents
# ============================================
@callback(
    Output("opti-run-tab-content", "children"),
    Input("opti-run-tabs", "active_tab")
)
def render_opti_run_tabs(active_tab):
    if active_tab == "bo-tab":
        return get_bo_tab_content()
    elif active_tab == "viz-tab":
        return get_visualization_tab_content()
    return html.Div("Unknown tab selected.")


# ============================================
# MAIN DISPLAY CALLBACK - Initial Load
# ============================================

@callback(
    Output("excel-table-container", "children"),
    [Input("current-excel-file", "data"),
     Input("selected-file-store", "data"),
     Input("url", "pathname")],
)
def display_excel_table(current_excel_data, selected_file_data, pathname):
    """Display Excel table with proper column formatting and domain information"""
    
    # Only trigger on navigation to /Opt-run page
    if pathname != "/Opt-run":
        return dash.no_update
    
    # Determine which Excel file to load
    excel_filename = None
    sheet_name = None
    
    if current_excel_data:
        # Coming from param page after creating new Excel
        excel_filename = current_excel_data
        sheet_name = "Experiments"
    elif selected_file_data:
        # Coming from home page with existing file
        excel_filename = selected_file_data.get('excel_file')
        sheet_name = selected_file_data.get('selected_sheet', 'Experiments')
    
    if not excel_filename:
        return html.Div([
            html.H4("⚠️ No Excel file selected", className="text-center text-muted mt-5"),
            html.P("Please go back and create/select an Excel file first.", className="text-center"),
        ])
    
    try:
        # Ensure filename has extension
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        
        file_path = os.path.join(EXCEL_FOLDER, excel_filename)
        
        if not os.path.exists(file_path):
            return html.Div([
                html.H4("❌ File not found", className="text-center text-danger mt-5"),
                html.P(f"The file '{excel_filename}' could not be found.", className="text-center")
            ])
        
        # Load Excel file
        df_excel = pd.read_excel(file_path, sheet_name=sheet_name or 0, engine="openpyxl")
        
        # Store metadata in a hidden div for dynamic updates
        metadata_store = html.Div(id="domain-metadata", style={"display": "none"})
        
        # Check if domain exists and load metadata
        if DomainStorage.domain_exists(excel_filename):
            success, domain_object, metadata = DomainStorage.load_domain(excel_filename)
            
            if success and metadata:
                # Store metadata as JSON in hidden div
                import json
                metadata_store = html.Div(
                    id="domain-metadata",
                    children=json.dumps({
                        "parameter_names": metadata.get("parameter_names", []),
                        "objective_names": metadata.get("objective_names", []),
                        "extra_column_names": metadata.get("extra_column_names", []),
                        "parameters": metadata.get("parameters", [])
                    }),
                    style={"display": "none"}
                )
                
                # Get column information from metadata
                param_names = metadata.get("parameter_names", [])
                objective_names = metadata.get("objective_names", [])
                extra_names = metadata.get("extra_column_names", [])
                
                # Initial count of completed experiments
                completed_experiments = 0
                if objective_names and param_names:
                    for _, row in df_excel.iterrows():
                        # Check both parameters and objectives are filled
                        params_filled = all(
                            pd.notna(row.get(param, None)) and 
                            str(row.get(param, "")).strip() != ""
                            for param in param_names if param in df_excel.columns
                        )
                        objectives_filled = all(
                            pd.notna(row.get(obj, None)) and 
                            str(row.get(obj, "")).strip() != ""
                            for obj in objective_names if obj in df_excel.columns
                        )
                        if params_filled and objectives_filled:
                            completed_experiments += 1
                
                # Create initial domain info card (will be updated dynamically)
                domain_info_card = html.Div(id="dynamic-domain-card", children=[
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🔒 Domain Configuration", className="card-title mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Badge(f"Extra: {len(extra_names)}", color="secondary", className="me-2"),
                                    dbc.Badge(f"Parameters: {len(param_names)}", color="primary", className="me-2"),
                                    dbc.Badge(f"Objectives: {len(objective_names)}", color="success", className="me-2"),
                                ]),
                                dbc.Col([
                                    html.Div(id="experiment-counter", children=[
                                        html.P(f"Completed Experiments: {completed_experiments}/{len(df_excel)}", 
                                              className="mb-0 text-end")
                                    ])
                                ])
                            ])
                        ])
                    ], className="mb-3", color="light")
                ])
                
                # Create optimization section with dynamic button
                optimization_section = html.Div(id="dynamic-optimization-section", children=[
                    html.Div(id="optimization-status-message"),
                    html.Div(id="optimization-button-container"),
                    # Add loading modal here
                    dbc.Modal([
                        dbc.ModalBody([
                            html.Div([
                                dbc.Spinner(
                                    color="primary",
                                    size="lg",
                                    spinner_style={"width": "3rem", "height": "3rem"}
                                ),
                                html.H4("Running Bayesian Optimization", className="mt-3"),
                                html.P("Please wait while we calculate the next optimal experiment...", className="text-muted"),
                                html.P([
                                    html.I(className="bi bi-info-circle me-2"),
                                    "This may take a few moments depending on your data complexity."
                                ], className="small text-info")
                            ], className="text-center")
                        ])
                    ], id="loading-modal", is_open=False, centered=True, backdrop="static", keyboard=False),
                    html.Div(id="optimization-results")
                ])
            else:
                domain_info_card = dbc.Alert([
                    "❌ Failed to load domain metadata"
                ], color="danger", className="mb-3")
                optimization_section = html.Div()
        else:
            domain_info_card = dbc.Alert([
                "⚠️ No domain found for this Excel file"
            ], color="warning", className="mb-3")
            optimization_section = html.Div()
            metadata_store = html.Div(id="domain-metadata", style={"display": "none"})
        
        # Create column configurations with color coding
        columns = []
        style_data_conditional = []
        
        # Determine column types if domain exists
        column_types = {}
        if DomainStorage.domain_exists(excel_filename):
            success, _, metadata = DomainStorage.load_domain(excel_filename)
            if success and metadata:
                for col in metadata.get('extra_column_names', []):
                    column_types[col] = 'extra'
                for col in metadata.get('parameter_names', []):
                    column_types[col] = 'parameter'
                for col in metadata.get('objective_names', []):
                    column_types[col] = 'objective'
        
        # Configure columns
        for col in df_excel.columns:
            col_type = column_types.get(col, 'unknown')
            
            columns.append({
                "name": col,
                "id": col,
                "editable": True,
            })
            
            # Add light background color based on type
            bg_color = COLUMN_COLORS.get(col_type, COLUMN_COLORS['unknown'])
            style_data_conditional.append({
                'if': {'column_id': col},
                'backgroundColor': f'{bg_color}20',
            })
            
            # Highlight empty cells differently for parameters and objectives
            if col_type in ['parameter', 'objective']:
                style_data_conditional.append({
                    'if': {
                        'column_id': col,
                        'filter_query': f'{{{col}}} = ""'
                    },
                    'backgroundColor': '#fff3cd',
                    'border': '2px solid #ffc107'
                })
        
        # Create the data table
        table = dash_table.DataTable(
            id="excel-editable-table",
            data=df_excel.to_dict('records'),
            columns=columns,
            editable=True,
            row_deletable=True,
            filter_action='native',
            sort_action='native',
            page_action='native',
            page_size=20,
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "center",
                "padding": "10px",
                "fontSize": "14px"
            },
            style_header={
                "fontWeight": "bold",
                "backgroundColor": "#343a40",
                "color": "white"
            },
            style_data_conditional=style_data_conditional,
            export_format="xlsx"
        )
        
        # Build the complete layout
        return html.Div([
            metadata_store,  # Hidden metadata storage
            html.H4(f"📊 Working with: {excel_filename}", className="mb-3"),
            domain_info_card,
            table,
            html.Div(id="save-status", className="mt-2"),
            optimization_section
        ])
        
    except Exception as e:
        return html.Div([
            html.H4("❌ Error loading Excel file", className="text-center text-danger mt-5"),
            html.P(f"Error: {str(e)}", className="text-center")
        ])


# ============================================
# DYNAMIC UPDATE CALLBACK - enable/disable button only
# ============================================

@callback(
    [Output('experiment-counter', 'children'),
     Output('optimization-status-message', 'children'),
     Output('run-BO-btn', 'disabled')],
    [Input('excel-editable-table', 'data')],
    [State('domain-metadata', 'children')],
    prevent_initial_call=True
)
def update_experiment_counter_and_button(table_data, metadata_json):
    """Update experiment counter and strictly disable button until ALL experiments are filled"""
    if not table_data or not metadata_json:
        return dash.no_update, dash.no_update, True

    try:
        import json
        metadata = json.loads(metadata_json)
        param_names = metadata.get("parameter_names", [])
        objective_names = metadata.get("objective_names", [])

        df = pd.DataFrame(table_data)

        completed_experiments = 0
        for _, row in df.iterrows():
            params_filled = all(pd.notna(row.get(param)) and str(row[param]).strip() != ""
                                for param in param_names if param in df.columns)
            objectives_filled = all(pd.notna(row.get(obj)) and str(row[obj]).strip() != ""
                                    for obj in objective_names if obj in df.columns)
            if params_filled and objectives_filled:
                completed_experiments += 1

        total_experiments = len(df)

        # Counter display
        counter_display = html.P(
            f"Completed Experiments: {completed_experiments}/{total_experiments}",
            className="mb-0 text-end"
        )

        # 3-stage logic
        if completed_experiments == 0:
            status_msg = dbc.Alert(
                "❌ You need to fill all experiments before starting BO.",
                color="danger"
            )
            button_disabled = True
        elif completed_experiments < total_experiments:
            status_msg = dbc.Alert(
                f"⚠️ You have filled {completed_experiments} experiments, "
                f"but you must fill ALL {total_experiments} to start BO.",
                color="warning"
            )
            button_disabled = True
        else:  # all filled
            status_msg = dbc.Alert(
                "✅ All experiments are filled! You can start BO by clicking the button.",
                color="success"
            )
            button_disabled = False

        return counter_display, status_msg, button_disabled

    except Exception as e:
        return html.P(f"Error: {str(e)}", className="text-danger"), dash.no_update, True

# FIXED: Single robust callback for Bayesian Optimization

@callback(
    [Output("optimization-results", "children"),
     Output("loading-modal", "is_open"),
     Output("save-status", "children", allow_duplicate=True)],
    Input("run-BO-btn", "n_clicks"),
    [State("current-excel-file", "data"),
     State("selected-file-store", "data"),
     State("excel-editable-table", "data"),
     State("domain-metadata", "children")],
    prevent_initial_call=True,
    running=[
        (Output("run-BO-btn", "disabled"), True, False),
        (Output("loading-modal", "is_open"), True, False)
    ]
)
def run_bayesian_optimization_single(n_clicks, current_excel_data, selected_file_data, table_data, metadata_json):
    """Single callback to handle entire BO process with proper error handling"""
    
    if not n_clicks:
        raise PreventUpdate
    
    # Clear previous results and status
    initial_status = ""
    
    try:
        
        # Step 1: Validate inputs
        if not table_data:
            error_msg = dbc.Alert("❌ No table data available", color="danger")
            return error_msg, False, error_msg
        
        # Step 2: Determine Excel filename with better validation
        excel_filename = None
        if current_excel_data:
            excel_filename = current_excel_data
        elif selected_file_data and isinstance(selected_file_data, dict):
            excel_filename = selected_file_data.get('excel_file')
        elif selected_file_data and isinstance(selected_file_data, str):
            excel_filename = selected_file_data
        
        if not excel_filename:
            error_msg = dbc.Alert([
                html.H6("❌ No Excel File Selected"),
                html.P("Please go back and create/select an Excel file first."),
                html.Small(f"Debug: current_excel={current_excel_data}, selected_file={selected_file_data}", className="text-muted")
            ], color="danger")
            return error_msg, False, error_msg
        
        # Step 3: Ensure filename has extension
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        
        # Step 4: Check domain exists
        if not DomainStorage.domain_exists(excel_filename):
            error_msg = dbc.Alert([
                html.H6("❌ No Domain Found"),
                html.P(f"No domain configuration found for '{excel_filename}'."),
                html.P("Please create a domain first in the Parameter Configuration page.")
            ], color="danger")
            return error_msg, False, error_msg
        
        # Step 5: Load domain and metadata
        success, domain, metadata = DomainStorage.load_domain(excel_filename)
        if not success:
            error_msg = dbc.Alert([
                html.H6("❌ Domain Loading Failed"),
                html.P(f"Failed to load domain: {domain}")
            ], color="danger")
            return error_msg, False, error_msg
        
        # Step 6: Parse metadata 
        if metadata_json:
            try:
                import json
                metadata_parsed = json.loads(metadata_json)
                param_names = metadata_parsed.get("parameter_names", [])
                obj_names = metadata_parsed.get("objective_names", [])
            except (json.JSONDecodeError, TypeError) as e:
                print(f"⚠️ Metadata parsing error: {e}")
                param_names = metadata.get('parameter_names', [])
                obj_names = metadata.get('objective_names', [])
        else:
            param_names = metadata.get('parameter_names', [])
            obj_names = metadata.get('objective_names', [])
        
        if not param_names or not obj_names:
            error_msg = dbc.Alert([
                html.H6("❌ Invalid Domain Configuration"),
                html.P("Domain must have at least one parameter and one objective.")
            ], color="danger")
            return error_msg, False, error_msg
        
        # Step 7: Process experiments data
        experiments_df = pd.DataFrame(table_data)
        
        # Filter to relevant columns
        relevant_columns = param_names + obj_names
        existing_columns = [col for col in relevant_columns if col in experiments_df.columns]
        
        if not existing_columns:
            error_msg = dbc.Alert([
                html.H6("❌ Column Mismatch"),
                html.P("No matching columns found between Excel and domain definition."),
                html.P(f"Expected: {relevant_columns}"),
                html.P(f"Available: {list(experiments_df.columns)}")
            ], color="danger")
            return error_msg, False, error_msg
        
        experiments_df = experiments_df[existing_columns].copy()
        
        # Step 8: Find complete experiments
        complete_rows = []
        for idx, row in experiments_df.iterrows():
            all_filled = True
            
            # Check parameters
            for param_col in param_names:
                if param_col in row:
                    val = row[param_col]
                    if pd.isna(val) or str(val).strip() == "" or str(val).lower() in ["none", "null"]:
                        all_filled = False
                        break
            
            # Check objectives
            if all_filled:
                for obj_col in obj_names:
                    if obj_col in row:
                        val = row[obj_col]
                        if pd.isna(val) or str(val).strip() == "" or str(val).lower() in ["none", "null"]:
                            all_filled = False
                            break
            
            if all_filled:
                complete_rows.append(idx)
        
        if not complete_rows:
            error_msg = dbc.Alert([
                html.H6("⚠️ No Complete Experiments"),
                html.P("Please fill all parameter and objective values before running optimization."),
                html.P(f"Found {len(experiments_df)} rows, but none have complete data.")
            ], color="warning")
            return error_msg, False, error_msg
        
        # Step 9: Get complete experiments
        experiments = experiments_df.loc[complete_rows].reset_index(drop=True)
        
        # Step 10: Run optimization
        result = optimization(obj_names, domain, Strategy=None, AF=None, experiments=experiments)
        
        # Step 11: Process results
        if result is None or (hasattr(result, 'empty') and result.empty):
            warning_msg = dbc.Alert([
                html.H6("⚠️ No Recommendations Generated"),
                html.P("The optimization algorithm couldn't generate new recommendations."),
                html.P("This might happen if the current experiments already cover the optimal space.")
            ], color="warning")
            return warning_msg, False, warning_msg
        
        result_df = result if isinstance(result, pd.DataFrame) else pd.DataFrame(result)
        
        # Step 12: Format results for display
        if metadata_json:
            try:
                import json
                metadata_full = json.loads(metadata_json)
                param_defs = metadata_full.get("parameters", [])
                
                # Round continuous parameters
                for p in param_defs:
                    pname = p.get("name")
                    ptype = p.get("type", "").lower()
                    if pname in result_df.columns and ptype == "float":
                        result_df[pname] = result_df[pname].round(2)
            except Exception as e:
                print(f"⚠️ Result formatting error: {e}")
        
        # Step 13: Create success response
        success_content = html.Div([
            dbc.Alert([
                html.I(className="bi bi-check-circle-fill me-2"),
                f"Optimization Complete! Generated {len(result_df)} recommendations."
            ], color="success", className="mb-3"),
            
            dbc.Card([
                dbc.CardHeader([
                    html.H5("🎯 Recommended Next Experiments", className="mb-0")
                ]),
                dbc.CardBody([
                    dash_table.DataTable(
                        data=result_df.to_dict('records'),
                        columns=[{"name": col, "id": col} for col in result_df.columns],
                        style_table={"overflowX": "auto"},
                        style_cell={"textAlign": "center", "padding": "10px"},
                        style_header={
                            "fontWeight": "bold",
                            "backgroundColor": "#007bff",
                            "color": "white"
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 0},
                                'backgroundColor': '#e3f2fd',
                                'fontWeight': 'bold'
                            }
                        ]
                    )
                ])
            ], className="mb-3"),
            
            dbc.Alert([
                html.H6("💡 Next Steps:", className="alert-heading"),
                html.Hr(),
                html.Ol([
                    html.Li("Run the recommended experiment(s) in your lab"),
                    html.Li("Add the results to the table above"),
                    html.Li("Save the Excel file"),
                    html.Li("Click 'Run BO' again for the next recommendation")
                ]),
                html.P([
                    html.I(className="bi bi-graph-up me-2"),
                    f"Based on {len(experiments)} completed experiments"
                ], className="mb-0 small text-muted")
            ], color="info")
        ])
        
        success_status = dbc.Alert(
            f"✅ BO completed: {len(result_df)} new recommendations generated", 
            color="success", 
            duration=5000
        )
        
        print(f"✅ BO optimization completed successfully")
        return success_content, False, success_status
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"💥 BO Error: {error_details}")
        
        error_content = dbc.Alert([
            html.H6("❌ Optimization Failed"),
            html.P(f"Error: {str(e)}"),
            html.Details([
                html.Summary("Click for technical details"),
                html.Pre(error_details, style={"fontSize": "12px", "whiteSpace": "pre-wrap"})
            ])
        ], color="danger")
        
        error_status = dbc.Alert(f"❌ BO failed: {str(e)}", color="danger", duration=5000)
        
        return error_content, False, error_status


# ============================================
# OTHER BUTTONS CALLBACKS 
# ============================================

@callback(
    Output('excel-editable-table', 'data', allow_duplicate=True),
    Input('add-row-btn', 'n_clicks'),
    [State('excel-editable-table', 'data'),
     State('excel-editable-table', 'columns')],
    prevent_initial_call=True
)
def add_row_to_table(n_clicks, data, columns):
    """Add a new empty row to the table with automatic 'BO' point type"""
    if n_clicks and data is not None:
        # Create new row with empty values
        new_row = {col['id']: '' for col in columns}
        
        # AUTOMATICALLY SET "Point type" TO "BO" FOR NEW ROWS
        if 'Point type' in new_row:
            new_row['Point type'] = 'BO'
        
        data.append(new_row)
        return data
    return dash.no_update


@callback(
    Output('save-status', 'children'),
    Input('save-excel-btn-opti', 'n_clicks'),
    [State('excel-editable-table', 'data'),
     State('current-excel-file', 'data'),
     State('selected-file-store', 'data')],
    prevent_initial_call=True
)
def save_excel_changes(n_clicks, table_data, current_excel_data, selected_file_data):
    """Save changes made to the Excel table"""
    if not n_clicks or not table_data:
        return dash.no_update
    
    # Determine Excel filename
    excel_filename = current_excel_data or (selected_file_data.get('excel_file') if selected_file_data else None)
    
    if not excel_filename:
        return dbc.Alert("❌ No Excel file to save", color="danger", duration=4000)
    
    try:
        # Ensure filename has extension
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        
        file_path = os.path.join(EXCEL_FOLDER, excel_filename)
        
        # Convert table data to DataFrame
        df = pd.DataFrame(table_data)
        
        # Load domain metadata to preserve column order
        if DomainStorage.domain_exists(excel_filename):
            success, _, metadata = DomainStorage.load_domain(excel_filename)
            if success and metadata:
                column_order = metadata.get('metadata', {}).get('column_order', [])
                if column_order:
                    # Reorder columns according to original order
                    existing_cols = [col for col in column_order if col in df.columns]
                    extra_cols = [col for col in df.columns if col not in column_order]
                    df = df[existing_cols + extra_cols]
        
        # Save to Excel with formatting
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Experiments')
            
            # Apply formatting
            worksheet = writer.sheets['Experiments']
            from openpyxl.styles import Font, PatternFill, Alignment
            
            # Format headers
            for cell in worksheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="343A40", end_color="343A40", fill_type="solid")
                cell.alignment = Alignment(horizontal='center', vertical='center')
        
        return dbc.Alert(
            f"✅ Successfully saved {len(df)} rows to {excel_filename}",
            color="success",
            duration=4000
        )
        
    except Exception as e:
        return dbc.Alert(f"❌ Failed to save: {str(e)}", color="danger", duration=4000)
    



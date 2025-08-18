import dash
from dash import Input, Output, State, callback, html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import os
from config_path import EXCEL_FOLDER, COLUMN_COLORS
from domain_storage import (
    DomainStorage,
    load_experiments_from_excel_file,
    prepare_experiments_from_excel_data
)
from utils.BoFire import optimization

@callback(
    Output("excel-table-container", "children"),
    [Input("current-excel-file", "data"),
     Input("selected-file-store", "data"),
     Input("url", "pathname")],
    prevent_initial_call=True
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
        
        # Check if domain exists and load metadata
        domain_info_card = html.Div()
        optimization_section = html.Div()
        
        if DomainStorage.domain_exists(excel_filename):
            success, domain_object, metadata = DomainStorage.load_domain(excel_filename)
            
            if success and metadata:
                # Get column information from metadata
                param_names = metadata.get("parameter_names", [])
                objective_names = metadata.get("objective_names", [])
                extra_names = metadata.get("extra_column_names", [])
                
                # Count completed experiments
                completed_experiments = 0
                if objective_names:
                    for _, row in df_excel.iterrows():
                        if all(pd.notna(row.get(obj, None)) and 
                               str(row.get(obj, "")).strip() != "" 
                               for obj in objective_names if obj in df_excel.columns):
                            completed_experiments += 1
                
                # Create domain info card
                domain_info_card = dbc.Card([
                    dbc.CardBody([
                        html.H5("🔒 Domain Configuration", className="card-title mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Badge(f"Extra: {len(extra_names)}", color="secondary", className="me-2"),
                                dbc.Badge(f"Parameters: {len(param_names)}", color="primary", className="me-2"),
                                dbc.Badge(f"Objectives: {len(objective_names)}", color="success", className="me-2"),
                            ]),
                            dbc.Col([
                                html.P(f"Completed Experiments: {completed_experiments}/{len(df_excel)}", 
                                      className="mb-0 text-end")
                            ])
                        ])
                    ])
                ], className="mb-3", color="light")
                
                # Add optimization controls if we have completed experiments
                if completed_experiments > 0 and objective_names:
                    optimization_section = html.Div([
                        dbc.Alert([
                            f"✅ {completed_experiments} experiments ready for optimization"
                        ], color="success", className="mb-3"),
                        html.Div(id="optimization-results")
                    ])
                elif objective_names:
                    optimization_section = dbc.Alert([
                        "⚠️ Fill in objective values to enable optimization"
                    ], color="warning", className="mb-3")
        else:
            domain_info_card = dbc.Alert([
                "⚠️ No domain found for this Excel file"
            ], color="warning", className="mb-3")
        
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
            
            # Highlight empty objective cells
            if col_type == 'objective':
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


@callback(
    Output('excel-editable-table', 'data'),
    Input('add-row-btn', 'n_clicks'),
    [State('excel-editable-table', 'data'),
     State('excel-editable-table', 'columns')],
    prevent_initial_call=True
)
def add_row_to_table(n_clicks, data, columns):
    """Add a new empty row to the table"""
    if n_clicks and data is not None:
        new_row = {col['id']: '' for col in columns}
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
    
@callback(
    [Output("loading-modal", "is_open", allow_duplicate=True),
     Output("run-BO-btn", "disabled", allow_duplicate=True),
     Output("optimization-store", "data", allow_duplicate=True)],
    Input("run-BO-btn", "n_clicks"),
    prevent_initial_call=True
)
def open_modal(n_clicks):
    # This triggers the second callback
    return True, True, {"trigger": n_clicks}


@callback(
    [Output("optimization-results", "children"),
     Output("loading-modal", "is_open", allow_duplicate=True),
     Output("run-BO-btn", "disabled", allow_duplicate=True)],
    Input("optimization-store", "data"),  # trigger when store updated
    State("current-excel-file", "data"),
    State("selected-file-store", "data"),
    State("excel-editable-table", "data"),
    prevent_initial_call=True
)
def run_bayesian_optimization(_, current_excel_data, selected_file_data, table_data):
    """Run Bayesian optimization using stored domain and current table data"""

    # Note: The modal will open immediately when the callback starts
    # and close when it ends, giving immediate feedback to the user
    
    try:
        # Determine Excel filename
        excel_filename = current_excel_data or (selected_file_data.get('excel_file') if selected_file_data else None)
        
        if not excel_filename:
            return dbc.Alert("❌ No Excel file selected", color="danger"), False, False
        
        # Ensure filename has extension
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        
        # Check if domain exists
        if not DomainStorage.domain_exists(excel_filename):
            return dbc.Alert(
                "❌ No domain found for this Excel file.",
                color="danger"
            ), False, False
        
        # Load domain and metadata
        success, domain, metadata = DomainStorage.load_domain(excel_filename)
        if not success:
            return dbc.Alert(f"❌ Failed to load domain: {domain}", color="danger"), False, False
        
        # Convert table data to DataFrame
        experiments_df = pd.DataFrame(table_data)
        
        # Get parameter and objective column names from metadata
        param_names = metadata.get('parameter_names', [])
        obj_names = metadata.get('objective_names', [])
        
        # Filter to only parameter and objective columns
        relevant_columns = param_names + obj_names
        existing_columns = [col for col in relevant_columns if col in experiments_df.columns]
        
        if not existing_columns:
            return dbc.Alert([
                html.H6("❌ Column Mismatch"),
                html.P("No matching columns found between Excel and domain definition.")
            ], color="danger"), False, False
        
        # Filter to relevant columns
        experiments_df = experiments_df[existing_columns].copy()
        
        # Filter rows with complete objective values
        complete_rows = []
        for idx, row in experiments_df.iterrows():
            # Check if all objectives have values (not NaN, not empty string)
            has_all_objectives = True
            for obj_col in obj_names:
                if obj_col in row:
                    val = row[obj_col]
                    if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "none":
                        has_all_objectives = False
                        break
                else:
                    has_all_objectives = False
                    break
            
            if has_all_objectives:
                complete_rows.append(idx)
        
        if not complete_rows:
            return dbc.Alert([
                html.H6("⚠️ No Complete Experiments Found"),
                html.P("Please ensure all objective values are filled for at least one experiment.")
            ], color="warning"), False, False
        
        # Get only complete experiments
        experiments = experiments_df.loc[complete_rows].reset_index(drop=True)
        
        # Run optimization - pass the DataFrame directly
        result = optimization(obj_names, domain, Strategy=None, AF=None, experiments=experiments)
        
        # Check if result is valid
        if result is None:
            return dbc.Alert("No recommendations generated. Check your optimization configuration.", color="warning"), False, False
        
        # Handle different result types
        if hasattr(result, 'empty'):
            # It's a DataFrame
            if result.empty:
                return dbc.Alert("No recommendations generated. Check your data.", color="warning"), False, False
            
            result_df = result
        elif isinstance(result, pd.DataFrame):
            if result.empty:
                return dbc.Alert("No recommendations generated. Check your data.", color="warning"), False, False
            result_df = result
        else:
            # Try to convert to DataFrame
            try:
                result_df = pd.DataFrame(result)
                if result_df.empty:
                    return dbc.Alert("No recommendations generated. Check your data.", color="warning"), False, False
            except:
                return dbc.Alert(f"Unexpected result type: {type(result)}", color="warning"), False, False
        
        # 🔹 Round continuous parameters (type == float)
        param_defs = metadata.get("parameters", [])
        for p in param_defs:
            pname = p.get("name")
            ptype = p.get("type", "").lower()
            if pname in result_df.columns and ptype == "float":
                result_df[pname] = result_df[pname].apply(
                    lambda v: round(v, 2) if pd.notna(v) else v
                )

        # 🔹 Round all columns after the parameter block (predictions, std, desirability)
        param_names = metadata.get("parameter_names", [])
        if param_names:
            try:
                last_param_index = max(result_df.columns.get_loc(p) for p in param_names if p in result_df.columns)
                post_param_cols = result_df.columns[last_param_index+1:]
                for col in post_param_cols:
                    result_df[col] = result_df[col].apply(lambda v: round(v, 2) if pd.notna(v) else v)
            except Exception as e:
                print(f"⚠️ Could not round post-parameter columns: {e}")

        # Format the result for display with animation
        result_content = html.Div([
            dbc.Alert([
                html.I(className="bi bi-check-circle-fill me-2"),
                "Optimization Complete!"
            ], color="success", className="mb-3", fade=True, is_open=True),
            
            dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        "Recommended Next Experiments"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dash_table.DataTable(
                        data=result_df.to_dict('records'),
                        columns=[{"name": col, "id": col, "format": {"specifier": ".4f"}} 
                               for col in result_df.columns],
                        style_table={"overflowX": "auto"},
                        style_cell={"textAlign": "center", "padding": "10px", "fontSize": "14px"},
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
                html.H6([
                    html.I(className="bi bi-lightbulb me-2"),
                    "Next Steps:"
                ], className="alert-heading"),
                html.Hr(),
                html.P([
                    "1. Run the recommended experiment(s) in your lab",
                    html.Br(),
                    "2. Add the results to the table above",
                    html.Br(),
                    "3. Save the Excel file",
                    html.Br(),
                    "4. Run optimization again for the next recommendation"
                ], className="mb-0"),
                html.Hr(),
                html.P([
                    html.I(className="bi bi-graph-up me-2"),
                    f"Based on {len(experiments)} completed experiments"
                ], className="mb-0 small")
            ], color="info")
        ])
        
        return result_content, False, False
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Optimization error: {error_details}")
        
        error_content = dbc.Alert([
            html.H6([
                html.I(className="bi bi-exclamation-triangle-fill me-2"),
                "Optimization Failed"
            ]),
            html.P(f"Error: {str(e)}"),
            html.Details([
                html.Summary("Technical Details"),
                html.Pre(error_details, style={"fontSize": "12px", "whiteSpace": "pre-wrap"})
            ])
        ], color="danger")
        
        return error_content, False, False
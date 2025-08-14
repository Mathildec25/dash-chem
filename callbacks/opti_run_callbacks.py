import dash
from dash import Input, Output, State, callback, html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import os
from config_path import SAVE_FOLDER, COLUMN_COLORS
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
            dbc.Button("← Go to Home", href="/", color="primary", className="mt-3")
        ])
    
    try:
        # Ensure filename has extension
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        
        file_path = os.path.join(SAVE_FOLDER, excel_filename)
        
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
                "type": "numeric" if col_type in ['parameter', 'objective'] else "text"
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
        
        file_path = os.path.join(SAVE_FOLDER, excel_filename)
        
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
    Output('optimization-results', 'children'),
    Input('run-BO-btn', 'n_clicks'),
    [State('current-excel-file', 'data'),
     State('selected-file-store', 'data'),
     State('excel-editable-table', 'data')],
    prevent_initial_call=True
)
def run_bayesian_optimization(n_clicks, current_excel_data, selected_file_data, table_data):
    """Run Bayesian optimization using stored domain and current table data"""
    if not n_clicks:
        return dash.no_update
    
    try:
        # Determine Excel filename
        excel_filename = current_excel_data or (selected_file_data.get('excel_file') if selected_file_data else None)
        
        if not excel_filename:
            return dbc.Alert("❌ No Excel file selected", color="danger")
        
        # Ensure filename has extension
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        
        # Check if domain exists
        if not DomainStorage.domain_exists(excel_filename):
            return dbc.Alert(
                "❌ No domain found for this Excel file.",
                color="danger"
            )
        
        # Load domain and metadata
        success, domain, metadata = DomainStorage.load_domain(excel_filename)
        if not success:
            return dbc.Alert(f"❌ Failed to load domain: {domain}", color="danger")
        
        # Prepare experiments data from current table
        experiments_df = pd.DataFrame(table_data)
        experiments = prepare_experiments_from_excel_data(experiments_df, metadata)
        
        if experiments is None or experiments.empty:
            return dbc.Alert([
                html.H6("⚠️ No Complete Experiments Found"),
                html.P("Please ensure all objective values are filled for at least one experiment.")
            ], color="warning")
        
        # Run optimization
        result = optimization(domain, strategy=None, AF=None, experiments=experiments)
        
        # Format the result for display
        if result is not None and not result.empty:
            return html.Div([
                dbc.Alert("✅ Optimization Complete!", color="success", className="mb-3"),
                html.H5("🎯 Recommended Next Experiments:", className="mb-3"),
                dash_table.DataTable(
                    data=result.to_dict('records'),
                    columns=[{"name": col, "id": col, "type": "numeric", "format": {"specifier": ".4f"}} 
                           for col in result.columns],
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "center", "padding": "10px"},
                    style_header={"fontWeight": "bold", "backgroundColor": "#007bff", "color": "white"}
                ),
                html.Hr(),
                html.P("💡 Run these experiments in your lab, add the results to the table above, and run optimization again.")
            ])
        else:
            return dbc.Alert("No recommendations generated. Check your data.", color="warning")
        
    except Exception as e:
        return dbc.Alert([
            html.H6("❌ Optimization Failed"),
            html.P(f"Error: {str(e)}")
        ], color="danger")
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

"""
Improved version of the display_excel_table callback with better debugging
Add this to callbacks/opti_run_callbacks/run_part.py
"""

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
    
    # Debug logging
    print(f"🔍 display_excel_table triggered:")
    print(f"   - current_excel_data: {current_excel_data}")
    print(f"   - selected_file_data: {selected_file_data}")
    print(f"   - pathname: {pathname}")
    
    # Determine which Excel file to load
    excel_filename = None
    sheet_name = None
    
    if current_excel_data:
        # Coming from param page after creating new Excel
        excel_filename = current_excel_data
        sheet_name = "Experiments"
        print(f"✅ Using current_excel_data: {excel_filename}")
    elif selected_file_data:
        # Coming from home page with existing file
        excel_filename = selected_file_data.get('excel_file')
        sheet_name = selected_file_data.get('selected_sheet', 'Experiments')
        print(f"✅ Using selected_file_data: {excel_filename}")
    
    if not excel_filename:
        error_msg = html.Div([
            dbc.Alert([
                html.H5("⚠️ No Excel file selected", className="alert-heading"),
                html.P("Please go back and create/select an Excel file first."),
                dcc.Link(
                    dbc.Button("Go to Home", color="primary", size="sm"),
                    href="/Opt-home"
                )
            ], color="warning", className="text-center mt-5")
        ])
        print("❌ No excel_filename found")
        return error_msg
    
    try:
        # Ensure filename has extension
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        
        file_path = os.path.join(EXCEL_FOLDER, excel_filename)
        print(f"📂 Looking for file: {file_path}")
        
        if not os.path.exists(file_path):
            error_msg = html.Div([
                dbc.Alert([
                    html.H5("❌ File not found", className="alert-heading"),
                    html.P(f"The file '{excel_filename}' could not be found."),
                    html.Small(f"Expected path: {file_path}", className="text-muted d-block"),
                    dcc.Link(
                        dbc.Button("Go Back", color="secondary", size="sm", className="mt-2"),
                        href="/Opt-home"
                    )
                ], color="danger", className="text-center mt-5")
            ])
            print(f"❌ File not found: {file_path}")
            return error_msg
        
        # Load Excel file
        print(f"📖 Reading Excel file: {excel_filename}, sheet: {sheet_name}")
        df_excel = pd.read_excel(file_path, sheet_name=sheet_name or 0, engine="openpyxl")
        print(f"✅ Loaded {len(df_excel)} rows, {len(df_excel.columns)} columns")
        print(f"   Columns: {list(df_excel.columns)}")
        
        # Store metadata in a hidden div for dynamic updates
        metadata_store = html.Div(id="domain-metadata", style={"display": "none"})
        
        # Check if domain exists and load metadata
        domain_info_card = None
        optimization_section = html.Div()
        
        if DomainStorage.domain_exists(excel_filename):
            success, domain_object, metadata = DomainStorage.load_domain(excel_filename)
            
            if success and metadata:
                print(f"✅ Domain loaded successfully")
                print(f"   Parameters: {metadata.get('parameter_names', [])}")
                print(f"   Objectives: {metadata.get('objective_names', [])}")
                
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
                
                print(f"📊 Completed experiments: {completed_experiments}/{len(df_excel)}")
                
                # Create initial domain info card (will be updated dynamically)
                domain_info_card = html.Div(id="dynamic-domain-card", children=[
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🔒 Domain Configuration", className="mb-3", style={"fontWeight": "600"}),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Badge(f"Extra: {len(extra_names)}", color="secondary", className="me-2"),
                                    dbc.Badge(f"Parameters: {len(param_names)}", color="primary", className="me-2"),
                                    dbc.Badge(f"Objectives: {len(objective_names)}", color="success", className="me-2"),
                                ], width="auto"),
                                dbc.Col([
                                    html.Div(id="experiment-counter", children=[
                                        html.P(f"Completed Experiments: {completed_experiments}/{len(df_excel)}", 
                                              className="mb-0 text-end",
                                              style={"fontWeight": "500"})
                                    ])
                                ], width=True)
                            ], className="align-items-center")
                        ], style={"padding": "1rem"})
                    ], className="mb-3", style={
                        "borderRadius": "8px",
                        "border": "1px solid #e0e0e0",
                        "backgroundColor": "#f8f9fa"
                    })
                ])
                
                # Create optimization section with dynamic button
                optimization_section = html.Div(id="dynamic-optimization-section", children=[
                    html.Div(id="optimization-status-message"),
                    html.Div(id="optimization-button-container"),
                    # Loading modal
                    dbc.Modal([
                        dbc.ModalBody([
                            html.Div([
                                dbc.Spinner(
                                    color="primary",
                                    size="lg",
                                    spinner_style={"width": "3rem", "height": "3rem"}
                                ),
                                html.H4("Running Bayesian Optimization", className="mt-3"),
                                html.P("Please wait while we calculate the next optimal experiment...", 
                                      className="text-muted"),
                                html.P([
                                    html.I(className="bi bi-info-circle me-2"),
                                    "This may take a few moments depending on your data complexity."
                                ], className="small text-info")
                            ], className="text-center py-4")
                        ])
                    ], id="loading-modal", is_open=False, centered=True, backdrop="static", keyboard=False),
                    html.Div(id="optimization-results")
                ])
            else:
                domain_info_card = dbc.Alert([
                    html.H6("❌ Failed to load domain metadata", className="alert-heading"),
                    html.P(str(domain_object))
                ], color="danger", className="mb-3")
        else:
            domain_info_card = dbc.Alert([
                html.H6("⚠️ No domain found", className="alert-heading"),
                html.P(f"No domain configuration found for '{excel_filename}'."),
                html.P("Please create a domain first in the Parameter Configuration page."),
                dcc.Link(
                    dbc.Button("Configure Domain", color="primary", size="sm"),
                    href="/Opt-param"
                )
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
        
        # Configure columns with color coding
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
                'backgroundColor': f'{bg_color}20',  # 20% opacity
            })
            
            # Highlight empty cells for parameters and objectives
            if col_type in ['parameter', 'objective']:
                style_data_conditional.append({
                    'if': {
                        'column_id': col,
                        'filter_query': f'{{{col}}} = ""'
                    },
                    'backgroundColor': '#fff3cd',
                    'border': '2px solid #ffc107'
                })
        
        print(f"✅ Created {len(columns)} columns with styling")
        
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
            style_table={
                "overflowX": "auto",
                "borderRadius": "8px"
            },
            style_cell={
                "textAlign": "center",
                "padding": "12px",
                "fontSize": "14px",
                "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
            },
            style_header={
                "fontWeight": "600",
                "backgroundColor": "#343a40",
                "color": "white",
                "border": "1px solid #343a40",
                "fontSize": "14px"
            },
            style_data={
                "border": "1px solid #e0e0e0"
            },
            style_data_conditional=style_data_conditional,
            export_format="xlsx",
            export_headers="display"
        )
        
        # Build the complete layout
        print("✅ Building complete layout")
        
        return html.Div([
            metadata_store,  # Hidden metadata storage
            html.H4([
                html.I(className="bi bi-file-earmark-spreadsheet me-2"),
                excel_filename
            ], className="mb-3", style={"color": "#1a1a1a", "fontWeight": "600"}),
            domain_info_card,
            table,
            html.Div(id="save-status", className="mt-2"),
            optimization_section
        ])
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"💥 Error in display_excel_table:")
        print(error_trace)
        
        return html.Div([
            dbc.Alert([
                html.H5("❌ Error loading Excel file", className="alert-heading"),
                html.P(f"Error: {str(e)}", className="mb-2"),
                html.Details([
                    html.Summary("Technical Details", style={"cursor": "pointer"}),
                    html.Pre(error_trace, style={
                        "fontSize": "12px", 
                        "whiteSpace": "pre-wrap",
                        "backgroundColor": "#f8f9fa",
                        "padding": "1rem",
                        "borderRadius": "4px",
                        "marginTop": "0.5rem"
                    })
                ])
            ], color="danger", className="mt-5")
        ])
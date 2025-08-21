import dash
from dash import Input, Output, State, callback, html, dash_table, dcc
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
from components.Figures_BO import create_parallel_coordinates, create_enhanced_objectives_scatter, create_iteration_plot

# ============================================
# VISUALIZATION UPDATE CALLBACK
# ============================================

@callback(
    Output("parallel-coordinates-plot", "figure"),
    [Input("url", "pathname")],
    [State("current-excel-file", "data"),
     State("selected-file-store", "data")]
)
def update_parallel_coordinates(pathname, current_excel_data, selected_file_data):
    """Update parallel coordinates plot when data is loaded"""
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
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="⚠️ No Excel file selected",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        empty_fig.update_layout(height=600)
        return empty_fig
    
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
        df = pd.read_excel(file_path, sheet_name=sheet_name or 0, engine="openpyxl")
        
        # Load domain metadata
        metadata = {}
        if DomainStorage.domain_exists(excel_filename):
            success, domain, domain_metadata = DomainStorage.load_domain(excel_filename)
            if success:
                metadata = {
                    "parameter_names": domain_metadata.get("parameter_names", []),
                    "objective_names": domain_metadata.get("objective_names", []),
                    "parameters": domain_metadata.get("parameters", [])
                }
        
        # Create the plot
        fig = create_parallel_coordinates(df, metadata)
        
        return fig
        
    except Exception as e:
        # Return error figure and message
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"Error creating visualization: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        error_fig.update_layout(
            title="Visualization Error",
            height=600
        )
        
        return error_fig
    

# ============================================
# POPULATE SCATTER DROPDOWNS WITH AVAILABLE COLUMNS
# ============================================

@callback(
    [Output("scatter-x-dropdown", "options"),
     Output("scatter-y-dropdown", "options"),
     Output("scatter-z-dropdown", "options"),
     Output("scatter-color-dropdown", "options"),
     Output("scatter-size-dropdown", "options"),
     Output("scatter-x-dropdown", "value"),
     Output("scatter-y-dropdown", "value"),
     Output("scatter-z-dropdown", "value")],
    [Input("url", "pathname")],
    [State("current-excel-file", "data"),
     State("selected-file-store", "data")]
)
def populate_scatter_dropdowns(pathname, current_excel_data, selected_file_data):
    """Populate the scatter plot dropdowns with available columns"""
    # Only trigger on navigation to /Opt-run page
    if pathname != "/Opt-run":
        return [[] for _ in range(5)] + [None, None, None]
    
    # Determine which Excel file to load
    excel_filename = None
    sheet_name = None
    
    if current_excel_data:
        excel_filename = current_excel_data
        sheet_name = "Experiments"
    elif selected_file_data:
        excel_filename = selected_file_data.get('excel_file')
        sheet_name = selected_file_data.get('selected_sheet', 'Experiments')
    
    if not excel_filename:
        return [[] for _ in range(5)] + [None, None, None]
    
    try:
        # Ensure filename has extension
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        
        file_path = os.path.join(EXCEL_FOLDER, excel_filename)
        
        if not os.path.exists(file_path):
            return [[] for _ in range(5)] + [None, None, None]
        
        # Load Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name or 0, engine="openpyxl")
        
        # Load domain metadata to get column types
        metadata = {}
        if DomainStorage.domain_exists(excel_filename):
            success, domain, domain_metadata = DomainStorage.load_domain(excel_filename)
            if success:
                metadata = {
                    "parameter_names": domain_metadata.get("parameter_names", []),
                    "objective_names": domain_metadata.get("objective_names", []),
                    "extra_column_names": domain_metadata.get("extra_column_names", [])
                }
        
        # Get all numeric columns, categorized by type
        numeric_options = []
        all_options = []
        
        # Add objectives first (highest priority)
        objective_names = metadata.get("objective_names", [])
        for col in objective_names:
            if col in df.columns:
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    option = {"label": f"🎯 {col} (Objective)", "value": col}
                    numeric_options.append(option)
                    all_options.append(option)
                except:
                    option = {"label": f"🎯 {col} (Objective - Text)", "value": col}
                    all_options.append(option)
        
        # Add parameters
        parameter_names = metadata.get("parameter_names", [])
        for col in parameter_names:
            if col in df.columns and col not in [opt["value"] for opt in all_options]:
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    option = {"label": f"⚙️ {col} (Parameter)", "value": col}
                    numeric_options.append(option)
                    all_options.append(option)
                except:
                    option = {"label": f"⚙️ {col} (Parameter - Text)", "value": col}
                    all_options.append(option)
        
        # Add extra columns (including Point type)
        extra_names = metadata.get("extra_column_names", [])
        for col in extra_names:
            if col in df.columns and col not in [opt["value"] for opt in all_options]:
                if col == "Point type":
                    option = {"label": f"🏷️ {col} (Point Type)", "value": col}
                    all_options.append(option)
                else:
                    try:
                        pd.to_numeric(df[col], errors='coerce')
                        option = {"label": f"📊 {col} (Extra)", "value": col}
                        numeric_options.append(option)
                        all_options.append(option)
                    except:
                        option = {"label": f"📊 {col} (Extra - Text)", "value": col}
                        all_options.append(option)
        
        # Add any remaining columns
        for col in df.columns:
            if col not in [opt["value"] for opt in all_options]:
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    option = {"label": f"📈 {col} (Numeric)", "value": col}
                    numeric_options.append(option)
                    all_options.append(option)
                except:
                    option = {"label": f"📝 {col} (Text)", "value": col}
                    all_options.append(option)
        
        # Set default values
        default_x = None
        default_y = None  
        default_z = None
        
        if objective_names:
            if len(objective_names) >= 1 and objective_names[0] in df.columns:
                default_x = objective_names[0]
            if len(objective_names) >= 2 and objective_names[1] in df.columns:
                default_y = objective_names[1]
            if len(objective_names) >= 3 and objective_names[2] in df.columns:
                default_z = objective_names[2]
        
        # If no objectives, use first numeric columns
        if not default_x and numeric_options:
            default_x = numeric_options[0]["value"]
        if not default_y and len(numeric_options) > 1:
            default_y = numeric_options[1]["value"]
        if not default_z and len(numeric_options) > 2:
            default_z = numeric_options[2]["value"]
        
        return (
            numeric_options,  # X options (numeric only)
            numeric_options,  # Y options (numeric only)
            [{"label": "None (2D Plot)", "value": ""}] + numeric_options,  # Z options (optional)
            all_options,      # Color options (all columns - supports categorical)
            all_options,      # Size options (all columns - now supports categorical)
            default_x,        # Default X
            default_y,        # Default Y
            default_z         # Default Z
        )
        
    except Exception as e:
        print(f"Error populating scatter dropdowns: {e}")
        return [[] for _ in range(5)] + [None, None, None]


# ============================================
# UPDATE ENHANCED SCATTER PLOT CALLBACK
# ============================================

@callback(
    Output("objectives-scatter", "figure"),
    [Input("generate-scatter-btn", "n_clicks"),
     Input("url", "pathname")],
    [State("scatter-x-dropdown", "value"),
     State("scatter-y-dropdown", "value"),
     State("scatter-z-dropdown", "value"),
     State("scatter-color-dropdown", "value"),
     State("scatter-size-dropdown", "value"),
     State("current-excel-file", "data"),
     State("selected-file-store", "data")]
)
def update_enhanced_scatter_plot(n_clicks, pathname, x_col, y_col, z_col, color_col, size_col, 
                               current_excel_data, selected_file_data):
    """Update enhanced scatter plot when button is clicked or page loads"""
    # Only trigger on navigation to /Opt-run page or button click
    if pathname != "/Opt-run" and not n_clicks:
        return dash.no_update
    
    # Determine which Excel file to load
    excel_filename = None
    sheet_name = None
    
    if current_excel_data:
        excel_filename = current_excel_data
        sheet_name = "Experiments"
    elif selected_file_data:
        excel_filename = selected_file_data.get('excel_file')
        sheet_name = selected_file_data.get('selected_sheet', 'Experiments')
    
    if not excel_filename:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="⚠️ No Excel file selected",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        empty_fig.update_layout(height=600, title="Enhanced Scatter Plot")
        return empty_fig
    
    try:
        # Ensure filename has extension
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        
        file_path = os.path.join(EXCEL_FOLDER, excel_filename)
        
        if not os.path.exists(file_path):
            error_fig = go.Figure()
            error_fig.add_annotation(
                text="❌ File not found",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="red")
            )
            error_fig.update_layout(height=600, title="Enhanced Scatter Plot - File Not Found")
            return error_fig
        
        # Load Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name or 0, engine="openpyxl")
        
        # Load domain metadata
        metadata = {}
        if DomainStorage.domain_exists(excel_filename):
            success, domain, domain_metadata = DomainStorage.load_domain(excel_filename)
            if success:
                metadata = {
                    "parameter_names": domain_metadata.get("parameter_names", []),
                    "objective_names": domain_metadata.get("objective_names", []),
                    "parameters": domain_metadata.get("parameters", [])
                }
        
        # Handle empty Z column (for 2D plots)
        if z_col == "":
            z_col = None
        
        # Create the plot
        fig = create_enhanced_objectives_scatter(
            df=df, 
            metadata=metadata, 
            x_col=x_col, 
            y_col=y_col, 
            z_col=z_col,
            color_col=color_col, 
            size_col=size_col
        )
        
        return fig
        
    except Exception as e:
        # Return error figure
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"Error creating enhanced scatter plot: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        error_fig.update_layout(
            title="Enhanced Scatter Plot - Error",
            height=600
        )
        
        return error_fig


# ============================================
# POPULATE DROPDOWN WITH AVAILABLE COLUMNS
# ============================================

@callback(
    Output("iteration-y-dropdown", "options"),
    Output("iteration-y-dropdown", "value"),
    [Input("url", "pathname")],
    [State("current-excel-file", "data"),
     State("selected-file-store", "data")]
)
def populate_iteration_dropdown(pathname, current_excel_data, selected_file_data):
    """Populate the Y-axis dropdown with available columns"""
    # Only trigger on navigation to /Opt-run page
    if pathname != "/Opt-run":
        return dash.no_update, dash.no_update
    
    # Determine which Excel file to load
    excel_filename = None
    sheet_name = None
    
    if current_excel_data:
        excel_filename = current_excel_data
        sheet_name = "Experiments"
    elif selected_file_data:
        excel_filename = selected_file_data.get('excel_file')
        sheet_name = selected_file_data.get('selected_sheet', 'Experiments')
    
    if not excel_filename:
        return [], None
    
    try:
        # Ensure filename has extension
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        
        file_path = os.path.join(EXCEL_FOLDER, excel_filename)
        
        if not os.path.exists(file_path):
            return [], None
        
        # Load Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name or 0, engine="openpyxl")
        
        # Load domain metadata to get objective columns
        metadata = {}
        if DomainStorage.domain_exists(excel_filename):
            success, domain, domain_metadata = DomainStorage.load_domain(excel_filename)
            if success:
                metadata = {
                    "parameter_names": domain_metadata.get("parameter_names", []),
                    "objective_names": domain_metadata.get("objective_names", []),
                    "extra_column_names": domain_metadata.get("extra_column_names", [])
                }
        
        # Get all numeric columns, prioritizing objectives
        numeric_columns = []
        
        # Add objectives first (highest priority)
        objective_names = metadata.get("objective_names", [])
        for col in objective_names:
            if col in df.columns:
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    numeric_columns.append({"label": f"🎯 {col} (Objective)", "value": col})
                except:
                    pass
        
        # Add parameters that are numeric
        parameter_names = metadata.get("parameter_names", [])
        for col in parameter_names:
            if col in df.columns and col not in [opt["value"] for opt in numeric_columns]:
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    numeric_columns.append({"label": f"⚙️ {col} (Parameter)", "value": col})
                except:
                    pass
        
        # Add other numeric columns
        for col in df.columns:
            if col not in [opt["value"] for opt in numeric_columns] and col != "Point type":
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    numeric_columns.append({"label": f"📊 {col}", "value": col})
                except:
                    pass
        
        # Set default value to first objective if available
        default_value = None
        if objective_names and any(obj in df.columns for obj in objective_names):
            default_value = next(obj for obj in objective_names if obj in df.columns)
        elif numeric_columns:
            default_value = numeric_columns[0]["value"]
        
        return numeric_columns, default_value
        
    except Exception as e:
        print(f"Error populating iteration dropdown: {e}")
        return [], None


# ============================================
# UPDATE ITERATION PLOT CALLBACK
# ============================================

@callback(
    Output("iteration-plot", "figure"),
    [Input("iteration-y-dropdown", "value"),
     Input("url", "pathname")],
    [State("current-excel-file", "data"),
     State("selected-file-store", "data")]
)
def update_iteration_plot(y_column, pathname, current_excel_data, selected_file_data):
    """Update iteration plot when Y-axis selection changes"""
    # Only trigger on navigation to /Opt-run page or when dropdown changes
    if pathname != "/Opt-run" and not y_column:
        return dash.no_update
    
    # Determine which Excel file to load
    excel_filename = None
    sheet_name = None
    
    if current_excel_data:
        excel_filename = current_excel_data
        sheet_name = "Experiments"
    elif selected_file_data:
        excel_filename = selected_file_data.get('excel_file')
        sheet_name = selected_file_data.get('selected_sheet', 'Experiments')
    
    if not excel_filename:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="⚠️ No Excel file selected",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        empty_fig.update_layout(height=500, title="Iteration Plot")
        return empty_fig
    
    try:
        # Ensure filename has extension
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        
        file_path = os.path.join(EXCEL_FOLDER, excel_filename)
        
        if not os.path.exists(file_path):
            error_fig = go.Figure()
            error_fig.add_annotation(
                text="❌ File not found",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="red")
            )
            error_fig.update_layout(height=500, title="Iteration Plot - File Not Found")
            return error_fig
        
        # Load Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name or 0, engine="openpyxl")
        
        # Load domain metadata
        metadata = {}
        if DomainStorage.domain_exists(excel_filename):
            success, domain, domain_metadata = DomainStorage.load_domain(excel_filename)
            if success:
                metadata = {
                    "parameter_names": domain_metadata.get("parameter_names", []),
                    "objective_names": domain_metadata.get("objective_names", []),
                    "parameters": domain_metadata.get("parameters", [])
                }
        
        # Create the plot
        fig = create_iteration_plot(df, metadata, y_column)
        
        return fig
        
    except Exception as e:
        # Return error figure
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"Error creating iteration plot: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        error_fig.update_layout(
            title="Iteration Plot - Error",
            height=500
        )
        
        return error_fig
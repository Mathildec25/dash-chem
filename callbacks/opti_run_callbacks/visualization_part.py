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
from components.Figures_BO import create_parallel_coordinates, create_objectives_scatter
    

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
    

 ### Scatter plot callback ###
@callback(
    Output("objectives-scatter", "figure"),
    [Input("url", "pathname")],
    [State("current-excel-file", "data"),
     State("selected-file-store", "data")]
)
def update_objectives_scatter(pathname, current_excel_data, selected_file_data):
    if pathname != "/Opt-run":
        return dash.no_update

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
        empty_fig.add_annotation(text="No Excel selected", x=0.5, y=0.5, xref="paper", yref="paper",
                                 showarrow=False, font=dict(size=18, color="gray"))
        empty_fig.update_layout(height=600)
        return empty_fig

    if not excel_filename.endswith('.xlsx'):
        excel_filename += '.xlsx'
    file_path = os.path.join(EXCEL_FOLDER, excel_filename)
    if not os.path.exists(file_path):
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="File not found", x=0.5, y=0.5, xref="paper", yref="paper",
                                 showarrow=False, font=dict(size=18, color="gray"))
        empty_fig.update_layout(height=600)
        return empty_fig

    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name or 0, engine="openpyxl")
    except Exception:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Error reading file", x=0.5, y=0.5, xref="paper", yref="paper",
                                 showarrow=False, font=dict(size=18, color="gray"))
        empty_fig.update_layout(height=600)
        return empty_fig

    # Load domain metadata if available
    metadata = {}
    if DomainStorage.domain_exists(excel_filename):
        success, _, domain_meta = DomainStorage.load_domain(excel_filename)
        if success:
            metadata = {
                "parameter_names": domain_meta.get("parameter_names", []),
                "objective_names": domain_meta.get("objective_names", []),
                "parameters": domain_meta.get("parameters", [])
            }

    objective_names = metadata.get("objective_names", [])
    if len(objective_names) not in (2, 3):
        fig = go.Figure()
        fig.add_annotation(text="Visualization requires 2 or 3 objectives", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False, font=dict(size=18, color="gray"))
        fig.update_layout(height=600)
        return fig

    # Prepare dataframe: keep rows where all objectives present
    needed_cols = [c for c in objective_names if c in df.columns]
    if not needed_cols:
        fig = go.Figure()
        fig.add_annotation(text="No objective columns found in the Excel file", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False, font=dict(size=18, color="gray"))
        fig.update_layout(height=600)
        return fig

    df_complete = df.loc[:, needed_cols].dropna()
    if df_complete.empty:
        fig = go.Figure()
        fig.add_annotation(text="No complete objective rows available", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False, font=dict(size=18, color="gray"))
        fig.update_layout(height=600)
        return fig

    # choose a sensible color_by: first parameter if exists
    param_names = metadata.get("parameter_names", [])
    color_by = param_names[0] if param_names and param_names[0] in df.columns else None

    # build fig
    fig = create_objectives_scatter(df, metadata, color_by=color_by)

    return fig
"""
Generate Report Callback
Creates a professional Word document report from optimization results
"""

from dash import callback, Input, Output, State, dcc, html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import os
import tempfile
from datetime import datetime

from domain_storage import DomainStorage
from config_path import EXCEL_FOLDER


@callback(
    [Output('download-report', 'data'),
     Output('generate-report-status', 'children'),
     Output('generate-report-status', 'is_open'),
     Output('generate-report-status', 'color')],
    Input('generate-report-btn', 'n_clicks'),
    State('current-excel-file', 'data'),
    prevent_initial_call=True
)
def generate_optimization_report(n_clicks, excel_file):
    """Generate a professional Word report from optimization data"""
    
    if not n_clicks or not excel_file:
        raise PreventUpdate
    
    try:
        print("Starting report generation...")
        
        # Load data
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        if not os.path.exists(file_path):
            return None, f"File not found: {excel_file}", True, "danger"
        
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Load domain
        domain_data = DomainStorage.load_domain(excel_file)
        if not domain_data:
            return None, "Domain configuration not found", True, "danger"
        
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        parameters = domain_data.get('parameters', [])
        objectives = domain_data.get('objectives', [])
        
        # Filter complete experiments
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) == 0:
            return None, "No completed experiments found", True, "warning"
        
        # Determine optimization type
        opt_type = "MOBO" if len(obj_names) >= 2 else "SOBO"
        
        # Count BO experiments
        bo_count = 0
        if 'Point type' in df_complete.columns:
            bo_count = (df_complete['Point type'] == 'BO').sum()
        
        # Find best result
        obj_col = obj_names[0]
        direction = 'min'
        for obj in objectives:
            if obj.get('name') == obj_col:
                direction = obj.get('direction', 'min')
                break
        
        if direction == 'min':
            best_idx = df_complete[obj_col].idxmin()
        else:
            best_idx = df_complete[obj_col].idxmax()
        
        best_result = df_complete.loc[best_idx].to_dict()
        
        # Calculate improvement
        improvement = None
        if len(df_complete) > 1:
            first_value = df_complete[obj_col].iloc[0]
            best_value = df_complete[obj_col].loc[best_idx]
            if direction == 'min':
                improvement = ((first_value - best_value) / abs(first_value)) * 100 if first_value != 0 else 0
            else:
                improvement = ((best_value - first_value) / abs(first_value)) * 100 if first_value != 0 else 0
        
        # Get top experiments
        ascending = (direction == 'min')
        df_sorted = df_complete.sort_values(by=obj_col, ascending=ascending)
        top_experiments = df_sorted.head(10).to_dict('records')
        
        # Generate plots and save as images
        temp_dir = tempfile.mkdtemp()
        image_paths = []
        
        try:
            # Convergence plot
            conv_fig = create_convergence_plot_for_report(df_complete, obj_names, objectives)
            conv_path = os.path.join(temp_dir, 'convergence.png')
            conv_fig.write_image(conv_path, width=800, height=600)
            image_paths.append(conv_path)
            
            # Distribution plot
            dist_fig = create_distribution_plot_for_report(df_complete, obj_names)
            dist_path = os.path.join(temp_dir, 'distribution.png')
            dist_fig.write_image(dist_path, width=800, height=600)
            image_paths.append(dist_path)
            
            print(f"Generated {len(image_paths)} plots")
        except Exception as e:
            print(f"Could not generate plots: {e}")
            image_paths = []
        
        # Prepare data for report
        report_data = {
            'projectName': excel_file.replace('.xlsx', ''),
            'totalExperiments': len(df_complete),
            'boExperiments': bo_count,
            'bestResult': {
                **best_result,
                'objectiveValue': f"{best_result[obj_col]:.4f}" if not pd.isna(best_result[obj_col]) else "N/A"
            },
            'improvement': f"{improvement:.1f}" if improvement is not None else None,
            'topExperiments': top_experiments,
            'parameters': parameters,
            'objectives': objectives,
            'optimizationType': opt_type,
            'imagePaths': image_paths
        }
        
        # Save data to temp JSON
        data_json_path = os.path.join(temp_dir, 'report_data.json')
        with open(data_json_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Generate report using Python script
        report_filename = excel_file.replace('.xlsx', '_Report.docx')
        output_path = os.path.join(temp_dir, report_filename)
        
        # Import the generator from the same directory
        from .generate_report_python import generate_word_report
        
        print("Generating Word document...")
        generate_word_report(report_data, output_path)
        
        if not os.path.exists(output_path):
            return None, "Report file was not created", True, "danger"
        
        print(f"Report generated successfully: {output_path}")
        
        # Return file for download
        return (
            dcc.send_file(output_path),
            "✅ Report generated successfully!",
            True,
            "success"
        )
    
    except Exception as e:
        import traceback
        print(f"Error generating report:\n{traceback.format_exc()}")
        return None, f"Error: {str(e)}", True, "danger"


def create_convergence_plot_for_report(df, obj_names, objectives):
    """Create convergence plot for report"""
    obj_col = obj_names[0]
    obj_values = pd.to_numeric(df[obj_col], errors='coerce').dropna()
    
    direction = 'min'
    for obj in objectives:
        if obj.get('name') == obj_col:
            direction = obj.get('direction', 'min')
            break
    
    if direction == 'min':
        cumulative_best = obj_values.cummin()
    else:
        cumulative_best = obj_values.cummax()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(range(1, len(obj_values) + 1)),
        y=obj_values.values,
        mode='markers',
        name='Experiments',
        marker=dict(size=8, color='#6366f1', opacity=0.6)
    ))
    
    fig.add_trace(go.Scatter(
        x=list(range(1, len(cumulative_best) + 1)),
        y=cumulative_best.values,
        mode='lines',
        name=f'Best {"Min" if direction == "min" else "Max"}',
        line=dict(color='#10b981', width=3)
    ))
    
    fig.update_layout(
        title=f"Optimization Convergence - {obj_col}",
        xaxis_title="Experiment Number",
        yaxis_title=obj_col,
        showlegend=True,
        font=dict(family="Arial", size=12),
        plot_bgcolor='white',
        xaxis=dict(gridcolor='#f0f0f0'),
        yaxis=dict(gridcolor='#f0f0f0')
    )
    
    return fig


def create_distribution_plot_for_report(df, obj_names):
    """Create distribution histogram for report"""
    obj_col = obj_names[0]
    obj_values = pd.to_numeric(df[obj_col], errors='coerce').dropna()
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=obj_values,
        nbinsx=15,
        marker_color='#6366f1',
        opacity=0.7
    ))
    
    fig.update_layout(
        title=f"Distribution of {obj_col}",
        xaxis_title=obj_col,
        yaxis_title="Count",
        font=dict(family="Arial", size=12),
        plot_bgcolor='white',
        xaxis=dict(gridcolor='#f0f0f0'),
        yaxis=dict(gridcolor='#f0f0f0')
    )
    
    return fig
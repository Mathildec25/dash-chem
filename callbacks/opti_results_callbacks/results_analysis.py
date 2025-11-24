"""
Results Analysis Callbacks
Generates visualizations for optimization results
"""

from dash import callback, Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

from domain_storage import DomainStorage
from config_path import EXCEL_FOLDER


# ===== LOAD AND ANALYZE RESULTS =====

@callback(
    [Output('total-experiments', 'children'),
     Output('best-objective-value', 'children'),
     Output('bo-experiments', 'children'),
     Output('improvement-percent', 'children'),
     Output('convergence-plot', 'figure'),
     Output('objective-distribution', 'figure'),
     Output('parallel-coordinates-plot', 'figure'),
     Output('parameter-importance-plot', 'figure'),
     Output('pareto-front-plot', 'figure'),
     Output('results-status-alert', 'children'),
     Output('results-status-alert', 'is_open'),
     Output('results-status-alert', 'color')],
    [Input('current-excel-file', 'data'),
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def load_and_analyze_results(excel_file, pathname):
    """Load data and generate all analysis plots"""
    
    # Only process on results page
    if pathname != '/Opt-results':
        raise PreventUpdate
    
    # Empty figures for errors
    empty_fig = go.Figure()
    empty_fig.add_annotation(text="No data available", xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="gray"))
    empty_fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    if not excel_file:
        return ("0", "-", "0", "-", empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                "No project selected", True, "warning")
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        
        if not os.path.exists(file_path):
            return ("0", "-", "0", "-", empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                    f"File not found: {excel_file}", True, "danger")
        
        # Load data
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Load domain info
        domain_data = DomainStorage.load_domain(excel_file)
        if not domain_data:
            return ("0", "-", "0", "-", empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                    "Domain configuration not found", True, "danger")
        
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        # Filter rows with complete objective data
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete = df_complete[pd.to_numeric(df_complete[obj], errors='coerce').notna()]
        
        if len(df_complete) == 0:
            return (str(len(df)), "-", "0", "-", empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                    "No completed experiments yet", True, "warning")
        
        # ===== SUMMARY STATS =====
        total_experiments = len(df_complete)
        
        # Count BO experiments
        bo_count = 0
        if 'Point type' in df_complete.columns:
            bo_count = (df_complete['Point type'] == 'BO').sum()
        
        # Best objective value (use first objective)
        if obj_names and obj_names[0] in df_complete.columns:
            obj_col = obj_names[0]
            obj_values = pd.to_numeric(df_complete[obj_col], errors='coerce')
            
            # Determine direction
            direction = 'min'
            for obj in objectives:
                if obj.get('name') == obj_col:
                    direction = obj.get('direction', 'min')
                    break
            
            if direction == 'min':
                best_value = obj_values.min()
                best_idx = obj_values.idxmin()
            else:
                best_value = obj_values.max()
                best_idx = obj_values.idxmax()
            
            best_value_str = f"{best_value:.4f}"
            
            # Calculate improvement
            if len(obj_values) > 1:
                first_value = obj_values.iloc[0]
                if direction == 'min':
                    improvement = ((first_value - best_value) / abs(first_value)) * 100 if first_value != 0 else 0
                else:
                    improvement = ((best_value - first_value) / abs(first_value)) * 100 if first_value != 0 else 0
                improvement_str = f"{improvement:.1f}%"
            else:
                improvement_str = "-"
        else:
            best_value_str = "-"
            improvement_str = "-"
        
        # ===== CONVERGENCE PLOT =====
        convergence_fig = create_convergence_plot(df_complete, obj_names, objectives)
        
        # ===== OBJECTIVE DISTRIBUTION =====
        distribution_fig = create_distribution_plot(df_complete, obj_names)
        
        # ===== PARALLEL COORDINATES =====
        parallel_fig = create_parallel_coordinates(df_complete, param_names, obj_names)
        
        # ===== PARAMETER IMPORTANCE =====
        importance_fig = create_parameter_importance(df_complete, param_names, obj_names)
        
        # ===== PARETO FRONT =====
        pareto_fig = create_pareto_front(df_complete, obj_names, objectives)
        
        return (str(total_experiments), best_value_str, str(bo_count), improvement_str,
                convergence_fig, distribution_fig, parallel_fig, importance_fig, pareto_fig,
                f"✅ Analyzed {total_experiments} experiments", True, "success")
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return ("0", "-", "0", "-", empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                f"Error: {str(e)}", True, "danger")


def create_convergence_plot(df, obj_names, objectives):
    """Create convergence plot showing best objective over iterations"""
    
    if not obj_names or obj_names[0] not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No objective data", xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    obj_col = obj_names[0]
    obj_values = pd.to_numeric(df[obj_col], errors='coerce').dropna()
    
    # Determine direction
    direction = 'min'
    for obj in objectives:
        if obj.get('name') == obj_col:
            direction = obj.get('direction', 'min')
            break
    
    # Calculate cumulative best
    if direction == 'min':
        cumulative_best = obj_values.cummin()
    else:
        cumulative_best = obj_values.cummax()
    
    fig = go.Figure()
    
    # Individual points
    fig.add_trace(go.Scatter(
        x=list(range(1, len(obj_values) + 1)),
        y=obj_values.values,
        mode='markers',
        name='Experiments',
        marker=dict(size=8, color='#6366f1', opacity=0.6)
    ))
    
    # Best line
    fig.add_trace(go.Scatter(
        x=list(range(1, len(cumulative_best) + 1)),
        y=cumulative_best.values,
        mode='lines',
        name=f'Best {"Min" if direction == "min" else "Max"}',
        line=dict(color='#10b981', width=3)
    ))
    
    fig.update_layout(
        xaxis_title="Experiment #",
        yaxis_title=obj_col,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=20, t=30, b=50),
        plot_bgcolor='white',
        xaxis=dict(gridcolor='#f0f0f0'),
        yaxis=dict(gridcolor='#f0f0f0')
    )
    
    return fig


def create_distribution_plot(df, obj_names):
    """Create histogram of objective values"""
    
    if not obj_names or obj_names[0] not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No objective data", xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
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
        xaxis_title=obj_col,
        yaxis_title="Count",
        margin=dict(l=50, r=20, t=20, b=50),
        plot_bgcolor='white',
        xaxis=dict(gridcolor='#f0f0f0'),
        yaxis=dict(gridcolor='#f0f0f0')
    )
    
    return fig


def create_parallel_coordinates(df, param_names, obj_names):
    """Create parallel coordinates plot"""
    
    # Get all numeric columns
    cols_to_use = []
    dimensions = []
    
    for col in param_names + obj_names:
        if col in df.columns:
            numeric_vals = pd.to_numeric(df[col], errors='coerce')
            if numeric_vals.notna().sum() > 0:
                cols_to_use.append(col)
                dimensions.append(dict(
                    label=col,
                    values=numeric_vals.fillna(numeric_vals.mean())
                ))
    
    if not dimensions:
        fig = go.Figure()
        fig.add_annotation(text="No numeric data for parallel coordinates", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Color by first objective
    color_col = obj_names[0] if obj_names and obj_names[0] in df.columns else cols_to_use[-1]
    color_values = pd.to_numeric(df[color_col], errors='coerce').fillna(0)
    
    fig = go.Figure(data=go.Parcoords(
        line=dict(
            color=color_values,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title=color_col)
        ),
        dimensions=dimensions
    ))
    
    fig.update_layout(
        margin=dict(l=80, r=80, t=50, b=50)
    )
    
    return fig


def create_parameter_importance(df, param_names, obj_names):
    """Create parameter importance plot based on correlation (without absolute values)"""
    
    if not param_names or not obj_names:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient data", xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    obj_col = obj_names[0]
    if obj_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No objective data", xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    obj_values = pd.to_numeric(df[obj_col], errors='coerce')
    
    # Calculate correlations (without absolute value)
    correlations = []
    for param in param_names:
        if param in df.columns:
            param_values = pd.to_numeric(df[param], errors='coerce')
            valid_mask = param_values.notna() & obj_values.notna()
            if valid_mask.sum() > 2:
                corr = param_values[valid_mask].corr(obj_values[valid_mask])
                correlations.append((param, corr if not np.isnan(corr) else 0))
            else:
                correlations.append((param, 0))
    
    if not correlations:
        fig = go.Figure()
        fig.add_annotation(text="Cannot calculate correlations", xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Sort by absolute value for display order, but show actual correlation
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    params, values = zip(*correlations)
    
    # Colors based on positive/negative correlation
    colors = []
    for v in values:
        if v > 0.3:
            colors.append('#10b981')  # Green for positive
        elif v < -0.3:
            colors.append('#ef4444')  # Red for negative
        else:
            colors.append('#6c757d')  # Gray for weak
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(values),
        y=list(params),
        orientation='h',
        marker_color=colors
    ))
    
    fig.update_layout(
        xaxis_title=f"Correlation with {obj_col}",
        yaxis_title="",
        margin=dict(l=100, r=20, t=20, b=50),
        plot_bgcolor='white',
        xaxis=dict(gridcolor='#f0f0f0', range=[-1, 1], zeroline=True, zerolinecolor='#000000', zerolinewidth=1),
        yaxis=dict(autorange="reversed")
    )
    
    return fig


def create_pareto_front(df, obj_names, objectives):
    """Create Pareto front plot for multi-objective optimization"""
    
    if len(obj_names) < 2:
        fig = go.Figure()
        fig.add_annotation(text="Pareto front requires 2+ objectives", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='white'
        )
        return fig
    
    obj1, obj2 = obj_names[0], obj_names[1]
    
    if obj1 not in df.columns or obj2 not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Missing objective columns", xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    x_vals = pd.to_numeric(df[obj1], errors='coerce')
    y_vals = pd.to_numeric(df[obj2], errors='coerce')
    
    # Find Pareto optimal points
    valid_mask = x_vals.notna() & y_vals.notna()
    x_valid = x_vals[valid_mask].values
    y_valid = y_vals[valid_mask].values
    
    # Determine directions
    dir1 = dir2 = 'min'
    for obj in objectives:
        if obj.get('name') == obj1:
            dir1 = obj.get('direction', 'min')
        if obj.get('name') == obj2:
            dir2 = obj.get('direction', 'min')
    
    # Find Pareto points
    pareto_mask = np.zeros(len(x_valid), dtype=bool)
    for i in range(len(x_valid)):
        is_pareto = True
        for j in range(len(x_valid)):
            if i != j:
                # Check if j dominates i
                if dir1 == 'min':
                    better_x = x_valid[j] <= x_valid[i]
                    strictly_better_x = x_valid[j] < x_valid[i]
                else:
                    better_x = x_valid[j] >= x_valid[i]
                    strictly_better_x = x_valid[j] > x_valid[i]
                
                if dir2 == 'min':
                    better_y = y_valid[j] <= y_valid[i]
                    strictly_better_y = y_valid[j] < y_valid[i]
                else:
                    better_y = y_valid[j] >= y_valid[i]
                    strictly_better_y = y_valid[j] > y_valid[i]
                
                if better_x and better_y and (strictly_better_x or strictly_better_y):
                    is_pareto = False
                    break
        pareto_mask[i] = is_pareto
    
    fig = go.Figure()
    
    # All points
    fig.add_trace(go.Scatter(
        x=x_valid[~pareto_mask],
        y=y_valid[~pareto_mask],
        mode='markers',
        name='Dominated',
        marker=dict(size=8, color='#6c757d', opacity=0.5)
    ))
    
    # Pareto points
    fig.add_trace(go.Scatter(
        x=x_valid[pareto_mask],
        y=y_valid[pareto_mask],
        mode='markers',
        name='Pareto Optimal',
        marker=dict(size=12, color='#10b981', symbol='star')
    ))
    
    fig.update_layout(
        xaxis_title=obj1,
        yaxis_title=obj2,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=20, t=30, b=50),
        plot_bgcolor='white',
        xaxis=dict(gridcolor='#f0f0f0'),
        yaxis=dict(gridcolor='#f0f0f0')
    )
    
    return fig


# ===== BEST EXPERIMENTS TABLE =====

@callback(
    Output('best-experiments-table', 'children'),
    [Input('current-excel-file', 'data'),
     Input('top-n-selector', 'value'),
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_best_experiments_table(excel_file, top_n, pathname):
    """Generate table of best experiments"""
    
    if pathname != '/Opt-results':
        raise PreventUpdate
    
    if not excel_file:
        return html.P("No data available", className="text-muted text-center")
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Load domain info
        domain_data = DomainStorage.load_domain(excel_file)
        if not domain_data:
            return html.P("Domain not found", className="text-muted text-center")
        
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        if not obj_names:
            return html.P("No objectives defined", className="text-muted text-center")
        
        # Filter complete rows
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) == 0:
            return html.P("No completed experiments", className="text-muted text-center")
        
        # Sort by first objective
        obj_col = obj_names[0]
        direction = 'min'
        for obj in objectives:
            if obj.get('name') == obj_col:
                direction = obj.get('direction', 'min')
                break
        
        ascending = (direction == 'min')
        df_sorted = df_complete.sort_values(by=obj_col, ascending=ascending)
        
        # Select top N
        if top_n != 'all':
            df_sorted = df_sorted.head(int(top_n))
        
        # Add rank column
        df_sorted = df_sorted.reset_index(drop=True)
        df_sorted.insert(0, 'Rank', range(1, len(df_sorted) + 1))
        
        # Create table
        table = dash_table.DataTable(
            columns=[{'name': col, 'id': col} for col in df_sorted.columns],
            data=df_sorted.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontSize': '0.875rem'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 0},
                    'backgroundColor': 'rgba(16, 185, 129, 0.2)',
                    'fontWeight': 'bold'
                }
            ],
            page_size=10
        )
        
        return table
    
    except Exception as e:
        return html.P(f"Error: {str(e)}", className="text-danger text-center")
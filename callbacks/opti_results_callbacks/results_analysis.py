"""
Results Analysis Callbacks
Generates adaptive visualizations for SOBO and MOBO optimization results
- Uses GP lengthscales for parameter importance (more accurate)
- Corrected regret calculation using theoretical bounds
- Adaptive visualizations for SOBO vs MOBO
"""

from dash import callback, Input, Output, State, html, no_update, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

from domain_storage import DomainStorage
from config_path import EXCEL_FOLDER


# ===== COLOR PALETTE =====
COLORS = {
    'primary': '#6366f1',
    'secondary': '#8b5cf6', 
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6',
    'gray': '#6b7280',
    'light_gray': '#f3f4f6',
    'pareto': '#ec4899',
    'dominated': '#94a3b8'
}

COLORSCALE_SEQUENTIAL = 'Viridis'
COLORSCALE_DIVERGING = 'RdYlGn'


# ===== HELPER FUNCTIONS =====

def get_empty_figure(message="No data available"):
    """Create an empty figure with a message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message, 
        xref="paper", yref="paper",
        x=0.5, y=0.5, 
        showarrow=False, 
        font=dict(size=14, color="gray")
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=20, b=20)
    )
    return fig


def apply_common_layout(fig, height=None):
    """Apply common styling to figures"""
    layout_updates = {
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'font': dict(family="Inter, -apple-system, sans-serif", size=11),
        'margin': dict(l=50, r=20, t=30, b=50),
        'xaxis': dict(gridcolor='#f0f0f0', zeroline=False),
        'yaxis': dict(gridcolor='#f0f0f0', zeroline=False),
        'legend': dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            bgcolor='rgba(255,255,255,0.8)'
        )
    }
    if height:
        layout_updates['height'] = height
    fig.update_layout(**layout_updates)
    return fig


def compute_pareto_front(df, obj_cols, directions):
    """Compute Pareto-optimal points for multi-objective optimization"""
    points = df[obj_cols].values
    n_points = len(points)
    is_pareto = np.ones(n_points, dtype=bool)
    
    for i in range(n_points):
        for j in range(n_points):
            if i != j:
                dominates = True
                strictly_better = False
                for k, (col, direction) in enumerate(zip(obj_cols, directions)):
                    if direction == 'min':
                        if points[j, k] > points[i, k]:
                            dominates = False
                            break
                        if points[j, k] < points[i, k]:
                            strictly_better = True
                    else:  # max
                        if points[j, k] < points[i, k]:
                            dominates = False
                            break
                        if points[j, k] > points[i, k]:
                            strictly_better = True
                
                if dominates and strictly_better:
                    is_pareto[i] = False
                    break
    
    return is_pareto


def compute_hypervolume_2d(pareto_points, ref_point, directions):
    """Compute 2D hypervolume indicator"""
    if len(pareto_points) == 0:
        return 0.0
    
    # Normalize directions (convert to minimization problem)
    points = pareto_points.copy()
    for i, d in enumerate(directions):
        if d == 'max':
            points[:, i] = -points[:, i]
            ref_point[i] = -ref_point[i]
    
    # Sort by first objective
    sorted_indices = np.argsort(points[:, 0])
    points = points[sorted_indices]
    
    # Compute hypervolume
    hv = 0.0
    prev_y = ref_point[1]
    
    for point in points:
        if point[0] < ref_point[0] and point[1] < prev_y:
            hv += (ref_point[0] - point[0]) * (prev_y - point[1])
            prev_y = point[1]
    
    return abs(hv)


def compute_shap_importance(domain_data, df_complete, obj_names):
    """
    Compute parameter importance using SHAP values.
    Works with all variable types (continuous, discrete, categorical).
    
    Returns:
        dict with:
            - 'importance': {param_name: absolute_importance}
            - 'direction': {param_name: mean_shap_value} (positive = increases objective)
            - 'shap_values': raw shap values array
            - 'X': encoded feature matrix
            - 'feature_names': list of encoded feature names
            - 'param_mapping': {original_param: [encoded_columns]}
    """
    try:
        import shap
        from sklearn.ensemble import RandomForestRegressor
        
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        
        if not param_names or not obj_names:
            return None
        
        obj_col = obj_names[0]
        
        # Prepare data
        df_model = df_complete.copy()
        
        # Encode categorical variables
        X_encoded = pd.DataFrame()
        encoding_map = {}  # Track which columns belong to which parameter
        
        for param in param_names:
            if param not in df_model.columns:
                continue
                
            col_data = df_model[param]
            
            # Check if categorical (non-numeric or object dtype)
            if col_data.dtype == 'object' or not np.issubdtype(col_data.dtype, np.number):
                # One-hot encode
                dummies = pd.get_dummies(col_data, prefix=param)
                X_encoded = pd.concat([X_encoded, dummies], axis=1)
                encoding_map[param] = list(dummies.columns)
            else:
                # Numeric - use as-is
                X_encoded[param] = pd.to_numeric(col_data, errors='coerce')
                encoding_map[param] = [param]
        
        # Target variable
        y = df_model[obj_col].values
        
        # Remove NaN
        mask = ~np.isnan(y) & ~X_encoded.isna().any(axis=1)
        X_clean = X_encoded[mask].reset_index(drop=True)
        y_clean = y[mask]
        
        if len(y_clean) < 3:
            print("⚠️ SHAP: Not enough data points")
            return None
        
        print(f"🔍 SHAP: Computing importance for {len(param_names)} parameters...")
        print(f"   Data shape: {X_clean.shape}, encoded features: {X_clean.columns.tolist()}")
        
        # Train a surrogate model (Random Forest works well for SHAP)
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=min(10, max(3, len(y_clean) // 2)),
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_clean.values, y_clean)
        
        # Compute SHAP values
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_clean.values)
        
        # Aggregate SHAP values back to original parameters
        importance = {}  # Absolute importance (raw mean |SHAP|)
        direction = {}   # Mean direction (positive/negative effect)
        mean_shap = {}   # Mean SHAP value (signed, for bar plot)
        
        for param, encoded_cols in encoding_map.items():
            # Find indices of encoded columns
            col_indices = [X_clean.columns.tolist().index(c) for c in encoded_cols]
            
            # For importance: mean of absolute SHAP values (RAW, no normalization)
            param_shap_abs = np.abs(shap_values[:, col_indices]).sum(axis=1).mean()
            importance[param] = float(param_shap_abs)
            
            # For direction and mean_shap: mean SHAP value (signed)
            if len(col_indices) == 1:
                # Single column (numeric parameter)
                param_shap_mean = shap_values[:, col_indices[0]].mean()
                direction[param] = float(param_shap_mean)
                mean_shap[param] = float(param_shap_mean)
            else:
                # Multiple columns (categorical one-hot)
                # Sum SHAP values across all categories for each sample, then mean
                param_shap_sum = shap_values[:, col_indices].sum(axis=1).mean()
                direction[param] = float(param_shap_sum)
                mean_shap[param] = float(param_shap_sum)
        
        print(f"   ✅ SHAP importance (raw mean |SHAP|): {importance}")
        print(f"   ✅ SHAP mean (signed): {mean_shap}")
        
        return {
            'importance': importance,  # Raw absolute values
            'direction': direction,
            'mean_shap': mean_shap,    # Signed mean values for bar plot
            'shap_values': shap_values,
            'X': X_clean,
            'feature_names': X_clean.columns.tolist(),
            'param_mapping': encoding_map,
            'y': y_clean,
            'model': model
        }
        
    except ImportError:
        print("⚠️ SHAP not installed. Install with: pip install shap")
        return None
    except Exception as e:
        print(f"⚠️ SHAP computation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# ===== MAIN CALLBACK: LOAD AND ANALYZE =====

@callback(
    [Output('total-experiments', 'children'),
     Output('best-objective-value', 'children'),
     Output('bo-experiments', 'children'),
     Output('improvement-percent', 'children'),
     Output('optimization-type-store', 'data'),
     Output('optimization-type-badge', 'children'),
     Output('convergence-objective-selector', 'options'),
     Output('convergence-objective-selector', 'value'),
     Output('convergence-objective-selector', 'style'),
     Output('param-x-selector', 'options'),
     Output('param-y-selector', 'options'),
     Output('param-x-selector', 'value'),
     Output('param-y-selector', 'value'),
     Output('slice-param-selector', 'options'),
     Output('slice-param-selector', 'value'),
     Output('shap-main-param-selector', 'options'),
     Output('shap-main-param-selector', 'value'),
     Output('shap-color-param-selector', 'options'),
     Output('sobo-section', 'style'),
     Output('mobo-section', 'style'),
     Output('convergence-title', 'children'),
     Output('secondary-metric-title', 'children'),
     Output('results-status-alert', 'children'),
     Output('results-status-alert', 'is_open'),
     Output('results-status-alert', 'color')],
    [Input('current-excel-file', 'data'),
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def initialize_results_page(excel_file, pathname):
    """Initialize the results page with data and determine SOBO vs MOBO"""
    
    if pathname != '/Opt-results':
        raise PreventUpdate
    
    # Default returns
    default_style = {"width": "150px", "display": "none"}
    hidden = {"display": "none"}
    
    if not excel_file:
        return ("0", "-", "0", "-", "SOBO", 
                dbc.Badge("No Data", color="secondary", className="px-3 py-2"),
                [], None, default_style, [], [], None, None, [], None, [], None, [],
                hidden, hidden, "Optimization Convergence", "Progress",
                "No project selected", True, "warning")
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        
        if not os.path.exists(file_path):
            return ("0", "-", "0", "-", "SOBO",
                    dbc.Badge("File Not Found", color="danger", className="px-3 py-2"),
                    [], None, default_style, [], [], None, None, [], None, [], None, [],
                    hidden, hidden, "Optimization Convergence", "Progress",
                    f"File not found: {excel_file}", True, "danger")
        
        # Load data
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Load domain info
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return ("0", "-", "0", "-", "SOBO",
                    dbc.Badge("No Domain", color="warning", className="px-3 py-2"),
                    [], None, default_style, [], [], None, None, [], None, [], None, [],
                    hidden, hidden, "Optimization Convergence", "Progress",
                    "Domain configuration not found", True, "warning")
        
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        # Determine optimization type
        is_mobo = len(obj_names) >= 2
        opt_type = "MOBO" if is_mobo else "SOBO"
        
        # Filter complete experiments
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        total_experiments = len(df_complete)
        
        # Count BO experiments
        bo_count = 0
        if 'Point type' in df_complete.columns:
            bo_count = (df_complete['Point type'] == 'BO').sum()
        
        # Calculate best value and improvement
        if obj_names and obj_names[0] in df_complete.columns:
            obj_col = obj_names[0]
            direction = 'min'
            for obj in objectives:
                if obj.get('name') == obj_col:
                    direction = obj.get('direction', 'min')
                    break
            
            if direction == 'min':
                best_value = df_complete[obj_col].min()
                first_value = df_complete[obj_col].iloc[0] if len(df_complete) > 0 else best_value
                improvement = ((first_value - best_value) / abs(first_value)) * 100 if first_value != 0 else 0
            else:
                best_value = df_complete[obj_col].max()
                first_value = df_complete[obj_col].iloc[0] if len(df_complete) > 0 else best_value
                improvement = ((best_value - first_value) / abs(first_value)) * 100 if first_value != 0 else 0
            
            best_value_str = f"{best_value:.4g}"
            improvement_str = f"{improvement:.1f}%"
        else:
            best_value_str = "-"
            improvement_str = "-"
        
        # Create selector options
        obj_options = [{"label": name, "value": name} for name in obj_names]
        param_options = [{"label": name, "value": name} for name in param_names]
        
        # SHAP color options (with "Auto" option)
        shap_color_options = [{"label": "Auto (best interaction)", "value": "auto"}] + param_options
        
        # Styles and titles based on optimization type
        if is_mobo:
            badge = dbc.Badge("Multi-Objective (MOBO)", color="info", className="px-3 py-2")
            sobo_style = {"display": "none"}
            mobo_style = {"display": "block"}
            conv_title = "Multi-Objective Convergence"
            secondary_title = "Objectives Overview"
            obj_selector_style = {"width": "150px", "display": "block"}
        else:
            badge = dbc.Badge("Single-Objective (SOBO)", color="success", className="px-3 py-2")
            sobo_style = {"display": "block"}
            mobo_style = {"display": "none"}
            conv_title = "Optimization Convergence"
            secondary_title = "Cumulative Best"
            obj_selector_style = {"width": "150px", "display": "none"}
        
        return (
            str(total_experiments),
            best_value_str,
            str(bo_count),
            improvement_str,
            opt_type,
            badge,
            obj_options,
            obj_names[0] if obj_names else None,
            obj_selector_style,
            param_options,
            param_options,
            param_names[0] if param_names else None,
            param_names[1] if len(param_names) > 1 else (param_names[0] if param_names else None),
            param_options,
            param_names[0] if param_names else None,
            param_options,  # SHAP main param options
            param_names[0] if param_names else None,  # SHAP main param default
            shap_color_options,  # SHAP color options
            sobo_style,
            mobo_style,
            conv_title,
            secondary_title,
            f"✅ Loaded {total_experiments} experiments ({opt_type})",
            True,
            "success"
        )
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return ("0", "-", "0", "-", "SOBO",
                dbc.Badge("Error", color="danger", className="px-3 py-2"),
                [], None, default_style, [], [], None, None, [], None, [], None, [],
                hidden, hidden, "Optimization Convergence", "Progress",
                f"Error: {str(e)}", True, "danger")


# ===== CONVERGENCE PLOT =====

@callback(
    Output('convergence-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('convergence-objective-selector', 'value'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_convergence_plot(excel_file, selected_obj, opt_type, pathname):
    """Create convergence plot - adaptive for SOBO/MOBO"""
    
    if pathname != '/Opt-results' or not excel_file:
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure("No domain configuration")
        
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        # Filter complete data
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) == 0:
            return get_empty_figure("No completed experiments")
        
        # Add iteration number
        df_complete = df_complete.reset_index(drop=True)
        df_complete['Iteration'] = range(1, len(df_complete) + 1)
        
        fig = go.Figure()
        
        if opt_type == "MOBO":
            # Multi-objective: show all objectives
            colors = [COLORS['primary'], COLORS['success'], COLORS['warning'], COLORS['info']]
            
            for i, obj_col in enumerate(obj_names[:4]):  # Max 4 objectives
                if obj_col not in df_complete.columns:
                    continue
                    
                obj_values = df_complete[obj_col].values
                
                # Get direction
                direction = 'min'
                for obj in objectives:
                    if obj.get('name') == obj_col:
                        direction = obj.get('direction', 'min')
                        break
                
                # Cumulative best
                if direction == 'min':
                    cumulative_best = pd.Series(obj_values).cummin()
                else:
                    cumulative_best = pd.Series(obj_values).cummax()
                
                # Individual points
                fig.add_trace(go.Scatter(
                    x=df_complete['Iteration'],
                    y=obj_values,
                    mode='markers',
                    name=f'{obj_col} (all)',
                    marker=dict(size=6, color=colors[i % len(colors)], opacity=0.4),
                    showlegend=False
                ))
                
                # Best line
                fig.add_trace(go.Scatter(
                    x=df_complete['Iteration'],
                    y=cumulative_best,
                    mode='lines+markers',
                    name=f'{obj_col} (best)',
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=5)
                ))
            
            fig.update_layout(
                xaxis_title="Experiment #",
                yaxis_title="Objective Value",
                showlegend=True
            )
            
        else:
            # Single-objective: detailed convergence
            obj_col = selected_obj or obj_names[0]
            
            if obj_col not in df_complete.columns:
                return get_empty_figure(f"Objective {obj_col} not found")
            
            obj_values = df_complete[obj_col].values
            
            # Get direction
            direction = 'min'
            for obj in objectives:
                if obj.get('name') == obj_col:
                    direction = obj.get('direction', 'min')
                    break
            
            # Cumulative best
            if direction == 'min':
                cumulative_best = pd.Series(obj_values).cummin()
            else:
                cumulative_best = pd.Series(obj_values).cummax()
            
            # Color by point type if available
            if 'Point type' in df_complete.columns:
                colors_points = [COLORS['primary'] if pt == 'BO' else COLORS['gray'] 
                                for pt in df_complete['Point type']]
            else:
                colors_points = [COLORS['primary']] * len(obj_values)
            
            # Individual experiments with point type coloring
            fig.add_trace(go.Scatter(
                x=df_complete['Iteration'],
                y=obj_values,
                mode='markers',
                name='Experiments',
                marker=dict(
                    size=10, 
                    color=colors_points,
                    opacity=0.7,
                    line=dict(width=1, color='white')
                ),
                hovertemplate="Exp %{x}<br>Value: %{y:.4g}<extra></extra>"
            ))
            
            # Best line with area fill
            fig.add_trace(go.Scatter(
                x=df_complete['Iteration'],
                y=cumulative_best,
                mode='lines',
                name=f'Best {"Min" if direction == "min" else "Max"}',
                line=dict(color=COLORS['success'], width=3),
                fill='tozeroy' if direction == 'min' else None,
                fillcolor='rgba(16, 185, 129, 0.1)'
            ))
            
            # Mark the best point
            best_idx = cumulative_best.idxmin() if direction == 'min' else cumulative_best.idxmax()
            best_val = cumulative_best.iloc[best_idx]
            
            fig.add_trace(go.Scatter(
                x=[best_idx + 1],
                y=[best_val],
                mode='markers',
                name='Best Found',
                marker=dict(size=15, color=COLORS['success'], symbol='star', 
                           line=dict(width=2, color='white')),
                hovertemplate=f"Best: {best_val:.4g}<extra></extra>"
            ))
            
            fig.update_layout(
                xaxis_title="Experiment #",
                yaxis_title=obj_col,
                showlegend=True
            )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        print(f"Error in convergence plot: {e}")
        return get_empty_figure(f"Error: {str(e)}")


# ===== SECONDARY METRIC PLOT (Cumulative Best / Overview) =====

@callback(
    Output('secondary-metric-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_secondary_metric_plot(excel_file, opt_type, pathname):
    """Secondary metric - cumulative improvement for SOBO, overview for MOBO"""
    
    if pathname != '/Opt-results' or not excel_file:
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) == 0:
            return get_empty_figure()
        
        fig = go.Figure()
        
        if opt_type == "SOBO" and obj_names:
            # Show improvement percentage over iterations
            obj_col = obj_names[0]
            direction = 'min'
            for obj in objectives:
                if obj.get('name') == obj_col:
                    direction = obj.get('direction', 'min')
                    break
            
            obj_values = df_complete[obj_col].values
            initial_value = obj_values[0]
            
            if direction == 'min':
                cumulative_best = pd.Series(obj_values).cummin()
                improvement_pct = (initial_value - cumulative_best) / abs(initial_value) * 100
            else:
                cumulative_best = pd.Series(obj_values).cummax()
                improvement_pct = (cumulative_best - initial_value) / abs(initial_value) * 100
            
            fig.add_trace(go.Scatter(
                x=list(range(1, len(improvement_pct) + 1)),
                y=improvement_pct,
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color=COLORS['success'], width=2),
                marker=dict(size=4),
                fillcolor='rgba(16, 185, 129, 0.2)'
            ))
            
            fig.update_layout(
                xaxis_title="Exp #",
                yaxis_title="Improvement %",
                showlegend=False,
                margin=dict(l=40, r=10, t=10, b=30)
            )
        else:
            # MOBO: Show a simple bar of current best per objective
            best_values = []
            for obj_col in obj_names:
                if obj_col in df_complete.columns:
                    direction = 'min'
                    for obj in objectives:
                        if obj.get('name') == obj_col:
                            direction = obj.get('direction', 'min')
                            break
                    
                    if direction == 'min':
                        best_values.append(df_complete[obj_col].min())
                    else:
                        best_values.append(df_complete[obj_col].max())
            
            fig.add_trace(go.Bar(
                x=obj_names[:len(best_values)],
                y=best_values,
                marker_color=[COLORS['primary'], COLORS['success']][:len(best_values)]
            ))
            
            fig.update_layout(
                showlegend=False,
                margin=dict(l=40, r=10, t=10, b=30)
            )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        return get_empty_figure()


# ===== OBJECTIVE DISTRIBUTION =====

@callback(
    Output('objective-distribution', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('convergence-objective-selector', 'value'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_distribution_plot(excel_file, selected_obj, opt_type, pathname):
    """Distribution histogram with KDE"""
    
    if pathname != '/Opt-results' or not excel_file:
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        obj_col = selected_obj or (obj_names[0] if obj_names else None)
        
        if not obj_col or obj_col not in df.columns:
            return get_empty_figure()
        
        obj_values = pd.to_numeric(df[obj_col], errors='coerce').dropna()
        
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=obj_values,
            nbinsx=min(20, max(5, len(obj_values) // 3)),
            marker_color=COLORS['primary'],
            opacity=0.7,
            name='Distribution'
        ))
        
        fig.update_layout(
            xaxis_title=obj_col,
            yaxis_title="Count",
            showlegend=False,
            margin=dict(l=40, r=10, t=10, b=30)
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        return get_empty_figure()


# ===== REGRET PLOT (SOBO) - CORRECTED WITH THEORETICAL BOUNDS =====

@callback(
    Output('regret-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_regret_plot(excel_file, opt_type, pathname):
    """
    Regret plot showing instantaneous and cumulative regret.
    CORRECTED: Uses theoretical bounds from objective configuration.
    """
    
    if pathname != '/Opt-results' or not excel_file or opt_type != "SOBO":
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        if not obj_names:
            return get_empty_figure()
        
        obj_col = obj_names[0]
        
        # Get direction and theoretical bounds
        direction = 'min'
        theoretical_best = None
        
        for obj in objectives:
            if obj.get('name') == obj_col:
                direction = obj.get('direction', 'min')
                # Get theoretical optimum from bounds
                if direction == 'min':
                    theoretical_best = obj.get('lower_bound')
                else:
                    theoretical_best = obj.get('upper_bound')
                break
        
        df_complete = df.copy()
        df_complete[obj_col] = pd.to_numeric(df_complete[obj_col], errors='coerce')
        df_complete = df_complete[df_complete[obj_col].notna()]
        
        if len(df_complete) == 0:
            return get_empty_figure()
        
        obj_values = df_complete[obj_col].values
        
        # If no theoretical bound defined, fall back to best found (with warning)
        if theoretical_best is None:
            print(f"⚠️ No theoretical bound defined for {obj_col}, using best found as reference")
            if direction == 'min':
                theoretical_best = obj_values.min()
            else:
                theoretical_best = obj_values.max()
            title_suffix = " (vs best found)"
        else:
            title_suffix = f" (vs theoretical: {theoretical_best})"
        
        # Calculate regret
        if direction == 'min':
            instantaneous_regret = obj_values - theoretical_best
        else:
            instantaneous_regret = theoretical_best - obj_values
        
        # Ensure regret is non-negative (can happen if we exceed theoretical best)
        instantaneous_regret = np.maximum(instantaneous_regret, 0)
        
        cumulative_regret = np.cumsum(instantaneous_regret)
        
        fig = make_subplots(
            rows=1, cols=2, 
            subplot_titles=(f"Instantaneous Regret{title_suffix}", "Cumulative Regret")
        )
        
        # Instantaneous regret
        fig.add_trace(go.Scatter(
            x=list(range(1, len(instantaneous_regret) + 1)),
            y=instantaneous_regret,
            mode='lines+markers',
            name='Instantaneous',
            line=dict(color=COLORS['warning']),
            marker=dict(size=5)
        ), row=1, col=1)
        
        # Add reference line at 0
        fig.add_hline(y=0, line_dash="dash", line_color=COLORS['success'], row=1, col=1)
        
        # Cumulative regret
        fig.add_trace(go.Scatter(
            x=list(range(1, len(cumulative_regret) + 1)),
            y=cumulative_regret,
            mode='lines',
            name='Cumulative',
            line=dict(color=COLORS['danger'], width=2),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.1)'
        ), row=1, col=2)
        
        fig.update_xaxes(title_text="Experiment #", row=1, col=1)
        fig.update_xaxes(title_text="Experiment #", row=1, col=2)
        fig.update_yaxes(title_text="Regret", row=1, col=1)
        fig.update_yaxes(title_text="Cumulative Regret", row=1, col=2)
        
        fig.update_layout(showlegend=False)
        
        return apply_common_layout(fig)
        
    except Exception as e:
        print(f"Error in regret plot: {e}")
        return get_empty_figure()


# ===== IMPROVEMENT RATE PLOT (SOBO) =====

@callback(
    Output('improvement-rate-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_improvement_rate_plot(excel_file, opt_type, pathname):
    """Rolling improvement rate over iterations"""
    
    if pathname != '/Opt-results' or not excel_file or opt_type != "SOBO":
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        if not obj_names:
            return get_empty_figure()
        
        obj_col = obj_names[0]
        direction = 'min'
        for obj in objectives:
            if obj.get('name') == obj_col:
                direction = obj.get('direction', 'min')
                break
        
        df_complete = df.copy()
        df_complete[obj_col] = pd.to_numeric(df_complete[obj_col], errors='coerce')
        df_complete = df_complete[df_complete[obj_col].notna()]
        
        if len(df_complete) < 3:
            return get_empty_figure("Need at least 3 experiments")
        
        obj_values = df_complete[obj_col].values
        
        # Calculate rolling best improvement
        if direction == 'min':
            cumulative_best = pd.Series(obj_values).cummin()
        else:
            cumulative_best = pd.Series(obj_values).cummax()
        
        # Improvement per iteration (change in best)
        improvements = cumulative_best.diff().fillna(0)
        
        # Rolling average of improvements
        window = min(5, len(improvements) // 2)
        if window < 1:
            window = 1
        rolling_improvement = improvements.rolling(window=window, min_periods=1).mean()
        
        fig = go.Figure()
        
        # Bar chart for individual improvements
        colors = [COLORS['success'] if imp < 0 else COLORS['gray'] for imp in improvements] if direction == 'min' \
                 else [COLORS['success'] if imp > 0 else COLORS['gray'] for imp in improvements]
        
        fig.add_trace(go.Bar(
            x=list(range(1, len(improvements) + 1)),
            y=improvements.abs(),
            name='Per-iteration improvement',
            marker_color=colors,
            opacity=0.6
        ))
        
        # Rolling average line
        fig.add_trace(go.Scatter(
            x=list(range(1, len(rolling_improvement) + 1)),
            y=rolling_improvement.abs(),
            mode='lines',
            name=f'Rolling avg (window={window})',
            line=dict(color=COLORS['primary'], width=3)
        ))
        
        fig.update_layout(
            xaxis_title="Experiment #",
            yaxis_title="Improvement Magnitude",
            showlegend=True,
            barmode='overlay'
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        return get_empty_figure()


# ===== PARETO FRONT PLOT (MOBO) =====

@callback(
    Output('pareto-front-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('optimization-type-store', 'data'),
     Input('pareto-2d-btn', 'n_clicks'),
     Input('pareto-3d-btn', 'n_clicks'),
     Input('url', 'pathname')]
)
def update_pareto_plot(excel_file, opt_type, btn_2d, btn_3d, pathname):
    """Pareto front visualization with evolution"""
    
    if pathname != '/Opt-results' or not excel_file or opt_type != "MOBO":
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        if len(obj_names) < 2:
            return get_empty_figure("Need at least 2 objectives for Pareto front")
        
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) == 0:
            return get_empty_figure()
        
        # Get directions
        directions = []
        for obj_col in obj_names[:2]:
            direction = 'min'
            for obj in objectives:
                if obj.get('name') == obj_col:
                    direction = obj.get('direction', 'min')
                    break
            directions.append(direction)
        
        # Compute Pareto front
        is_pareto = compute_pareto_front(df_complete, obj_names[:2], directions)
        df_complete['is_pareto'] = is_pareto
        df_complete['iteration'] = range(1, len(df_complete) + 1)
        
        fig = go.Figure()
        
        # Dominated points
        dominated = df_complete[~df_complete['is_pareto']]
        if len(dominated) > 0:
            fig.add_trace(go.Scatter(
                x=dominated[obj_names[0]],
                y=dominated[obj_names[1]],
                mode='markers',
                name='Dominated',
                marker=dict(
                    size=8,
                    color=dominated['iteration'],
                    colorscale='Blues',
                    opacity=0.5,
                    showscale=False
                ),
                hovertemplate=f"{obj_names[0]}: %{{x:.3g}}<br>{obj_names[1]}: %{{y:.3g}}<br>Exp: %{{customdata}}<extra></extra>",
                customdata=dominated['iteration']
            ))
        
        # Pareto-optimal points
        pareto = df_complete[df_complete['is_pareto']].sort_values(by=obj_names[0])
        if len(pareto) > 0:
            fig.add_trace(go.Scatter(
                x=pareto[obj_names[0]],
                y=pareto[obj_names[1]],
                mode='markers+lines',
                name='Pareto Front',
                marker=dict(
                    size=12,
                    color=COLORS['pareto'],
                    symbol='star',
                    line=dict(width=1, color='white')
                ),
                line=dict(color=COLORS['pareto'], width=2, dash='dot'),
                hovertemplate=f"{obj_names[0]}: %{{x:.3g}}<br>{obj_names[1]}: %{{y:.3g}}<br>Exp: %{{customdata}}<extra></extra>",
                customdata=pareto['iteration']
            ))
        
        # Add direction arrows
        x_range = df_complete[obj_names[0]].max() - df_complete[obj_names[0]].min()
        y_range = df_complete[obj_names[1]].max() - df_complete[obj_names[1]].min()
        
        arrow_text = f"{'←' if directions[0] == 'min' else '→'} {obj_names[0]} ({directions[0]})\n"
        arrow_text += f"{'↓' if directions[1] == 'min' else '↑'} {obj_names[1]} ({directions[1]})"
        
        fig.add_annotation(
            x=0.02, y=0.98,
            xref="paper", yref="paper",
            text=arrow_text,
            showarrow=False,
            font=dict(size=10, color=COLORS['gray']),
            align="left",
            bgcolor="rgba(255,255,255,0.8)"
        )
        
        fig.update_layout(
            xaxis_title=obj_names[0],
            yaxis_title=obj_names[1],
            showlegend=True
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        print(f"Error in Pareto plot: {e}")
        return get_empty_figure()


# ===== HYPERVOLUME PLOT (MOBO) =====

@callback(
    Output('hypervolume-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_hypervolume_plot(excel_file, opt_type, pathname):
    """Hypervolume indicator evolution over iterations"""
    
    if pathname != '/Opt-results' or not excel_file or opt_type != "MOBO":
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        if len(obj_names) < 2:
            return get_empty_figure()
        
        df_complete = df.copy()
        for obj in obj_names[:2]:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) < 2:
            return get_empty_figure("Need at least 2 experiments")
        
        # Get directions
        directions = []
        for obj_col in obj_names[:2]:
            direction = 'min'
            for obj in objectives:
                if obj.get('name') == obj_col:
                    direction = obj.get('direction', 'min')
                    break
            directions.append(direction)
        
        # Reference point (worst values + margin)
        ref_point = []
        for i, obj_col in enumerate(obj_names[:2]):
            if directions[i] == 'min':
                ref_point.append(df_complete[obj_col].max() * 1.1)
            else:
                ref_point.append(df_complete[obj_col].min() * 0.9)
        
        # Calculate hypervolume at each iteration
        hypervolumes = []
        for i in range(1, len(df_complete) + 1):
            df_subset = df_complete.iloc[:i]
            is_pareto = compute_pareto_front(df_subset, obj_names[:2], directions)
            pareto_points = df_subset[is_pareto][obj_names[:2]].values
            
            if len(pareto_points) > 0:
                hv = compute_hypervolume_2d(pareto_points, ref_point.copy(), directions)
            else:
                hv = 0
            hypervolumes.append(hv)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=list(range(1, len(hypervolumes) + 1)),
            y=hypervolumes,
            mode='lines+markers',
            name='Hypervolume',
            line=dict(color=COLORS['info'], width=3),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))
        
        fig.update_layout(
            xaxis_title="Experiment #",
            yaxis_title="Hypervolume",
            showlegend=False
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        print(f"Error in hypervolume plot: {e}")
        return get_empty_figure()


# ===== PARAMETER EXPLORATION PLOT =====

@callback(
    Output('parameter-exploration-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('param-x-selector', 'value'),
     Input('param-y-selector', 'value'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_parameter_exploration(excel_file, param_x, param_y, opt_type, pathname):
    """Parameter space exploration visualization"""
    
    if pathname != '/Opt-results' or not excel_file:
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        if not param_x or not param_y:
            return get_empty_figure("Select parameters")
        
        if param_x not in df.columns or param_y not in df.columns:
            return get_empty_figure("Parameters not found")
        
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) == 0:
            return get_empty_figure()
        
        df_complete['iteration'] = range(1, len(df_complete) + 1)
        
        # Color by objective value
        obj_col = obj_names[0] if obj_names else None
        
        fig = go.Figure()
        
        if obj_col and obj_col in df_complete.columns:
            # Get direction for colorscale
            direction = 'min'
            for obj in objectives:
                if obj.get('name') == obj_col:
                    direction = obj.get('direction', 'min')
                    break
            
            colorscale = 'RdYlGn' if direction == 'min' else 'RdYlGn_r'
            
            fig.add_trace(go.Scatter(
                x=df_complete[param_x],
                y=df_complete[param_y],
                mode='markers',
                marker=dict(
                    size=12,
                    color=df_complete[obj_col],
                    colorscale=colorscale,
                    showscale=True,
                    colorbar=dict(title=obj_col, thickness=15),
                    line=dict(width=1, color='white')
                ),
                text=df_complete['iteration'],
                hovertemplate=f"{param_x}: %{{x:.3g}}<br>{param_y}: %{{y:.3g}}<br>{obj_col}: %{{marker.color:.3g}}<br>Exp: %{{text}}<extra></extra>"
            ))
            
            # Connect points by iteration order
            fig.add_trace(go.Scatter(
                x=df_complete[param_x],
                y=df_complete[param_y],
                mode='lines',
                line=dict(color='rgba(0,0,0,0.2)', width=1),
                showlegend=False,
                hoverinfo='skip'
            ))
        else:
            fig.add_trace(go.Scatter(
                x=df_complete[param_x],
                y=df_complete[param_y],
                mode='markers',
                marker=dict(
                    size=10,
                    color=df_complete['iteration'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title='Iteration')
                )
            ))
        
        fig.update_layout(
            xaxis_title=param_x,
            yaxis_title=param_y,
            showlegend=False
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        return get_empty_figure()


# ===== PARAMETER IMPORTANCE PLOT - USING SHAP (Signed Mean) =====

@callback(
    Output('parameter-importance-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_parameter_importance(excel_file, opt_type, pathname):
    """
    Parameter importance using signed mean SHAP values.
    Shows the average effect direction and magnitude.
    - Positive (right): increasing parameter increases objective on average
    - Negative (left): increasing parameter decreases objective on average
    """
    
    if pathname != '/Opt-results' or not excel_file:
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        
        if not param_names or not obj_names:
            return get_empty_figure()
        
        # Filter complete experiments
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) < 3:
            return get_empty_figure("Need at least 3 experiments")
        
        # Compute SHAP importance
        shap_result = compute_shap_importance(domain_data, df_complete, obj_names)
        
        if not shap_result:
            return get_empty_figure("Could not compute SHAP importance")
        
        importance = shap_result['importance']  # Absolute for sorting
        mean_shap = shap_result.get('mean_shap', shap_result['direction'])  # Signed values
        
        # Sort by absolute importance (descending)
        sorted_params = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        param_labels = [p[0] for p in sorted_params]
        
        # Get signed mean values
        signed_values = [mean_shap.get(param, 0) for param in param_labels]
        
        # Colors based on sign
        colors = [COLORS['success'] if v >= 0 else COLORS['danger'] for v in signed_values]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=signed_values,
            y=param_labels,
            orientation='h',
            marker_color=colors,
            text=[f"{v:+.3g}" for v in signed_values],
            textposition='outside'
        ))
        
        # Add vertical line at 0
        fig.add_vline(x=0, line_dash="solid", line_color=COLORS['gray'], line_width=1)
        
        # Determine x-axis range based on data
        max_abs = max(abs(v) for v in signed_values) if signed_values else 1
        x_range = [-max_abs * 1.3, max_abs * 1.3]
        
        # Get objective name for label
        obj_name = obj_names[0] if obj_names else "objective"
        
        fig.update_layout(
            xaxis_title=f"Mean SHAP value (impact on {obj_name})",
            yaxis_title="",
            xaxis=dict(range=x_range, zeroline=True),
            showlegend=False,
            title=dict(
                text="<b>Mean SHAP Value</b>",
                font=dict(size=12),
                x=0.5
            )
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        print(f"Error in parameter importance: {e}")
        import traceback
        traceback.print_exc()
        return get_empty_figure()


# ===== SHAP BEESWARM PLOT =====

@callback(
    Output('shap-beeswarm-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_shap_beeswarm(excel_file, opt_type, pathname):
    """
    SHAP Beeswarm/Summary plot.
    Each dot represents one experiment.
    X-axis: SHAP value (impact on prediction)
    Color: Feature value (red = high, blue = low)
    """
    
    if pathname != '/Opt-results' or not excel_file:
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        
        if not param_names or not obj_names:
            return get_empty_figure()
        
        # Filter complete experiments
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) < 3:
            return get_empty_figure("Need at least 3 experiments")
        
        # Compute SHAP values
        shap_result = compute_shap_importance(domain_data, df_complete, obj_names)
        
        if not shap_result:
            return get_empty_figure("Could not compute SHAP values")
        
        shap_values = shap_result['shap_values']
        X = shap_result['X']
        feature_names = shap_result['feature_names']
        param_mapping = shap_result['param_mapping']
        importance = shap_result['importance']
        
        # Sort parameters by importance
        sorted_params = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        fig = go.Figure()
        
        # For each parameter (in order of importance)
        y_position = 0
        y_labels = []
        
        for param, _ in sorted_params:
            if param not in param_mapping:
                continue
            
            encoded_cols = param_mapping[param]
            col_indices = [feature_names.index(c) for c in encoded_cols if c in feature_names]
            
            if not col_indices:
                continue
            
            # Get SHAP values for this parameter
            if len(col_indices) == 1:
                param_shap = shap_values[:, col_indices[0]]
                # Get original feature values for coloring
                if param in df_complete.columns:
                    feature_vals = df_complete[param].values[:len(param_shap)]
                    # Normalize for coloring (handle categorical)
                    if df_complete[param].dtype == 'object':
                        # Categorical: use category codes
                        feature_vals_norm = pd.Categorical(feature_vals).codes
                        feature_vals_norm = (feature_vals_norm - feature_vals_norm.min()) / (feature_vals_norm.max() - feature_vals_norm.min() + 1e-10)
                    else:
                        feature_vals_numeric = pd.to_numeric(feature_vals, errors='coerce')
                        feature_vals_norm = (feature_vals_numeric - np.nanmin(feature_vals_numeric)) / (np.nanmax(feature_vals_numeric) - np.nanmin(feature_vals_numeric) + 1e-10)
                else:
                    feature_vals = X.iloc[:, col_indices[0]].values
                    feature_vals_norm = (feature_vals - feature_vals.min()) / (feature_vals.max() - feature_vals.min() + 1e-10)
            else:
                # Categorical with multiple columns - sum SHAP values
                param_shap = shap_values[:, col_indices].sum(axis=1)
                # For coloring, use original categorical values
                if param in df_complete.columns:
                    feature_vals = df_complete[param].values[:len(param_shap)]
                    feature_vals_norm = pd.Categorical(feature_vals).codes
                    feature_vals_norm = (feature_vals_norm - feature_vals_norm.min()) / (feature_vals_norm.max() - feature_vals_norm.min() + 1e-10)
                else:
                    feature_vals_norm = np.zeros(len(param_shap))
            
            # Add jitter to y position for beeswarm effect
            jitter = np.random.uniform(-0.3, 0.3, len(param_shap))
            y_vals = y_position + jitter
            
            # Create hover text
            if param in df_complete.columns:
                feature_vals_display = df_complete[param].values[:len(param_shap)]
                hover_text = [f"{param}: {fv}<br>SHAP: {sv:.3f}" for fv, sv in zip(feature_vals_display, param_shap)]
            else:
                hover_text = [f"SHAP: {sv:.3f}" for sv in param_shap]
            
            fig.add_trace(go.Scatter(
                x=param_shap,
                y=y_vals,
                mode='markers',
                marker=dict(
                    size=8,
                    color=feature_vals_norm,
                    colorscale='RdBu_r',  # Red = high, Blue = low
                    showscale=(y_position == 0),  # Only show colorbar once
                    colorbar=dict(
                        title="Feature<br>value",
                        titleside="right",
                        thickness=15,
                        tickvals=[0, 1],
                        ticktext=["Low", "High"]
                    ) if y_position == 0 else None,
                    opacity=0.7,
                    line=dict(width=0.5, color='white')
                ),
                text=hover_text,
                hovertemplate="%{text}<extra></extra>",
                showlegend=False
            ))
            
            y_labels.append(param)
            y_position += 1
        
        # Add vertical line at 0
        fig.add_vline(x=0, line_dash="solid", line_color=COLORS['gray'], line_width=1)
        
        # Get objective name for label
        obj_name = obj_names[0] if obj_names else "objective"
        
        fig.update_layout(
            xaxis_title=f"SHAP value (impact on {obj_name})",
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(y_labels))),
                ticktext=y_labels,
                title=""
            ),
            showlegend=False,
            title=dict(
                text="<b>SHAP Summary Plot</b><br><sup>Each dot = one experiment | Color = feature value (red=high, blue=low)</sup>",
                font=dict(size=12),
                x=0.5
            )
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        print(f"Error in SHAP beeswarm: {e}")
        import traceback
        traceback.print_exc()
        return get_empty_figure()


# ===== SHAP DEPENDENCE PLOT =====

@callback(
    Output('shap-dependence-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('shap-main-param-selector', 'value'),
     Input('shap-color-param-selector', 'value'),
     Input('url', 'pathname')]
)
def update_shap_dependence_plot(excel_file, main_param, color_param, pathname):
    """
    SHAP Dependence Plot: Shows how a parameter affects the prediction.
    X-axis: Parameter value
    Y-axis: SHAP value (contribution to prediction)
    Color: Another parameter to show interactions
    """
    
    if pathname != '/Opt-results' or not excel_file or not main_param:
        return get_empty_figure("Select a parameter")
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        
        if not param_names or not obj_names:
            return get_empty_figure()
        
        # Filter complete experiments
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) < 3:
            return get_empty_figure("Need at least 3 experiments")
        
        # Compute SHAP values
        shap_result = compute_shap_importance(domain_data, df_complete, obj_names)
        
        if not shap_result:
            return get_empty_figure("Could not compute SHAP values")
        
        shap_values = shap_result['shap_values']
        X = shap_result['X']
        feature_names = shap_result['feature_names']
        param_mapping = shap_result['param_mapping']
        
        # Find the column index for main parameter
        if main_param not in param_mapping:
            return get_empty_figure(f"Parameter {main_param} not found")
        
        main_cols = param_mapping[main_param]
        
        # Get original parameter values for x-axis
        if main_param in df_complete.columns:
            x_values = df_complete[main_param].values[:len(shap_values)]
        else:
            return get_empty_figure(f"Parameter {main_param} not in data")
        
        # Get SHAP values for this parameter
        main_indices = [feature_names.index(c) for c in main_cols if c in feature_names]
        
        if len(main_indices) == 1:
            # Single column (numeric parameter)
            y_shap = shap_values[:, main_indices[0]]
        else:
            # Multiple columns (categorical) - sum SHAP values
            y_shap = shap_values[:, main_indices].sum(axis=1)
        
        # Determine color values
        if color_param and color_param != "auto" and color_param in df_complete.columns:
            color_values = df_complete[color_param].values[:len(shap_values)]
            color_label = color_param
            
            # Check if categorical
            if df_complete[color_param].dtype == 'object':
                # Use category codes for coloring
                color_categorical = pd.Categorical(color_values)
                color_numeric = color_categorical.codes
                color_text = color_values
            else:
                color_numeric = pd.to_numeric(color_values, errors='coerce')
                color_text = [f"{v:.3g}" for v in color_numeric]
        elif color_param == "auto" and len(param_names) > 1:
            # Auto-select: find parameter with strongest interaction
            # Use the parameter with highest correlation to SHAP variance
            best_interaction_param = None
            best_corr = 0
            
            for p in param_names:
                if p == main_param:
                    continue
                if p in df_complete.columns:
                    p_values = pd.to_numeric(df_complete[p], errors='coerce').values[:len(shap_values)]
                    if not np.isnan(p_values).all():
                        # Correlation between parameter and SHAP value variance
                        valid_mask = ~np.isnan(p_values)
                        if valid_mask.sum() > 2:
                            corr = abs(np.corrcoef(p_values[valid_mask], y_shap[valid_mask])[0, 1])
                            if not np.isnan(corr) and corr > best_corr:
                                best_corr = corr
                                best_interaction_param = p
            
            if best_interaction_param:
                color_values = df_complete[best_interaction_param].values[:len(shap_values)]
                color_label = f"{best_interaction_param} (auto)"
                
                if df_complete[best_interaction_param].dtype == 'object':
                    color_categorical = pd.Categorical(color_values)
                    color_numeric = color_categorical.codes
                    color_text = color_values
                else:
                    color_numeric = pd.to_numeric(color_values, errors='coerce')
                    color_text = [f"{v:.3g}" for v in color_numeric]
            else:
                color_numeric = None
                color_text = None
                color_label = None
        else:
            color_numeric = None
            color_text = None
            color_label = None
        
        fig = go.Figure()
        
        # Check if main parameter is categorical
        is_categorical = df_complete[main_param].dtype == 'object'
        
        if is_categorical:
            # For categorical: use strip/jitter plot
            categories = df_complete[main_param].unique()
            x_numeric = pd.Categorical(x_values, categories=categories).codes
            
            # Add jitter
            jitter = np.random.uniform(-0.2, 0.2, len(x_numeric))
            x_jittered = x_numeric + jitter
            
            if color_numeric is not None:
                fig.add_trace(go.Scatter(
                    x=x_jittered,
                    y=y_shap,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=color_numeric,
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title=color_label, thickness=15),
                        line=dict(width=1, color='white')
                    ),
                    text=[f"{main_param}: {x}<br>SHAP: {y:.3f}<br>{color_label}: {c}" 
                          for x, y, c in zip(x_values, y_shap, color_text)],
                    hovertemplate="%{text}<extra></extra>"
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=x_jittered,
                    y=y_shap,
                    mode='markers',
                    marker=dict(size=10, color=COLORS['primary'], opacity=0.7),
                    text=[f"{main_param}: {x}<br>SHAP: {y:.3f}" for x, y in zip(x_values, y_shap)],
                    hovertemplate="%{text}<extra></extra>"
                ))
            
            # Update x-axis for categories
            fig.update_xaxes(
                tickmode='array',
                tickvals=list(range(len(categories))),
                ticktext=categories
            )
        else:
            # Numeric parameter
            x_numeric = pd.to_numeric(x_values, errors='coerce')
            
            if color_numeric is not None:
                fig.add_trace(go.Scatter(
                    x=x_numeric,
                    y=y_shap,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=color_numeric,
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title=color_label, thickness=15),
                        line=dict(width=1, color='white')
                    ),
                    text=[f"{main_param}: {x:.3g}<br>SHAP: {y:.3f}<br>{color_label}: {c}" 
                          for x, y, c in zip(x_numeric, y_shap, color_text)],
                    hovertemplate="%{text}<extra></extra>"
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=x_numeric,
                    y=y_shap,
                    mode='markers',
                    marker=dict(size=10, color=COLORS['primary'], opacity=0.7),
                    text=[f"{main_param}: {x:.3g}<br>SHAP: {y:.3f}" for x, y in zip(x_numeric, y_shap)],
                    hovertemplate="%{text}<extra></extra>"
                ))
            
            # Add trend line
            if len(x_numeric) >= 3:
                valid_mask = ~np.isnan(x_numeric)
                if valid_mask.sum() >= 3:
                    z = np.polyfit(x_numeric[valid_mask], y_shap[valid_mask], 1)
                    p = np.poly1d(z)
                    x_trend = np.linspace(np.nanmin(x_numeric), np.nanmax(x_numeric), 100)
                    fig.add_trace(go.Scatter(
                        x=x_trend,
                        y=p(x_trend),
                        mode='lines',
                        line=dict(color=COLORS['gray'], width=2, dash='dash'),
                        name='Trend',
                        showlegend=False
                    ))
        
        # Add horizontal line at y=0
        fig.add_hline(y=0, line_dash="solid", line_color=COLORS['gray'], line_width=1, opacity=0.5)
        
        fig.update_layout(
            xaxis_title=main_param,
            yaxis_title=f"SHAP value (impact on {obj_names[0]})",
            showlegend=False,
            title=dict(
                text=f"<b>Effect of {main_param}</b><br><sup>Points above 0 increase the objective</sup>",
                font=dict(size=12),
                x=0.5
            )
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        print(f"Error in SHAP dependence plot: {e}")
        import traceback
        traceback.print_exc()
        return get_empty_figure()


# ===== PARALLEL COORDINATES PLOT =====

@callback(
    Output('parallel-coordinates-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('parallel-color-selector', 'value'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_parallel_coordinates(excel_file, color_by, opt_type, pathname):
    """Interactive parallel coordinates plot"""
    
    if pathname != '/Opt-results' or not excel_file:
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) == 0:
            return get_empty_figure()
        
        df_complete['iteration'] = range(1, len(df_complete) + 1)
        
        # Build dimensions
        dimensions = []
        for col in param_names + obj_names:
            if col in df_complete.columns:
                numeric_vals = pd.to_numeric(df_complete[col], errors='coerce')
                if numeric_vals.notna().sum() > 0:
                    dimensions.append(dict(
                        label=col[:15],  # Truncate long names
                        values=numeric_vals.fillna(numeric_vals.median()),
                        range=[numeric_vals.min(), numeric_vals.max()]
                    ))
        
        if not dimensions:
            return get_empty_figure("No numeric data")
        
        # Determine color
        if color_by == 'iteration':
            color_values = df_complete['iteration']
            colorscale = 'Viridis'
            colorbar_title = 'Iteration'
        elif color_by == 'point_type' and 'Point type' in df_complete.columns:
            color_values = (df_complete['Point type'] == 'BO').astype(int)
            colorscale = [[0, COLORS['gray']], [1, COLORS['primary']]]
            colorbar_title = 'BO'
        else:  # objective
            obj_col = obj_names[0] if obj_names else None
            if obj_col and obj_col in df_complete.columns:
                color_values = df_complete[obj_col]
                colorscale = 'RdYlGn_r'
                colorbar_title = obj_col[:10]
            else:
                color_values = df_complete['iteration']
                colorscale = 'Viridis'
                colorbar_title = 'Iteration'
        
        fig = go.Figure(data=
            go.Parcoords(
                line=dict(
                    color=color_values,
                    colorscale=colorscale,
                    showscale=True,
                    colorbar=dict(title=colorbar_title, thickness=15)
                ),
                dimensions=dimensions
            )
        )
        
        fig.update_layout(
            margin=dict(l=80, r=80, t=30, b=30)
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        return get_empty_figure()


# ===== CORRELATION HEATMAP =====

@callback(
    Output('correlation-heatmap', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('url', 'pathname')]
)
def update_correlation_heatmap(excel_file, pathname):
    """Correlation heatmap between parameters and objectives"""
    
    if pathname != '/Opt-results' or not excel_file:
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        
        # Get numeric columns
        cols_to_use = []
        for col in param_names + obj_names:
            if col in df.columns:
                numeric_vals = pd.to_numeric(df[col], errors='coerce')
                if numeric_vals.notna().sum() > 2:
                    df[col] = numeric_vals
                    cols_to_use.append(col)
        
        if len(cols_to_use) < 2:
            return get_empty_figure("Not enough numeric columns")
        
        # Compute Spearman correlation matrix (more robust)
        corr_matrix = df[cols_to_use].corr(method='spearman')
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=cols_to_use,
            y=cols_to_use,
            colorscale='RdBu_r',
            zmin=-1,
            zmax=1,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            textfont=dict(size=10),
            hovertemplate="%{x} vs %{y}<br>Correlation: %{z:.3f}<extra></extra>"
        ))
        
        fig.update_layout(
            xaxis=dict(tickangle=45),
            yaxis=dict(autorange='reversed'),
            margin=dict(l=80, r=20, t=20, b=80)
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        return get_empty_figure()


# ===== SLICE PLOT (1D EFFECT) =====

@callback(
    Output('slice-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('slice-param-selector', 'value'),
     Input('url', 'pathname')]
)
def update_slice_plot(excel_file, selected_param, pathname):
    """1D slice plot showing parameter effect on objective"""
    
    if pathname != '/Opt-results' or not excel_file or not selected_param:
        return get_empty_figure()
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return get_empty_figure()
        
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        
        if not obj_names:
            return get_empty_figure()
        
        obj_col = obj_names[0]
        
        if selected_param not in df.columns or obj_col not in df.columns:
            return get_empty_figure()
        
        df_plot = df[[selected_param, obj_col]].copy()
        df_plot[selected_param] = pd.to_numeric(df_plot[selected_param], errors='coerce')
        df_plot[obj_col] = pd.to_numeric(df_plot[obj_col], errors='coerce')
        df_plot = df_plot.dropna()
        
        if len(df_plot) < 2:
            return get_empty_figure("Not enough data")
        
        fig = go.Figure()
        
        # Scatter points
        fig.add_trace(go.Scatter(
            x=df_plot[selected_param],
            y=df_plot[obj_col],
            mode='markers',
            marker=dict(size=10, color=COLORS['primary'], opacity=0.7),
            name='Experiments'
        ))
        
        # Add trend line (simple linear regression)
        if len(df_plot) >= 3:
            z = np.polyfit(df_plot[selected_param], df_plot[obj_col], 1)
            p = np.poly1d(z)
            x_trend = np.linspace(df_plot[selected_param].min(), df_plot[selected_param].max(), 100)
            
            fig.add_trace(go.Scatter(
                x=x_trend,
                y=p(x_trend),
                mode='lines',
                line=dict(color=COLORS['danger'], width=2, dash='dash'),
                name='Linear trend'
            ))
        
        # Add LOWESS smoothing if enough data
        if len(df_plot) >= 10:
            try:
                from scipy.signal import savgol_filter
                sorted_df = df_plot.sort_values(by=selected_param)
                window = min(len(sorted_df) // 2, 11)
                if window % 2 == 0:
                    window += 1
                if window >= 3:
                    smoothed = savgol_filter(sorted_df[obj_col].values, window, 2)
                    fig.add_trace(go.Scatter(
                        x=sorted_df[selected_param],
                        y=smoothed,
                        mode='lines',
                        line=dict(color=COLORS['success'], width=2),
                        name='Smoothed (Savitzky-Golay)'
                    ))
            except:
                pass
        
        fig.update_layout(
            xaxis_title=selected_param,
            yaxis_title=obj_col,
            showlegend=True
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        return get_empty_figure()


# ===== BEST EXPERIMENTS TABLE =====

@callback(
    Output('best-experiments-table', 'children'),
    [Input('current-excel-file', 'data'),
     Input('top-n-selector', 'value'),
     Input('url', 'pathname')]
)
def update_best_experiments_table(excel_file, top_n, pathname):
    """Generate table of best experiments"""
    
    if pathname != '/Opt-results' or not excel_file:
        return html.P("No data available", className="text-muted text-center")
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')
        
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return html.P("No domain configuration", className="text-muted text-center")
        
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) == 0:
            return html.P("No completed experiments", className="text-muted text-center")
        
        # Add rank column
        df_complete = df_complete.reset_index(drop=True)
        df_complete.insert(0, '#', range(1, len(df_complete) + 1))
        
        # Sort by first objective
        if obj_names:
            obj_col = obj_names[0]
            direction = 'min'
            for obj in objectives:
                if obj.get('name') == obj_col:
                    direction = obj.get('direction', 'min')
                    break
            
            df_sorted = df_complete.sort_values(by=obj_col, ascending=(direction == 'min'))
        else:
            df_sorted = df_complete
        
        # Limit rows
        if top_n != 'all':
            df_sorted = df_sorted.head(int(top_n))
        
        # Select columns to display
        display_cols = ['#'] + param_names + obj_names
        if 'Point type' in df_sorted.columns:
            display_cols.append('Point type')
        
        display_cols = [c for c in display_cols if c in df_sorted.columns]
        df_display = df_sorted[display_cols].copy()
        
        # Round numeric columns
        for col in df_display.columns:
            if df_display[col].dtype in ['float64', 'float32']:
                df_display[col] = df_display[col].round(4)
        
        # Create DataTable
        table = dash_table.DataTable(
            data=df_display.to_dict('records'),
            columns=[{"name": col, "id": col} for col in df_display.columns],
            style_cell={
                'textAlign': 'center',
                'padding': '10px',
                'fontFamily': 'Inter, -apple-system, sans-serif',
                'fontSize': '13px'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': '600',
                'borderBottom': '2px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 0},
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                    'fontWeight': '600'
                },
                {
                    'if': {'column_id': obj_names},
                    'backgroundColor': 'rgba(99, 102, 241, 0.05)'
                }
            ],
            page_size=10,
            style_table={'overflowX': 'auto'}
        )
        
        return table
        
    except Exception as e:
        return html.P(f"Error: {str(e)}", className="text-danger text-center")


# ===== PARETO BUTTON STYLES =====

@callback(
    [Output('pareto-2d-btn', 'outline'),
     Output('pareto-3d-btn', 'outline')],
    [Input('pareto-2d-btn', 'n_clicks'),
     Input('pareto-3d-btn', 'n_clicks')]
)
def update_pareto_button_styles(btn_2d, btn_3d):
    """Toggle Pareto view button styles"""
    triggered = ctx.triggered_id
    
    if triggered == 'pareto-3d-btn':
        return True, False
    return False, True
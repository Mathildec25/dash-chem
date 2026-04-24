"""Adaptive result-analysis callbacks for SOBO and MOBO optimization runs."""

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


def compute_shap_importance(domain_data, df_complete, obj_name):
    """
    Compute parameter importance using SHAP values for a SPECIFIC objective.
    
    Args:
        domain_data: Domain configuration
        df_complete: DataFrame with complete experiments
        obj_name: Name of the objective to analyze (STRING, not list)
    
    CORRECTION: Utilise mean(abs(SHAP)) au lieu de abs(mean(SHAP))
    """
    try:
        import shap
        from sklearn.ensemble import GradientBoostingRegressor
        
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        parameters = domain_data.get('parameters', [])
        
        if not param_names or not obj_name:
            return None
        
        # Prepare features with proper encoding
        X = pd.DataFrame()
        encoding_map = {}  # Maps original param name -> list of encoded column names
        
        for param in parameters:
            name = param.get('name')
            if name not in df_complete.columns:
                continue
            
            param_type = param.get('type', 'float')
            
            if param_type == 'cat':
                # One-hot encode categorical variables
                dummies = pd.get_dummies(df_complete[name], prefix=name, dtype=float)
                X = pd.concat([X, dummies], axis=1)
                encoding_map[name] = dummies.columns.tolist()
            else:
                # Numeric
                X[name] = pd.to_numeric(df_complete[name], errors='coerce')
                encoding_map[name] = [name]
        
        # Target: specified objective
        y = pd.to_numeric(df_complete[obj_name], errors='coerce')
        
        # Drop rows with NaN
        valid_idx = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_idx]
        y = y[valid_idx]
        
        if len(X) < 3:
            return None
        
        # Train model
        model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X, y)
        
        # Compute SHAP values
        explainer = shap.Explainer(model, X)
        shap_values = explainer(X).values
        
        # Aggregate SHAP values per parameter
        # CORRECTION: mean(abs(SHAP)) au lieu de abs(mean(SHAP))
        importance = {}
        mean_shap = {}
        
        for param, encoded_cols in encoding_map.items():
            col_indices = [X.columns.get_loc(c) for c in encoded_cols if c in X.columns]
            if col_indices:
                param_shap_values = shap_values[:, col_indices]
                if param_shap_values.ndim == 1:
                    param_shap_values = param_shap_values.reshape(-1, 1)
                
                # CORRECTION: mean(abs()) au lieu de abs(mean())
                importance[param] = np.mean(np.abs(param_shap_values.sum(axis=1)))
                mean_shap[param] = np.mean(param_shap_values.sum(axis=1))
        
        return {
            'shap_values': shap_values,
            'X': X,
            'feature_names': X.columns.tolist(),
            'param_mapping': encoding_map,
            'importance': importance,
            'mean_shap': mean_shap
        }
        
    except Exception as e:
        print(f"Error computing SHAP: {e}")
        return None


# ===== INITIALIZATION CALLBACK =====

@callback(
    [Output('results-status-alert', 'children'),
     Output('results-status-alert', 'color'),
     Output('results-status-alert', 'is_open'),
     Output('total-experiments', 'children'),
     Output('bo-experiments', 'children'),
     Output('best-objective-value', 'children'),
     Output('optimization-type-badge', 'children'),
     Output('optimization-type-store', 'data'),
     Output('mobo-section', 'style'),
     Output('sobo-section', 'style'),
     Output('param-x-selector', 'options'),
     Output('param-y-selector', 'options'),
     Output('param-x-selector', 'value'),
     Output('param-y-selector', 'value'),
     Output('convergence-objective-selector', 'options'),
     Output('convergence-objective-selector', 'style'),
     Output('shap-objective-selector', 'options'),  # NOUVEAU
     Output('shap-objective-selector', 'style')],   # NOUVEAU
    [Input('current-excel-file', 'data'),
     Input('url', 'pathname')]
)
def initialize_results_page(excel_file, pathname):
    """Initialize the results page with file data"""
    
    if pathname != '/Opt-results' or not excel_file:
        raise PreventUpdate
    
    default_style = {"display": "none"}
    
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        
        if not os.path.exists(file_path):
            return ("File not found", "danger", True, "0", "0", "N/A", 
                    html.Div(), "SOBO", {"display": "none"}, {"display": "none"}, 
                    [], [], None, None, [], default_style, [], default_style)
        
        df = pd.read_excel(file_path, engine='openpyxl')
        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        
        if not domain_data:
            return ("Domain data not found", "warning", True, "0", "0", "N/A",
                    html.Div(), "SOBO", {"display": "none"}, {"display": "none"},
                    [], [], None, None, [], default_style, [], default_style)
        
        # Get metadata
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        objectives = domain_data.get('objectives', [])
        opt_type = "MOBO" if len(obj_names) > 1 else "SOBO"
        
        # Count experiments
        total_exp = len(df)
        bo_exp = len(df[df['Point type'] == 'BO']) if 'Point type' in df.columns else 0
        
        # Get best objective value
        if obj_names and obj_names[0] in df.columns:
            df_complete = df[df[obj_names[0]].notna()]
            if len(df_complete) > 0:
                direction = 'min'
                for obj in objectives:
                    if obj.get('name') == obj_names[0]:
                        direction = obj.get('direction', 'min')
                        break
                
                if direction == 'min':
                    best_val = df_complete[obj_names[0]].min()
                else:
                    best_val = df_complete[obj_names[0]].max()
                best_val_str = f"{best_val:.4g}"
            else:
                best_val_str = "N/A"
        else:
            best_val_str = "N/A"
        
        # Create badge
        badge_color = "success" if opt_type == "MOBO" else "primary"
        badge = dbc.Badge(opt_type, color=badge_color, className="me-2", style={"fontSize": "1rem"})
        
        # Section visibility
        mobo_style = {"display": "block"} if opt_type == "MOBO" else {"display": "none"}
        sobo_style = {"display": "block"} if opt_type == "SOBO" else {"display": "none"}
        
        # Parameter selectors
        param_options = [{"label": p, "value": p} for p in param_names]
        param_x_default = param_names[0] if len(param_names) > 0 else None
        param_y_default = param_names[1] if len(param_names) > 1 else (param_names[0] if param_names else None)
        
        # Objective selectors
        obj_options = [{"label": obj, "value": obj} for obj in obj_names]
        
        # Convergence objective selector (MOBO only)
        conv_obj_selector_style = {"width": "150px", "display": "inline-block"} if opt_type == "MOBO" else {"display": "none"}
        
        # SHAP objective selector (always visible if multiple objectives)
        shap_obj_selector_style = {"width": "150px", "display": "inline-block"} if len(obj_names) > 1 else {"display": "none"}
        
        return (
            f"Loaded: {excel_file}", "success", True,
            str(total_exp), str(bo_exp), best_val_str,
            badge, opt_type,
            mobo_style, sobo_style,
            param_options, param_options,
            param_x_default, param_y_default,
            obj_options, conv_obj_selector_style,
            obj_options, shap_obj_selector_style  # NOUVEAU
        )
        
    except Exception as e:
        print(f"Error initializing results: {e}")
        return (f"Error: {str(e)}", "danger", True, "0", "0", "N/A",
                html.Div(), "SOBO", {"display": "none"}, {"display": "none"},
                [], [], None, None, [], default_style, [], default_style)


# ===== CONVERGENCE PLOT (CODE ORIGINAL - NON MODIFIÉ) =====

@callback(
    Output('convergence-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('convergence-objective-selector', 'value'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_convergence_plot(excel_file, selected_obj, opt_type, pathname):
    """
    Create convergence plot - adaptive for SOBO/MOBO.
    CODE ORIGINAL (NON MODIFIÉ)
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
        
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        
        if not obj_names:
            return get_empty_figure()
        
        # Select objective column
        if opt_type == "MOBO" and selected_obj:
            obj_col = selected_obj
        else:
            obj_col = obj_names[0]
        
        if obj_col not in df.columns:
            return get_empty_figure(f"Objective '{obj_col}' not found")
        
        # Filter complete experiments
        df_complete = df[df[obj_col].notna()].copy()
        df_complete[obj_col] = pd.to_numeric(df_complete[obj_col], errors='coerce')
        df_complete = df_complete.dropna(subset=[obj_col])
        
        if len(df_complete) == 0:
            return get_empty_figure()
        
        df_complete = df_complete.reset_index(drop=True)
        df_complete['Iteration'] = range(1, len(df_complete) + 1)
        
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
        
        fig = go.Figure()
        
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
        
        title_suffix = f" — {obj_col}" if opt_type == "MOBO" else ""
        fig.update_layout(
            xaxis_title="Experiment #",
            yaxis_title=obj_col,
            showlegend=True,
            title=dict(
                text=f"<b>Convergence{title_suffix}</b><br><sup>{direction}imize | Best: {best_val:.4g}</sup>",
                font=dict(size=12),
                x=0.5
            ) if opt_type == "MOBO" else None
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        print(f"Error in convergence plot: {e}")
        return get_empty_figure(f"Error: {str(e)}")


# ===== REGRET PLOT (SOBO) =====

@callback(
    Output('regret-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('optimization-type-store', 'data'),
     Input('url', 'pathname')]
)
def update_regret_plot(excel_file, opt_type, pathname):
    """Regret analysis for single-objective optimization"""
    
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
        if obj_col not in df.columns:
            return get_empty_figure()
        
        df_complete = df[df[obj_col].notna()].copy()
        df_complete[obj_col] = pd.to_numeric(df_complete[obj_col], errors='coerce')
        df_complete = df_complete[df_complete[obj_col].notna()]
        
        if len(df_complete) < 2:
            return get_empty_figure("Need at least 2 experiments")
        
        # Get direction
        direction = 'min'
        for obj in objectives:
            if obj.get('name') == obj_col:
                direction = obj.get('direction', 'min')
                break
        
        # Compute cumulative best
        if direction == 'min':
            cumulative_best = df_complete[obj_col].cummin().values
        else:
            cumulative_best = df_complete[obj_col].cummax().values
        
        # Compute regret
        best_overall = cumulative_best[-1]
        if direction == 'min':
            instantaneous_regret = df_complete[obj_col].values - best_overall
        else:
            instantaneous_regret = best_overall - df_complete[obj_col].values
        
        cumulative_regret = np.cumsum(instantaneous_regret)
        
        title_suffix = " (lower is better)" if direction == 'min' else " (higher is better)"
        
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


# ===== PARETO FRONT PLOT - MODIFIÉ =====

@callback(
    Output('pareto-front-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('optimization-type-store', 'data'),
     Input('pareto-2d-btn', 'n_clicks'),
     Input('pareto-3d-btn', 'n_clicks'),
     Input('url', 'pathname')]
)
def update_pareto_plot(excel_file, opt_type, btn_2d, btn_3d, pathname):
    """
    Pareto front visualization with evolution
    
    MODIFICATIONS:
    - Tous les points ont le même gradient de couleur selon l'itération (Purples)
    - Les points Pareto sont juste en forme d'étoile
    - Lignes reliant les points dans l'ordre chronologique
    """
    
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
        
        # Ligne reliant TOUS les points dans l'ordre chronologique
        fig.add_trace(go.Scatter(
            x=df_complete[obj_names[0]],
            y=df_complete[obj_names[1]],
            mode='lines',
            name='Evolution path',
            line=dict(color='rgba(150, 150, 150, 0.3)', width=1.5),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # TOUS les points avec le même gradient (Purples)
        dominated = df_complete[~df_complete['is_pareto']]
        if len(dominated) > 0:
            fig.add_trace(go.Scatter(
                x=dominated[obj_names[0]],
                y=dominated[obj_names[1]],
                mode='markers',
                name='Dominated',
                marker=dict(
                    size=10,
                    color=dominated['iteration'],
                    colorscale='Teal',
                    opacity=1,
                    showscale=True,
                    colorbar=dict(
                        title="Exp #",
                        thickness=15,
                        len=0.7
                    ),
                    symbol='circle'
                ),
                hovertemplate=f"{obj_names[0]}: %{{x:.3g}}<br>{obj_names[1]}: %{{y:.3g}}<br>Exp: %{{customdata}}<extra></extra>",
                customdata=dominated['iteration']
            ))
        
        # Points Pareto: même gradient mais en ÉTOILES
        pareto = df_complete[df_complete['is_pareto']]
        if len(pareto) > 0:
            fig.add_trace(go.Scatter(
                x=pareto[obj_names[0]],
                y=pareto[obj_names[1]],
                mode='markers',
                name='Pareto Front',
                marker=dict(
                    size=18,
                    color=pareto['iteration'],
                    colorscale='Teal',
                    symbol='star',
                    line=dict(width=1.5, color='white'),
                    showscale=False
                ),
                hovertemplate=f"{obj_names[0]}: %{{x:.3g}}<br>{obj_names[1]}: %{{y:.3g}}<br>Exp: %{{customdata}}<extra></extra>",
                customdata=pareto['iteration']
            ))
        
        # Add direction arrows
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
            
            colorscale = COLORSCALE_DIVERGING if direction == 'min' else COLORSCALE_DIVERGING
            
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
                    opacity=0.8,
                    line=dict(width=1, color='white')
                ),
                text=[f"Exp {i+1}<br>{param_x}: {x}<br>{param_y}: {y}<br>{obj_col}: {o:.4g}"
                      for i, (x, y, o) in enumerate(zip(
                          df_complete[param_x], df_complete[param_y], df_complete[obj_col]))],
                hovertemplate="%{text}<extra></extra>"
            ))
        else:
            fig.add_trace(go.Scatter(
                x=df_complete[param_x],
                y=df_complete[param_y],
                mode='markers',
                marker=dict(size=10, color=COLORS['primary'], opacity=0.7)
            ))
        
        fig.update_layout(
            xaxis_title=param_x,
            yaxis_title=param_y,
            showlegend=False
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        return get_empty_figure()


# ===== PARAMETER IMPORTANCE - AVEC SÉLECTEUR D'OBJECTIF =====

@callback(
    Output('parameter-importance-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('shap-objective-selector', 'value'),  # NOUVEAU
     Input('url', 'pathname')]
)
def update_parameter_importance(excel_file, selected_obj, pathname):
    """
    Parameter importance using SHAP values - bar plot
    
    MODIFICATIONS:
    1. Utilise mean(abs(SHAP)) au lieu de abs(mean(SHAP))
    2. Barres négatives vers la gauche (valeurs négatives quand rouge)
    3. SÉLECTEUR D'OBJECTIF pour choisir quel objectif analyser
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
        
        # Sélectionner l'objectif
        if selected_obj and selected_obj in obj_names:
            obj_name = selected_obj
        else:
            obj_name = obj_names[0]
        
        # Filter complete experiments
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) < 3:
            return get_empty_figure("Need at least 3 experiments")
        
        # MODIFIÉ: passer obj_name (string) au lieu de obj_names (list)
        shap_result = compute_shap_importance(domain_data, df_complete, obj_name)
        
        if not shap_result:
            return get_empty_figure("Could not compute SHAP values")
        
        importance = shap_result['importance']
        mean_shap = shap_result['mean_shap']
        
        # Sort by importance (mean(abs(SHAP)))
        sorted_params = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        fig = go.Figure()
        
        params = [p[0] for p in sorted_params]
        mean_signed = [mean_shap.get(p, 0) for p in params]
        importance_vals = [importance.get(p, 0) for p in params]
        
        # Barres vers la gauche si négatif
        x_values = [imp if ms > 0 else -imp for imp, ms in zip(importance_vals, mean_signed)]
        colors = [COLORS['success'] if v > 0 else COLORS['danger'] for v in mean_signed]
        
        fig.add_trace(go.Bar(
            y=params,
            x=x_values,
            orientation='h',
            marker_color=colors,
            text=[f"{abs(v):.3f}" for v in x_values],
            textposition='outside',
            hovertemplate="%{y}<br>Mean |SHAP|: %{customdata:.4f}<extra></extra>",
            customdata=importance_vals
        ))
        
        # Ligne verticale à 0
        fig.add_vline(x=0, line_width=2, line_color='black')
        
        fig.update_layout(
            xaxis_title=f"Mean |SHAP| (impact on {obj_name})",
            yaxis=dict(autorange='reversed'),
            showlegend=False,
            title=dict(
                text=f"<b>Parameter Influence on {obj_name}</b><br><sup>Green (right) = increases | Red (left) = decreases</sup>",
                font=dict(size=12),
                x=0.5
            )
        )
        
        return apply_common_layout(fig)
        
    except Exception as e:
        print(f"Error in parameter importance: {e}")
        return get_empty_figure()


# ===== SHAP BEESWARM PLOT - AVEC SÉLECTEUR D'OBJECTIF =====

@callback(
    Output('shap-beeswarm-plot', 'figure'),
    [Input('current-excel-file', 'data'),
     Input('shap-objective-selector', 'value'),  # NOUVEAU
     Input('url', 'pathname')]
)
def update_shap_beeswarm(excel_file, selected_obj, pathname):
    """
    SHAP Beeswarm (Summary) Plot.
    Each dot represents one experiment.
    X-axis: SHAP value (impact on prediction)
    Color: Feature value (red = high, blue = low)
    
    MODIFICATION: Sélecteur d'objectif
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
        
        # Sélectionner l'objectif
        if selected_obj and selected_obj in obj_names:
            obj_name = selected_obj
        else:
            obj_name = obj_names[0]
        
        # Filter complete experiments
        df_complete = df.copy()
        for obj in obj_names:
            if obj in df_complete.columns:
                df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
                df_complete = df_complete[df_complete[obj].notna()]
        
        if len(df_complete) < 3:
            return get_empty_figure("Need at least 3 experiments")
        
        # MODIFIÉ: passer obj_name (string) au lieu de obj_names (list)
        shap_result = compute_shap_importance(domain_data, df_complete, obj_name)
        
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
        
        y_labels = []
        y_position = 0
        
        for param, imp in sorted_params:
            if param not in param_mapping:
                continue
            
            encoded_cols = param_mapping[param]
            col_indices = [feature_names.index(c) for c in encoded_cols if c in feature_names]
            
            if not col_indices:
                continue
            
            # Get SHAP values for this parameter
            if len(col_indices) == 1:
                param_shap = shap_values[:, col_indices[0]]
                feature_vals = X[encoded_cols[0]].values
            else:
                param_shap = shap_values[:, col_indices].sum(axis=1)
                feature_vals = X[encoded_cols].values.argmax(axis=1)
            
            # Normalize feature values for coloring
            fv_min = np.nanmin(feature_vals)
            fv_max = np.nanmax(feature_vals)
            if fv_max > fv_min:
                normalized_fv = (feature_vals - fv_min) / (fv_max - fv_min)
            else:
                normalized_fv = np.ones_like(feature_vals) * 0.5
            
            # Add jitter to y position
            jitter = np.random.normal(0, 0.12, len(param_shap))
            
            # Create hover text
            if param in df_complete.columns:
                orig_vals = df_complete[param].values[:len(param_shap)]
                hover_text = [f"{param}: {ov}<br>SHAP: {sv:.3f}" 
                             for ov, sv in zip(orig_vals, param_shap)]
            else:
                hover_text = [f"SHAP: {sv:.3f}" for sv in param_shap]
            
            fig.add_trace(go.Scatter(
                x=param_shap,
                y=y_position + jitter,
                mode='markers',
                marker=dict(
                    size=12,
                    color=normalized_fv,
                    colorscale=[[0, '#3b82f6'], [1, '#ef4444']],
                    colorbar=dict(
                        title="Feature<br>value",
                        thickness=15,
                        tickvals=[0, 1],
                        ticktext=['Low', 'High'],
                        len=0.5
                    ) if y_position == 0 else None,
                    opacity=1,
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
                text=f"<b>SHAP Summary Plot - {obj_name}</b><br><sup>Each dot = one experiment | Color = feature value (red=high, blue=low)</sup>",
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
        objectives = domain_data.get('objectives', [])
        
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
        
        for param in param_names:
            if param not in df_complete.columns:
                continue
            
            if df_complete[param].dtype == 'object':
                # Categorical: encode as integers
                categories = df_complete[param].unique().tolist()
                cat_codes = [categories.index(v) if v in categories else -1 for v in df_complete[param]]
                dimensions.append(dict(
                    label=param,
                    values=cat_codes,
                    tickvals=list(range(len(categories))),
                    ticktext=categories
                ))
            else:
                numeric_vals = pd.to_numeric(df_complete[param], errors='coerce')
                dimensions.append(dict(
                    label=param,
                    values=numeric_vals.values,
                    range=[numeric_vals.min(), numeric_vals.max()]
                ))
        
        for obj_col in obj_names:
            if obj_col in df_complete.columns:
                dimensions.append(dict(
                    label=obj_col,
                    values=df_complete[obj_col].values,
                    range=[df_complete[obj_col].min(), df_complete[obj_col].max()]
                ))
        
        if not dimensions:
            return get_empty_figure("No valid dimensions")
        
        # Color configuration
        if color_by == "iteration":
            color_values = df_complete['iteration'].values
            colorscale = 'Viridis'
            colorbar_title = 'Experiment #'
        elif color_by == "point_type" and 'Point type' in df_complete.columns:
            pt_codes = [1 if pt == 'BO' else 0 for pt in df_complete['Point type']]
            color_values = pt_codes
            colorscale = [[0, COLORS['gray']], [1, COLORS['primary']]]
            colorbar_title = 'Point Type'
        else:
            # Default: color by first objective
            if obj_names and obj_names[0] in df_complete.columns:
                color_values = df_complete[obj_names[0]].values
                colorscale = COLORSCALE_DIVERGING
                colorbar_title = obj_names[0]
            else:
                color_values = df_complete['iteration'].values
                colorscale = 'Viridis'
                colorbar_title = 'Experiment #'
        
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
        
        # Augmenter marges pour voir les labels
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Inter, -apple-system, sans-serif", size=11),
            margin=dict(l=60, r=20, t=80, b=80)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error in parallel coordinates: {e}")
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
            
            ascending = (direction == 'min')
            df_complete = df_complete.sort_values(by=obj_col, ascending=ascending)
        
        # Limit rows
        if top_n and top_n != 999:
            df_complete = df_complete.head(int(top_n))
        
        # Select columns to display
        display_cols = ['#']
        if 'Point type' in df_complete.columns:
            display_cols.append('Point type')
        display_cols.extend([p for p in param_names if p in df_complete.columns])
        display_cols.extend([o for o in obj_names if o in df_complete.columns])
        
        df_display = df_complete[display_cols]
        
        # Create DataTable
        columns = []
        for col in df_display.columns:
            col_def = {"name": col, "id": col}
            if col in obj_names:
                col_def["type"] = "numeric"
                col_def["format"] = {"specifier": ".4g"}
            columns.append(col_def)
        
        table = dash_table.DataTable(
            data=df_display.to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontSize': '0.85rem',
                'fontFamily': 'Inter, -apple-system, sans-serif'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'borderBottom': '2px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 0},
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'column_id': obj_names},
                    'backgroundColor': 'rgba(99, 102, 241, 0.05)'
                }
            ],
            page_size=20,
            sort_action='native',
            filter_action='native'
        )
        
        return table
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return html.P(f"Error: {str(e)}", className="text-danger text-center")
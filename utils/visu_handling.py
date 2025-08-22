import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ============================================
# HELPER FUNCTIONS FOR VISUALIZATION
# ============================================

def _create_empty_figure(message, height=600, title="Plot"):
    """Create an empty figure with a message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray")
    )
    fig.update_layout(
        height=height,
        title=title,
        plot_bgcolor="rgba(240,240,240,0.95)",
        paper_bgcolor="white"
    )
    return fig

def _add_projection_lines(fig, df_plot, x_col, y_col, z_col, objective_names):
    """Add projection lines for best points in 3D plots"""
    if not objective_names or df_plot is None or df_plot.empty or not z_col:
        return
    
    try:
        obj_cols = [col for col in objective_names if col in df_plot.columns]
        if not obj_cols:
            return
        
        # Normalize objectives and find best points
        obj_data = df_plot[obj_cols].copy()
        for col in obj_cols:
            if pd.api.types.is_numeric_dtype(obj_data[col]):
                col_range = obj_data[col].max() - obj_data[col].min()
                if col_range > 0:
                    obj_data[col] = (obj_data[col] - obj_data[col].min()) / col_range
        
        if len(obj_data.columns) == 0:
            return
        
        df_plot = df_plot.copy()
        df_plot['objective_score'] = obj_data.sum(axis=1)
        top_points = df_plot.nlargest(min(2, len(df_plot)), 'objective_score')
        
        # Add projection lines
        for idx, (_, point) in enumerate(top_points.iterrows()):
            color = '#ff0000' if idx == 0 else '#ff8800'
            
            x_min, x_max = df_plot[x_col].min(), df_plot[x_col].max()
            y_min, y_max = df_plot[y_col].min(), df_plot[y_col].max()
            z_min, z_max = df_plot[z_col].min(), df_plot[z_col].max()
            
            # Projection lines to each plane
            projections = [
                ([point[x_col], point[x_col]], [point[y_col], point[y_col]], [point[z_col], z_min]),
                ([point[x_col], point[x_col]], [point[y_col], y_min], [point[z_col], point[z_col]]),
                ([point[x_col], x_min], [point[y_col], point[y_col]], [point[z_col], point[z_col]])
            ]
            
            for i, (x_vals, y_vals, z_vals) in enumerate(projections):
                fig.add_trace(go.Scatter3d(
                    x=x_vals, y=y_vals, z=z_vals,
                    mode='lines',
                    line=dict(color=color, width=4, dash='dash'),
                    name=f'Best points projections' if i == 0 and idx == 0 else '',
                    showlegend=i == 0 and idx == 0,
                    hoverinfo='skip'
                ))
    except Exception as e:
        print(f"Warning: Could not add projection lines: {e}")
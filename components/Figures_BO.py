import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, dash_table, State
from dash.dash_table.Format import Format
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import numpy as np
from sklearn.manifold import TSNE
import plotly.colors as pc
import os

from config_path import EXCEL_FOLDER

# ============================================
# PARALLEL COORDINATES FUNCTION
# ============================================

def create_parallel_coordinates(data, domain_metadata):
    """
    Create a Parallel coordinates plot with:

    - data: pandas.DataFrame
    - domain_metadata: dict with 'parameter_names' and 'objective_names'
    
    Coloring logic:
        - 1 objective: all lines same color
        - 2+ objectives: last objective used as color scale, others shown as dimensions
    """
    if data is None or data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=20, color="gray")
        )
        fig.update_layout(height=600)
        return fig

    param_names = domain_metadata.get("parameter_names", [])
    objective_names = domain_metadata.get("objective_names", [])
    
    # Decide which column to use for color
    if len(objective_names) >= 2:
        color_column = objective_names[-1]  # last objective for color
        dimensions_objectives = objective_names[:-1]  # all except last
        show_colorbar = True
    elif len(objective_names) == 1:
        color_column = None
        dimensions_objectives = objective_names
        show_colorbar = False
    else:
        color_column = None
        dimensions_objectives = []

    all_columns = param_names + dimensions_objectives
    plot_data = data[[col for col in all_columns if col in data.columns]].dropna()
    if plot_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No complete experiments available",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=20, color="gray")
        )
        fig.update_layout(height=600)
        return fig
    
    # number of iterations (rows) used for the plot
    n_iter = len(plot_data)

    dimensions_list = []

    for col in all_columns:
        if col not in plot_data.columns:
            continue

        # Map categorical/string columns to numeric
        if plot_data[col].dtype == 'object' or plot_data[col].dtype.name == 'category':
            categories = plot_data[col].unique().tolist()
            cat_to_num = {cat: i for i, cat in enumerate(categories)}
            values = plot_data[col].map(cat_to_num)
            tickvals = list(cat_to_num.values())
            ticktext = list(cat_to_num.keys())
            dim = dict(
                label=col,
                values=values,
                tickvals=tickvals,
                ticktext=ticktext,
                range=[min(values), max(values)],
            )
        else:
            dim = dict(
                label=col,
                values=plot_data[col],
                range=[plot_data[col].min(), plot_data[col].max()],
            )

        dimensions_list.append(dim)

    # Configure line coloring
    if color_column and color_column in data.columns:
        color_values = data[color_column]
        line_dict = dict(
            color=color_values,
            colorscale='Bluered',
            showscale=show_colorbar,
            colorbar=dict(
                title=dict(
                    text=color_column,
                    side="right",
                    font=dict(size=16)
                )
            ),
        )
    else:
        line_dict = dict(color='blue')

    fig = go.Figure(data=go.Parcoords(
        line=line_dict,
        dimensions=dimensions_list
    ))

    # Generate dynamic title 
    color_part = f" (Colored by {color_column})" if color_column else ""
    plural = "iteration" if n_iter == 1 else "iterations"
    title = f"Parallel Coordinates Plot with {n_iter} {plural}{color_part}"

    # 1) increase the dimension label font and tick font
    fig.update_traces(
        labelfont=dict(size=15, family="Arial", color="black"),
        tickfont=dict(size=10, family="Arial"),
        rangefont=dict(size=10, family="Arial"),
        selector=dict(type="parcoords")
    )

    # 2) Colorbar font
    fig.update_traces(
        line_colorbar_title_font=dict(size=16, family="Arial", color="black"),
        selector=dict(type="parcoords")
    )

    # 3) layout tweaks (title padding / center)
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5, xanchor="center",
            font=dict(size=30, color="black"),
        ),
        height=600,
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    return fig

def create_enhanced_objectives_scatter(df, metadata, x_col=None, y_col=None, z_col=None, 
                                      color_col=None, size_col=None, marker_size=10):
    """
    Create an enhanced interactive scatter plot for 2D or 3D visualization with full categorical support
    
    Args:
        df: DataFrame containing experimental data
        metadata: Domain metadata containing parameter and objective information
        x_col, y_col, z_col: Column names for axes
        color_col: Column name for coloring points (supports categorical and numeric)
        size_col: Column name for sizing points (supports categorical and numeric)
        marker_size: Default marker size
    
    Returns:
        plotly Figure object with categorical support, enhanced legends, and Bluered colorscale
    """
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            height=600, 
            title="Enhanced Scatter Plot - No Data",
            plot_bgcolor="rgba(240,240,240,0.95)",
            paper_bgcolor="white"
        )
        return fig
    
    # Auto-select columns if not specified
    objective_names = metadata.get("objective_names", [])
    parameter_names = metadata.get("parameter_names", [])
    
    if not x_col and objective_names:
        x_col = objective_names[0] if objective_names[0] in df.columns else None
    if not y_col and len(objective_names) > 1:
        y_col = objective_names[1] if objective_names[1] in df.columns else None
    if not z_col and len(objective_names) > 2:
        z_col = objective_names[2] if objective_names[2] in df.columns else None
    
    # Validate required columns
    if not x_col or x_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Please select a valid X-axis column",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=600, title="Enhanced Scatter Plot - Missing X Column")
        return fig
    
    if not y_col or y_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Please select a valid Y-axis column",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=600, title="Enhanced Scatter Plot - Missing Y Column")
        return fig
    
    # Filter data to only include rows with valid x and y values
    required_cols = [x_col, y_col]
    if z_col and z_col in df.columns:
        required_cols.append(z_col)
    
    # Only drop NaN for required columns (x, y, z)
    df_plot = df.dropna(subset=required_cols).copy()
    
    if df_plot.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No complete data points for selected columns",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=600, title="Enhanced Scatter Plot - No Complete Data")
        return fig
    
    # Convert required columns to numeric if possible
    for col in required_cols:
        try:
            df_plot[col] = pd.to_numeric(df_plot[col], errors='coerce')
        except:
            pass
    
    # Remove rows that couldn't be converted to numeric for required columns
    df_plot = df_plot.dropna(subset=required_cols)
    
    if df_plot.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No numeric data points for selected columns",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=600, title="Enhanced Scatter Plot - No Numeric Data")
        return fig
    
    # Determine if this is 2D or 3D
    is_3d = z_col and z_col in df_plot.columns and df_plot[z_col].notna().any()
    
    # Analyze color and size column types
    color_is_categorical = False
    size_is_categorical = False
    
    if color_col and color_col in df_plot.columns:
        color_is_categorical = (df_plot[color_col].dtype == 'object' or 
                               df_plot[color_col].dtype.name == 'category')
    
    if size_col and size_col in df_plot.columns:
        size_is_categorical = (df_plot[size_col].dtype == 'object' or 
                              df_plot[size_col].dtype.name == 'category')
    
    # Handle categorical size mapping
    if size_is_categorical:
        unique_categories = df_plot[size_col].dropna().unique()
        size_mapping = {cat: (i + 1) * 6 + 12 for i, cat in enumerate(unique_categories)}  # Range 18-42
        df_plot['size_numeric'] = df_plot[size_col].map(size_mapping)
        df_plot['size_numeric'] = df_plot['size_numeric'].fillna(marker_size)  # Default for NaN
    
    # Create global color mapping for categorical variables (to ensure consistency across point types)
    global_color_mapping = {}
    if color_col and color_col in df_plot.columns and color_is_categorical:
        unique_colors = df_plot[color_col].dropna().unique()
        colors_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        global_color_mapping = {cat: colors_palette[i % len(colors_palette)] for i, cat in enumerate(unique_colors)}
    
    # Create the plot
    fig = go.Figure()
    
    # Track if we've shown a colorbar to avoid duplicates
    colorbar_shown = False
    
    # Handle Point type distinction if available, with enhanced categorical support
    if 'Point type' in df_plot.columns:
        point_types = df_plot['Point type'].unique()
        
        color_map = {
            'Init': '#1f77b4',  # Blue for initial sampling
            'BO': '#ff7f0e',    # Orange for Bayesian optimization
            'init': '#1f77b4',  # Handle lowercase
            'bo': '#ff7f0e'     # Handle lowercase
        }
        
        symbol_map = {
            'Init': 'circle',
            'BO': 'diamond',
            'init': 'circle',
            'bo': 'diamond'
        }
        
        for point_type in point_types:
            if pd.isna(point_type):
                continue
                
            subset = df_plot[df_plot['Point type'] == point_type]
            if subset.empty:
                continue
            
            # Handle color mapping (categorical vs numeric)
            if color_col and color_col in subset.columns:
                if color_is_categorical:
                    # For categorical colors, create separate traces for each category using global mapping
                    unique_colors = subset[color_col].dropna().unique()
                    
                    for color_cat in unique_colors:
                        if pd.isna(color_cat):
                            continue
                        color_subset = subset[subset[color_col] == color_cat]
                        if color_subset.empty:
                            continue
                        
                        # Base marker properties for this color category using global mapping
                        marker_props = {
                            'size': marker_size,
                            'symbol': symbol_map.get(point_type, 'circle'),
                            'line': {'width': 2, 'color': 'white'},
                            'opacity': 0.8,
                            'color': global_color_mapping.get(color_cat, '#808080')
                        }
                        
                        # Handle size for this color category
                        if size_col and size_col in color_subset.columns:
                            if size_is_categorical:
                                marker_props['size'] = color_subset['size_numeric']
                            else:
                                try:
                                    size_values = pd.to_numeric(color_subset[size_col], errors='coerce')
                                    if size_values.notna().any():
                                        min_size, max_size = 8, 45
                                        size_range = size_values.max() - size_values.min()
                                        if size_range > 0:
                                            normalized_sizes = ((size_values - size_values.min()) / size_range * 
                                                              (max_size - min_size) + min_size)
                                            marker_props['size'] = normalized_sizes
                                except:
                                    pass
                        
                        # Create comprehensive hover template
                        hover_template = f'<b>{point_type} - {color_cat}</b><br>'
                        hover_template += f'<b>{x_col}:</b> %{{x}}<br>'
                        hover_template += f'<b>{y_col}:</b> %{{y}}<br>'
                        if is_3d:
                            hover_template += f'<b>{z_col}:</b> %{{z}}<br>'
                        hover_template += f'<b>{color_col}:</b> {color_cat}<br>'
                        if size_col and size_col in color_subset.columns:
                            hover_template += f'<b>{size_col}:</b> %{{customdata[0]}}<br>'
                        hover_template += '<extra></extra>'
                        
                        # Prepare customdata for hover
                        customdata = color_subset[[size_col]].values if (size_col and size_col in color_subset.columns) else None
                        
                        if is_3d:
                            fig.add_trace(go.Scatter3d(
                                x=color_subset[x_col],
                                y=color_subset[y_col],
                                z=color_subset[z_col],
                                mode='markers',
                                marker=marker_props,
                                name=f'{point_type} - {color_cat}',
                                hovertemplate=hover_template,
                                customdata=customdata
                            ))
                        else:
                            fig.add_trace(go.Scatter(
                                x=color_subset[x_col],
                                y=color_subset[y_col],
                                mode='markers',
                                marker=marker_props,
                                name=f'{point_type} - {color_cat}',
                                hovertemplate=hover_template,
                                customdata=customdata
                            ))
                
                else:
                    # Numeric color mapping
                    marker_props = {
                        'size': marker_size,
                        'symbol': symbol_map.get(point_type, 'circle'),
                        'line': {'width': 2, 'color': 'white'},
                        'opacity': 0.8
                    }
                    
                    try:
                        color_values = pd.to_numeric(subset[color_col], errors='coerce')
                        if color_values.notna().any():
                            marker_props['color'] = color_values
                            marker_props['colorscale'] = 'Bluered'  # Use Bluered colorscale
                            # Only show colorbar for the first trace to avoid duplicates
                            if not colorbar_shown:
                                marker_props['showscale'] = True
                                marker_props['colorbar'] = {'title': color_col}
                                colorbar_shown = True
                            else:
                                marker_props['showscale'] = False
                        else:
                            marker_props['color'] = color_map.get(point_type, '#2ca02c')
                    except:
                        marker_props['color'] = color_map.get(point_type, '#2ca02c')
                    
                    # Handle size mapping
                    if size_col and size_col in subset.columns:
                        if size_is_categorical:
                            marker_props['size'] = subset['size_numeric']
                        else:
                            try:
                                size_values = pd.to_numeric(subset[size_col], errors='coerce')
                                if size_values.notna().any():
                                    min_size, max_size = 8, 45
                                    size_range = size_values.max() - size_values.min()
                                    if size_range > 0:
                                        normalized_sizes = ((size_values - size_values.min()) / size_range * 
                                                          (max_size - min_size) + min_size)
                                        marker_props['size'] = normalized_sizes
                            except:
                                pass
                    
                    # Create comprehensive hover template
                    hover_template = f'<b>{point_type}</b><br>'
                    hover_template += f'<b>{x_col}:</b> %{{x}}<br>'
                    hover_template += f'<b>{y_col}:</b> %{{y}}<br>'
                    if is_3d:
                        hover_template += f'<b>{z_col}:</b> %{{z}}<br>'
                    if color_col:
                        hover_template += f'<b>{color_col}:</b> %{{customdata[0]}}<br>'
                    if size_col and color_col:
                        hover_template += f'<b>{size_col}:</b> %{{customdata[1]}}<br>'
                    elif size_col:
                        hover_template += f'<b>{size_col}:</b> %{{customdata[0]}}<br>'
                    hover_template += '<extra></extra>'
                    
                    # Prepare customdata for hover
                    customdata_cols = []
                    if color_col and color_col in subset.columns:
                        customdata_cols.append(color_col)
                    if size_col and size_col in subset.columns:
                        customdata_cols.append(size_col)
                    customdata = subset[customdata_cols].values if customdata_cols else None
                    
                    if is_3d:
                        fig.add_trace(go.Scatter3d(
                            x=subset[x_col],
                            y=subset[y_col],
                            z=subset[z_col],
                            mode='markers',
                            marker=marker_props,
                            name=f'{point_type} points',
                            hovertemplate=hover_template,
                            customdata=customdata
                        ))
                    else:
                        fig.add_trace(go.Scatter(
                            x=subset[x_col],
                            y=subset[y_col],
                            mode='markers',
                            marker=marker_props,
                            name=f'{point_type} points',
                            hovertemplate=hover_template,
                            customdata=customdata
                        ))
            
            else:
                # No color mapping - use default point type colors
                marker_props = {
                    'size': marker_size,
                    'symbol': symbol_map.get(point_type, 'circle'),
                    'line': {'width': 2, 'color': 'white'},
                    'opacity': 0.8,
                    'color': color_map.get(point_type, '#2ca02c')
                }
                
                # Handle size mapping
                if size_col and size_col in subset.columns:
                    if size_is_categorical:
                        marker_props['size'] = subset['size_numeric']
                    else:
                        try:
                            size_values = pd.to_numeric(subset[size_col], errors='coerce')
                            if size_values.notna().any():
                                min_size, max_size = 8, 45
                                size_range = size_values.max() - size_values.min()
                                if size_range > 0:
                                    normalized_sizes = ((size_values - size_values.min()) / size_range * 
                                                      (max_size - min_size) + min_size)
                                    marker_props['size'] = normalized_sizes
                        except:
                            pass
                
                # Create hover template
                hover_template = f'<b>{point_type}</b><br>'
                hover_template += f'<b>{x_col}:</b> %{{x}}<br>'
                hover_template += f'<b>{y_col}:</b> %{{y}}<br>'
                if is_3d:
                    hover_template += f'<b>{z_col}:</b> %{{z}}<br>'
                if size_col and size_col in subset.columns:
                    hover_template += f'<b>{size_col}:</b> %{{customdata[0]}}<br>'
                hover_template += '<extra></extra>'
                
                customdata = subset[[size_col]].values if (size_col and size_col in subset.columns) else None
                
                if is_3d:
                    fig.add_trace(go.Scatter3d(
                        x=subset[x_col],
                        y=subset[y_col],
                        z=subset[z_col],
                        mode='markers',
                        marker=marker_props,
                        name=f'{point_type} points',
                        hovertemplate=hover_template,
                        customdata=customdata
                    ))
                else:
                    fig.add_trace(go.Scatter(
                        x=subset[x_col],
                        y=subset[y_col],
                        mode='markers',
                        marker=marker_props,
                        name=f'{point_type} points',
                        hovertemplate=hover_template,
                        customdata=customdata
                    ))
    
    else:
        # No point type distinction - single trace with enhanced categorical support
        if color_col and color_col in df_plot.columns and color_is_categorical:
            # Create separate traces for each color category
            unique_colors = df_plot[color_col].dropna().unique()
            colors_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            for i, color_cat in enumerate(unique_colors):
                if pd.isna(color_cat):
                    continue
                color_subset = df_plot[df_plot[color_col] == color_cat]
                if color_subset.empty:
                    continue
                
                marker_props = {
                    'size': marker_size,
                    'line': {'width': 1, 'color': 'white'},
                    'opacity': 0.8,
                    'color': colors_palette[i % len(colors_palette)]
                }
                
                # Handle size for this color category
                if size_col and size_col in color_subset.columns:
                    if size_is_categorical:
                        marker_props['size'] = color_subset['size_numeric']
                    else:
                        try:
                            size_values = pd.to_numeric(color_subset[size_col], errors='coerce')
                            if size_values.notna().any():
                                min_size, max_size = 8, 45
                                size_range = size_values.max() - size_values.min()
                                if size_range > 0:
                                    normalized_sizes = ((size_values - size_values.min()) / size_range * 
                                                      (max_size - min_size) + min_size)
                                    marker_props['size'] = normalized_sizes
                        except:
                            pass
                
                # Enhanced hover template
                hover_template = f'<b>{color_cat}</b><br>'
                hover_template += f'<b>{x_col}:</b> %{{x}}<br>'
                hover_template += f'<b>{y_col}:</b> %{{y}}<br>'
                if is_3d:
                    hover_template += f'<b>{z_col}:</b> %{{z}}<br>'
                hover_template += f'<b>{color_col}:</b> {color_cat}<br>'
                if size_col and size_col in color_subset.columns:
                    hover_template += f'<b>{size_col}:</b> %{{customdata[0]}}<br>'
                hover_template += '<extra></extra>'
                
                customdata = color_subset[[size_col]].values if (size_col and size_col in color_subset.columns) else None
                
                if is_3d:
                    fig.add_trace(go.Scatter3d(
                        x=color_subset[x_col],
                        y=color_subset[y_col],
                        z=color_subset[z_col],
                        mode='markers',
                        marker=marker_props,
                        name=str(color_cat),
                        hovertemplate=hover_template,
                        customdata=customdata
                    ))
                else:
                    fig.add_trace(go.Scatter(
                        x=color_subset[x_col],
                        y=color_subset[y_col],
                        mode='markers',
                        marker=marker_props,
                        name=str(color_cat),
                        hovertemplate=hover_template,
                        customdata=customdata
                    ))
        
        else:
            # Single trace (no categorical color or no Point type)
            marker_props = {
                'size': marker_size,
                'line': {'width': 1, 'color': 'white'},
                'opacity': 0.8,
                'color': '#1f77b4'
            }
            
            # Handle numeric color mapping
            if color_col and color_col in df_plot.columns and not color_is_categorical:
                try:
                    color_values = pd.to_numeric(df_plot[color_col], errors='coerce')
                    if color_values.notna().any():
                        marker_props['color'] = color_values
                        marker_props['colorscale'] = 'Bluered'  # Use Bluered colorscale
                        # Only show colorbar once to avoid duplicates
                        if not colorbar_shown:
                            marker_props['showscale'] = True
                            marker_props['colorbar'] = {'title': color_col}
                            colorbar_shown = True
                        else:
                            marker_props['showscale'] = False
                except:
                    pass
            
            # Handle size mapping
            if size_col and size_col in df_plot.columns:
                if size_is_categorical:
                    marker_props['size'] = df_plot['size_numeric']
                else:
                    try:
                        size_values = pd.to_numeric(df_plot[size_col], errors='coerce')
                        if size_values.notna().any():
                            min_size, max_size = 8, 45
                            size_range = size_values.max() - size_values.min()
                            if size_range > 0:
                                normalized_sizes = ((size_values - size_values.min()) / size_range * 
                                                  (max_size - min_size) + min_size)
                                marker_props['size'] = normalized_sizes
                    except:
                        pass
            
            # Enhanced hover template
            hover_template = '<b>Experiment</b><br>'
            hover_template += f'<b>{x_col}:</b> %{{x}}<br>'
            hover_template += f'<b>{y_col}:</b> %{{y}}<br>'
            if is_3d:
                hover_template += f'<b>{z_col}:</b> %{{z}}<br>'
            
            customdata_cols = []
            if color_col and color_col in df_plot.columns:
                hover_template += f'<b>{color_col}:</b> %{{customdata[0]}}<br>'
                customdata_cols.append(color_col)
            if size_col and size_col in df_plot.columns:
                idx = len(customdata_cols)
                hover_template += f'<b>{size_col}:</b> %{{customdata[{idx}]}}<br>'
                customdata_cols.append(size_col)
            hover_template += '<extra></extra>'
            
            customdata = df_plot[customdata_cols].values if customdata_cols else None
            
            if is_3d:
                fig.add_trace(go.Scatter3d(
                    x=df_plot[x_col],
                    y=df_plot[y_col],
                    z=df_plot[z_col],
                    mode='markers',
                    marker=marker_props,
                    name='Experiments',
                    hovertemplate=hover_template,
                    customdata=customdata
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=df_plot[x_col],
                    y=df_plot[y_col],
                    mode='markers',
                    marker=marker_props,
                    name='Experiments',
                    hovertemplate=hover_template,
                    customdata=customdata
                ))
    
    # Enhanced 3D features - Add projection lines for best points
    if is_3d and len(df_plot) > 0:
        # Find the 2 best points (simple approach: highest sum of objectives)
        objective_names = metadata.get("objective_names", [])
        if objective_names:
            obj_cols = [col for col in objective_names if col in df_plot.columns]
            if obj_cols:
                # Normalize objectives and sum them
                obj_data = df_plot[obj_cols].copy()
                for col in obj_cols:
                    if pd.api.types.is_numeric_dtype(obj_data[col]):
                        col_range = obj_data[col].max() - obj_data[col].min()
                        if col_range > 0:
                            obj_data[col] = (obj_data[col] - obj_data[col].min()) / col_range
                
                if len(obj_data.columns) > 0:
                    df_plot['objective_score'] = obj_data.sum(axis=1)
                    top_points = df_plot.nlargest(min(2, len(df_plot)), 'objective_score')
                    
                    # Add projection lines for top points
                    for idx, (_, point) in enumerate(top_points.iterrows()):
                        color = '#ff0000' if idx == 0 else '#ff8800'  # Red for best, orange for second
                        
                        # Get axis ranges
                        x_min, x_max = df_plot[x_col].min(), df_plot[x_col].max()
                        y_min, y_max = df_plot[y_col].min(), df_plot[y_col].max()
                        z_min, z_max = df_plot[z_col].min(), df_plot[z_col].max()
                        
                        # Add projection lines to XY plane (bottom)
                        fig.add_trace(go.Scatter3d(
                            x=[point[x_col], point[x_col]],
                            y=[point[y_col], point[y_col]],
                            z=[point[z_col], z_min],
                            mode='lines',
                            line=dict(color=color, width=4, dash='dash'),
                            name=f'Best {idx+1} projection' if idx == 0 else '',
                            showlegend=idx == 0,
                            hoverinfo='skip'
                        ))
                        
                        # Add projection to XZ plane (back)
                        fig.add_trace(go.Scatter3d(
                            x=[point[x_col], point[x_col]],
                            y=[point[y_col], y_min],
                            z=[point[z_col], point[z_col]],
                            mode='lines',
                            line=dict(color=color, width=4, dash='dash'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        
                        # Add projection to YZ plane (left)
                        fig.add_trace(go.Scatter3d(
                            x=[point[x_col], x_min],
                            y=[point[y_col], point[y_col]],
                            z=[point[z_col], point[z_col]],
                            mode='lines',
                            line=dict(color=color, width=4, dash='dash'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
    
    # Build dynamic title with color and size information
    title_parts = [f"{y_col} vs {x_col}"]
    if is_3d:
        title_parts.append(f"vs {z_col}")
    if color_col:
        color_type = "(categorical)" if color_is_categorical else "(continuous)"
        title_parts.append(f"Color={color_col} {color_type}")
    if size_col:
        size_type = "(categorical)" if size_is_categorical else "(continuous)"
        title_parts.append(f"Size={size_col} {size_type}")
    
    title = " | ".join(title_parts)
    
    layout_updates = {
        'title': {
            'text': f'Enhanced Scatter: {title}',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        'hovermode': 'closest',
        'height': 600,
        'showlegend': True,
        'legend': {
            'yanchor': "top",
            'y': 0.99,
            'xanchor': "left",
            'x': 0.01,
            'bgcolor': 'rgba(255,255,255,0.8)',
            'bordercolor': 'rgba(0,0,0,0.2)',
            'borderwidth': 1
        },
        'plot_bgcolor': 'rgba(240,240,240,0.95)',
        'paper_bgcolor': 'white'
    }
    
    if is_3d:
        layout_updates['scene'] = {
            'xaxis': {
                'title': x_col, 
                'backgroundcolor': "rgb(230, 230, 230)", 
                'gridcolor': "white",
                'showspikes': True,
                'spikesides': True,
                'spikecolor': "#999999",
                'spikethickness': 2
            },
            'yaxis': {
                'title': y_col, 
                'backgroundcolor': "rgb(230, 230, 230)", 
                'gridcolor': "white",
                'showspikes': True,
                'spikesides': True,
                'spikecolor': "#999999",
                'spikethickness': 2
            },
            'zaxis': {
                'title': z_col, 
                'backgroundcolor': "rgb(230, 230, 230)", 
                'gridcolor': "white",
                'showspikes': True,
                'spikesides': True,
                'spikecolor': "#999999",
                'spikethickness': 2
            },
            'camera': {
                'eye': {'x': 1.2, 'y': 1.2, 'z': 1.2}
            },
            'aspectmode': 'cube'
        }
    else:
        layout_updates.update({
            'xaxis': {
                'title': x_col,
                'showgrid': True,
                'gridcolor': 'lightgray',
                'zeroline': True,
                'zerolinecolor': 'gray'
            },
            'yaxis': {
                'title': y_col,
                'showgrid': True,
                'gridcolor': 'lightgray',
                'zeroline': True,
                'zerolinecolor': 'gray'
            }
        })
    
    fig.update_layout(**layout_updates)
    
    return fig

def create_iteration_plot(df, metadata, y_column=None):
    """
    Create an iteration vs objective plot showing progression over experiments
    
    Args:
        df: DataFrame containing experimental data
        metadata: Domain metadata containing parameter and objective information
        y_column: Column name to plot on Y-axis
    
    Returns:
        plotly Figure object
    """
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=500, title="Iteration Plot - No Data")
        return fig
    
    # If no y_column specified, try to use first objective
    if not y_column:
        objective_names = metadata.get("objective_names", [])
        if objective_names:
            y_column = objective_names[0]
        else:
            available_cols = [col for col in df.columns if col not in ['Point type']]
            if available_cols:
                y_column = available_cols[0]
            else:
                fig = go.Figure()
                fig.add_annotation(
                    text="No suitable columns found for plotting",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
                fig.update_layout(height=500, title="Iteration Plot - No Suitable Columns")
                return fig
    
    # Check if y_column exists in dataframe
    if y_column not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Column '{y_column}' not found in data",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=500, title=f"Iteration Plot - Column '{y_column}' Not Found")
        return fig
    
    # Create a copy and add iteration number
    df_plot = df.copy()
    df_plot['Iteration'] = range(1, len(df_plot) + 1)
    
    # Filter out rows where y_column is empty/NaN
    df_plot = df_plot[df_plot[y_column].notna() & (df_plot[y_column] != "")]
    
    if df_plot.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No valid data points for '{y_column}'",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=500, title=f"Iteration Plot - No Valid Data for '{y_column}'")
        return fig
    
    # Convert y_column to numeric if possible
    try:
        df_plot[y_column] = pd.to_numeric(df_plot[y_column], errors='coerce')
        df_plot = df_plot.dropna(subset=[y_column])
    except:
        pass
    
    if df_plot.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No numeric data points for '{y_column}'",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=500, title=f"Iteration Plot - No Numeric Data for '{y_column}'")
        return fig
    
    # Create the plot
    fig = go.Figure()
    
    # Check if 'Point type' column exists for distinguishing points
    if 'Point type' in df_plot.columns:
        # Get unique point types
        point_types = df_plot['Point type'].unique()
        
        # Color mapping for point types
        color_map = {
            'Init': '#1f77b4',  # Blue for initial sampling
            'BO': '#ff7f0e',    # Orange for Bayesian optimization
            'init': '#1f77b4',  # Handle lowercase
            'bo': '#ff7f0e'     # Handle lowercase
        }
        
        # Symbol mapping for point types
        symbol_map = {
            'Init': 'circle',
            'BO': 'diamond',
            'init': 'circle',
            'bo': 'diamond'
        }
        
        for point_type in point_types:
            if pd.isna(point_type):
                continue
                
            subset = df_plot[df_plot['Point type'] == point_type]
            if subset.empty:
                continue
            
            color = color_map.get(point_type, '#2ca02c')  # Default green
            symbol = symbol_map.get(point_type, 'circle')
            
            fig.add_trace(go.Scatter(
                x=subset['Iteration'],
                y=subset[y_column],
                mode='markers+lines',
                name=f'{point_type} points',
                marker=dict(
                    color=color,
                    size=10,
                    symbol=symbol,
                    line=dict(width=2, color='white')
                ),
                line=dict(color=color, width=2),
                hovertemplate=f'<b>Iteration:</b> %{{x}}<br><b>{y_column}:</b> %{{y}}<br><b>Type:</b> {point_type}<extra></extra>'
            ))
    else:
        # No point type distinction - single trace
        fig.add_trace(go.Scatter(
            x=df_plot['Iteration'],
            y=df_plot[y_column],
            mode='markers+lines',
            name='All points',
            marker=dict(
                color='#1f77b4',
                size=8,
                line=dict(width=1, color='white')
            ),
            line=dict(color='#1f77b4', width=2),
            hovertemplate=f'<b>Iteration:</b> %{{x}}<br><b>{y_column}:</b> %{{y}}<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title=f'Optimization Progress: {y_column} vs Iteration',
        xaxis_title='Iteration Number',
        yaxis_title=y_column,
        hovermode='closest',
        height=500,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Add grid
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    return fig
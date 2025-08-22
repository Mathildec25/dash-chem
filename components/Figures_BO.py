import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from utils.visu_handling import _create_empty_figure, _add_projection_lines


# ============================================
# MAIN PLOTTING FUNCTIONS
# ============================================

def create_parallel_coordinates(data, domain_metadata):
    """Create a Parallel coordinates plot with automatic coloring"""
    if data is None or data.empty:
        return _create_empty_figure("No data available", 600, "Parallel Coordinates")

    try:
        param_names = domain_metadata.get("parameter_names", []) if domain_metadata else []
        objective_names = domain_metadata.get("objective_names", []) if domain_metadata else []
        
        # Determine coloring strategy
        if len(objective_names) >= 2:
            color_column = objective_names[-1]
            dimensions_objectives = objective_names[:-1]
            show_colorbar = True
        elif len(objective_names) == 1:
            color_column = None
            dimensions_objectives = objective_names
            show_colorbar = False
        else:
            color_column = None
            dimensions_objectives = []

        all_columns = param_names + dimensions_objectives
        
        # Filter columns that actually exist in the data
        existing_columns = [col for col in all_columns if col in data.columns]
        
        if not existing_columns:
            return _create_empty_figure("No valid columns found in data", 600, "Parallel Coordinates")
        
        plot_data = data[existing_columns].copy()
        
        # Remove rows with any NaN values
        plot_data = plot_data.dropna()
        
        if plot_data.empty:
            return _create_empty_figure("No complete experiments available", 600, "Parallel Coordinates")

        # Create dimensions
        dimensions_list = []
        for col in existing_columns:
            if col not in plot_data.columns:
                continue

            # Handle categorical columns
            if plot_data[col].dtype == 'object' or plot_data[col].dtype.name == 'category':
                try:
                    categories = plot_data[col].unique().tolist()
                    cat_to_num = {cat: i for i, cat in enumerate(categories)}
                    values = plot_data[col].map(cat_to_num)
                    dimensions_list.append(dict(
                        label=col,
                        values=values,
                        tickvals=list(cat_to_num.values()),
                        ticktext=list(cat_to_num.keys()),
                        range=[min(values), max(values)]
                    ))
                except Exception as e:
                    print(f"Warning: Could not process categorical column '{col}': {e}")
                    continue
            else:
                try:
                    # Ensure numeric data
                    numeric_values = pd.to_numeric(plot_data[col], errors='coerce')
                    numeric_values = numeric_values.dropna()
                    
                    if len(numeric_values) == 0:
                        continue
                        
                    dimensions_list.append(dict(
                        label=col,
                        values=numeric_values,
                        range=[numeric_values.min(), numeric_values.max()]
                    ))
                except Exception as e:
                    print(f"Warning: Could not process numeric column '{col}': {e}")
                    continue

        if not dimensions_list:
            return _create_empty_figure("No valid dimensions for parallel coordinates", 600, "Parallel Coordinates")

        # Configure coloring
        line_dict = dict(color='blue')  # Default color
        
        if color_column and color_column in data.columns:
            try:
                color_values = pd.to_numeric(data[color_column], errors='coerce')
                color_values = color_values.dropna()
                
                if len(color_values) > 0:
                    line_dict = dict(
                        color=color_values,
                        colorscale='Bluered',
                        showscale=show_colorbar,
                        colorbar=dict(title=dict(text=color_column, side="right", font=dict(size=16)))
                    )
            except Exception as e:
                print(f"Warning: Could not apply color mapping for '{color_column}': {e}")

        # Create figure
        fig = go.Figure(data=go.Parcoords(line=line_dict, dimensions=dimensions_list))

        # Update styling
        n_iter = len(plot_data)
        color_part = f" (Colored by {color_column})" if color_column and color_column in data.columns else ""
        plural = "iteration" if n_iter == 1 else "iterations"
        title = f"Parallel Coordinates Plot with {n_iter} {plural}{color_part}"

        fig.update_traces(
            labelfont=dict(size=15, family="Arial", color="black"),
            tickfont=dict(size=10, family="Arial"),
            rangefont=dict(size=10, family="Arial"),
            line_colorbar_title_font=dict(size=16, family="Arial", color="black"),
            selector=dict(type="parcoords")
        )

        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor="center", font=dict(size=30, color="black")),
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        return fig
        
    except Exception as e:
        print(f"Error creating parallel coordinates plot: {e}")
        return _create_empty_figure(f"Error creating plot: {str(e)}", 600, "Parallel Coordinates")

def create_enhanced_objectives_scatter(df, metadata, x_col=None, y_col=None, z_col=None, 
                                      color_col=None, marker_size=10):
    """Create enhanced interactive scatter plot with proper point type differentiation"""
    
    if df is None or df.empty:
        return _create_empty_figure("No data available", 600, "Enhanced Scatter Plot")
    
    try:
        # Auto-select columns ONLY if not explicitly provided
        objective_names = metadata.get("objective_names", []) if metadata else []
        
        # Only auto-select if columns are None (not explicitly chosen by user)
        if x_col is None and objective_names:
            x_col = objective_names[0] if objective_names[0] in df.columns else None
        if y_col is None and len(objective_names) > 1:
            y_col = objective_names[1] if objective_names[1] in df.columns else None
        if z_col is None and len(objective_names) > 2:
            z_col = objective_names[2] if objective_names[2] in df.columns else None
        
        # Handle user explicitly selecting "None (2D Plot)" - this comes as empty string ""
        if z_col == "":
            z_col = None
        
        # Validate required columns
        if not x_col or x_col not in df.columns:
            return _create_empty_figure("X-axis column not found", 600, "Enhanced Scatter Plot")
        if not y_col or y_col not in df.columns:
            return _create_empty_figure("Y-axis column not found", 600, "Enhanced Scatter Plot")
        
        # Create working dataframe
        required_cols = [x_col, y_col]
        if z_col and z_col in df.columns:
            required_cols.append(z_col)
        if color_col and color_col in df.columns:
            required_cols.append(color_col)
        if 'Point type' in df.columns:
            required_cols.append('Point type')
        
        df_plot = df[required_cols].copy()
        
        # Remove rows with NaN in x or y
        df_plot = df_plot.dropna(subset=[x_col, y_col])
        
        if df_plot.empty:
            return _create_empty_figure("No valid data points", 600, "Enhanced Scatter Plot")
        
        # Check if 3D plot
        is_3d = z_col and z_col in df_plot.columns and df_plot[z_col].notna().any()
        
        # Point type configurations (matching iteration plot style)
        point_type_config = {
            'Init': {'color': '#1f77b4', 'symbol': 'circle'},
            'BO': {'color': '#ff7f0e', 'symbol': 'diamond'},
            'init': {'color': '#1f77b4', 'symbol': 'circle'},
            'bo': {'color': '#ff7f0e', 'symbol': 'diamond'}
        }
        
        # Create figure
        fig = go.Figure()
        
        # Handle color column type
        color_is_categorical = False
        colorbar_shown = False  # Track if colorbar has been shown to avoid duplicates
        if color_col and color_col in df_plot.columns:
            try:
                pd.to_numeric(df_plot[color_col], errors='raise')
                color_is_categorical = False
            except:
                color_is_categorical = True
        
        # Handle point type distinction
        if 'Point type' in df_plot.columns:
            point_types = df_plot['Point type'].dropna().unique()
            
            for point_type in point_types:
                subset = df_plot[df_plot['Point type'] == point_type].copy()
                if subset.empty:
                    continue
                
                # Get point style
                base_color = point_type_config.get(point_type, {}).get('color', '#2ca02c')
                symbol = point_type_config.get(point_type, {}).get('symbol', 'circle')
                
                # Handle coloring
                if color_col and color_col in subset.columns:
                    if color_is_categorical:
                        # For categorical, create separate traces per category
                        categories = subset[color_col].dropna().unique()
                        colors = px.colors.qualitative.Set1
                        
                        for i, category in enumerate(categories):
                            cat_subset = subset[subset[color_col] == category]
                            if cat_subset.empty:
                                continue
                            
                            marker_props = dict(
                                color=colors[i % len(colors)],
                                size=marker_size,
                                symbol=symbol,
                                line=dict(width=2, color='white')
                            )
                            
                            # Create hover template
                            hover_template = f'<b>{x_col}:</b> %{{x}}<br><b>{y_col}:</b> %{{y}}'
                            if is_3d:
                                hover_template += f'<br><b>{z_col}:</b> %{{z}}'
                            hover_template += f'<br><b>Type:</b> {point_type}<br><b>{color_col}:</b> {category}<extra></extra>'
                            
                            # Add trace
                            trace_func = go.Scatter3d if is_3d else go.Scatter
                            trace_data = {
                                'x': cat_subset[x_col],
                                'y': cat_subset[y_col],
                                'mode': 'markers',
                                'marker': marker_props,
                                'name': f'{point_type} - {category}',
                                'hovertemplate': hover_template
                            }
                            
                            if is_3d:
                                trace_data['z'] = cat_subset[z_col]
                            
                            fig.add_trace(trace_func(**trace_data))
                    
                    else:
                        # For numeric color, use colorscale
                        color_values = pd.to_numeric(subset[color_col], errors='coerce')
                        color_values = color_values.dropna()
                        
                        if len(color_values) > 0:
                            # Filter subset to match color_values length
                            valid_color_indices = subset[color_col].notna()
                            subset_with_color = subset[valid_color_indices]
                            
                            marker_props = dict(
                                color=pd.to_numeric(subset_with_color[color_col], errors='coerce'),
                                colorscale='Bluered',
                                size=marker_size,
                                symbol=symbol,
                                line=dict(width=1, color='white'),
                                showscale=not colorbar_shown,
                                colorbar=dict(title=dict(text=color_col, font=dict(size=14))) if not colorbar_shown else None
                            )
                            
                            # Mark colorbar as shown
                            if not colorbar_shown:
                                colorbar_shown = True
                            
                            # Create hover template
                            hover_template = f'<b>{x_col}:</b> %{{x}}<br><b>{y_col}:</b> %{{y}}'
                            if is_3d:
                                hover_template += f'<br><b>{z_col}:</b> %{{z}}'
                            hover_template += f'<br><b>Type:</b> {point_type}<br><b>{color_col}:</b> %{{marker.color}}<extra></extra>'
                            
                            # Add trace
                            trace_func = go.Scatter3d if is_3d else go.Scatter
                            trace_data = {
                                'x': subset_with_color[x_col],
                                'y': subset_with_color[y_col],
                                'mode': 'markers',
                                'marker': marker_props,
                                'name': f'{point_type} points',
                                'hovertemplate': hover_template
                            }
                            
                            if is_3d:
                                trace_data['z'] = subset_with_color[z_col]
                            
                            fig.add_trace(trace_func(**trace_data))
                        else:
                            # Fallback to base color if numeric conversion fails
                            marker_props = dict(
                                color=base_color,
                                size=marker_size,
                                symbol=symbol,
                                line=dict(width=2, color='white')
                            )
                            
                            # Create hover template
                            hover_template = f'<b>{x_col}:</b> %{{x}}<br><b>{y_col}:</b> %{{y}}'
                            if is_3d:
                                hover_template += f'<br><b>{z_col}:</b> %{{z}}'
                            hover_template += f'<br><b>Type:</b> {point_type}<extra></extra>'
                            
                            # Add trace
                            trace_func = go.Scatter3d if is_3d else go.Scatter
                            trace_data = {
                                'x': subset[x_col],
                                'y': subset[y_col],
                                'mode': 'markers',
                                'marker': marker_props,
                                'name': f'{point_type} points',
                                'hovertemplate': hover_template
                            }
                            
                            if is_3d:
                                trace_data['z'] = subset[z_col]
                            
                            fig.add_trace(trace_func(**trace_data))
                
                else:
                    # No color column, use base color
                    marker_props = dict(
                        color=base_color,
                        size=marker_size,
                        symbol=symbol,
                        line=dict(width=2, color='white')
                    )
                    
                    # Create hover template
                    hover_template = f'<b>{x_col}:</b> %{{x}}<br><b>{y_col}:</b> %{{y}}'
                    if is_3d:
                        hover_template += f'<br><b>{z_col}:</b> %{{z}}'
                    hover_template += f'<br><b>Type:</b> {point_type}<extra></extra>'
                    
                    # Add trace
                    trace_func = go.Scatter3d if is_3d else go.Scatter
                    trace_data = {
                        'x': subset[x_col],
                        'y': subset[y_col],
                        'mode': 'markers',
                        'marker': marker_props,
                        'name': f'{point_type} points',
                        'hovertemplate': hover_template
                    }
                    
                    if is_3d:
                        trace_data['z'] = subset[z_col]
                    
                    fig.add_trace(trace_func(**trace_data))
        
        else:
            # No point type distinction - single trace
            if color_col and color_col in df_plot.columns:
                if color_is_categorical:
                    # Use plotly express for categorical coloring
                    if is_3d:
                        fig = px.scatter_3d(df_plot, x=x_col, y=y_col, z=z_col, color=color_col,
                                          hover_data=[color_col])
                    else:
                        fig = px.scatter(df_plot, x=x_col, y=y_col, color=color_col,
                                       hover_data=[color_col])
                else:
                    # Numeric coloring
                    color_values = pd.to_numeric(df_plot[color_col], errors='coerce')
                    valid_indices = color_values.notna()
                    plot_subset = df_plot[valid_indices]
                    
                    marker_props = dict(
                        color=pd.to_numeric(plot_subset[color_col], errors='coerce'),
                        colorscale='Bluered',
                        size=marker_size,
                        line=dict(width=1, color='white'),
                        showscale=not colorbar_shown,
                        colorbar=dict(title=dict(text=color_col, font=dict(size=14))) if not colorbar_shown else None
                    )
                    
                    # Mark colorbar as shown
                    if not colorbar_shown:
                        colorbar_shown = True
                    
                    hover_template = f'<b>{x_col}:</b> %{{x}}<br><b>{y_col}:</b> %{{y}}'
                    if is_3d:
                        hover_template += f'<br><b>{z_col}:</b> %{{z}}'
                    hover_template += f'<br><b>{color_col}:</b> %{{marker.color}}<extra></extra>'
                    
                    trace_func = go.Scatter3d if is_3d else go.Scatter
                    trace_data = {
                        'x': plot_subset[x_col],
                        'y': plot_subset[y_col],
                        'mode': 'markers',
                        'marker': marker_props,
                        'name': 'Experiments',
                        'hovertemplate': hover_template
                    }
                    
                    if is_3d:
                        trace_data['z'] = plot_subset[z_col]
                    
                    fig.add_trace(trace_func(**trace_data))
            else:
                # No color, simple scatter
                marker_props = dict(
                    color='#1f77b4',
                    size=marker_size,
                    line=dict(width=1, color='white')
                )
                
                hover_template = f'<b>{x_col}:</b> %{{x}}<br><b>{y_col}:</b> %{{y}}'
                if is_3d:
                    hover_template += f'<br><b>{z_col}:</b> %{{z}}'
                hover_template += '<extra></extra>'
                
                trace_func = go.Scatter3d if is_3d else go.Scatter
                trace_data = {
                    'x': df_plot[x_col],
                    'y': df_plot[y_col],
                    'mode': 'markers',
                    'marker': marker_props,
                    'name': 'Experiments',
                    'hovertemplate': hover_template
                }
                
                if is_3d:
                    trace_data['z'] = df_plot[z_col]
                
                fig.add_trace(trace_func(**trace_data))
        
        # Add 3D projection lines for objectives
        if is_3d and objective_names:
            _add_projection_lines(fig, df_plot, x_col, y_col, z_col, objective_names)
        
        # Build title
        title_parts = [f"{y_col} vs {x_col}"]
        if is_3d:
            title_parts.append(f"vs {z_col}")
        if color_col:
            title_parts.append(f"Color = {color_col}")
        
        title = " | ".join(title_parts)
        
        # Update layout
        layout_updates = {
            'title': {'text': f'Scatter plot: {title}', 'x': 0.5, 'xanchor': 'center', 'font': {'size': 18}},
            'hovermode': 'closest',
            'height': 600,
            'showlegend': True,
            'legend': {
                'yanchor': "top", 'y': 0.99, 'xanchor': "left", 'x': 0.01,
                'bgcolor': 'rgba(255,255,255,0.8)', 'bordercolor': 'rgba(0,0,0,0.2)', 'borderwidth': 1
            },
            'plot_bgcolor': 'rgba(240,240,240,0.95)',
            'paper_bgcolor': 'white'
        }
        
        if is_3d:
            layout_updates['scene'] = {
                'xaxis': {'title': x_col, 'backgroundcolor': "rgb(230, 230, 230)", 'gridcolor': "white",
                         'showspikes': True, 'spikesides': True, 'spikecolor': "#999999", 'spikethickness': 2},
                'yaxis': {'title': y_col, 'backgroundcolor': "rgb(230, 230, 230)", 'gridcolor': "white",
                         'showspikes': True, 'spikesides': True, 'spikecolor': "#999999", 'spikethickness': 2},
                'zaxis': {'title': z_col, 'backgroundcolor': "rgb(230, 230, 230)", 'gridcolor': "white",
                         'showspikes': True, 'spikesides': True, 'spikecolor': "#999999", 'spikethickness': 2},
                'camera': {'eye': {'x': 1.2, 'y': 1.2, 'z': 1.2}},
                'aspectmode': 'cube'
            }
        else:
            layout_updates.update({
                'xaxis': {'title': x_col, 'showgrid': True, 'gridcolor': 'lightgray', 'zeroline': True, 'zerolinecolor': 'gray'},
                'yaxis': {'title': y_col, 'showgrid': True, 'gridcolor': 'lightgray', 'zeroline': True, 'zerolinecolor': 'gray'}
            })
        
        fig.update_layout(**layout_updates)
        return fig
        
    except Exception as e:
        print(f"Error creating enhanced scatter plot: {e}")
        return _create_empty_figure(f"Error creating plot: {str(e)}", 600, "Enhanced Scatter Plot")

def create_iteration_plot(df, metadata, y_column=None):
    """Create an iteration vs objective plot showing progression over experiments"""
    
    if df is None or df.empty:
        return _create_empty_figure("No data available", 500, "Iteration Plot")
    
    try:
        # Auto-select y_column
        if not y_column:
            objective_names = metadata.get("objective_names", []) if metadata else []
            if objective_names:
                # Find first objective that exists in the data
                for obj in objective_names:
                    if obj in df.columns:
                        y_column = obj
                        break
            
            if not y_column:
                # Fall back to first numeric column
                numeric_cols = []
                for col in df.columns:
                    if col != 'Point type':
                        try:
                            pd.to_numeric(df[col], errors='raise')
                            numeric_cols.append(col)
                        except:
                            continue
                
                y_column = numeric_cols[0] if numeric_cols else None
        
        if not y_column or y_column not in df.columns:
            return _create_empty_figure(f"Column '{y_column}' not found in data", 500, "Iteration Plot")
        
        # Prepare data
        df_plot = df.copy()
        df_plot['Iteration'] = range(1, len(df_plot) + 1)
        
        # Filter for valid y_column data
        df_plot = df_plot[df_plot[y_column].notna() & (df_plot[y_column] != "")]
        
        if df_plot.empty:
            return _create_empty_figure(f"No valid data points for '{y_column}'", 500, "Iteration Plot")
        
        # Convert to numeric
        try:
            df_plot[y_column] = pd.to_numeric(df_plot[y_column], errors='coerce')
            df_plot = df_plot.dropna(subset=[y_column])
        except Exception as e:
            print(f"Warning: Could not convert '{y_column}' to numeric: {e}")
            return _create_empty_figure(f"Could not convert '{y_column}' to numeric", 500, "Iteration Plot")
        
        if df_plot.empty:
            return _create_empty_figure(f"No numeric data points for '{y_column}'", 500, "Iteration Plot")
        
        # Create plot
        fig = go.Figure()
        
        # Handle point type distinction
        if 'Point type' in df_plot.columns:
            point_types = df_plot['Point type'].unique()
            color_map = {'Init': '#1f77b4', 'BO': '#ff7f0e', 'init': '#1f77b4', 'bo': '#ff7f0e'}
            symbol_map = {'Init': 'circle', 'BO': 'diamond', 'init': 'circle', 'bo': 'diamond'}
            
            for point_type in point_types:
                if pd.isna(point_type):
                    continue
                    
                subset = df_plot[df_plot['Point type'] == point_type]
                if subset.empty:
                    continue
                
                color = color_map.get(point_type, '#2ca02c')
                symbol = symbol_map.get(point_type, 'circle')
                
                fig.add_trace(go.Scatter(
                    x=subset['Iteration'],
                    y=subset[y_column],
                    mode='markers+lines',
                    name=f'{point_type} points',
                    marker=dict(color=color, size=10, symbol=symbol, line=dict(width=2, color='white')),
                    line=dict(color=color, width=2),
                    hovertemplate=f'<b>Iteration:</b> %{{x}}<br><b>{y_column}:</b> %{{y}}<br><b>Type:</b> {point_type}<extra></extra>'
                ))
        else:
            # Single trace
            fig.add_trace(go.Scatter(
                x=df_plot['Iteration'],
                y=df_plot[y_column],
                mode='markers+lines',
                name='All points',
                marker=dict(color='#1f77b4', size=8, line=dict(width=1, color='white')),
                line=dict(color='#1f77b4', width=2),
                hovertemplate=f'<b>Iteration:</b> %{{x}}<br><b>{y_column}:</b> %{{y}}<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title=f'Optimization Progress: {y_column} vs Iteration',
            xaxis_title='Iterations',
            yaxis_title=y_column,
            hovermode='closest',
            height=500,
            showlegend=True,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            margin=dict(l=50, r=50, t=80, b=50),
            xaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
            yaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray')
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating iteration plot: {e}")
        return _create_empty_figure(f"Error creating plot: {str(e)}", 500, "Iteration Plot")
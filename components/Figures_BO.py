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

def create_objectives_scatter(data, domain_metadata, color_by=None, marker_size=9):
    """
    Build a scatter plot for 2 or 3 objectives.

    - data: pandas.DataFrame
    - domain_metadata: dict with 'parameter_names' and 'objective_names'
    - color_by: optional column name to color points by (categorical or numeric)
    - marker_size: marker size for points
    """
    # Basic checks
    if data is None or data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=18, color="gray"))
        fig.update_layout(height=600)
        return fig

    objective_names = domain_metadata.get("objective_names", [])
    if len(objective_names) not in (2, 3):
        fig = go.Figure()
        fig.add_annotation(text="Requires exactly 2 or 3 objectives for this visualization",
                           x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                           font=dict(size=18, color="gray"))
        fig.update_layout(height=600)
        return fig

    # choose color column if available
    color_col = color_by if (color_by and color_by in data.columns) else None

    # Build a hover columns list (exclude objectives and color column)
    hover_cols = [c for c in data.columns if c not in objective_names and c != color_col]

    # --- 2D case ---
    if len(objective_names) == 2:
        x_col, y_col = objective_names[0], objective_names[1]

        # quick check: do we have at least one row with both objectives?
        df_obj = data[[c for c in [x_col, y_col] if c in data.columns]].dropna().copy()
        if df_obj.empty:
            fig = go.Figure()
            fig.add_annotation(text="No complete objective pairs available", x=0.5, y=0.5,
                               xref="paper", yref="paper", showarrow=False,
                               font=dict(size=18, color="gray"))
            fig.update_layout(height=600)
            return fig

        # build unique ordered list of columns to pass to plotly
        cols = [x_col, y_col]
        if color_col and color_col not in cols and color_col in data.columns:
            cols.append(color_col)
        for c in hover_cols:
            if c not in cols:
                cols.append(c)

        # IMPORTANT: only dropna on objective columns (and optionally color_col) to avoid removing rows
        subset_for_drop = [x_col, y_col]
        # include color in subset only if you want to require it to be present for coloring
        # subset_for_drop.append(color_col)  # <-- optional
        df_plot_full = data.loc[:, cols].dropna(subset=subset_for_drop).copy()

        if df_plot_full.empty:
            fig = go.Figure()
            fig.add_annotation(text="No rows left after filtering", x=0.5, y=0.5,
                               xref="paper", yref="paper", showarrow=False,
                               font=dict(size=18, color="gray"))
            fig.update_layout(height=600)
            return fig

        # compute hover_data from actual df passed to plotly
        hover_data = [c for c in df_plot_full.columns if c not in (x_col, y_col, color_col)]

        # Build the plot, pass only the cleaned df_plot_full
        if color_col and color_col in df_plot_full.columns:
            fig = px.scatter(
                df_plot_full,
                x=x_col,
                y=y_col,
                color=color_col,
                hover_data=hover_data,
                labels={x_col: x_col, y_col: y_col}
            )
        else:
            fig = px.scatter(
                df_plot_full,
                x=x_col,
                y=y_col,
                hover_data=hover_data
            )
            # unify marker appearance for single-color case
            fig.update_traces(marker=dict(color="steelblue", size=marker_size, opacity=0.85),
                              selector=dict(mode="markers"))

        # --- Title & global layout (2D) ---
        title_text = f"Objectives scatter: {y_col} vs {x_col}"
        fig.update_layout(
            title={
                "text": title_text,
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 24, "family": "Arial", "color": "black"},
                "pad": {"b": 12}
            },
            font={"family": "Arial", "size": 12, "color": "black"},
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=600,
            margin=dict(l=80, r=40, t=110, b=80)
        )

        # --- Axes styling (2D) ---
        fig.update_xaxes(title_text=x_col, title_font=dict(size=16, family="Arial"),
                         tickfont=dict(size=12), automargin=True)
        fig.update_yaxes(title_text=y_col, title_font=dict(size=16, family="Arial"),
                         tickfont=dict(size=12), automargin=True)

        # --- Legend styling (use color_col name if present) ---
        legend_title_text = color_col if color_col else "Color by"
        fig.update_layout(
            legend=dict(
                title=dict(text=legend_title_text, font=dict(size=13)),
                font=dict(size=11),
                orientation="v",
                yanchor="bottom",
                y=0.98,
                xanchor="right",
                x=0.99
            )
        )

        # ensure markers sized consistently even when px creates grouped traces
        fig.update_traces(marker=dict(size=marker_size, opacity=0.85), selector=dict(mode="markers"))

        return fig

    # --- 3D case ---
    x_col, y_col, z_col = objective_names[0], objective_names[1], objective_names[2]

    # quick check: do we have at least one row with all three objectives?
    df_obj3 = data[[c for c in [x_col, y_col, z_col] if c in data.columns]].dropna().copy()
    if df_obj3.empty:
        fig = go.Figure()
        fig.add_annotation(text="No complete objective triplets available", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=18, color="gray"))
        fig.update_layout(height=600)
        return fig

    # build unique ordered list of columns to pass to plotly for 3D
    cols = [x_col, y_col, z_col]
    if color_col and color_col not in cols and color_col in data.columns:
        cols.append(color_col)
    for c in hover_cols:
        if c not in cols:
            cols.append(c)

    # only drop rows based on objective columns
    subset_for_drop = [x_col, y_col, z_col]
    df_plot_full = data.loc[:, cols].dropna(subset=subset_for_drop).copy()

    if df_plot_full.empty:
        fig = go.Figure()
        fig.add_annotation(text="No rows left after filtering", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=18, color="gray"))
        fig.update_layout(height=600)
        return fig

    hover_data = [c for c in df_plot_full.columns if c not in (x_col, y_col, z_col, color_col)]

    if color_col and color_col in df_plot_full.columns:
        fig = px.scatter_3d(
            df_plot_full,
            x=x_col,
            y=y_col,
            z=z_col,
            color=color_col,
            hover_data=hover_data,
            labels={x_col: x_col, y_col: y_col, z_col: z_col}
        )
    else:
        fig = px.scatter_3d(
            df_plot_full,
            x=x_col,
            y=y_col,
            z=z_col,
            hover_data=hover_data
        )
        fig.update_traces(marker=dict(color="steelblue", size=marker_size, opacity=0.85),
                          selector=dict(mode="markers"))

    # --- Title & global layout (3D) ---
    title_text = f"3D Objectives scatter: {z_col} vs {y_col} vs {x_col}"
    fig.update_layout(
        title={
            "text": title_text,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 24, "family": "Arial", "color": "black"},
            "pad": {"b": 12}
        },
        font={"family": "Arial", "size": 12, "color": "black"},
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=700,
        margin=dict(l=60, r=60, t=110, b=60)
    )

    # --- Scene axes formatting to match 2D fonts ---
    scene = dict(
        xaxis=dict(title=dict(text=x_col, font=dict(size=16, family="Arial")), tickfont=dict(size=12)),
        yaxis=dict(title=dict(text=y_col, font=dict(size=16, family="Arial")), tickfont=dict(size=12)),
        zaxis=dict(title=dict(text=z_col, font=dict(size=16, family="Arial")), tickfont=dict(size=12))
    )
    fig.update_layout(scene=scene)

    # --- Legend styling for 3D ---
    legend_title_text = color_col if color_col else "Color by"
    fig.update_layout(
        legend=dict(
            title=dict(text=legend_title_text, font=dict(size=13)),
            font=dict(size=11),
            orientation="v",
            yanchor="bottom",
            y=0.98,
            xanchor="right",
            x=0.99
        )
    )

    # ensure 3D markers consistent size
    fig.update_traces(marker=dict(size=marker_size, opacity=0.85), selector=dict(mode="markers"))

    return fig
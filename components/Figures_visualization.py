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

### FUNCTIONS TO CREATE GRAPHS ###

# Load the selected sheet with formatting
def load_filtered_df_graph(excel, sheet):
    # Ensure we look in the subfolder (e.g. "data")
    file_path = os.path.join(EXCEL_FOLDER, excel)

    df = pd.read_excel(file_path, sheet_name=sheet, engine="openpyxl")
    dff = df.copy()

    if 'Date' in dff.columns:
        dff['Date'] = pd.to_datetime(dff['Date'], dayfirst=True).dt.strftime('%d/%m/%Y')
    
    # Replace special values
    with pd.option_context('future.no_silent_downcasting', True):
        dff = dff.replace({
            'nd': np.nan,
            'rt': 25,
            r'^\s*<1\s*$': 1,
            r'^\s*>99\s*$': 99,
            r'^\s*>100\s*$': np.nan
        }, regex=True)
    
    # Convert columns to numeric where possible
    for col in dff.columns:
        try:
            dff[col] = pd.to_numeric(dff[col])
        except (ValueError, TypeError):
            pass

    # Dynamically detect "React" and "equivalent" columns
    react_cols = [col for col in dff.columns if col.lower().startswith('react')]
    react_cols.sort()
    eq_cols = []
    for react_col in react_cols:
        react_idx = dff.columns.get_loc(react_col)
        for i in range(react_idx + 1, len(dff.columns)):
            next_col = dff.columns[i]
            if any(keyword in next_col.lower() for keyword in ['eq', 'c ', 'conc', 'concentration', '(m)']):
                eq_cols.append(next_col)
                break

    if len(react_cols) != len(eq_cols):
        print(f"Warning: Found {len(react_cols)} React columns but {len(eq_cols)} equivalent columns")
        min_len = min(len(react_cols), len(eq_cols))
        react_cols = react_cols[:min_len]
        eq_cols = eq_cols[:min_len]

    if not react_cols:
        return dff
    
    id_vars_common = dff.columns.difference(react_cols + eq_cols).tolist()
    df_react = dff.melt(id_vars=id_vars_common, value_vars=react_cols,
                        var_name='react_type', value_name='Reactant')
    df_eq = dff.melt(id_vars=id_vars_common, value_vars=eq_cols,
                     var_name='eq_type', value_name='C/eq')
    df_react['index'] = df_react['react_type'].str.extract(r'(\d+)')
    eq_col_to_index = {col: str(i+1) for i, col in enumerate(eq_cols)}
    df_eq['index'] = df_eq['eq_type'].map(eq_col_to_index)
    df_merged = pd.merge(df_react, df_eq, on=id_vars_common + ['index'])

    base_cols = [col for col in dff.columns if col not in react_cols + eq_cols]
    first_react_pos = dff.columns.get_loc(react_cols[0])
    first_eq_pos = dff.columns.get_loc(eq_cols[0])
    base_cols.insert(first_react_pos, 'Reactant')
    eq_insert_pos = first_eq_pos + 1 if first_eq_pos > first_react_pos else first_eq_pos
    base_cols.insert(eq_insert_pos, 'C/eq')
    df_merged = df_merged[base_cols]

    return df_merged


# Create a scatter graph
def graph_scatter(df, x_axis, y_axis, colors=None, size_param=None, hover=None):
    # --- Drop only necessary NaNs ---
    drop_cols = [c for c in [x_axis, y_axis, colors, size_param] if c]
    df = df.dropna(subset=drop_cols)

    # Default hover handling
    hover_args = {}
    if hover:
        hover_args["hover_name"] = hover

    fig = None

    # Case 1: categorical size_param
    if size_param and (df[size_param].dtype == 'object' or df[size_param].dtype.name == 'category'):
        unique_categories = df[size_param].unique()
        size_mapping = {cat: (i + 1) * 12 for i, cat in enumerate(unique_categories)}
        df_plot = df.copy()
        df_plot['size_numeric'] = df_plot[size_param].map(size_mapping)

        fig = px.scatter(
            df_plot,
            x=x_axis,
            y=y_axis,
            color=colors if colors else None,
            size="size_numeric",
            color_continuous_scale="bluered" if colors else None,
            size_max=35,
            hover_data={size_param: True, "size_numeric": False},
            **hover_args
        )

    # Case 2: numeric size_param
    elif size_param:
        fig = px.scatter(
            df,
            x=x_axis,
            y=y_axis,
            color=colors if colors else None,
            size=size_param,
            color_continuous_scale="bluered" if colors else None,
            size_max=35,
            **hover_args
        )

    # Case 3: only x,y,(color)
    else:
        fig = px.scatter(
            df,
            x=x_axis,
            y=y_axis,
            color=colors if colors else None,
            color_continuous_scale="bluered" if colors else None,
            **hover_args
        )

    # --- Dynamic title ---
    title_parts = [f"{y_axis} vs {x_axis}"]
    if colors:
        title_parts.append(f"Color={colors}")
    if size_param:
        title_parts.append(f"Size={size_param}")
    title = " | ".join(title_parts)

    # --- Layout updates ---
    fig.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 24}
        },
        xaxis_title={"text": x_axis, "font": {"size": 18}},
        yaxis_title={"text": y_axis, "font": {"size": 18}},
        legend_title_text=""
    )

    # --- Marker style ---
    fig.update_traces(
        marker=dict(
            sizemin=5,
            opacity=0.6,
            line=dict(width=0)
        )
    )

    return fig

# Create a boxplot
def graph_box(df, x_axis, y_axis):
    fig = px.box(df, x=x_axis, y=y_axis)
    # Generate dynamic title
    title = f"Boxplot of {y_axis} Vs {x_axis}"
    
    # Update layout with title and larger axis labels
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,  # Center the title
            'xanchor': 'center',
            'font': {'size': 28}
        },
        xaxis={
            'title': {
                'text': x_axis,
                'font': {'size': 20}
            }
        },
        yaxis={
            'title': {
                'text': y_axis,
                'font': {'size': 20}
            }
        }
    )
    return fig

# # Create a pie chart
# def graph_pie(sheet, values, names):
#     data = load_filtered_df_graph(sheet)
#     fig = px.pie(data, values=values, names=names)
#     return fig

# Create a histogram
def graph_histo(df, column):
    # df["Sub system"] = df["System"]
    # df["System"] = "flow"
    # df.loc[df["Sub system"].str.contains("batch", case=False, na=False), "System"] = "batch"
    fig = px.histogram(df, x=column)
    # Generate dynamic title
    title = f"Histogramm of {column}"
    
    # Update layout with title and larger axis labels
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,  # Center the title
            'xanchor': 'center',
            'font': {'size': 28}
        },
        xaxis={
            'title': {
                'text': column,
                'font': {'size': 20}
            }
        },
    )
    return fig

# Create a 2D histogram
def graph_2Dhisto(df, column_1, column_2):
    fig = px.density_heatmap(df, x=column_1, y=column_2)
    # Generate dynamic title
    title = f"2D Histogramm of {column_1} Vs {column_2}"
    
    # Update layout with title and larger axis labels
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,  # Center the title
            'xanchor': 'center',
            'font': {'size': 28}
        },
        xaxis={
            'title': {
                'text': column_1,
                'font': {'size': 20}
            }
        },
        yaxis={
            'title': {
                'text': column_2,
                'font': {'size': 20}
            }
        }
    )
    return fig

def graph_histo_col(df): 
    uniques_count = df.nunique()  # Get number of unique values per column
    fig = px.bar(
        x=uniques_count.index,
        y=uniques_count.values,
        labels={'x': 'Columns', 'y': 'Number of Unique Values'},
    )
    title = f"Histogram of all the columns"
    
    # Update layout with title and larger axis labels
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,  # Center the title
            'xanchor': 'center',
            'font': {'size': 28}
        },
        xaxis={
            'title': {
                'text': "All columns",
                'font': {'size': 20}
            }
        },
        yaxis={
            'title': {
                'text': "Number of uniques values",
                'font': {'size': 20}
            }
        }
    )
    return fig

# # Create a contour plot
# def graph_contour(sheet, col_filtre, val_filtre, y_axis, x_axis, z_axis):
#     dff = load_filtered_df_graph(sheet)
#     df = dff.copy()
#     if col_filtre == "System":
#         if val_filtre == "batch":
#             filtered_df = df[df[col_filtre].str.contains("batch")]
#         else:
#             filtered_df = df[df[col_filtre] == val_filtre]
#     else :
#         filtered_df = df[df[col_filtre] == val_filtre]

#     filtered_df[z_axis] = pd.to_numeric(filtered_df[z_axis], errors='coerce')
#     filtered_df = filtered_df.dropna(subset=[z_axis])

#     # Pivot the table to get a 2D array of z values
#     pivot = filtered_df.pivot_table(index=y_axis, columns=x_axis, values=z_axis, aggfunc='mean')

#     # Extract x, y, and z
#     x = pivot.columns.values       # x-axis values
#     y = pivot.index.values         # y-axis values
#     z = pivot.values               # 2D array for contour

#     # Plot with Plotly
#     fig = go.Figure(data=
#         go.Contour(
#             x=x,
#             y=y,
#             z=z
#         )
#     )
#     return fig

### LAYOUT ###

def layout(**kwargs):
    return dbc.Row(
        [
        dbc.Col(html.Div(
             id="page-content",
             
        )
        , width=12)
        ]
    )

### CALLBACKS ###


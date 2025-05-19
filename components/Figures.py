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

### FUNCTIONS TO CREATE GRAPHS ###

# Load the selected sheet with formatting
def load_filtered_df_graph(sheet):
    df = pd.read_excel("results.xlsx", sheet_name=sheet)
    dff = df.copy()
    if 'Date' in dff.columns:
        dff['Date'] = pd.to_datetime(dff['Date'], dayfirst=True).dt.strftime('%d/%m/%Y')
    dff = dff.replace('nd', np.nan)
    dff = dff.replace('rt', 25)
    dff = dff.replace(r'^\s*<1\s*$', 1, regex=True)
    dff = dff.replace(r'^\s*>99\s*$', 99, regex=True)
    for col in dff.columns:
        dff[col] = pd.to_numeric(dff[col], errors='ignore')

    
    react_cols = ['React 1', 'React 2', 'React 3', 'React 4']
    eq_cols = ['C react 1 (M)', 'eq react 2', 'eq react 3', 'eq react 4']

    # Step 2: ID columns = all except the above
    id_vars_common = dff.columns.difference(react_cols + eq_cols).tolist()

    # Step 3: Melt both
    df_react = dff.melt(id_vars=id_vars_common, value_vars=react_cols,
                        var_name='react_type', value_name='Reactant')
    df_eq = dff.melt(id_vars=id_vars_common, value_vars=eq_cols,
                    var_name='eq_type', value_name='C/eq')

    # Step 4: Extract indices
    df_react['index'] = df_react['react_type'].str.extract(r'(\d+)')
    df_eq['index'] = df_eq['eq_type'].str.extract(r'(\d+)')

    # Step 5: Merge on all metadata + index
    df_merged = pd.merge(df_react, df_eq, on=id_vars_common + ['index'])

    # Step 6: Reorder columns to match original DataFrame
    # Remove old react/eq cols from the original
    base_cols = [col for col in dff.columns if col not in react_cols + eq_cols]

    # Find the position of 'React 1' and 'C react 1 (M)' in the original dataframe
    react1_pos = dff.columns.get_loc('React 1')
    eq1_pos = dff.columns.get_loc('C react 1 (M)')

    # Insert the new columns at the right positions
    # Note: adjust position for second insert since list length increases
    base_cols.insert(react1_pos, 'Reactant')
    base_cols.insert(eq1_pos + 1 if eq1_pos < react1_pos else eq1_pos, 'C/eq')

    # Reorder final df
    df_merged = df_merged[base_cols]

    return df_merged


# Create a scatter graph
def graph_scatter(sheet, x_axis, y_axis, colors):
    data = load_filtered_df_graph(sheet)
    data = data.dropna(subset=[colors])
    fig= px.scatter(data, x=x_axis, y=y_axis , color=colors, hover_name="Exp code", color_continuous_scale="bluered") 
    return fig

# Create a boxplot
def graph_box(sheet, x_axis, y_axis):
    data = load_filtered_df_graph(sheet)
    fig = px.box(data, x=x_axis, y=y_axis)
    return fig

# Create a pie chart
def graph_pie(sheet, values, names):
    data = load_filtered_df_graph(sheet)
    fig = px.pie(data, values=values, names=names)
    return fig

# Create a histogram
def graph_histo(sheet, column):
    data = load_filtered_df_graph(sheet)
    data["Sub system"] = data["System"]
    data["System"] = "flow"
    data.loc[data["Sub system"].str.contains("batch", case=False, na=False), "System"] = "batch"
    fig = px.histogram(data, x=column)
    return fig

# Create a 2D histogram
def graph_2Dhisto(sheet, column_1, column_2):
    data = load_filtered_df_graph(sheet)
    fig = px.density_heatmap(data, x=column_1, y=column_2)
    return fig

# Create a contour plot
def graph_contour(sheet, col_filtre, val_filtre, y_axis, x_axis, z_axis):
    dff = load_filtered_df_graph(sheet)
    df = dff.copy()
    if col_filtre == "System":
        if val_filtre == "batch":
            filtered_df = df[df[col_filtre].str.contains("batch")]
        else:
            filtered_df = df[df[col_filtre] == val_filtre]
    else :
        filtered_df = df[df[col_filtre] == val_filtre]

    filtered_df[z_axis] = pd.to_numeric(filtered_df[z_axis], errors='coerce')
    filtered_df = filtered_df.dropna(subset=[z_axis])

    # Pivot the table to get a 2D array of z values
    pivot = filtered_df.pivot_table(index=y_axis, columns=x_axis, values=z_axis, aggfunc='mean')

    # Extract x, y, and z
    x = pivot.columns.values       # x-axis values
    y = pivot.index.values         # y-axis values
    z = pivot.values               # 2D array for contour

    # Plot with Plotly
    fig = go.Figure(data=
        go.Contour(
            x=x,
            y=y,
            z=z
        )
    )
    return fig












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


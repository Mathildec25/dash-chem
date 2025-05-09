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
    if all(col in df.columns for col in ['Conversion', 'Yield', 'Selectivity']):
        df = df[~((df['Conversion'] == 'nd') & (df['Yield'] == 'nd') & (df['Selectivity'] == 'nd'))]
        #df = df[~((df['Yield'] == 'nd') & (df['Selectivity'] == 'nd'))]
    return df

# Create a scatter graph
def graph_scatter(sheet, x_axis, y_axis, colors):
    data = load_filtered_df_graph(sheet)
    df = data.copy()
    df[colors] = pd.to_numeric(df[colors], errors='coerce')
    fig= px.scatter(df, x=x_axis, y=y_axis , color=colors, hover_name="Exp code", color_continuous_scale="bluered") 
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


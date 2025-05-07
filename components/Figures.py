import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, dash_table, State
from dash.dash_table.Format import Format
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

### FUNCTIONS ###

# Load the selected sheet
def load_filtered_df_graph(sheet):
    df = pd.read_excel("results.xlsx", sheet_name=sheet)
    if all(col in df.columns for col in ['Conversion', 'Yield', 'Selectivity']):
        df = df[~((df['Conversion'] == 'nd') & (df['Yield'] == 'nd') & (df['Selectivity'] == 'nd'))]
    return df

# Create a scatter graph
def graph_scatter(sheet, x_axis, y_axis):
    data = load_filtered_df_graph(sheet)
    fig= px.scatter(data, x=x_axis, y=y_axis)
    return fig

# Create a boxplot
def graph_pie(sheet, x_axis, y_axis):
    data = load_filtered_df_graph(sheet)
    fig = px.box(data, x=x_axis, y=y_axis)
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


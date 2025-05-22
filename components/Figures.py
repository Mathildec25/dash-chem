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
def load_filtered_df_graph(excel, sheet):
    df = pd.read_excel(excel, sheet_name=sheet)
    dff = df.copy()
    if 'Date' in dff.columns:
        dff['Date'] = pd.to_datetime(dff['Date'], dayfirst=True).dt.strftime('%d/%m/%Y')
    
    # Combine all replace calls into one
    with pd.option_context('future.no_silent_downcasting', True):  ### Don't trigger error of changing element type while replacing
        dff = dff.replace({
            'nd': np.nan,
            'rt': 25,
            r'^\s*<1\s*$': 1,
            r'^\s*>99\s*$': 99,
            r'^\s*>100\s*$': np.nan
        }, regex=True)
    
    for col in dff.columns:     # try for col where is needed else do nothing (to don't raise error with ignore argument of pd.to_numeric)
        try:
            dff[col] = pd.to_numeric(dff[col])
        except (ValueError, TypeError):
            pass
   
    # Dynamically detect React columns (columns that start with 'React')
    react_cols = [col for col in dff.columns if col.lower().startswith('react')]
    react_cols.sort()  # Sort to ensure consistent ordering
    
    # Dynamically detect equivalent/concentration columns
    # These come after each React column and contain 'eq' or 'c' (case insensitive)
    eq_cols = []
    
    for react_col in react_cols:
        react_idx = dff.columns.get_loc(react_col)
        # Look for the next column that contains concentration/equivalent info
        for i in range(react_idx + 1, len(dff.columns)):
            next_col = dff.columns[i]
            # Check if this column is likely a concentration/equivalent column
            if any(keyword in next_col.lower() for keyword in ['eq', 'c ', 'conc', 'concentration', '(m)']):
                eq_cols.append(next_col)
                break
    
    # Ensure we have matching pairs
    if len(react_cols) != len(eq_cols):
        print(f"Warning: Found {len(react_cols)} React columns but {len(eq_cols)} equivalent columns")
        # Truncate to the minimum length to avoid errors
        min_len = min(len(react_cols), len(eq_cols))
        react_cols = react_cols[:min_len]
        eq_cols = eq_cols[:min_len]
    
    # If no React columns found, return original dataframe
    if not react_cols:
        return dff
    
    # Step 2: ID columns = all except the above
    id_vars_common = dff.columns.difference(react_cols + eq_cols).tolist()
    
    # Step 3: Melt both
    df_react = dff.melt(id_vars=id_vars_common, value_vars=react_cols,
                        var_name='react_type', value_name='Reactant')
    df_eq = dff.melt(id_vars=id_vars_common, value_vars=eq_cols,
                    var_name='eq_type', value_name='C/eq')
    
    # Step 4: Extract indices - more robust extraction
    # Extract number from React column names
    df_react['index'] = df_react['react_type'].str.extract(r'(\d+)')
    # For equivalent columns, we'll use the position in the list since naming might vary
    eq_col_to_index = {col: str(i+1) for i, col in enumerate(eq_cols)}
    df_eq['index'] = df_eq['eq_type'].map(eq_col_to_index)
    
    # Step 5: Merge on all metadata + index
    df_merged = pd.merge(df_react, df_eq, on=id_vars_common + ['index'])
    
    # Step 6: Reorder columns to match original DataFrame
    # Remove old react/eq cols from the original
    base_cols = [col for col in dff.columns if col not in react_cols + eq_cols]
    
    # Find the position of the first React column to insert new columns
    first_react_pos = dff.columns.get_loc(react_cols[0])
    first_eq_pos = dff.columns.get_loc(eq_cols[0])
    
    # Insert the new columns at appropriate positions
    # Insert Reactant at the position of the first React column
    base_cols.insert(first_react_pos, 'Reactant')
    # Insert C/eq at the position of the first equivalent column, adjusted for the previous insert
    eq_insert_pos = first_eq_pos + 1 if first_eq_pos > first_react_pos else first_eq_pos
    base_cols.insert(eq_insert_pos, 'C/eq')
    
    # Reorder final df
    df_merged = df_merged[base_cols]
    
    return df_merged


# Create a scatter graph
def graph_scatter(df, x_axis, y_axis, colors):
    df = df.dropna(subset=[colors])
    fig = px.scatter(df, x=x_axis, y=y_axis, color=colors, hover_name="Exp code", color_continuous_scale="bluered")
    return fig

# Create a boxplot
def graph_box(df, x_axis, y_axis):
    fig = px.box(df, x=x_axis, y=y_axis)
    return fig

# Create a pie chart
def graph_pie(sheet, values, names):
    data = load_filtered_df_graph(sheet)
    fig = px.pie(data, values=values, names=names)
    return fig

# Create a histogram
def graph_histo(df, column):
    # df["Sub system"] = df["System"]
    # df["System"] = "flow"
    # df.loc[df["Sub system"].str.contains("batch", case=False, na=False), "System"] = "batch"
    fig = px.histogram(df, x=column)
    return fig

# Create a 2D histogram
def graph_2Dhisto(df, column_1, column_2):
    fig = px.density_heatmap(df, x=column_1, y=column_2)
    return fig

def graph_histo_col(df): 
    uniques_count = df.nunique()  # Get number of unique values per column
    fig = px.bar(
        x=uniques_count.index,
        y=uniques_count.values,
        labels={'x': 'Columns', 'y': 'Number of Unique Values'},
    )
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


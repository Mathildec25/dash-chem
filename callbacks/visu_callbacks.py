from dash import callback, Input, Output, State, ctx, dash
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from components.Figures_visualization import (
    load_filtered_df_graph, 
    graph_scatter, 
    graph_box, 
    graph_histo, 
    graph_2Dhisto, 
    graph_histo_col
)
from utils.data_handling import get_column_dropdown_options

# ============================================
# HELPER FUNCTION FOR RANDOM COLUMN SELECTION
# ============================================

def get_random_columns(df, n=2, numeric_only=False, categorical_only=False):
    """Get random columns from dataframe based on type requirements"""
    if df.empty:
        return []
    
    if numeric_only:
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) >= n:
            return np.random.choice(numeric_cols, n, replace=False).tolist()
        return numeric_cols
    
    elif categorical_only:
        # Get categorical columns
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        if len(cat_cols) >= n:
            return np.random.choice(cat_cols, n, replace=False).tolist()
        return cat_cols
    
    else:
        # Get any columns
        all_cols = df.columns.tolist()
        if len(all_cols) >= n:
            return np.random.choice(all_cols, n, replace=False).tolist()
        return all_cols

@callback(
    Output("Scatter_graph", "figure"),
    [Input("url", "pathname"),
     Input("generate-graph-button-scatter", "n_clicks")],
    [State("DD-x-axis-scatter", "value"),
     State("DD-y-axis-scatter", "value"),
     State("DD-colors-scatter", "value"),
     State("DD-size-scatter", "value"),
     State("DD-hover-scatter", "value"),
     State("selected-excel-store", "data"),
     State("selected-sheet-store", "data")]
)
def handle_scatter_update(pathname, n_clicks, x_axis, y_axis, colors, size, hover, excel, sheet):
    """Handle scatter plot updates with robust page-load example and avoid empty columns"""
    triggered = ctx.triggered  # list of triggered entries
    triggered_sources = [t['prop_id'].split('.')[0] for t in triggered] if triggered else []
    # debug: uncomment if you need to inspect triggers
    # print("DEBUG scatter trigger:", triggered, "pathname:", pathname, "sources:", triggered_sources)

    # Normalize pathname and allow trailing slash
    normalized_path = (pathname or "").rstrip('/')

    # Treat as page load when on /visu and either no explicit trigger (first call) or url triggered it
    is_page_load = (normalized_path == "/visu") and (not triggered_sources or "url" in triggered_sources)

    # no data selected -> placeholder
    if not sheet or not excel:
        fig = go.Figure()
        fig.update_layout(title="No data selected - Please select an Excel file and sheet from the Home page", height=400)
        return fig

    try:
        df = load_filtered_df_graph(excel, sheet)

        # helper checks
        def col_has_values(df_, col):
            return col in df_.columns and df_[col].notna().any()

        def numeric_col_has_values(df_, col):
            # try to coerce to numeric and check non-nulls
            if col not in df_.columns:
                return False
            ser = pd.to_numeric(df_[col], errors='coerce')
            return ser.notna().any()

        # ----------------- PAGE LOAD EXAMPLE -----------------
        if is_page_load:
            # get candidate pools then filter to columns that actually have values
            numeric_candidates = [c for c in get_random_columns(df, n=10, numeric_only=True) if numeric_col_has_values(df, c)]
            all_candidates = [c for c in get_random_columns(df, n=20) if col_has_values(df, c)]

            # helper to pick first unused candidate
            def pick_unique(candidates, used):
                for c in candidates:
                    if c and c not in used:
                        used.add(c)
                        return c
                return None

            if len(numeric_candidates) >= 2:
                used = set()
                example_x = pick_unique(numeric_candidates, used) or pick_unique(all_candidates, used)
                example_y = pick_unique([c for c in numeric_candidates if c != example_x], used) or pick_unique(all_candidates, used)

                # color: prefer numeric candidate, then any candidate
                example_color = pick_unique([c for c in numeric_candidates if c not in {example_x, example_y}], used) \
                                or pick_unique(all_candidates, used)

                # size: prefer numeric, else any
                example_size = pick_unique([c for c in numeric_candidates if c not in {example_x, example_y, example_color}], used) \
                               or pick_unique(all_candidates, used)

                # hover: any remaining column with values
                example_hover = pick_unique(all_candidates, used)

                # Final safety: ensure picked columns indeed have values (they should)
                if not (col_has_values(df, example_x) and col_has_values(df, example_y)):
                    fig = go.Figure()
                    fig.update_layout(title="Insufficient non-empty columns for example scatter plot", height=400)
                else:
                    fig = graph_scatter(df, example_x, example_y, example_color, example_size, example_hover)
                    current_title = fig.layout.title.text if fig.layout.title else ""
                    fig.update_layout(
                        title=f"📌 EXAMPLE: {current_title}",
                    )
            else:
                fig = go.Figure()
                fig.update_layout(title="Insufficient numeric columns for example scatter plot", height=400)

        # ----------------- USER-GENERATED PLOT -----------------
        elif triggered and any(t['prop_id'].split('.')[0] == "generate-graph-button-scatter" for t in triggered) \
             and n_clicks and x_axis and y_axis:
            # Validate x and y exist and have values
            if not col_has_values(df, x_axis):
                fig = go.Figure()
                fig.update_layout(title=f"Selected X column '{x_axis}' has no values", height=400)
                return fig
            if not col_has_values(df, y_axis):
                fig = go.Figure()
                fig.update_layout(title=f"Selected Y column '{y_axis}' has no values", height=400)
                return fig

            # Optional columns: only use them if they have values, otherwise set to None
            use_color = colors if (colors and col_has_values(df, colors)) else None
            use_size = size if (size and col_has_values(df, size)) else None
            use_hover = hover if (hover and col_has_values(df, hover)) else None

            # Build and return plot (graph_scatter should accept None for optional args)
            fig = graph_scatter(df, x_axis, y_axis, use_color, use_size, use_hover)

        # ----------------- DEFAULT PLACEHOLDER -----------------
        else:
            fig = go.Figure()
            fig.update_layout(title="Configure the dropdowns above and click 'Generate Scatter Plot'", height=400)

        fig.update_layout(height=500)
        return fig

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(title=f"Error creating plot: {str(e)}", height=400)
        return fig
    
# -------------------------
# BOX PLOT CALLBACK
# -------------------------
@callback(
    Output("Box_graph", "figure"),
    [Input("url", "pathname"),
     Input("generate-graph-button-box", "n_clicks")],
    [State("DD-x-axis-box", "value"),
     State("DD-y-axis-box", "value"),
     State("selected-excel-store", "data"),
     State("selected-sheet-store", "data")]
)
def handle_box_graph(pathname, n_clicks, x_axis, y_axis, excel, sheet):
    """Handle box plot updates with robust example selection and validation of non-empty columns"""
    triggered = ctx.triggered
    triggered_sources = [t["prop_id"].split(".")[0] for t in triggered] if triggered else []
    normalized_path = (pathname or "").rstrip("/")
    is_page_load = (normalized_path == "/visu") and (not triggered_sources or "url" in triggered_sources)

    # placeholders
    empty_placeholder = lambda msg, h=400: (go.Figure().update_layout(title=msg, height=h) or go.Figure())

    if not sheet or not excel:
        fig = go.Figure()
        fig.update_layout(title="No data selected - Please select an Excel file and sheet from the Home page", height=400)
        return fig

    try:
        df = load_filtered_df_graph(excel, sheet)

        # helpers: check columns have non-null values; numeric check coerces to numeric
        def col_has_values(df_, col):
            return col in df_.columns and df_[col].notna().any()

        def numeric_col_has_values(df_, col):
            if col not in df_.columns:
                return False
            ser = pd.to_numeric(df_[col], errors='coerce')
            return ser.notna().any()

        if is_page_load:
            # Prefer categorical + numeric picks with actual values
            cat_candidates = [c for c in get_random_columns(df, n=6, categorical_only=True) if col_has_values(df, c)]
            num_candidates = [c for c in get_random_columns(df, n=6, numeric_only=True) if numeric_col_has_values(df, c)]

            cat_choice = cat_candidates[0] if cat_candidates else None
            num_choice = None
            for nc in num_candidates:
                if nc and nc != cat_choice:
                    num_choice = nc
                    break

            if cat_choice and num_choice:
                fig = graph_box(df, cat_choice, num_choice)
                current_title = fig.layout.title.text if fig.layout.title else ""
                fig.update_layout(
                    title=f"📌 EXAMPLE: {current_title}",
                )
            else:
                # fallback: try any two distinct non-empty columns
                all_candidates = [c for c in get_random_columns(df, n=6) if col_has_values(df, c)]
                if len(all_candidates) >= 2:
                    a, b = all_candidates[0], all_candidates[1]
                    if a != b:
                        fig = graph_box(df, a, b)
                        fig.update_layout(title="📌 EXAMPLE: Box Plot")
                    else:
                        fig = empty_placeholder("Insufficient columns for example box plot")
                else:
                    fig = empty_placeholder("Insufficient columns for example box plot")
        elif triggered and any(t["prop_id"].split(".")[0] == "generate-graph-button-box" for t in triggered) \
             and n_clicks and x_axis and y_axis:
            # Validate selected columns
            if x_axis not in df.columns or y_axis not in df.columns:
                fig = empty_placeholder("Selected columns not found in data")
            elif not col_has_values(df, x_axis):
                fig = empty_placeholder(f"Selected X column '{x_axis}' has no data")
            elif not col_has_values(df, y_axis):
                fig = empty_placeholder(f"Selected Y column '{y_axis}' has no data")
            else:
                fig = graph_box(df, x_axis, y_axis)
        else:
            fig = go.Figure()
            fig.update_layout(title="Configure the dropdowns above and click 'Generate Box Plot'", height=400)

        fig.update_layout(height=500)
        return fig

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(title=f"Error creating plot: {str(e)}", height=400)
        return fig


# -------------------------
# HISTOGRAM CALLBACK
# -------------------------
@callback(
    Output("Histo_graph", "figure"),
    [Input("url", "pathname"),
     Input("generate-graph-button-histo", "n_clicks")],
    [State("DD-col-histo", "value"),
     State("selected-excel-store", "data"),
     State("selected-sheet-store", "data")]
)
def handle_histo_graph(pathname, n_clicks, x_axis, excel, sheet):
    """Handle histogram updates with example selection and validation of non-empty columns"""
    triggered = ctx.triggered
    triggered_sources = [t["prop_id"].split(".")[0] for t in triggered] if triggered else []
    normalized_path = (pathname or "").rstrip("/")
    is_page_load = (normalized_path == "/visu") and (not triggered_sources or "url" in triggered_sources)

    if not sheet or not excel:
        fig = go.Figure()
        fig.update_layout(title="No data selected", height=350, plot_bgcolor="white", paper_bgcolor="white")
        return fig

    try:
        df = load_filtered_df_graph(excel, sheet)

        def col_has_values(df_, col):
            return col in df_.columns and df_[col].notna().any()

        if is_page_load:
            random_cols = [c for c in get_random_columns(df, n=4) if col_has_values(df, c)]
            if random_cols:
                col = random_cols[0]
                fig = graph_histo(df, col)
                current_title = fig.layout.title.text if fig.layout.title else ""
                fig.update_layout(title=f"📌 EXAMPLE: {current_title}")
            else:
                fig = go.Figure()
                fig.update_layout(title="No columns available for histogram", height=350)
        elif triggered and any(t["prop_id"].split(".")[0] == "generate-graph-button-histo" for t in triggered) \
             and n_clicks and x_axis:
            # Validate selected column
            if x_axis not in df.columns:
                fig = go.Figure(); fig.update_layout(title="Selected column not found in data", height=350)
            elif not col_has_values(df, x_axis):
                fig = go.Figure(); fig.update_layout(title=f"Selected column '{x_axis}' has no data", height=350)
            else:
                fig = graph_histo(df, x_axis)
        else:
            fig = go.Figure()
            fig.update_layout(title="Select a column and click 'Generate'", height=350, plot_bgcolor="white", paper_bgcolor="white")

        fig.update_layout(height=350)
        return fig

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(title=f"Error: {str(e)}", height=350)
        return fig


# -------------------------
# 2D HISTOGRAM CALLBACK
# -------------------------
@callback(
    Output("2DHisto_graph", "figure"),
    [Input("url", "pathname"),
     Input("generate-graph-button-2Dhisto", "n_clicks")],
    [State("DD-col1-2Dhisto", "value"),
     State("DD-col2-2Dhisto", "value"),
     State("selected-excel-store", "data"),
     State("selected-sheet-store", "data")]
)
def handle_2Dhisto_graph(pathname, n_clicks, column_1, column_2, excel, sheet):
    """Handle 2D histogram (density_heatmap) updates with example picking and validation"""
    triggered = ctx.triggered
    triggered_sources = [t["prop_id"].split(".")[0] for t in triggered] if triggered else []
    normalized_path = (pathname or "").rstrip("/")
    is_page_load = (normalized_path == "/visu") and (not triggered_sources or "url" in triggered_sources)

    if not sheet or not excel:
        fig = go.Figure()
        fig.update_layout(title="No data selected", height=350, plot_bgcolor="white", paper_bgcolor="white")
        return fig

    try:
        df = load_filtered_df_graph(excel, sheet)

        def col_has_values(df_, col):
            return col in df_.columns and df_[col].notna().any()

        if is_page_load:
            random_cols = [c for c in get_random_columns(df, n=6) if col_has_values(df, c)]
            if len(random_cols) >= 2:
                # pick two distinct non-empty columns
                a = random_cols[0]
                b = None
                for c in random_cols[1:]:
                    if c != a:
                        b = c
                        break
                if b:
                    fig = graph_2Dhisto(df, a, b)
                    current_title = fig.layout.title.text if fig.layout.title else ""
                    fig.update_layout(title=f"📌 EXAMPLE: {current_title}")
                else:
                    fig = go.Figure(); fig.update_layout(title="Insufficient distinct non-empty columns", height=350)
            else:
                fig = go.Figure(); fig.update_layout(title="Insufficient columns for 2D histogram", height=350)
        elif triggered and any(t["prop_id"].split(".")[0] == "generate-graph-button-2Dhisto" for t in triggered) \
             and n_clicks and column_1 and column_2:
            # Validate user selections
            if column_1 not in df.columns or column_2 not in df.columns:
                fig = go.Figure(); fig.update_layout(title="Selected columns not found in data", height=350)
            elif column_1 == column_2:
                fig = go.Figure(); fig.update_layout(title="Please select two different columns", height=350)
            else:
                df_plot = df.loc[:, [c for c in (column_1, column_2) if c in df.columns]].dropna(subset=[column_1, column_2])
                if df_plot.empty:
                    fig = go.Figure(); fig.update_layout(title="No rows with both selected columns present", height=350)
                else:
                    fig = graph_2Dhisto(df, column_1, column_2)
        else:
            fig = go.Figure(); fig.update_layout(title="Select two columns and click 'Generate'", height=350)

        fig.update_layout(height=350)
        return fig

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(title=f"Error: {str(e)}", height=350)
        return fig
    

# ============================================
# BAR GRAPH (DATA OVERVIEW) CALLBACK
# ============================================

@callback(
    Output("Bar_graph", "figure"),
    Input("url", "pathname"),
    [State("selected-excel-store", "data"),
     State("selected-sheet-store", "data")]
)
def handle_bar_graph(pathname, excel, sheet):
    """Generate bar graph showing unique values per column"""
    
    if pathname != "/visu":
        return dash.no_update
    
    if not sheet or not excel:
        fig = px.bar(title="No data selected - Please select an Excel file and sheet")
        fig.update_layout(height=400)
        return fig
    
    try:
        df = load_filtered_df_graph(excel, sheet)
        fig = graph_histo_col(df)
        fig.update_layout(height=400)
        return fig
    except Exception as e:
        fig = px.bar(title=f"Error creating overview: {str(e)}")
        fig.update_layout(height=400)
        return fig

# ============================================
# DROPDOWN OPTIONS CALLBACK
# ============================================

@callback(
    [Output("DD-x-axis-scatter", "options"),
     Output("DD-y-axis-scatter", "options"),
     Output("DD-colors-scatter", "options"),
     Output("DD-size-scatter", "options"),
     Output("DD-hover-scatter", "options"),
     Output("DD-x-axis-box", "options"),
     Output("DD-y-axis-box", "options"),
     Output("DD-col-histo", "options"),
     Output("DD-col1-2Dhisto", "options"),
     Output("DD-col2-2Dhisto", "options")],
    [Input("url", "pathname"),
     Input("selected-sheet-store", "data")],
    State("selected-excel-store", "data")
)
def fill_dropdowns(pathname, sheet, excel):
    """Fill all dropdowns with column options when page loads or sheet changes"""
    
    # Only update on visu page or when sheet changes
    if pathname != "/visu" and ctx.triggered_id != "selected-sheet-store":
        return dash.no_update
    
    if not sheet or not excel:
        empty_options = []
        return (empty_options,) * 10
    
    try:
        df = load_filtered_df_graph(excel, sheet)
        options = get_column_dropdown_options(df)
        
        # Add helpful prefixes to options for better UX
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        enhanced_options = []
        for opt in options:
            col_name = opt['value']
            if col_name in numeric_cols:
                enhanced_options.append({
                    'label': f"📊 {col_name} (numeric)",
                    'value': col_name
                })
            elif col_name in cat_cols:
                enhanced_options.append({
                    'label': f"📝 {col_name} (text)",
                    'value': col_name
                })
            else:
                enhanced_options.append(opt)
        
        return (enhanced_options,) * 10
        
    except Exception as e:
        print(f"Error filling dropdowns: {e}")
        empty_options = []
        return (empty_options,) * 10


# # Return the pie chart graph
# @callback(
#     Output("Pie_graph", "figure"),
#     Input("generate-graph-button-pie", "n_clicks"),
#     State("DD-values-pie", "value"),
#     State("DD-names-pie", "value"),
#     State("selected-sheet-store", "data"),
#     prevent_initial_call=True
# )
# def update_pie_graph(n_clicks, values, names, sheet):
#     if n_clicks > 0 and sheet:
#         return graph_pie(sheet, values, names)
#     return no_update


# # Return the contour graph
# @callback(
#     Output("Contour_graph", "figure"),
#     Input("generate-graph-button-contour", "n_clicks"),
#     State("DD-x-axis-contour", "value"),
#     State("DD-y-axis-contour", "value"),
#     State("DD-z-axis-contour", "value"),
#     State("DD-filtre-col-contour", "value"),
#     State("DD-filtre-val-contour", "value"),
#     State("selected-sheet-store", "data"),
#     prevent_initial_call=True
# )
# def update_contour_graph(n_clicks, x_axis, y_axis, z_axis, col_filtre, val_filtre, sheet):
#     if n_clicks > 0 and sheet:
#         return graph_contour(sheet, col_filtre, val_filtre, y_axis, x_axis, z_axis)
#     return no_update

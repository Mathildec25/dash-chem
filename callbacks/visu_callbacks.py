from dash import callback, Input, Output, State, no_update, ctx
import plotly.express as px
from components.Figures import load_filtered_df_graph, graph_scatter, graph_box, graph_pie, graph_histo, graph_2Dhisto, graph_histo_col, graph_contour
from utils.data_handling import load_filtered_df, get_columns, get_column_dropdown_options

###CALLBACKS TO GENERATE GRAPHS ### (visualization part)

from dash import callback, Output, Input, State, ctx
import plotly.express as px
import dash.exceptions as exceptions

@callback(
    Output("Scatter_graph", "figure"),
    Input("url", "pathname"),
    Input("generate-graph-button-scatter", "n_clicks"),
    State("DD-x-axis-scatter", "value"),
    State("DD-y-axis-scatter", "value"),
    State("DD-colors-scatter", "value"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True,
)
def handle_scatter_update(pathname, n_clicks, x_axis, y_axis, colors, sheet):
    triggered_id = ctx.triggered_id

    if not sheet:
        return px.scatter(title="No sheet selected")

    if triggered_id == "url":
        if pathname != "/visu":
            raise exceptions.PreventUpdate

        df = load_filtered_df_graph(sheet)
        if all(col in df.columns for col in ["Solvent", "T (°C)", "Conversion"]):
            return graph_scatter(df, "Solvent", "T (°C)", "Conversion")
        else:
            return px.scatter(title="Required columns not found")

    elif triggered_id == "generate-graph-button-scatter":
        if n_clicks and x_axis and y_axis and colors:
            df = load_filtered_df_graph(sheet)
            return graph_scatter(df, x_axis, y_axis, colors)
        else:
            return px.scatter(title="Incomplete axis selection")

    raise exceptions.PreventUpdate

@callback(
    Output("Box_graph", "figure"),
    Input("url", "pathname"),
    Input("generate-graph-button-box", "n_clicks"),
    State("DD-x-axis-box", "value"),
    State("DD-y-axis-box", "value"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True,
)
def handle_box_graph(pathname, n_clicks, x_axis, y_axis, sheet):
    triggered_id = ctx.triggered_id

    if not sheet:
        return px.scatter(title="No sheet selected")

    if triggered_id == "url":
        if pathname != "/visu":
            raise exceptions.PreventUpdate

        df = load_filtered_df_graph(sheet)
        if all(col in df.columns for col in ["Solvent", "Conversion"]):
            return graph_box(df, "Solvent", "Conversion")
        else:
            return px.scatter(title="Required columns not found")

    elif triggered_id == "generate-graph-button-box":
        if n_clicks and x_axis and y_axis:
            df = load_filtered_df_graph(sheet)
            return graph_box(df, x_axis, y_axis)
        else:
            return px.scatter(title="Incomplete axis selection")

    raise exceptions.PreventUpdate

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

@callback(
    Output("Histo_graph", "figure"),
    Input("url", "pathname"),
    Input("generate-graph-button-histo", "n_clicks"),
    State("DD-col-histo", "value"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True,
)
def handle_histo_graph(pathname, n_clicks, x_axis, sheet):
    triggered_id = ctx.triggered_id

    if not sheet:
        return px.scatter(title="No sheet selected")

    if triggered_id == "url":
        if pathname != "/visu":
            raise exceptions.PreventUpdate

        df = load_filtered_df_graph(sheet)
        if all(col in df.columns for col in ["Solvent"]):
            return graph_histo(df, "Solvent")
        else:
            return px.scatter(title="Required columns not found")

    elif triggered_id == "generate-graph-button-box":
        if n_clicks and x_axis:
            df = load_filtered_df_graph(sheet)
            return graph_histo(df, x_axis)
        else:
            return px.scatter(title="Incomplete axis selection")

    raise exceptions.PreventUpdate

@callback(
    Output("2DHisto_graph", "figure"),
    Input("url", "pathname"),
    Input("generate-graph-button-2Dhisto", "n_clicks"),
    State("DD-col1-2Dhisto", "value"),
    State("DD-col2-2Dhisto", "value"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True,
)
def handle_2Dhisto_graph(pathname, n_clicks, column_1, column_2, sheet):
    triggered_id = ctx.triggered_id

    if not sheet:
        return px.scatter(title="No sheet selected")

    if triggered_id == "url":
        if pathname != "/visu":
            raise exceptions.PreventUpdate

        df = load_filtered_df_graph(sheet)
        if all(col in df.columns for col in ["Solvent", "Conversion"]):
            return graph_2Dhisto(df, "Solvent", "Conversion")
        else:
            return px.scatter(title="Required columns not found")

    elif triggered_id == "generate-graph-button-box":
        if n_clicks and column_1 and column_2:
            df = load_filtered_df_graph(sheet)
            return graph_2Dhisto(df, column_1, column_2)
        else:
            return px.scatter(title="Incomplete axis selection")

    raise exceptions.PreventUpdate

@callback(
    Output("Bar_graph", "figure"),
    Input("url", "pathname"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True,
)
def handle_bar_graph(pathname, sheet):
    if not sheet:
        return px.scatter(title="No sheet selected")

    if pathname != "/visu":
        raise exceptions.PreventUpdate

    df = load_filtered_df_graph(sheet)
    return graph_histo_col(df)



# Return options for all dropdowns in the visualization part of the dashboard
@callback(
    [Output("DD-x-axis-scatter", "options"),
     Output("DD-y-axis-scatter", "options"),
     Output("DD-colors-scatter", "options"),
     Output("DD-x-axis-box", "options"),
     Output("DD-y-axis-box", "options"),
     Output("DD-col-histo", "options"),
     Output("DD-col1-2Dhisto", "options"),
     Output("DD-col2-2Dhisto", "options"),],
    Input("selected-sheet-store", "data")
)
def fill_dropdowns(sheet):
    if not sheet:
        return [], [], [], [], [], [], [], [], 

    df = load_filtered_df_graph(sheet)

    options = get_column_dropdown_options(df)
    return  options, options, options, options, options, options, options, options

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

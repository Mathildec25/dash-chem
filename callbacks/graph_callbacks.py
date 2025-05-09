from dash import callback, Input, Output, State, no_update
from components.Figures import graph_scatter, graph_box, graph_pie, graph_histo, graph_2Dhisto, graph_contour

###CALLBACKS TO GENERATE GRAPHS ### (visualization part)

# Return the scatter graph
@callback(
    Output("Scatter_graph", "figure"),
    Input("generate-graph-button-scatter", "n_clicks"),
    State("DD-x-axis-scatter", "value"),
    State("DD-y-axis-scatter", "value"),
    State("DD-colors-scatter", "value"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True
)
def update_scatter_graph(n_clicks, x_axis, y_axis, colors, sheet):
    if n_clicks > 0 and sheet:
        return graph_scatter(sheet, x_axis, y_axis, colors)
    return no_update

# Return the boxplot graph
@callback(
    Output("Box_graph", "figure"),
    Input("generate-graph-button-box", "n_clicks"),
    State("DD-x-axis-box", "value"),
    State("DD-y-axis-box", "value"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True
)
def update_box_graph(n_clicks, x_axis, y_axis, sheet):
    if n_clicks > 0 and sheet:
        return graph_box(sheet, x_axis, y_axis)
    return no_update

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

# Return the 1D histogram graph
@callback(
    Output("Histo_graph", "figure"),
    Input("generate-graph-button-histo", "n_clicks"),
    State("DD-col-histo", "value"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True
)
def update_histo_graph(n_clicks, column, sheet):
    if n_clicks > 0 and sheet:
        return graph_histo(sheet, column)
    return no_update

# Return the 2D histogram graph
@callback(
    Output("2DHisto_graph", "figure"),
    Input("generate-graph-button-2Dhisto", "n_clicks"),
    State("DD-col1-2Dhisto", "value"),
    State("DD-col2-2Dhisto", "value"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True
)
def update_2Dhisto_graph(n_clicks, column_1, column_2, sheet):
    if n_clicks > 0 and sheet:
        return graph_2Dhisto(sheet, column_1, column_2)
    return no_update

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

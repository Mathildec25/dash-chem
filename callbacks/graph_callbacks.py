from dash import callback, Input, Output, State, no_update
from components.Figures import graph_scatter, graph_pie

@callback(
    Output("Scatter_graph", "figure"),
    Input("generate-graph-button-scatter", "n_clicks"),
    State("DD-x-axis-scatter", "value"),
    State("DD-y-axis-scatter", "value"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True
)
def update_scatter_graph(n_clicks, x_axis, y_axis, sheet):
    if n_clicks > 0 and sheet:
        return graph_scatter(sheet, x_axis, y_axis)
    return no_update

@callback(
    Output("Pie_graph", "figure"),
    Input("generate-graph-button-pie", "n_clicks"),
    State("DD-x-axis-pie", "value"),
    State("DD-y-axis-pie", "value"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True
)
def update_pie_graph(n_clicks, x_axis, y_axis, sheet):
    if n_clicks > 0 and sheet:
        return graph_pie(sheet, x_axis, y_axis)
    return no_update

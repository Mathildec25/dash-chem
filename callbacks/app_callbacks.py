import dash
from dash import Input, Output, State, MATCH, ALL, ctx

# Define and return callbacks for the gloabl app (general layout)
def register_app_callbacks(app):

    # Return in the store the selected sheet name to be later shared with other python files/pages
    @app.callback(
    Output("selected-excel-store", "data"),
    Output("selected-sheet-store", "data"),
    Input({'type': 'sheet-dropdown', 'index': ALL}, 'value')
)
    def store_selected_sheet(selected_values):
        triggered = ctx.triggered_id
        if triggered is None:
            return dash.no_update

        return triggered["index"], selected_values[0] 
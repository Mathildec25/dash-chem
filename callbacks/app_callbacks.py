from dash import Input, Output, State

# Define and return callbacks for the gloabl app (general layout)
def register_app_callbacks(app):

    # Return in the store the selected sheet name to be later shared with other python files/pages
    @app.callback(
        Output("selected-sheet-store", "data"),
        Input("sheet-dropdown", "value")
    )
    def store_selected_sheet(selected):
        return selected

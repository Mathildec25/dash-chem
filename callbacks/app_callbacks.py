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

    # Hide/Show the sidebar when the button is clicked
    @app.callback(
        [Output("collapse-sidebar", "is_open"),
         Output("main-row", "style")],
        Input("toggle-btn", "n_clicks"),
        State("collapse-sidebar", "is_open"),
        prevent_initial_call=True
    )
    def toggle_sidebar(n_clicks, is_open):
        if n_clicks:
            new_is_open = not is_open
            new_margin_right = "0rem" if not new_is_open else "12rem"
            return new_is_open, {
                "display": "flex",
                "flex-wrap": "nowrap",
                "height": "100vh",
                "margin-right": new_margin_right
            }
        return is_open, {
            "display": "flex",
            "flex-wrap": "nowrap",
            "height": "100vh",
            "margin-right": "12rem"
        }

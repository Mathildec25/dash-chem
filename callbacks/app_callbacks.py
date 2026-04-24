"""Global callbacks registered from ``app.py``."""

import dash
from dash import ALL, Input, Output, ctx


def register_app_callbacks(app):
    """Register callbacks that live outside any specific page."""

    @app.callback(
        Output("selected-excel-store", "data"),
        Output("selected-sheet-store", "data"),
        Input({"type": "sheet-dropdown", "index": ALL}, "value"),
    )
    def store_selected_sheet(selected_values):
        triggered = ctx.triggered_id
        if triggered is None:
            return dash.no_update
        return triggered["index"], selected_values[0]

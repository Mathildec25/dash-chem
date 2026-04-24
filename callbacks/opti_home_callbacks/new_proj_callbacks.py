"""Callbacks for the 'new project' section of the home page."""

import dash
from dash import Input, Output, State, callback


@callback(
    [Output("selected-file-store", "data", allow_duplicate=True),
     Output("current-excel-file", "data", allow_duplicate=True),
     Output("current-domain", "data", allow_duplicate=True),
     Output("parameter-store", "data", allow_duplicate=True),
     Output("objective-store", "data", allow_duplicate=True),
     Output("extra-columns-store", "data", allow_duplicate=True),
     Output("constraints-store", "data", allow_duplicate=True)],
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def reset_stores_on_home(pathname):
    """Clear every project-related store when the user lands on the home page."""
    if pathname in ("/", "/Opt-home"):
        return None, None, None, None, None, None, None
    return (dash.no_update,) * 7


@callback(
    Output("start-opti-button", "style"),
    Input("new-proj", "value"),
    prevent_initial_call=True,
)
def toggle_go_button(project_name):
    """Show the GO button once the user has typed a project name."""
    visible = bool(project_name and project_name.strip())
    return {"marginTop": "12px", "display": "inline-block" if visible else "none"}


@callback(
    Output("project-name-store", "data"),
    Output("url", "pathname"),
    Input("start-opti-button", "n_clicks"),
    State("new-proj", "value"),
    prevent_initial_call=True,
)
def handle_go_button_click(n_clicks, project_name):
    """Store the project name and navigate to the parameterization page."""
    if n_clicks and project_name and project_name.strip():
        return project_name.strip(), "/Opt-param"
    return dash.no_update, dash.no_update

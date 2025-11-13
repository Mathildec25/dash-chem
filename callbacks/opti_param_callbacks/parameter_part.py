# Add these to callbacks/opti_param_callbacks/parameter_part.py

import dash
from dash import callback, Input, Output, State, MATCH, ALL, html, dcc, ctx, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid

# COMPACT: Add parameter callback
@callback(
    Output("parameter-container", "children", allow_duplicate=True),
    Input("add-para-button", "n_clicks"),
    State("parameter-container", "children"),
    prevent_initial_call=True
)
def add_new_parameter_compact(n_clicks, current_children):
    """Add new parameter row - compact version"""
    if not n_clicks:
        raise PreventUpdate

    new_id = str(uuid.uuid4())

    new_row = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Input(
                    id={'type': 'parameter-name', 'index': new_id},
                    placeholder="Parameter name",
                    size="sm",
                    style={"borderRadius": "6px"}
                )
            ], width=4),
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'parameter-type', 'index': new_id},
                    options=[
                        {"label": "Continuous", "value": "float"},
                        {"label": "Discrete", "value": "int"},
                        {"label": "Categorical", "value": "cat"},
                    ],
                    value="float",
                    placeholder="Type",
                    clearable=False,
                    style={"fontSize": "0.875rem"}
                )
            ], width=3, style={"paddingLeft": "0.25rem", "paddingRight": "0.25rem"}),
            dbc.Col([
                dbc.Input(
                    id={'type': 'parameter-type-specific-lower', 'index': new_id},
                    placeholder="Min",
                    type="number",
                    step="any",
                    size="sm",
                    style={"borderRadius": "6px"}
                )
            ], width=2, style={"paddingLeft": "0.25rem", "paddingRight": "0.25rem"}),
            dbc.Col([
                dbc.Input(
                    id={'type': 'parameter-type-specific-upper', 'index': new_id},
                    placeholder="Max",
                    type="number",
                    step="any",
                    size="sm",
                    style={"borderRadius": "6px"}
                )
            ], width=2, style={"paddingLeft": "0.25rem", "paddingRight": "0.25rem"}),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-parameter', 'index': new_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=1, style={"paddingLeft": "0.25rem"}),
        ], className="mb-2 align-items-center"),
        # Hidden divs for compatibility
        html.Div(id={'type': 'parameter-type-container', 'index': new_id}, style={"display": "none"}),
        html.Div(id={'type': 'parameter-type-specific-container', 'index': new_id}, style={"display": "none"}),
        html.Div(id={'type': 'parameter-block', 'index': new_id}, style={"display": "none"}),
    ])

    return current_children + [new_row]


# COMPACT: Add objective callback
@callback(
    Output("objective-container", "children", allow_duplicate=True),
    Input("add-objective-button", "n_clicks"),
    State("objective-container", "children"),
    prevent_initial_call=True
)
def add_new_objective_compact(n_clicks, current_children):
    """Add new objective row - compact version"""
    if not n_clicks:
        raise PreventUpdate

    new_id = str(uuid.uuid4())

    new_row = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Input(
                    id={'type': 'objective-name', 'index': new_id},
                    placeholder="Objective name",
                    size="sm",
                    style={"borderRadius": "6px"}
                )
            ], width=4),
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'objective-direction', 'index': new_id},
                    options=[
                        {"label": "Minimize", "value": "min"},
                        {"label": "Maximize", "value": "max"}
                    ],
                    placeholder="Direction",
                    clearable=False,
                    style={"fontSize": "0.875rem"}
                )
            ], width=3, style={"paddingLeft": "0.25rem", "paddingRight": "0.25rem"}),
            dbc.Col([
                dbc.Input(
                    id={'type': 'objective-lower-bound', 'index': new_id},
                    placeholder="Min",
                    type="number",
                    step="any",
                    size="sm",
                    style={"borderRadius": "6px"}
                )
            ], width=2, style={"paddingLeft": "0.25rem", "paddingRight": "0.25rem"}),
            dbc.Col([
                dbc.Input(
                    id={'type': 'objective-upper-bound', 'index': new_id},
                    placeholder="Max",
                    type="number",
                    step="any",
                    size="sm",
                    style={"borderRadius": "6px"}
                )
            ], width=2, style={"paddingLeft": "0.25rem", "paddingRight": "0.25rem"}),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-objective-btn', 'index': new_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=1, style={"paddingLeft": "0.25rem"}),
        ], className="mb-2 align-items-center"),
        # Hidden divs for compatibility
        html.Div(id={'type': 'objective-direction-container', 'index': new_id}, style={"display": "none"}),
        html.Div(id={'type': 'objective-bounds-container', 'index': new_id}, style={"display": "none"}),
        html.Div(id={'type': 'objective-block', 'index': new_id}, style={"display": "none"}),
    ])

    return current_children + [new_row]


# Toggle extra columns
@callback(
    [Output("extra-columns-collapse", "is_open", allow_duplicate=True),
     Output("toggle-extra-columns", "children", allow_duplicate=True)],
    Input("toggle-extra-columns", "n_clicks"),
    State("extra-columns-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_extra_columns(n_clicks, is_open):
    """Toggle the extra columns section"""
    if n_clicks:
        new_state = not is_open
        button_text = [
            html.I(className="bi bi-dash-square me-2" if new_state else "bi bi-plus-square me-2"),
            "Hide Extra Columns" if new_state else "Add Extra Columns (Optional)"
        ]
        return new_state, button_text
    return is_open, no_update


# Callback to handle domain creation and redirect
@callback(
    Output('redirect-to-opti-run', 'href', allow_duplicate=True),
    Input('create-domain-btn', 'n_clicks'),
    [State({'type': 'parameter-name', 'index': ALL}, 'value'),
     State({'type': 'parameter-type', 'index': ALL}, 'value'),
     State({'type': 'parameter-type-specific-lower', 'index': ALL}, 'value'),
     State({'type': 'parameter-type-specific-upper', 'index': ALL}, 'value'),
     State({'type': 'objective-name', 'index': ALL}, 'value'),
     State({'type': 'objective-direction', 'index': ALL}, 'value'),
     State('starting-sampling-DD', 'value'),
     State('nb-sampling-points', 'value')],
    prevent_initial_call=True
)
def create_domain_and_redirect(n_clicks, param_names, param_types, param_lowers, param_uppers,
                                obj_names, obj_directions, sampling_method, num_samples):
    """Create domain and redirect to optimization run page"""
    if not n_clicks:
        raise PreventUpdate
    
    # Validate inputs
    if not param_names or not any(param_names):
        return no_update
    
    if not obj_names or not any(obj_names):
        return no_update
    
    # Here you would normally save the domain configuration
    # This callback should call the same logic as your existing domain creation callback
    # For now, just redirect
    return '/Opt-run'
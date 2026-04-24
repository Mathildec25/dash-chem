"""
Parameter configuration callbacks - ALL add/delete operations
NO DUPLICATE OUTPUTS - each output appears only once
"""

from dash import callback, Input, Output, State, MATCH, ALL, html, dcc, ctx, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid

from components.forms import make_objective_row
# ===== PARAMETERS =====

@callback(
    Output("parameter-container", "children"),
    [Input("add-para-button", "n_clicks"),
     Input({'type': 'delete-parameter', 'index': ALL}, 'n_clicks')],
    State("parameter-container", "children"),
    prevent_initial_call=True
)
def manage_parameters(add_clicks, delete_clicks, current_children):
    """Handle both add and delete for parameters"""
    triggered = ctx.triggered_id
    
    if triggered == "add-para-button":
        # ADD new parameter
        if not add_clicks:
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
                ], width=3),
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
                ], width=2),
                dbc.Col([
                    html.Div(id={'type': 'parameter-inputs', 'index': new_id}, children=[
                        dbc.Row([
                            dbc.Col([
                                dbc.Input(
                                    id={'type': 'parameter-min', 'index': new_id},
                                    placeholder="Min",
                                    type="number",
                                    step="any",
                                    size="sm",
                                    style={"borderRadius": "6px"}
                                )
                            ], width=4),
                            dbc.Col([
                                dbc.Input(
                                    id={'type': 'parameter-max', 'index': new_id},
                                    placeholder="Max",
                                    type="number",
                                    step="any",
                                    size="sm",
                                    style={"borderRadius": "6px"}
                                )
                            ], width=4),
                            dbc.Col([
                                dbc.Input(
                                    id={'type': 'parameter-step', 'index': new_id},
                                    placeholder="Step (opt)",
                                    type="number",
                                    step="any",
                                    min=0.001,
                                    size="sm",
                                    style={"borderRadius": "6px"}
                                )
                            ], width=4),
                        ])
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Button(
                        html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                        id={'type': 'delete-parameter', 'index': new_id},
                        color="danger",
                        outline=True,
                        size="sm",
                        style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                    )
                ], width=1),
            ], className="mb-2 align-items-center"),
        ], id={'type': 'parameter-row', 'index': new_id})
        
        return current_children + [new_row]
    
    elif isinstance(triggered, dict) and triggered.get('type') == 'delete-parameter':
        # DELETE parameter
        if not any(delete_clicks):
            raise PreventUpdate
        
        index_to_delete = triggered['index']
        new_children = []
        for child in current_children:
            try:
                if child['props']['id']['index'] != index_to_delete:
                    new_children.append(child)
            except:
                new_children.append(child)
        
        return new_children
    
    raise PreventUpdate


# Update parameter inputs based on type
@callback(
    Output({'type': 'parameter-inputs', 'index': MATCH}, 'children'),
    Input({'type': 'parameter-type', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def update_parameter_inputs(param_type):
    """Show appropriate inputs based on parameter type"""
    idx = ctx.triggered_id['index']
    
    if param_type == 'float':
        # Continuous: Min, Max, and Step (for discretization)
        return dbc.Row([
            dbc.Col([
                dbc.Input(
                    id={'type': 'parameter-min', 'index': idx},
                    placeholder="Min",
                    type="number",
                    step="any",
                    size="sm",
                    style={"borderRadius": "6px"}
                )
            ], width=4),
            dbc.Col([
                dbc.Input(
                    id={'type': 'parameter-max', 'index': idx},
                    placeholder="Max",
                    type="number",
                    step="any",
                    size="sm",
                    style={"borderRadius": "6px"}
                )
            ], width=4),
            dbc.Col([
                dbc.Input(
                    id={'type': 'parameter-step', 'index': idx},
                    placeholder="Step (opt)",
                    type="number",
                    step="any",
                    min=0.001,
                    size="sm",
                    style={"borderRadius": "6px"}
                )
            ], width=4),
        ])

    
    elif param_type == 'int' or param_type == 'cat':
        # Discrete or Categorical: comma-separated values
        placeholder = "Values (comma-separated): 1, 2, 3, 4, 5" if param_type == 'int' else "Values (comma-separated): A, B, C"
        return dbc.Input(
            id={'type': 'parameter-categories', 'index': idx},
            placeholder=placeholder,
            type="text",
            size="sm",
            style={"borderRadius": "6px"}
        )
    
    return html.Div()


# ===== OBJECTIVES =====

@callback(
    Output("objective-container", "children"),
    [Input("add-objective-button", "n_clicks"),
     Input({'type': 'delete-objective', 'index': ALL}, 'n_clicks')],
    State("objective-container", "children"),
    prevent_initial_call=True
)
def manage_objectives(add_clicks, delete_clicks, current_children):
    """Handle both add and delete for objectives"""
    triggered = ctx.triggered_id
    
    if triggered == "add-objective-button":
        if not add_clicks:
            raise PreventUpdate
        new_id = str(uuid.uuid4())
        return current_children + [make_objective_row(new_id)]
    
    elif isinstance(triggered, dict) and triggered.get('type') == 'delete-objective':
        # DELETE objective
        if not any(delete_clicks):
            raise PreventUpdate
        
        index_to_delete = triggered['index']
        new_children = []
        for child in current_children:
            try:
                if child['props']['id']['index'] != index_to_delete:
                    new_children.append(child)
            except:
                new_children.append(child)
        
        return new_children
    
    raise PreventUpdate


# ===== EXTRA COLUMNS =====

@callback(
    [Output("extra-columns-collapse", "is_open"),
     Output("toggle-extra-columns", "children")],
    Input("toggle-extra-columns", "n_clicks"),
    State("extra-columns-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_extra_columns(n_clicks, is_open):
    """Toggle extra columns section visibility"""
    if n_clicks:
        new_state = not is_open
        button_text = [
            html.I(className="bi bi-dash-square me-2" if new_state else "bi bi-plus-square me-2"),
            "Hide Extra Columns" if new_state else "Add Extra Columns (Optional)"
        ]
        return new_state, button_text
    return is_open, no_update


@callback(
    Output("extra-column-container", "children"),
    [Input("add-extra-column-button", "n_clicks"),
     Input({'type': 'delete-extra-column', 'index': ALL}, 'n_clicks')],
    State("extra-column-container", "children"),
    prevent_initial_call=True
)
def manage_extra_columns(add_clicks, delete_clicks, current_children):
    """Handle both add and delete for extra columns"""
    triggered = ctx.triggered_id
    
    if triggered == "add-extra-column-button":
        # ADD new extra column
        if not add_clicks:
            raise PreventUpdate
        
        new_id = str(uuid.uuid4())
        new_row = html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Input(
                        id={'type': 'extra-column-name', 'index': new_id},
                        placeholder="Column name",
                        size="sm",
                        style={"borderRadius": "6px"}
                    )
                ], width=10),
                dbc.Col([
                    dbc.Button(
                        "✕",
                        id={'type': 'delete-extra-column', 'index': new_id},
                        color="danger",
                        outline=True,
                        size="sm",
                        style={"borderRadius": "6px"}
                    )
                ], width=2),
            ], className="mb-2 align-items-center"),
        ], id={'type': 'extra-column-row', 'index': new_id})
        
        return current_children + [new_row]
    
    elif isinstance(triggered, dict) and triggered.get('type') == 'delete-extra-column':
        # DELETE extra column
        if not any(delete_clicks):
            raise PreventUpdate
        
        index_to_delete = triggered['index']
        new_children = []
        for child in current_children:
            try:
                if child['props']['id']['index'] != index_to_delete:
                    new_children.append(child)
            except:
                new_children.append(child)
        
        return new_children
    
    raise PreventUpdate
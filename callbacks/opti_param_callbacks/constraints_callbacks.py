"""
Constraints configuration callbacks
Handles constraints related to solvent boiling points

DYNAMIC CONSTRAINT: Temperature adapts to the suggested solvent's boiling point
- Methanol suggested → Temperature < 64.7°C
- Ethanol suggested → Temperature < 78.4°C
"""

from dash import callback, Input, Output, State, ALL, ctx, html, dcc, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid

from utils.descriptor_data import SOLVENT_DESCRIPTORS


def get_solvent_boiling_point(solvent_name: str) -> float:
    """Get boiling point for a specific solvent."""
    if solvent_name in SOLVENT_DESCRIPTORS:
        return SOLVENT_DESCRIPTORS[solvent_name].get('Boiling point')
    return None


def get_min_boiling_point(solvents: list) -> float:
    """Get the minimum boiling point from selected solvents."""
    boiling_points = []
    for solvent in solvents:
        bp = get_solvent_boiling_point(solvent)
        if bp is not None:
            boiling_points.append(bp)
    return min(boiling_points) if boiling_points else None


def get_boiling_points_dict(solvents: list) -> dict:
    """Get dictionary of solvent -> boiling point for all selected solvents."""
    bp_dict = {}
    for solvent in solvents:
        bp = get_solvent_boiling_point(solvent)
        if bp is not None:
            bp_dict[solvent] = bp
    return bp_dict


def get_boiling_points_info(solvents: list) -> list:
    """Get boiling point information for display."""
    info = []
    for solvent in solvents:
        bp = get_solvent_boiling_point(solvent)
        if bp is not None:
            info.append((solvent, bp))
    return info


def validate_and_adjust_suggestion(suggestion_row: dict, constraints_config: dict, solvent_param_name: str) -> tuple:
    """
    Validate a BO suggestion against dynamic boiling point constraints.
    Adjusts parameter values if they violate constraints.
    
    Args:
        suggestion_row: Dictionary with suggested parameter values
        constraints_config: Constraint configuration from constraints-store
        solvent_param_name: Name of the solvent parameter (e.g., "Solvent")
    
    Returns:
        Tuple of (adjusted_row, adjustments_made)
        - adjusted_row: Dictionary with corrected values
        - adjustments_made: List of adjustment details for display
    """
    if not constraints_config or not constraints_config.get('constraints'):
        return suggestion_row, []
    
    # Get the suggested solvent
    suggested_solvent = suggestion_row.get(solvent_param_name)
    if not suggested_solvent:
        return suggestion_row, []
    
    # Get boiling point for the suggested solvent
    bp_dict = constraints_config.get('boiling_points', {})
    solvent_bp = bp_dict.get(suggested_solvent)
    
    if solvent_bp is None:
        return suggestion_row, []
    
    # Check and adjust each constrained parameter
    adjusted_row = suggestion_row.copy()
    adjustments_made = []
    
    for constraint in constraints_config.get('constraints', []):
        if constraint['type'] == 'less_than_bp':
            param_name = constraint['parameter_name']
            
            if param_name in adjusted_row:
                current_value = adjusted_row[param_name]
                
                # Check if constraint is violated
                if current_value is not None and current_value >= solvent_bp:
                    # Adjust to just below boiling point (with small margin)
                    margin = 2.0  # 2°C safety margin
                    adjusted_value = round(solvent_bp - margin, 1)
                    adjusted_row[param_name] = adjusted_value
                    adjustments_made.append({
                        'parameter': param_name,
                        'original': round(current_value, 1),
                        'adjusted': adjusted_value,
                        'solvent': suggested_solvent,
                        'boiling_point': solvent_bp
                    })
    
    return adjusted_row, adjustments_made


def create_constraint_row(row_id: str, parameter_options: list = None):
    """Create a single constraint row."""
    if parameter_options is None:
        parameter_options = []
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'constraint-param-select', 'index': row_id},
                    options=parameter_options,
                    placeholder="Select parameter",
                    clearable=True,
                    style={"fontSize": "0.875rem"}
                )
            ], width=5),
            dbc.Col([
                html.Span([
                    "< BP of ",
                    html.Strong("suggested solvent", style={"color": "#6366f1"})
                ], 
                className="text-muted",
                style={"fontSize": "0.875rem", "lineHeight": "38px"})
            ], width=5),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-constraint-row', 'index': row_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=2),
        ], className="mb-2 align-items-center"),
    ], id={'type': 'constraint-row', 'index': row_id})


# ===== SHOW/HIDE CONSTRAINTS CARD =====

@callback(
    Output("constraints-card", "style"),
    Input("solvent-config-store", "data"),
    prevent_initial_call=True
)
def toggle_constraints_card(solvent_config):
    """Show constraints card when solvents are configured"""
    if solvent_config and solvent_config.get('solvents'):
        return {
            "display": "block",
            "borderRadius": "12px",
            "border": "1px solid #e0e0e0",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
            "backgroundColor": "white"
        }
    return {"display": "none"}


# ===== UPDATE BOILING POINT INFO DISPLAY =====

@callback(
    Output("bp-info-display", "children"),
    Input("solvent-config-store", "data"),
    prevent_initial_call=True
)
def update_bp_info(solvent_config):
    """Update the boiling point information display"""
    if not solvent_config or not solvent_config.get('solvents'):
        return ""
    
    solvents = solvent_config.get('solvents', [])
    bp_info = get_boiling_points_info(solvents)
    
    if not bp_info:
        return dbc.Alert(
            "No boiling point data available for selected solvents.",
            color="warning",
            className="mb-2 py-2"
        )
    
    # Create table-like display
    bp_rows = []
    for solvent, bp in sorted(bp_info, key=lambda x: x[1]):
        bp_rows.append(
            html.Tr([
                html.Td(solvent, style={"padding": "0.25rem 0.5rem"}),
                html.Td(f"{bp}°C", style={"padding": "0.25rem 0.5rem", "fontWeight": "600"})
            ])
        )
    
    return html.Div([
        html.Small([
            html.Strong("Boiling points - constraint adapts to suggested solvent:"),
        ], className="text-muted d-block mb-2"),
        html.Table([
            html.Tbody(bp_rows)
        ], className="table table-sm table-borderless mb-0", style={"fontSize": "0.8rem"}),
        html.Div([
            html.I(className="bi bi-info-circle me-1"),
            html.Small("The constraint limit will match the solvent suggested by optimization", 
                      className="text-muted fst-italic")
        ], className="mt-2")
    ], className="mb-3 p-2", style={
        "backgroundColor": "#f8f9fa",
        "borderRadius": "6px",
        "border": "1px solid #e9ecef"
    })


# ===== UPDATE PARAMETER OPTIONS IN CONSTRAINT DROPDOWN =====

@callback(
    Output({'type': 'constraint-param-select', 'index': ALL}, 'options'),
    [Input({'type': 'parameter-name', 'index': ALL}, 'value'),
     Input({'type': 'parameter-type', 'index': ALL}, 'value')],
    [State({'type': 'parameter-name', 'index': ALL}, 'id'),
     State({'type': 'constraint-param-select', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def update_constraint_param_options(param_names, param_types, param_ids, constraint_ids):
    """Update the parameter options in constraint dropdowns"""
    if not param_names or not constraint_ids:
        raise PreventUpdate
    
    options = []
    for i, (name, ptype, pid) in enumerate(zip(param_names, param_types, param_ids)):
        if name and ptype in ['float', 'int']:
            options.append({
                "label": name,
                "value": pid['index']
            })
    
    return [options] * len(constraint_ids)


# ===== ADD CONSTRAINT ROW =====

@callback(
    Output("constraint-rows-container", "children", allow_duplicate=True),
    Input("add-constraint-btn", "n_clicks"),
    [State("constraint-rows-container", "children"),
     State({'type': 'parameter-name', 'index': ALL}, 'value'),
     State({'type': 'parameter-type', 'index': ALL}, 'value'),
     State({'type': 'parameter-name', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def add_constraint_row(n_clicks, current_rows, param_names, param_types, param_ids):
    """Add a new constraint row"""
    if not n_clicks:
        raise PreventUpdate
    
    options = []
    if param_names and param_types and param_ids:
        for name, ptype, pid in zip(param_names, param_types, param_ids):
            if name and ptype in ['float', 'int']:
                options.append({
                    "label": name,
                    "value": pid['index']
                })
    
    new_id = str(uuid.uuid4())
    new_row = create_constraint_row(new_id, options)
    
    if current_rows is None:
        current_rows = []
    
    return current_rows + [new_row]


# ===== DELETE CONSTRAINT ROW =====

@callback(
    Output("constraint-rows-container", "children", allow_duplicate=True),
    Input({'type': 'delete-constraint-row', 'index': ALL}, 'n_clicks'),
    State("constraint-rows-container", "children"),
    prevent_initial_call=True
)
def delete_constraint_row(n_clicks, current_rows):
    """Delete a constraint row"""
    if not any(n_clicks):
        raise PreventUpdate
    
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        raise PreventUpdate
    
    row_to_delete = triggered.get('index')
    
    updated_rows = []
    for row in current_rows:
        row_id = None
        if hasattr(row, 'id') and isinstance(row.id, dict):
            row_id = row.id.get('index')
        
        if row_id != row_to_delete:
            updated_rows.append(row)
    
    return updated_rows


# ===== SAVE CONSTRAINTS TO STORE =====

@callback(
    Output("constraints-store", "data"),
    [Input({'type': 'constraint-param-select', 'index': ALL}, 'value'),
     Input("solvent-config-store", "data")],
    [State({'type': 'constraint-param-select', 'index': ALL}, 'id'),
     State({'type': 'parameter-name', 'index': ALL}, 'value'),
     State({'type': 'parameter-name', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def save_constraints(constraint_values, solvent_config, constraint_ids, param_names, param_ids):
    """
    Save constraint configuration to store.
    
    The store now contains:
    - boiling_points: dict mapping solvent name -> boiling point
    - solvent_param_name: name of the solvent parameter
    - constraints: list of constraint definitions
    
    The actual constraint enforcement happens post-optimization using
    validate_and_adjust_suggestion()
    """
    if not solvent_config:
        return None
    
    solvents = solvent_config.get('solvents', [])
    
    # Get boiling points for ALL solvents (not just minimum)
    bp_dict = get_boiling_points_dict(solvents)
    
    if not bp_dict:
        return None
    
    # Build parameter name lookup
    param_name_lookup = {}
    if param_names and param_ids:
        for name, pid in zip(param_names, param_ids):
            if name:
                param_name_lookup[pid['index']] = name
    
    # Build constraints list
    constraints = []
    if constraint_values and constraint_ids:
        for value, cid in zip(constraint_values, constraint_ids):
            if value:
                param_name = param_name_lookup.get(value)
                if param_name:
                    constraints.append({
                        'id': cid['index'],
                        'type': 'less_than_bp',
                        'parameter_id': value,
                        'parameter_name': param_name,
                        'description': f"{param_name} < BP(solvent)"
                    })
    
    return {
        'boiling_points': bp_dict,  # Dict: solvent -> BP
        'solvents': solvents,
        'solvent_param_id': solvent_config.get('param_id'),
        'constraints': constraints
    }
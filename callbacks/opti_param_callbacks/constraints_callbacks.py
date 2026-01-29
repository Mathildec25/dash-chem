"""
Constraints configuration callbacks
Handles constraints related to solvent boiling points AND melting points

DYNAMIC CONSTRAINTS:
- Temperature < Boiling Point (avoid boiling)
- Temperature > Melting Point (avoid freezing)

The constraint adapts to the suggested solvent:
- Methanol suggested → Temperature < 64.7°C (BP) and > -97.6°C (MP)
- DMSO suggested → Temperature < 189°C (BP) and > 18.5°C (MP) ⚠️
"""

from dash import callback, Input, Output, State, ALL, ctx, html, dcc, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid

from utils.descriptor_data import SOLVENT_DESCRIPTORS


# ============================================================================
# BOILING POINT FUNCTIONS (existing)
# ============================================================================

def get_solvent_boiling_point(solvent_name: str) -> float:
    """Get boiling point for a specific solvent."""
    if solvent_name in SOLVENT_DESCRIPTORS:
        return SOLVENT_DESCRIPTORS[solvent_name].get('bp')
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


# ============================================================================
# MELTING POINT FUNCTIONS (NEW)
# ============================================================================

def get_solvent_melting_point(solvent_name: str) -> float:
    """Get melting point for a specific solvent."""
    if solvent_name in SOLVENT_DESCRIPTORS:
        return SOLVENT_DESCRIPTORS[solvent_name].get('mp')
    return None


def get_max_melting_point(solvents: list) -> float:
    """Get the maximum melting point from selected solvents.
    
    This is the critical value for the lower temperature constraint:
    Temperature must be ABOVE this to ensure all solvents are liquid.
    """
    melting_points = []
    for solvent in solvents:
        mp = get_solvent_melting_point(solvent)
        if mp is not None:
            melting_points.append(mp)
    return max(melting_points) if melting_points else None


def get_melting_points_dict(solvents: list) -> dict:
    """Get dictionary of solvent -> melting point for all selected solvents."""
    mp_dict = {}
    for solvent in solvents:
        mp = get_solvent_melting_point(solvent)
        if mp is not None:
            mp_dict[solvent] = mp
    return mp_dict


def get_melting_points_info(solvents: list) -> list:
    """Get melting point information for display."""
    info = []
    for solvent in solvents:
        mp = get_solvent_melting_point(solvent)
        if mp is not None:
            info.append((solvent, mp))
    return info


# ============================================================================
# VALIDATION FUNCTION (updated for both BP and MP)
# ============================================================================

def validate_and_adjust_suggestion(suggestion_row: dict, constraints_config: dict, solvent_param_name: str) -> tuple:
    """
    Validate a BO suggestion against dynamic boiling point AND melting point constraints.
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
    
    # Get boiling and melting points for the suggested solvent
    bp_dict = constraints_config.get('boiling_points', {})
    mp_dict = constraints_config.get('melting_points', {})
    
    solvent_bp = bp_dict.get(suggested_solvent)
    solvent_mp = mp_dict.get(suggested_solvent)
    
    # Check and adjust each constrained parameter
    adjusted_row = suggestion_row.copy()
    adjustments_made = []
    safety_margin = constraints_config.get('safety_margin', 5.0)
    
    for constraint in constraints_config.get('constraints', []):
        param_name = constraint['parameter_name']
        constraint_type = constraint.get('type', 'less_than_bp')
        
        if param_name not in adjusted_row:
            continue
            
        current_value = adjusted_row[param_name]
        if current_value is None:
            continue
        
        # ===== CONSTRAINT: Temperature < Boiling Point =====
        if constraint_type == 'less_than_bp' and solvent_bp is not None:
            limit = solvent_bp - safety_margin
            if current_value >= limit:
                adjusted_value = round(limit - 2.0, 1)  # Additional 2°C margin
                adjusted_row[param_name] = adjusted_value
                adjustments_made.append({
                    'parameter': param_name,
                    'original': round(current_value, 1),
                    'adjusted': adjusted_value,
                    'solvent': suggested_solvent,
                    'limit_type': 'boiling_point',
                    'limit_value': solvent_bp,
                    'reason': f"T >= {limit}°C (BP={solvent_bp}°C - margin)"
                })
        
        # ===== CONSTRAINT: Temperature > Melting Point =====
        elif constraint_type == 'greater_than_mp' and solvent_mp is not None:
            limit = solvent_mp + safety_margin
            if current_value <= limit:
                adjusted_value = round(limit + 2.0, 1)  # Additional 2°C margin
                adjusted_row[param_name] = adjusted_value
                adjustments_made.append({
                    'parameter': param_name,
                    'original': round(current_value, 1),
                    'adjusted': adjusted_value,
                    'solvent': suggested_solvent,
                    'limit_type': 'melting_point',
                    'limit_value': solvent_mp,
                    'reason': f"T <= {limit}°C (MP={solvent_mp}°C + margin)"
                })
    
    return adjusted_row, adjustments_made


# ============================================================================
# UI COMPONENT CREATION
# ============================================================================

def create_constraint_row(row_id: str, parameter_options: list = None):
    """Create a single constraint row with constraint type selector."""
    if parameter_options is None:
        parameter_options = []
    
    return html.Div([
        dbc.Row([
            # Parameter selector
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'constraint-param-select', 'index': row_id},
                    options=parameter_options,
                    placeholder="Select parameter",
                    clearable=True,
                    style={"fontSize": "0.875rem"}
                )
            ], width=4),
            # Constraint type selector
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'constraint-type-select', 'index': row_id},
                    options=[
                        {"label": "< Boiling Point (avoid boiling)", "value": "less_than_bp"},
                        {"label": "> Melting Point (avoid freezing)", "value": "greater_than_mp"},
                    ],
                    value="less_than_bp",
                    clearable=False,
                    style={"fontSize": "0.875rem"}
                )
            ], width=5),
            # Delete button
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


# ============================================================================
# CALLBACKS
# ============================================================================

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


# ===== UPDATE BOILING/MELTING POINT INFO DISPLAY =====

@callback(
    Output("bp-info-display", "children"),
    Input("solvent-config-store", "data"),
    prevent_initial_call=True
)
def update_bp_mp_info(solvent_config):
    """Update the boiling point AND melting point information display"""
    if not solvent_config or not solvent_config.get('solvents'):
        return ""
    
    solvents = solvent_config.get('solvents', [])
    bp_info = get_boiling_points_info(solvents)
    mp_info = get_melting_points_info(solvents)
    
    if not bp_info:
        return dbc.Alert(
            "No boiling point data available for selected solvents.",
            color="warning",
            className="mb-2 py-2"
        )
    
    # Create mp lookup for easy access
    mp_lookup = {s: mp for s, mp in mp_info}
    
    # Create table-like display with both BP and MP
    rows = []
    critical_solvents = []
    
    for solvent, bp in sorted(bp_info, key=lambda x: x[1]):
        mp = mp_lookup.get(solvent)
        mp_str = f"{mp}°C" if mp is not None else "N/A"
        
        # Flag solvents with high melting points (> -20°C)
        is_critical = mp is not None and mp > -20
        if is_critical:
            critical_solvents.append((solvent, mp))
        
        row_style = {"padding": "0.25rem 0.5rem"}
        if is_critical:
            row_style["backgroundColor"] = "#fff3cd"
        
        rows.append(
            html.Tr([
                html.Td(solvent, style=row_style),
                html.Td(f"{bp}°C", style={**row_style, "fontWeight": "600"}),
                html.Td(mp_str, style={**row_style, "fontWeight": "600", "color": "#dc3545" if is_critical else "inherit"})
            ])
        )
    
    # Warning for critical solvents
    warning_div = None
    if critical_solvents:
        warning_text = ", ".join([f"{s} ({mp}°C)" for s, mp in critical_solvents])
        warning_div = dbc.Alert([
            html.I(className="bi bi-exclamation-triangle-fill me-2"),
            html.Strong("Attention: "),
            f"These solvents have high melting points and may freeze: {warning_text}"
        ], color="warning", className="mb-2 py-2", style={"fontSize": "0.8rem"})
    
    return html.Div([
        html.Small([
            html.Strong("Phase limits - constraints adapt to suggested solvent:"),
        ], className="text-muted d-block mb-2"),
        warning_div,
        html.Table([
            html.Thead([
                html.Tr([
                    html.Th("Solvent", style={"padding": "0.25rem 0.5rem", "fontSize": "0.75rem"}),
                    html.Th("BP (max)", style={"padding": "0.25rem 0.5rem", "fontSize": "0.75rem"}),
                    html.Th("MP (min)", style={"padding": "0.25rem 0.5rem", "fontSize": "0.75rem"})
                ])
            ]),
            html.Tbody(rows)
        ], className="table table-sm table-borderless mb-0", style={"fontSize": "0.8rem"}),
        html.Div([
            html.I(className="bi bi-info-circle me-1"),
            html.Small("Constraints ensure temperature stays in the liquid phase range", 
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
     Input({'type': 'constraint-type-select', 'index': ALL}, 'value'),
     Input("solvent-config-store", "data")],
    [State({'type': 'constraint-param-select', 'index': ALL}, 'id'),
     State({'type': 'constraint-type-select', 'index': ALL}, 'id'),
     State({'type': 'parameter-name', 'index': ALL}, 'value'),
     State({'type': 'parameter-name', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def save_constraints(constraint_values, constraint_types, solvent_config, 
                     constraint_ids, constraint_type_ids, param_names, param_ids):
    """
    Save constraint configuration to store.
    
    ✅ UPDATED VERSION with melting points and constraint types
    
    The store now contains:
    - boiling_points: dict mapping solvent name -> boiling point
    - melting_points: dict mapping solvent name -> melting point
    - solvent_param_name: name of the solvent parameter
    - constraints: list of constraint definitions with type
    - safety_margin: configurable safety margin in °C
    """
    if not solvent_config:
        return None
    
    solvents = solvent_config.get('solvents', [])
    
    # Get boiling points and melting points for ALL solvents
    bp_dict = get_boiling_points_dict(solvents)
    mp_dict = get_melting_points_dict(solvents)
    
    if not bp_dict and not mp_dict:
        return None
    
    # ✅ GET SOLVENT PARAMETER NAME (critical for native constraints)
    solvent_param_name = None
    solvent_param_id = solvent_config.get('param_id')
    
    # Try to find the parameter name from param_ids/param_names
    if solvent_param_id and param_ids and param_names:
        for name, pid in zip(param_names, param_ids):
            if pid['index'] == solvent_param_id and name:
                solvent_param_name = name.strip()
                break
    
    # Fallback: assume it's called "Solvent"
    if not solvent_param_name:
        solvent_param_name = "Solvent"
    
    print(f"🔍 Constraint store - Solvent parameter name: '{solvent_param_name}'")
    
    # Build parameter name lookup
    param_name_lookup = {}
    if param_names and param_ids:
        for name, pid in zip(param_names, param_ids):
            if name:
                param_name_lookup[pid['index']] = name
    
    # Build constraints list with type
    constraints = []
    if constraint_values and constraint_ids and constraint_types:
        for value, cid, ctype in zip(constraint_values, constraint_ids, constraint_types):
            if value:
                param_name = param_name_lookup.get(value)
                if param_name:
                    constraint_type = ctype if ctype else 'less_than_bp'
                    
                    if constraint_type == 'less_than_bp':
                        description = f"{param_name} < BP(solvent)"
                    else:
                        description = f"{param_name} > MP(solvent)"
                    
                    constraints.append({
                        'id': cid['index'],
                        'type': constraint_type,
                        'parameter_id': value,
                        'parameter_name': param_name,
                        'description': description
                    })
    
    print(f"🔍 Constraint store - {len(constraints)} constraint(s) configured")
    for c in constraints:
        print(f"   - {c['description']} (type: {c['type']})")
    
    # ✅ RETURN WITH both boiling_points and melting_points
    return {
        'boiling_points': bp_dict,      # Dict: solvent -> BP
        'melting_points': mp_dict,      # Dict: solvent -> MP (NEW)
        'solvents': solvents,
        'solvent_param_id': solvent_param_id,
        'solvent_param_name': solvent_param_name,
        'constraints': constraints,
        'safety_margin': 5.0            # Configurable safety margin
    }
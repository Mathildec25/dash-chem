"""
Constraints configuration callbacks
Handles constraints related to solvent boiling points, melting points,
AND inter-parameter linear constraints (inequality AND equality).

UPDATED:
- Constraints card is ALWAYS visible
- Phase constraints section (BP/MP) shown/hidden based on solvent config
- Linear constraints always available (inequality ≤ or equality =)
- save_constraints works even without solvent config

DYNAMIC CONSTRAINTS:
- Temperature < Boiling Point (avoid boiling)
- Temperature > Melting Point (avoid freezing)

INTER-PARAMETER LINEAR CONSTRAINTS:
- Parameter A ≤ Parameter B + offset  (inequality)
- Parameter A = Parameter B + offset  (equality)
"""

from dash import callback, Input, Output, State, ALL, ctx, html, dcc, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid

from utils.descriptor_data import SOLVENT_DESCRIPTORS


# ============================================================================
# BOILING POINT FUNCTIONS
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
# MELTING POINT FUNCTIONS
# ============================================================================

def get_solvent_melting_point(solvent_name: str) -> float:
    """Get melting point for a specific solvent."""
    if solvent_name in SOLVENT_DESCRIPTORS:
        return SOLVENT_DESCRIPTORS[solvent_name].get('mp')
    return None


def get_max_melting_point(solvents: list) -> float:
    """Get the maximum melting point from selected solvents."""
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
# HELPER: Resolve parameter name from ID
# ============================================================================

def _resolve_param_name(param_id, param_names, param_ids):
    """Resolve a parameter name from its UUID index."""
    if param_names and param_ids:
        for name, pid in zip(param_names, param_ids):
            if pid['index'] == param_id and name:
                return name.strip()
    return None

def _get_row_index(row) -> str | None:
    """
    Extrait l'index d'un composant Dash, qu'il arrive comme objet Python
    ou comme dict sérialisé (cas des children passés via State).
    """
    try:
        if isinstance(row, dict):
            return row.get('props', {}).get('id', {}).get('index')
        row_id = getattr(row, 'id', None)
        if isinstance(row_id, dict):
            return row_id.get('index')
    except Exception:
        pass
    return None
# ============================================================================
# VALIDATION FUNCTION (BP, MP, AND linear constraints)
# ============================================================================

def validate_and_adjust_suggestion(suggestion_row: dict, constraints_config: dict, solvent_param_name: str) -> tuple:
    """
    Validate a BO suggestion against dynamic boiling point, melting point,
    AND inter-parameter linear constraints (inequality and equality).
    Adjusts parameter values if they violate constraints.
    
    Args:
        suggestion_row: Dictionary with suggested parameter values
        constraints_config: Constraint configuration from constraints-store
        solvent_param_name: Name of the solvent parameter (e.g., "Solvent")
    
    Returns:
        Tuple of (adjusted_row, adjustments_made)
    """
    if not constraints_config:
        return suggestion_row, []
    
    has_phase_constraints = constraints_config.get('constraints')
    has_ineq_constraints = constraints_config.get('inequality_constraints')
    
    if not has_phase_constraints and not has_ineq_constraints:
        return suggestion_row, []
    
    adjusted_row = suggestion_row.copy()
    adjustments_made = []
    
    # ===== PHASE CONSTRAINTS (BP/MP) =====
    if has_phase_constraints:
        suggested_solvent = suggestion_row.get(solvent_param_name)
        
        if suggested_solvent:
            bp_dict = constraints_config.get('boiling_points', {})
            mp_dict = constraints_config.get('melting_points', {})
            solvent_bp = bp_dict.get(suggested_solvent)
            solvent_mp = mp_dict.get(suggested_solvent)
            safety_margin = constraints_config.get('safety_margin', 5.0)
            
            for constraint in constraints_config.get('constraints', []):
                param_name = constraint['parameter_name']
                constraint_type = constraint.get('type', 'less_than_bp')
                
                if param_name not in adjusted_row:
                    continue
                    
                current_value = adjusted_row[param_name]
                if current_value is None:
                    continue
                
                try:
                    current_value = float(current_value)
                except (ValueError, TypeError):
                    continue
                
                if constraint_type == 'less_than_bp' and solvent_bp is not None:
                    limit = solvent_bp - safety_margin
                    if current_value >= limit:
                        adjusted_value = round(limit - 2.0, 1)
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
                
                elif constraint_type == 'greater_than_mp' and solvent_mp is not None:
                    limit = solvent_mp + safety_margin
                    if current_value <= limit:
                        adjusted_value = round(limit + 2.0, 1)
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
    
    # ===== INTER-PARAMETER LINEAR CONSTRAINTS (inequality + equality) =====
    for ineq in constraints_config.get('inequality_constraints', []):
        left = ineq['param_left']
        right = ineq['param_right']
        offset = ineq.get('offset', 0.0)
        relation = ineq.get('relation', 'leq')  # ✅ NEW: default to "leq" for backward compat
        
        if left in adjusted_row and right in adjusted_row:
            val_left = adjusted_row[left]
            val_right = adjusted_row[right]
            if val_left is not None and val_right is not None:
                try:
                    val_left = float(val_left)
                    val_right = float(val_right)
                except (ValueError, TypeError):
                    continue
                
                limit = val_right + offset
                
                if relation == "eq":
                    # ✅ Equality constraint — force param_left = param_right + offset
                    if abs(val_left - limit) > 1e-6:
                        adjusted_value = round(limit, 1)
                        adjustments_made.append({
                            'parameter': left,
                            'original': round(val_left, 1),
                            'adjusted': adjusted_value,
                            'limit_type': 'linear_equality',
                            'reason': f"{left}={val_left} ≠ {right}+{offset}={limit}"
                        })
                        adjusted_row[left] = adjusted_value
                else:
                    # Inequality constraint (existing logic)
                    if val_left > limit:
                        adjusted_value = round(limit - 1.0, 1)
                        adjustments_made.append({
                            'parameter': left,
                            'original': round(val_left, 1),
                            'adjusted': adjusted_value,
                            'limit_type': 'linear_inequality',
                            'reason': f"{left}={val_left} > {right}+{offset}={limit}"
                        })
                        adjusted_row[left] = adjusted_value
    
    return adjusted_row, adjustments_made


# ============================================================================
# UI COMPONENT CREATION
# ============================================================================

def create_constraint_row(row_id: str, parameter_options: list = None):
    """Create a single phase constraint row (BP/MP)."""
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
            ], width=4),
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


def create_linear_constraint_row(row_id: str, parameter_options: list = None):
    """Create a linear constraint row: param_left ≤/= param_right + offset."""
    if parameter_options is None:
        parameter_options = []
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'ineq-param-left', 'index': row_id},
                    options=parameter_options,
                    placeholder="Param A",
                    clearable=True,
                    style={"fontSize": "0.875rem"}
                )
            ], width=3),
            # ✅ Dropdown for ≤ or = instead of static "≤"
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'ineq-relation-type', 'index': row_id},
                    options=[
                        {"label": "≤", "value": "leq"},
                        {"label": "=", "value": "eq"},
                    ],
                    value="leq",
                    clearable=False,
                    style={"fontSize": "1rem", "fontWeight": "bold", "textAlign": "center"}
                )
            ], width=1, className="px-0"),
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'ineq-param-right', 'index': row_id},
                    options=parameter_options,
                    placeholder="Param B",
                    clearable=True,
                    style={"fontSize": "0.875rem"}
                )
            ], width=3),
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText("+", style={"fontSize": "0.8rem", "padding": "0.25rem 0.5rem"}),
                    dbc.Input(
                        id={'type': 'ineq-offset', 'index': row_id},
                        placeholder="0",
                        type="number",
                        step="any",
                        value=0,
                        size="sm",
                        style={"borderRadius": "0 6px 6px 0"}
                    ),
                ], size="sm")
            ], width=3),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-ineq-constraint-row', 'index': row_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=2),
        ], className="mb-2 align-items-center"),
    ], id={'type': 'ineq-constraint-row', 'index': row_id})


# ✅ Keep old name as alias for backward compatibility
create_inequality_constraint_row = create_linear_constraint_row


# ============================================================================
# CALLBACKS
# ============================================================================

# ===== SHOW/HIDE PHASE CONSTRAINTS SECTION (not the whole card) =====

@callback(
    Output("phase-constraints-section", "style"),
    Input("solvent-config-store", "data"),
    prevent_initial_call=True
)
def toggle_phase_constraints_section(solvent_config):
    """Show phase constraints section only when solvents are configured."""
    if solvent_config and solvent_config.get('solvents'):
        return {"display": "block"}
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
    
    mp_lookup = {s: mp for s, mp in mp_info}
    
    rows = []
    critical_solvents = []
    
    for solvent, bp in sorted(bp_info, key=lambda x: x[1]):
        mp = mp_lookup.get(solvent)
        mp_str = f"{mp}°C" if mp is not None else "N/A"
        
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


# ============================================================================
# PHASE CONSTRAINT CALLBACKS (BP/MP)
# ============================================================================

@callback(
    Output({'type': 'constraint-param-select', 'index': ALL}, 'options'),
    [Input({'type': 'parameter-name', 'index': ALL}, 'value'),
     Input({'type': 'parameter-type', 'index': ALL}, 'value')],
    [State({'type': 'parameter-name', 'index': ALL}, 'id'),
     State({'type': 'constraint-param-select', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def update_constraint_param_options(param_names, param_types, param_ids, constraint_ids):
    """Update the parameter options in phase constraint dropdowns"""
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
    """Add a new phase constraint row"""
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


@callback(
    Output("constraint-rows-container", "children", allow_duplicate=True),
    Input({'type': 'delete-constraint-row', 'index': ALL}, 'n_clicks'),
    State("constraint-rows-container", "children"),
    prevent_initial_call=True
)
def delete_constraint_row(n_clicks, current_rows):
    """Delete a phase constraint row"""
    if not any(n_clicks):
        raise PreventUpdate
    
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        raise PreventUpdate
    
    row_to_delete = triggered.get('index')
    
    updated_rows = [row for row in current_rows if _get_row_index(row) != row_to_delete]
    return updated_rows


# ============================================================================
# LINEAR CONSTRAINT CALLBACKS (inequality + equality)
# ============================================================================

@callback(
    [Output({'type': 'ineq-param-left', 'index': ALL}, 'options'),
     Output({'type': 'ineq-param-right', 'index': ALL}, 'options')],
    [Input({'type': 'parameter-name', 'index': ALL}, 'value'),
     Input({'type': 'parameter-type', 'index': ALL}, 'value')],
    [State({'type': 'parameter-name', 'index': ALL}, 'id'),
     State({'type': 'ineq-param-left', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def update_ineq_param_options(param_names, param_types, param_ids, ineq_ids):
    """Update parameter options in linear constraint dropdowns"""
    if not param_names or not ineq_ids:
        raise PreventUpdate
    
    options = []
    for name, ptype, pid in zip(param_names, param_types, param_ids):
        if name and ptype in ['float', 'int']:
            options.append({
                "label": name,
                "value": pid['index']
            })
    
    return [options] * len(ineq_ids), [options] * len(ineq_ids)


@callback(
    Output("ineq-constraint-rows-container", "children", allow_duplicate=True),
    Input("add-ineq-constraint-btn", "n_clicks"),
    [State("ineq-constraint-rows-container", "children"),
     State({'type': 'parameter-name', 'index': ALL}, 'value'),
     State({'type': 'parameter-type', 'index': ALL}, 'value'),
     State({'type': 'parameter-name', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def add_ineq_constraint_row(n_clicks, current_rows, param_names, param_types, param_ids):
    """Add a new linear constraint row"""
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
    new_row = create_linear_constraint_row(new_id, options)
    
    if current_rows is None:
        current_rows = []
    
    return current_rows + [new_row]


@callback(
    Output("ineq-constraint-rows-container", "children", allow_duplicate=True),
    Input({'type': 'delete-ineq-constraint-row', 'index': ALL}, 'n_clicks'),
    State("ineq-constraint-rows-container", "children"),
    prevent_initial_call=True
)
def delete_ineq_constraint_row(n_clicks, current_rows):
    """Delete a linear constraint row"""
    if not any(n_clicks):
        raise PreventUpdate
    
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        raise PreventUpdate
    
    row_to_delete = triggered.get('index')
    
    updated_rows = [row for row in current_rows if _get_row_index(row) != row_to_delete]
    return updated_rows


# ============================================================================
# SAVE ALL CONSTRAINTS TO STORE
# ============================================================================

@callback(
    Output("constraints-store", "data"),
    [Input({'type': 'constraint-param-select', 'index': ALL}, 'value'),
     Input({'type': 'constraint-type-select', 'index': ALL}, 'value'),
     Input("solvent-config-store", "data"),
     Input({'type': 'ineq-param-left', 'index': ALL}, 'value'),
     Input({'type': 'ineq-param-right', 'index': ALL}, 'value'),
     Input({'type': 'ineq-offset', 'index': ALL}, 'value'),
     Input({'type': 'ineq-relation-type', 'index': ALL}, 'value')],  # ✅ NEW
    [State({'type': 'constraint-param-select', 'index': ALL}, 'id'),
     State({'type': 'constraint-type-select', 'index': ALL}, 'id'),
     State({'type': 'parameter-name', 'index': ALL}, 'value'),
     State({'type': 'parameter-name', 'index': ALL}, 'id'),
     State({'type': 'ineq-param-left', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def save_constraints(constraint_values, constraint_types, solvent_config,
                     ineq_left_values, ineq_right_values, ineq_offset_values,
                     ineq_relation_types,  # ✅ NEW parameter
                     constraint_ids, constraint_type_ids, param_names, param_ids,
                     ineq_left_ids):
    """
    Save constraint configuration to store.
    
    ✅ Works with or without solvent config.
    - Phase constraints (BP/MP) require solvent config
    - Linear constraints work independently (inequality + equality)
    """
    # ===== SOLVENT INFO (optional) =====
    bp_dict = {}
    mp_dict = {}
    solvents = []
    solvent_param_name = "Solvent"
    solvent_param_id = None
    
    if solvent_config:
        solvents = solvent_config.get('solvents', [])
        bp_dict = get_boiling_points_dict(solvents)
        mp_dict = get_melting_points_dict(solvents)
        solvent_param_id = solvent_config.get('param_id')
        
        if solvent_param_id and param_ids and param_names:
            for name, pid in zip(param_names, param_ids):
                if pid['index'] == solvent_param_id and name:
                    solvent_param_name = name.strip()
                    break
    
    print(f"🔍 Constraint store - Solvent parameter name: '{solvent_param_name}'")
    
    # Build parameter name lookup
    param_name_lookup = {}
    if param_names and param_ids:
        for name, pid in zip(param_names, param_ids):
            if name:
                param_name_lookup[pid['index']] = name
    
    # ===== PHASE CONSTRAINTS (BP/MP) =====
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
    
    print(f"🔍 Constraint store - {len(constraints)} phase constraint(s)")
    for c in constraints:
        print(f"   - {c['description']} (type: {c['type']})")
    
    # ===== LINEAR CONSTRAINTS (inequality + equality) =====
    inequality_constraints = []
    if ineq_left_values and ineq_right_values:
        # ✅ Handle case where ineq_relation_types might be empty or shorter
        # (backward compat if rows were created before the dropdown existed)
        relation_list = ineq_relation_types if ineq_relation_types else []
        
        for i, (left_val, right_val, offset_val, left_id) in enumerate(zip(
            ineq_left_values, ineq_right_values, ineq_offset_values, ineq_left_ids
        )):
            if left_val and right_val:
                left_name = _resolve_param_name(left_val, param_names, param_ids)
                right_name = _resolve_param_name(right_val, param_names, param_ids)
                if left_name and right_name and left_name != right_name:
                    offset = float(offset_val) if offset_val is not None else 0.0
                    # ✅ Get relation type, default to "leq" for backward compatibility
                    relation = relation_list[i] if i < len(relation_list) and relation_list[i] else "leq"
                    symbol = "≤" if relation == "leq" else "="
                    constraint_type = "linear_inequality" if relation == "leq" else "linear_equality"
                    
                    inequality_constraints.append({
                        'id': left_id['index'],
                        'type': constraint_type,
                        'relation': relation,
                        'param_left': left_name,
                        'param_right': right_name,
                        'offset': offset,
                        'description': f"{left_name} {symbol} {right_name} + {offset}"
                    })
    
    print(f"🔍 Constraint store - {len(inequality_constraints)} linear constraint(s)")
    for ic in inequality_constraints:
        print(f"   - {ic['description']}")
    
    # ✅ Return data even without solvents (linear constraints still need saving)
    if not constraints and not inequality_constraints and not bp_dict and not mp_dict:
        return None
    
    return {
        'boiling_points': bp_dict,
        'melting_points': mp_dict,
        'solvents': solvents,
        'solvent_param_id': solvent_param_id,
        'solvent_param_name': solvent_param_name,
        'constraints': constraints,
        'inequality_constraints': inequality_constraints,
        'safety_margin': 5.0
    }
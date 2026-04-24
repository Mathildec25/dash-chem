"""
Bases and descriptors configuration callbacks
Handles base selection modal and related functionality
"""

from dash import callback, Input, Output, State, ALL, ctx, html, dcc, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid

# ============================================================================
# IMPORT DESCRIPTORS FROM AUTO-GENERATED FILES
# ============================================================================

try:
    from bofire_solvent_descriptors import SOLVENT_DESCRIPTORS
    from bofire_base_descriptors import BASE_DESCRIPTORS
except ImportError:
    try:
        from bofire_solvent_descriptors import SOLVENT_DESCRIPTORS
        from bofire_base_descriptors import BASE_DESCRIPTORS
    except ImportError:
        print("WARNING: Could not import descriptor files; using minimal fallback.")
        SOLVENT_DESCRIPTORS = {}
        BASE_DESCRIPTORS = {
            "Triethylamine": {}, "Pyridine": {}, "DBU": {}
        }

# ============================================================================
# DYNAMIC LISTS FROM IMPORTED DESCRIPTORS
# ============================================================================

# Common bases list (now dynamic from descriptors, mutable to allow adding custom bases)
COMMON_BASES = sorted(list(BASE_DESCRIPTORS.keys()))

# Fixed base descriptors (auto-selected, no user choice)
FIXED_BASE_DESCRIPTORS = ['pKa_DMSO', 'MW']

# Get ALL descriptor keys from the first base entry (excluding CAS)
def _get_base_descriptor_keys():
    """Get all descriptor keys from BASE_DESCRIPTORS (excluding CAS)."""
    if not BASE_DESCRIPTORS:
        return []
    first_base = next(iter(BASE_DESCRIPTORS.values()))
    return sorted([k for k in first_base.keys() if k != 'CAS'])

BASE_DESCRIPTOR_KEYS = _get_base_descriptor_keys()

# Print confirmation on import
print(f"Loaded {len(COMMON_BASES)} bases from descriptor files")
print(f"Fixed base descriptors: {FIXED_BASE_DESCRIPTORS}")
print(f"All base descriptor keys: {BASE_DESCRIPTOR_KEYS}")


def create_base_row(row_id):
    """Create a single base selection row"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'base-select', 'index': row_id},
                    options=[{"label": b, "value": b} for b in COMMON_BASES],
                    placeholder="Select base",
                    clearable=True,
                    style={"fontSize": "0.875rem"}
                )
            ], width=10),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-base-row', 'index': row_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=2),
        ], className="mb-2 align-items-center"),
    ], id={'type': 'base-row', 'index': row_id})


# ===== OPEN/CLOSE MAIN MODAL =====

@callback(
    Output("base-modal", "is_open"),
    [Input("add-base-button", "n_clicks"),
     Input("save-bases-btn", "n_clicks")],
    State("base-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_base_modal(open_clicks, save_clicks, is_open):
    """Open modal when Base button clicked, close when Save clicked"""
    if ctx.triggered_id == "add-base-button":
        return True
    elif ctx.triggered_id == "save-bases-btn":
        return False
    return is_open


# ===== TOGGLE CUSTOM BASE COLLAPSE =====

@callback(
    [Output("custom-base-collapse", "style"),
     Output("toggle-custom-base-btn", "children")],
    Input("toggle-custom-base-btn", "n_clicks"),
    State("custom-base-collapse", "style"),
    prevent_initial_call=True
)
def toggle_custom_base_collapse(n_clicks, current_style):
    """Toggle custom base form"""
    if n_clicks:
        # Toggle display
        if current_style and current_style.get("display") == "block":
            new_style = {"display": "none"}
        else:
            new_style = {"display": "block"}
        
        button_text = [
            html.I(className="bi bi-plus-circle me-1", style={"fontSize": "0.75rem"}),
            "Create Custom"
        ]
        return new_style, button_text
    raise PreventUpdate


# ===== ADD CUSTOM BASE =====

@callback(
    [Output("base-rows-container", "children", allow_duplicate=True),
     Output({'type': 'base-select', 'index': ALL}, 'options'),
     Output("custom-base-name", "value"),
     Output({'type': 'custom-base-desc', 'index': ALL}, 'value'),
     Output("custom-base-collapse", "style", allow_duplicate=True),
     Output("toggle-custom-base-btn", "children", allow_duplicate=True),
     Output("validation-alert", "children", allow_duplicate=True),
     Output("validation-alert", "is_open", allow_duplicate=True)],
    Input("confirm-custom-base-btn", "n_clicks"),
    [State("custom-base-name", "value"),
     State({'type': 'custom-base-desc', 'index': ALL}, 'value'),
     State({'type': 'custom-base-desc', 'index': ALL}, 'id'),
     State("base-rows-container", "children"),
     State({'type': 'base-select', 'index': ALL}, 'options')],
    prevent_initial_call=True
)
def add_custom_base(n_clicks, name, desc_values, desc_ids, current_rows, current_options):
    """Add a custom base with all descriptor values to the list and select it"""
    if not n_clicks:
        raise PreventUpdate
    
    # Validate name
    if not name or not name.strip():
        alert = dbc.Alert("❌ Base name is required", color="danger")
        n_desc = len(desc_values)
        return (no_update, no_update, no_update, [no_update] * n_desc,
                no_update, no_update, alert, True)
    
    base_name = name.strip()
    
    # Check for duplicate name
    if base_name in COMMON_BASES:
        alert = dbc.Alert(f"❌ Base '{base_name}' already exists", color="danger")
        n_desc = len(desc_values)
        return (no_update, no_update, no_update, [no_update] * n_desc,
                no_update, no_update, alert, True)
    
    # Validate all descriptor values
    descriptor_data = {}
    for desc_id, desc_val in zip(desc_ids, desc_values):
        desc_key = desc_id['index']
        if desc_val is None or desc_val == '':
            alert = dbc.Alert(f"❌ Value for '{desc_key}' is required", color="danger")
            n_desc = len(desc_values)
            return (no_update, no_update, no_update, [no_update] * n_desc,
                    no_update, no_update, alert, True)
        try:
            descriptor_data[desc_key] = float(desc_val)
        except (ValueError, TypeError):
            alert = dbc.Alert(f"❌ Invalid numeric value for '{desc_key}'", color="danger")
            n_desc = len(desc_values)
            return (no_update, no_update, no_update, [no_update] * n_desc,
                    no_update, no_update, alert, True)
    
    # === SUCCESS: Add to BASE_DESCRIPTORS and COMMON_BASES ===
    BASE_DESCRIPTORS[base_name] = descriptor_data
    COMMON_BASES.append(base_name)
    
    print(f"Added custom base '{base_name}' to BASE_DESCRIPTORS")
    print(f"   Descriptors: {descriptor_data}")
    
    # Update all dropdown options
    new_options = [{"label": b, "value": b} for b in sorted(COMMON_BASES)]
    updated_options = [new_options] * len(current_options)
    
    # Create a new row with the custom base already selected
    new_id = str(uuid.uuid4())
    new_row = html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'base-select', 'index': new_id},
                    options=new_options,
                    value=base_name,  # Pre-select the new base
                    placeholder="Select base",
                    clearable=True,
                    style={"fontSize": "0.875rem"}
                )
            ], width=10),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-base-row', 'index': new_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=2),
        ], className="mb-2 align-items-center"),
    ], id={'type': 'base-row', 'index': new_id})
    
    # Add the new row to current rows
    updated_rows = current_rows + [new_row]
    
    # Reset button text
    button_text = [
        html.I(className="bi bi-plus-circle me-1", style={"fontSize": "0.75rem"}),
        "Create Custom"
    ]
    
    alert = dbc.Alert([
        html.I(className="bi bi-check-circle-fill me-2"),
        f"✅ Added custom base: {base_name}"
    ], color="success")
    
    # Clear all descriptor inputs
    cleared_desc_values = [None] * len(desc_values)
    
    return (updated_rows, updated_options, "", cleared_desc_values,
            {"display": "none"}, button_text, alert, True)

# ===== INITIALIZE MODAL WITH DEFAULT ROWS =====

@callback(
    Output("base-rows-container", "children", allow_duplicate=True),
    Input("base-modal", "is_open"),
    prevent_initial_call=True
)
def initialize_base_modal_content(is_open):
    """Initialize modal with one base row when opened via button"""
    triggered_id = ctx.triggered_id
    
    if triggered_id != "add-base-button":
        raise PreventUpdate
    
    if is_open:
        base_id = str(uuid.uuid4())
        return [create_base_row(base_id)]
    
    raise PreventUpdate

# ===== MANAGE BASE ROWS =====

@callback(
    Output("base-rows-container", "children", allow_duplicate=True),
    [Input("add-base-row-btn", "n_clicks"),
     Input({'type': 'delete-base-row', 'index': ALL}, 'n_clicks')],
    State("base-rows-container", "children"),
    prevent_initial_call=True
)
def manage_base_rows(add_clicks, delete_clicks, current_rows):
    """Handle adding and deleting base rows"""
    triggered = ctx.triggered_id
    
    if triggered == "add-base-row-btn":
        if not add_clicks:
            raise PreventUpdate
        new_id = str(uuid.uuid4())
        new_row = create_base_row(new_id)
        return current_rows + [new_row]
    
    elif isinstance(triggered, dict) and triggered.get('type') == 'delete-base-row':
        if not any(delete_clicks):
            raise PreventUpdate
        
        index_to_delete = triggered['index']
        new_rows = []
        for row in current_rows:
            try:
                if row['props']['id']['index'] != index_to_delete:
                    new_rows.append(row)
            except:
                new_rows.append(row)
        
        if not new_rows:
            new_id = str(uuid.uuid4())
            new_rows = [create_base_row(new_id)]
        
        return new_rows
    
    raise PreventUpdate


# ===== SAVE BASE CONFIGURATION =====

@callback(
    [Output("parameter-container", "children", allow_duplicate=True),
     Output("base-config-store", "data"),
     Output("validation-alert", "children", allow_duplicate=True),
     Output("validation-alert", "is_open", allow_duplicate=True)],
    Input("save-bases-btn", "n_clicks"),
    [State({'type': 'base-select', 'index': ALL}, 'value'),
     State("parameter-container", "children"),
     State("base-config-store", "data")],
    prevent_initial_call=True
)
def save_base_configuration(n_clicks, bases, current_params, current_config):
    """Save the selected bases and descriptors as a categorical parameter"""
    if not n_clicks:
        raise PreventUpdate
    
    selected_bases = [b for b in bases if b]
    selected_descriptors = FIXED_BASE_DESCRIPTORS
    
    if not selected_bases:
        alert = dbc.Alert("❌ Please select at least one base", color="danger")
        return no_update, no_update, alert, True
    
    print(f"Saved bases: {selected_bases}")
    print(f"Using fixed descriptors: {selected_descriptors}")
    
    # Get existing base parameter ID if it exists
    base_param_id = None
    if current_config and 'param_id' in current_config:
        base_param_id = current_config['param_id']
    
    if base_param_id is None:
        base_param_id = str(uuid.uuid4())
    
    # Store configuration - no more 'custom_bases' with SMILES
    config_data = {
        'param_id': base_param_id,
        'bases': selected_bases,
        'descriptors': selected_descriptors,
    }
    
    # Remove existing Base parameter if it exists
    updated_params = []
    for param in current_params:
        try:
            param_row_id = param['props']['id']
            if param_row_id['type'] == 'parameter-row' and param_row_id['index'] == base_param_id:
                continue
        except:
            pass
        updated_params.append(param)
    
    # Create base parameter row
    base_values = ", ".join(selected_bases)
    descriptor_info = f"Descriptors: {', '.join(selected_descriptors)}"
    
    new_row = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Input(
                    id={'type': 'parameter-name', 'index': base_param_id},
                    value="Base",
                    size="sm",
                    style={"borderRadius": "6px"},
                    disabled=True
                )
            ], width=3),
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'parameter-type', 'index': base_param_id},
                    options=[
                        {"label": "Continuous", "value": "float"},
                        {"label": "Discrete", "value": "int"},
                        {"label": "Categorical", "value": "cat"},
                    ],
                    value="cat",
                    placeholder="Type",
                    clearable=False,
                    disabled=True,
                    style={"fontSize": "0.875rem"}
                )
            ], width=2),
            dbc.Col([
                html.Div(id={'type': 'parameter-inputs', 'index': base_param_id}, children=[
                    html.Div([
                        dbc.Input(
                            id={'type': 'parameter-categories', 'index': base_param_id},
                            value=base_values,
                            type="text",
                            size="sm",
                            disabled=True,
                            style={"borderRadius": "6px"}
                        ),
                        dbc.Tooltip(
                            descriptor_info,
                            target={'type': 'parameter-categories', 'index': base_param_id},
                            placement="top"
                        )
                    ])
                ])
            ], width=5),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-pencil-square", style={"fontSize": "0.875rem"}),
                    id={'type': 'edit-base', 'index': base_param_id},
                    color="primary",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=1),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-parameter', 'index': base_param_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=1),
        ], className="mb-2 align-items-center"),
    ], id={'type': 'parameter-row', 'index': base_param_id})
    
    updated_params = [new_row] + updated_params
    
    alert = dbc.Alert([
        html.I(className="bi bi-check-circle-fill me-2"),
        f"Saved {len(selected_bases)} base(s) as parameter"
    ], color="success")
    
    return updated_params, config_data, alert, True

# ===== EDIT BASE - REOPEN MODAL WITH CURRENT VALUES =====

@callback(
    [Output("base-modal", "is_open", allow_duplicate=True),
     Output("base-rows-container", "children", allow_duplicate=True)],
    Input({'type': 'edit-base', 'index': ALL}, 'n_clicks'),
    State("base-config-store", "data"),
    prevent_initial_call=True
)
def edit_base_parameter(n_clicks, config_data):
    """Reopen modal with current base configuration"""
    if not any(n_clicks) or not config_data:
        raise PreventUpdate
    
    selected_bases = config_data.get('bases', [])
    
    # Recreate base rows with selected values
    base_rows = []
    for base in selected_bases:
        row_id = str(uuid.uuid4())
        base_rows.append(html.Div([
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id={'type': 'base-select', 'index': row_id},
                        options=[{"label": b, "value": b} for b in sorted(COMMON_BASES)],
                        value=base,
                        placeholder="Select base",
                        clearable=True,
                        style={"fontSize": "0.875rem"}
                    )
                ], width=10),
                dbc.Col([
                    dbc.Button(
                        html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                        id={'type': 'delete-base-row', 'index': row_id},
                        color="danger",
                        outline=True,
                        size="sm",
                        style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                    )
                ], width=2),
            ], className="mb-2 align-items-center"),
        ], id={'type': 'base-row', 'index': row_id}))
    
    if not base_rows:
        row_id = str(uuid.uuid4())
        base_rows = [create_base_row(row_id)]
    
    return True, base_rows
"""
Solvents and descriptors configuration callbacks
Handles solvent selection modal and related functionality
"""

from dash import callback, Input, Output, State, ALL, ctx, html, dcc, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid

# ============================================================================
# IMPORT DESCRIPTORS FROM AUTO-GENERATED FILES
# ============================================================================

try:
    # Try importing from utils folder
    from bofire_solvent_descriptors import SOLVENT_DESCRIPTORS
    from bofire_base_descriptors import BASE_DESCRIPTORS
except ImportError:
    try:
        # Try importing from root folder
        from bofire_solvent_descriptors import SOLVENT_DESCRIPTORS
        from bofire_base_descriptors import BASE_DESCRIPTORS
    except ImportError:
        print("⚠️ WARNING: Could not import descriptor files!")
        print("   Using minimal fallback. Run: python advanced_descriptor_calculator.py")
        # Minimal fallback
        SOLVENT_DESCRIPTORS = {
        }
        BASE_DESCRIPTORS = {}

# ============================================================================
# DYNAMIC LISTS FROM IMPORTED DESCRIPTORS
# ============================================================================

# Common solvents list (now dynamic from descriptors, mutable to allow adding custom solvents)
COMMON_SOLVENTS = sorted(list(SOLVENT_DESCRIPTORS.keys()))

# Fixed solvent descriptors (auto-selected, no user choice)
FIXED_SOLVENT_DESCRIPTORS = ['dielectric', 'dipole_moment', 'HBA', 'HBD', 'AN', 'DN']

# Get ALL descriptor keys from the first solvent entry (excluding CAS)
def _get_solvent_descriptor_keys():
    """Get all descriptor keys from SOLVENT_DESCRIPTORS (excluding CAS)."""
    if not SOLVENT_DESCRIPTORS:
        return []
    first_solvent = next(iter(SOLVENT_DESCRIPTORS.values()))
    return sorted([k for k in first_solvent.keys() if k != 'CAS'])

SOLVENT_DESCRIPTOR_KEYS = _get_solvent_descriptor_keys()

# Print confirmation on import
print(f"✓ Loaded {len(COMMON_SOLVENTS)} solvents from descriptor files")
print(f"✓ Fixed solvent descriptors: {FIXED_SOLVENT_DESCRIPTORS}")
print(f"✓ All solvent descriptor keys: {SOLVENT_DESCRIPTOR_KEYS}")


# ============================================================================
# LAYOUT HELPER: Custom Solvent Form (to be used in modal layout)
# ============================================================================

def create_custom_solvent_form():
    """
    Create the custom solvent form with Name + all descriptor inputs.
    Call this function in your layout file inside the solvent modal,
    replacing the old Name + SMILES form.
    
    Returns:
        html.Div with the toggle button, collapse, and form content
    """
    # Build descriptor input rows
    descriptor_inputs = []
    for desc_key in SOLVENT_DESCRIPTOR_KEYS:
        descriptor_inputs.append(
            dbc.Row([
                dbc.Col([
                    dbc.Label(desc_key, className="small mb-0")
                ], width=4),
                dbc.Col([
                    dbc.Input(
                        id={'type': 'custom-solvent-desc', 'index': desc_key},
                        type="number",
                        placeholder=f"Value for {desc_key}",
                        size="sm",
                        style={"borderRadius": "6px"}
                    )
                ], width=8),
            ], className="mb-2 align-items-center")
        )
    
    return html.Div([
        # Collapsible form (initially hidden)
        html.Div([
            dbc.Card([
                dbc.CardBody([
                    # Solvent name
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Solvent Name", className="small mb-0 fw-bold")
                        ], width=4),
                        dbc.Col([
                            dbc.Input(
                                id="custom-solvent-name",
                                type="text",
                                placeholder="e.g. My Custom Solvent",
                                size="sm",
                                style={"borderRadius": "6px"}
                            )
                        ], width=8),
                    ], className="mb-3 align-items-center"),
                    
                    html.Hr(className="my-2"),
                    html.P("Descriptor values:", className="small fw-bold mb-2 text-muted"),
                    
                    # All descriptor inputs
                    *descriptor_inputs,
                    
                    html.Hr(className="my-2"),
                    
                    # Save button
                    dbc.Button(
                        [html.I(className="bi bi-check-circle me-2"), "Save Custom Solvent"],
                        id="confirm-custom-solvent-btn",
                        color="success",
                        size="sm",
                        className="w-100"
                    )
                ])
            ], className="border-info"),
        ], id="custom-solvent-collapse", style={"display": "none"})
    ])


def create_solvent_row(row_id):
    """Create a single solvent selection row"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'solvent-select', 'index': row_id},
                    options=[{"label": s, "value": s} for s in COMMON_SOLVENTS],
                    placeholder="Select solvent",
                    clearable=True,
                    style={"fontSize": "0.875rem"}
                )
            ], width=10),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-solvent-row', 'index': row_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=2),
        ], className="mb-2 align-items-center"),
    ], id={'type': 'solvent-row', 'index': row_id})


# ===== OPEN/CLOSE MAIN MODAL =====

@callback(
    Output("solvent-modal", "is_open"),
    [Input("add-solvent-button", "n_clicks"),
     Input("save-solvents-btn", "n_clicks")],
    State("solvent-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_solvent_modal(open_clicks, save_clicks, is_open):
    """Open modal when Solvant button clicked, close when Save clicked"""
    if ctx.triggered_id == "add-solvent-button":
        return True
    elif ctx.triggered_id == "save-solvents-btn":
        return False
    return is_open


# ===== TOGGLE CUSTOM SOLVENT COLLAPSE =====

@callback(
    [Output("custom-solvent-collapse", "style"),
     Output("toggle-custom-solvent-btn", "children")],
    Input("toggle-custom-solvent-btn", "n_clicks"),
    State("custom-solvent-collapse", "style"),
    prevent_initial_call=True
)
def toggle_custom_solvent_collapse(n_clicks, current_style):
    """Toggle custom solvent form"""
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


# ===== ADD CUSTOM SOLVENT =====

@callback(
    [Output("solvent-rows-container", "children", allow_duplicate=True),
     Output({'type': 'solvent-select', 'index': ALL}, 'options'),
     Output("custom-solvent-name", "value"),
     Output({'type': 'custom-solvent-desc', 'index': ALL}, 'value'),
     Output("custom-solvent-collapse", "style", allow_duplicate=True),
     Output("toggle-custom-solvent-btn", "children", allow_duplicate=True),
     Output("validation-alert", "children", allow_duplicate=True),
     Output("validation-alert", "is_open", allow_duplicate=True)],
    Input("confirm-custom-solvent-btn", "n_clicks"),
    [State("custom-solvent-name", "value"),
     State({'type': 'custom-solvent-desc', 'index': ALL}, 'value'),
     State({'type': 'custom-solvent-desc', 'index': ALL}, 'id'),
     State("solvent-rows-container", "children"),
     State({'type': 'solvent-select', 'index': ALL}, 'options')],
    prevent_initial_call=True
)
def add_custom_solvent(n_clicks, name, desc_values, desc_ids, current_rows, current_options):
    """Add a custom solvent with all descriptor values to the list and select it"""
    if not n_clicks:
        raise PreventUpdate
    
    # Validate name
    if not name or not name.strip():
        alert = dbc.Alert("❌ Solvent name is required", color="danger")
        n_desc = len(desc_values)
        return (no_update, no_update, no_update, [no_update] * n_desc,
                no_update, no_update, alert, True)
    
    solvent_name = name.strip()
    
    # Check for duplicate name
    if solvent_name in COMMON_SOLVENTS:
        alert = dbc.Alert(f"❌ Solvent '{solvent_name}' already exists", color="danger")
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
    
    # === SUCCESS: Add to SOLVENT_DESCRIPTORS and COMMON_SOLVENTS ===
    SOLVENT_DESCRIPTORS[solvent_name] = descriptor_data
    COMMON_SOLVENTS.append(solvent_name)
    
    print(f"✅ Added custom solvent '{solvent_name}' to SOLVENT_DESCRIPTORS")
    print(f"   Descriptors: {descriptor_data}")
    
    # Update all dropdown options
    new_options = [{"label": s, "value": s} for s in sorted(COMMON_SOLVENTS)]
    updated_options = [new_options] * len(current_options)
    
    # Create a new row with the custom solvent already selected
    new_id = str(uuid.uuid4())
    new_row = html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'solvent-select', 'index': new_id},
                    options=new_options,
                    value=solvent_name,  # Pre-select the new solvent
                    placeholder="Select solvent",
                    clearable=True,
                    style={"fontSize": "0.875rem"}
                )
            ], width=10),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-solvent-row', 'index': new_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=2),
        ], className="mb-2 align-items-center"),
    ], id={'type': 'solvent-row', 'index': new_id})
    
    # Add the new row to current rows
    updated_rows = current_rows + [new_row]
    
    # Reset button text
    button_text = [
        html.I(className="bi bi-plus-circle me-1", style={"fontSize": "0.75rem"}),
        "Create Custom"
    ]
    
    alert = dbc.Alert([
        html.I(className="bi bi-check-circle-fill me-2"),
        f"✅ Added custom solvent: {solvent_name}"
    ], color="success")
    
    # Clear all descriptor inputs
    cleared_desc_values = [None] * len(desc_values)
    
    # Return: updated rows, updated options, clear name, clear descriptors, close collapse, reset button, alert
    return (updated_rows, updated_options, "", cleared_desc_values,
            {"display": "none"}, button_text, alert, True)

# ===== INITIALIZE MODAL WITH DEFAULT ROWS =====

@callback(
    Output("solvent-rows-container", "children", allow_duplicate=True),
    Input("solvent-modal", "is_open"),
    prevent_initial_call=True
)
def initialize_modal_content(is_open):
    """Initialize modal with one solvent row when opened via button"""
    triggered_id = ctx.triggered_id
    
    if triggered_id != "add-solvent-button":
        raise PreventUpdate
    
    if is_open:
        solvent_id = str(uuid.uuid4())
        return [create_solvent_row(solvent_id)]
    
    raise PreventUpdate

# ===== MANAGE SOLVENT ROWS =====

@callback(
    Output("solvent-rows-container", "children", allow_duplicate=True),
    [Input("add-solvent-row-btn", "n_clicks"),
     Input({'type': 'delete-solvent-row', 'index': ALL}, 'n_clicks')],
    State("solvent-rows-container", "children"),
    prevent_initial_call=True
)
def manage_solvent_rows(add_clicks, delete_clicks, current_rows):
    """Handle adding and deleting solvent rows"""
    triggered = ctx.triggered_id
    
    if triggered == "add-solvent-row-btn":
        if not add_clicks:
            raise PreventUpdate
        new_id = str(uuid.uuid4())
        new_row = create_solvent_row(new_id)
        return current_rows + [new_row]
    
    elif isinstance(triggered, dict) and triggered.get('type') == 'delete-solvent-row':
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
            new_rows = [create_solvent_row(new_id)]
        
        return new_rows
    
    raise PreventUpdate


# ===== SAVE SOLVENT CONFIGURATION =====

@callback(
    [Output("parameter-container", "children", allow_duplicate=True),
     Output("solvent-config-store", "data"),
     Output("validation-alert", "children", allow_duplicate=True),
     Output("validation-alert", "is_open", allow_duplicate=True)],
    Input("save-solvents-btn", "n_clicks"),
    [State({'type': 'solvent-select', 'index': ALL}, 'value'),
     State("parameter-container", "children"),
     State("solvent-config-store", "data")],
    prevent_initial_call=True
)
def save_solvent_configuration(n_clicks, solvents, current_params, current_config):
    """Save the selected solvents and descriptors as a categorical parameter"""
    if not n_clicks:
        raise PreventUpdate
    
    # Filter out None/empty values
    selected_solvents = [s for s in solvents if s]
    selected_descriptors = FIXED_SOLVENT_DESCRIPTORS
    
    if not selected_solvents:
        alert = dbc.Alert("❌ Please select at least one solvent", color="danger")
        return no_update, no_update, alert, True
    
    print(f"✅ Saved solvents: {selected_solvents}")
    print(f"✅ Using fixed descriptors: {selected_descriptors}")
    
    # Get existing solvent parameter ID if it exists
    solvent_param_id = None
    if current_config and 'param_id' in current_config:
        solvent_param_id = current_config['param_id']
    
    if solvent_param_id is None:
        solvent_param_id = str(uuid.uuid4())
    
    # Store configuration with parameter ID
    # No more 'custom_solvents' with SMILES - custom solvents are now in SOLVENT_DESCRIPTORS
    config_data = {
        'param_id': solvent_param_id,
        'solvents': selected_solvents,
        'descriptors': selected_descriptors,
    }
    
    # Remove existing Solvent parameter if it exists
    updated_params = []
    for param in current_params:
        try:
            param_row_id = param['props']['id']
            if param_row_id['type'] == 'parameter-row' and param_row_id['index'] == solvent_param_id:
                continue
        except:
            pass
        updated_params.append(param)
    
    # Create solvent parameter row
    solvent_values = ", ".join(selected_solvents)
    descriptor_info = f"Descriptors: {', '.join(selected_descriptors)}"
    
    new_row = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Input(
                    id={'type': 'parameter-name', 'index': solvent_param_id},
                    value="Solvent",
                    size="sm",
                    style={"borderRadius": "6px"},
                    disabled=True
                )
            ], width=3),
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'parameter-type', 'index': solvent_param_id},
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
                html.Div(id={'type': 'parameter-inputs', 'index': solvent_param_id}, children=[
                    html.Div([
                        dbc.Input(
                            id={'type': 'parameter-categories', 'index': solvent_param_id},
                            value=solvent_values,
                            type="text",
                            size="sm",
                            disabled=True,
                            style={"borderRadius": "6px"}
                        ),
                        dbc.Tooltip(
                            descriptor_info,
                            target={'type': 'parameter-categories', 'index': solvent_param_id},
                            placement="top"
                        )
                    ])
                ])
            ], width=5),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-pencil-square", style={"fontSize": "0.875rem"}),
                    id={'type': 'edit-solvent', 'index': solvent_param_id},
                    color="primary",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=1),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-parameter', 'index': solvent_param_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=1),
        ], className="mb-2 align-items-center"),
    ], id={'type': 'parameter-row', 'index': solvent_param_id})
    
    updated_params = [new_row] + updated_params
    
    alert = dbc.Alert([
        html.I(className="bi bi-check-circle-fill me-2"),
        f"Saved {len(selected_solvents)} solvent(s) as parameter"
    ], color="success")
    
    return updated_params, config_data, alert, True

# ===== EDIT SOLVENT - REOPEN MODAL WITH CURRENT VALUES =====

@callback(
    [Output("solvent-modal", "is_open", allow_duplicate=True),
     Output("solvent-rows-container", "children", allow_duplicate=True)],
    Input({'type': 'edit-solvent', 'index': ALL}, 'n_clicks'),
    State("solvent-config-store", "data"),
    prevent_initial_call=True
)
def edit_solvent_parameter(n_clicks, config_data):
    """Reopen modal with current solvent configuration"""
    if not any(n_clicks) or not config_data:
        raise PreventUpdate
    
    selected_solvents = config_data.get('solvents', [])
    
    # Recreate solvent rows with selected values
    solvent_rows = []
    for solvent in selected_solvents:
        row_id = str(uuid.uuid4())
        solvent_rows.append(html.Div([
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id={'type': 'solvent-select', 'index': row_id},
                        options=[{"label": s, "value": s} for s in sorted(COMMON_SOLVENTS)],
                        value=solvent,
                        placeholder="Select solvent",
                        clearable=True,
                        style={"fontSize": "0.875rem"}
                    )
                ], width=10),
                dbc.Col([
                    dbc.Button(
                        html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                        id={'type': 'delete-solvent-row', 'index': row_id},
                        color="danger",
                        outline=True,
                        size="sm",
                        style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                    )
                ], width=2),
            ], className="mb-2 align-items-center"),
        ], id={'type': 'solvent-row', 'index': row_id}))
    
    if not solvent_rows:
        row_id = str(uuid.uuid4())
        solvent_rows = [create_solvent_row(row_id)]
    
    return True, solvent_rows
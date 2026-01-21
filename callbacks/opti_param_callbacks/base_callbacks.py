"""
Bases and descriptors configuration callbacks
Handles base selection modal and related functionality
"""

from dash import callback, Input, Output, State, ALL, ctx, html, dcc, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid


# Common bases list (mutable to allow adding custom bases)
COMMON_BASES = [
    "Triethylamine", "Pyridine", "DIPEA", "DBU", "Sodium hydroxide",
    "Potassium carbonate", "Cesium carbonate", "Sodium bicarbonate",
    "DMAP", "Imidazole", "Potassium tert-butoxide", "Lithium diisopropylamide"
]

# Common descriptors list
COMMON_BASE_DESCRIPTORS = [
    "pKa", "Basicity", "Nucleophilicity", "Steric hindrance",
    "Solubility", "Boiling point", "Molecular weight", "Dipole moment"
]

# Store custom bases with their SMILES
CUSTOM_BASES = {}


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


def create_base_descriptor_row(row_id):
    """Create a single descriptor selection row for bases"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'base-descriptor-select', 'index': row_id},
                    options=[{"label": d, "value": d} for d in COMMON_BASE_DESCRIPTORS],
                    placeholder="Select descriptor",
                    clearable=True,
                    style={"fontSize": "0.875rem"}
                )
            ], width=10),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-base-descriptor-row', 'index': row_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=2),
        ], className="mb-2 align-items-center"),
    ], id={'type': 'base-descriptor-row', 'index': row_id})


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
    [Output("custom-base-collapse", "is_open"),
     Output("toggle-custom-base", "children")],
    Input("toggle-custom-base", "n_clicks"),
    State("custom-base-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_custom_base_collapse(n_clicks, is_open):
    """Toggle custom base form"""
    if n_clicks:
        new_state = not is_open
        button_text = [
            html.I(className="bi bi-flask me-2"),
            "Create Custom Base"
        ]
        return new_state, button_text
    raise PreventUpdate


# ===== ADD CUSTOM BASE =====

@callback(
    [Output("base-rows-container", "children", allow_duplicate=True),
     Output({'type': 'base-select', 'index': ALL}, 'options'),
     Output("custom-base-name", "value"),
     Output("custom-base-smiles", "value"),
     Output("custom-base-collapse", "is_open", allow_duplicate=True),
     Output("toggle-custom-base", "children", allow_duplicate=True),
     Output("validation-alert", "children", allow_duplicate=True),
     Output("validation-alert", "is_open", allow_duplicate=True)],
    Input("confirm-custom-base-btn", "n_clicks"),
    [State("custom-base-name", "value"),
     State("custom-base-smiles", "value"),
     State("base-rows-container", "children"),
     State({'type': 'base-select', 'index': ALL}, 'options')],
    prevent_initial_call=True
)
def add_custom_base(n_clicks, name, smiles, current_rows, current_options):
    """Add a custom base to the list and create a new row with it selected"""
    if not n_clicks:
        raise PreventUpdate
    
    # Validate inputs
    if not name or not name.strip():
        alert = dbc.Alert("❌ Base name is required", color="danger")
        return no_update, no_update, no_update, no_update, no_update, no_update, alert, True
    
    if not smiles or not smiles.strip():
        alert = dbc.Alert("❌ SMILES is required", color="danger")
        return no_update, no_update, no_update, no_update, no_update, no_update, alert, True
    
    # Add to global lists
    base_name = name.strip()
    if base_name not in COMMON_BASES:
        COMMON_BASES.append(base_name)
        CUSTOM_BASES[base_name] = smiles.strip()
    
    # Update all dropdown options
    new_options = [{"label": b, "value": b} for b in COMMON_BASES]
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
        html.I(className="bi bi-flask me-2"),
        "Create Custom Base"
    ]
    
    alert = dbc.Alert([
        html.I(className="bi bi-check-circle-fill me-2"),
        f"✅ Added custom base: {base_name}"
    ], color="success")
    
    return updated_rows, updated_options, "", "", False, button_text, alert, True


# ===== INITIALIZE MODAL WITH DEFAULT ROWS =====

@callback(
    [Output("base-rows-container", "children", allow_duplicate=True),
     Output("base-descriptor-rows-container", "children", allow_duplicate=True)],
    Input("base-modal", "is_open"),
    prevent_initial_call=True
)
def initialize_base_modal_content(is_open):
    """Initialize modal with one base row and one descriptor row when opened via button"""
    # Only initialize if modal was opened by the "Base" button, not by the "Edit" button
    triggered_id = ctx.triggered_id
    
    # If opened by edit button, don't reinitialize (it's already filled by edit_base_parameter)
    if triggered_id != "add-base-button":
        raise PreventUpdate
    
    if is_open:
        base_id = str(uuid.uuid4())
        descriptor_id = str(uuid.uuid4())
        
        return [create_base_row(base_id)], [create_base_descriptor_row(descriptor_id)]
    
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
        # Add new base row
        if not add_clicks:
            raise PreventUpdate
        
        new_id = str(uuid.uuid4())
        new_row = create_base_row(new_id)
        return current_rows + [new_row]
    
    elif isinstance(triggered, dict) and triggered.get('type') == 'delete-base-row':
        # Delete base row
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
        
        # Keep at least one row
        if not new_rows:
            new_id = str(uuid.uuid4())
            new_rows = [create_base_row(new_id)]
        
        return new_rows
    
    raise PreventUpdate


# ===== MANAGE BASE DESCRIPTOR ROWS =====

@callback(
    Output("base-descriptor-rows-container", "children", allow_duplicate=True),
    [Input("add-base-descriptor-row-btn", "n_clicks"),
     Input({'type': 'delete-base-descriptor-row', 'index': ALL}, 'n_clicks')],
    State("base-descriptor-rows-container", "children"),
    prevent_initial_call=True
)
def manage_base_descriptor_rows(add_clicks, delete_clicks, current_rows):
    """Handle adding and deleting base descriptor rows"""
    triggered = ctx.triggered_id
    
    if triggered == "add-base-descriptor-row-btn":
        # Add new descriptor row
        if not add_clicks:
            raise PreventUpdate
        
        new_id = str(uuid.uuid4())
        new_row = create_base_descriptor_row(new_id)
        return current_rows + [new_row]
    
    elif isinstance(triggered, dict) and triggered.get('type') == 'delete-base-descriptor-row':
        # Delete descriptor row
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
        
        # Keep at least one row
        if not new_rows:
            new_id = str(uuid.uuid4())
            new_rows = [create_base_descriptor_row(new_id)]
        
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
     State({'type': 'base-descriptor-select', 'index': ALL}, 'value'),
     State("parameter-container", "children"),
     State("base-config-store", "data")],
    prevent_initial_call=True
)
def save_base_configuration(n_clicks, bases, descriptors, current_params, current_config):
    """Save the selected bases and descriptors as a categorical parameter"""
    if not n_clicks:
        raise PreventUpdate
    
    # Filter out None/empty values
    selected_bases = [b for b in bases if b]
    selected_descriptors = [d for d in descriptors if d]
    
    if not selected_bases:
        alert = dbc.Alert("❌ Please select at least one base", color="danger")
        return no_update, no_update, alert, True
    
    print(f"✅ Saved bases: {selected_bases}")
    print(f"✅ Saved descriptors: {selected_descriptors}")
    
    # Print SMILES for custom bases
    for base in selected_bases:
        if base in CUSTOM_BASES:
            print(f"   - {base}: {CUSTOM_BASES[base]}")
    
    # Get existing base parameter ID if it exists
    base_param_id = None
    if current_config and 'param_id' in current_config:
        base_param_id = current_config['param_id']
    
    # If no existing ID, create new one
    if base_param_id is None:
        base_param_id = str(uuid.uuid4())
    
    # Store configuration with parameter ID
    config_data = {
        'param_id': base_param_id,
        'bases': selected_bases,
        'descriptors': selected_descriptors,
        'custom_bases': {b: CUSTOM_BASES[b] for b in selected_bases if b in CUSTOM_BASES}
    }
    
    # Remove existing Base parameter if it exists (using the stored ID)
    updated_params = []
    for param in current_params:
        try:
            param_row_id = param['props']['id']
            if param_row_id['type'] == 'parameter-row' and param_row_id['index'] == base_param_id:
                # Skip this parameter, we'll recreate it
                continue
        except:
            pass
        updated_params.append(param)
    
    # Create base parameter row
    base_values = ", ".join(selected_bases)
    descriptor_info = f"Descriptors: {', '.join(selected_descriptors)}" if selected_descriptors else "No descriptors selected"
    
    new_row = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Input(
                    id={'type': 'parameter-name', 'index': base_param_id},
                    value="Base",
                    size="sm",
                    style={"borderRadius": "6px"},
                    disabled=True  # Can't edit the name
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
                    disabled=True,  # Can't change type
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
                            disabled=True,  # Can't edit directly
                            style={"borderRadius": "6px"}
                        ),
                        dbc.Tooltip(
                            descriptor_info,
                            target={'type': 'parameter-categories', 'index': base_param_id},
                            placement="top"
                        ) if selected_descriptors else None
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
    
    # Add to beginning of parameters list
    updated_params = [new_row] + updated_params
    
    alert = dbc.Alert([
        html.I(className="bi bi-check-circle-fill me-2"),
        f"Saved {len(selected_bases)} base(s) as parameter"
    ], color="success")
    
    return updated_params, config_data, alert, True

# ===== EDIT BASE - REOPEN MODAL WITH CURRENT VALUES =====

@callback(
    [Output("base-modal", "is_open", allow_duplicate=True),
     Output("base-rows-container", "children", allow_duplicate=True),
     Output("base-descriptor-rows-container", "children", allow_duplicate=True)],
    Input({'type': 'edit-base', 'index': ALL}, 'n_clicks'),
    State("base-config-store", "data"),
    prevent_initial_call=True
)
def edit_base_parameter(n_clicks, config_data):
    """Reopen modal with current base configuration"""
    if not any(n_clicks) or not config_data:
        raise PreventUpdate
    
    selected_bases = config_data.get('bases', [])
    selected_descriptors = config_data.get('descriptors', [])
    custom_bases = config_data.get('custom_bases', {})
    
    # Add custom bases back to COMMON_BASES if needed
    for base_name, smiles in custom_bases.items():
        if base_name not in COMMON_BASES:
            COMMON_BASES.append(base_name)
            CUSTOM_BASES[base_name] = smiles
    
    # Recreate base rows with selected values
    base_rows = []
    for base in selected_bases:
        row_id = str(uuid.uuid4())
        base_rows.append(html.Div([
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id={'type': 'base-select', 'index': row_id},
                        options=[{"label": b, "value": b} for b in COMMON_BASES],
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
    
    # If no bases, add empty row
    if not base_rows:
        row_id = str(uuid.uuid4())
        base_rows = [create_base_row(row_id)]
    
    # Recreate descriptor rows with selected values
    descriptor_rows = []
    for descriptor in selected_descriptors:
        row_id = str(uuid.uuid4())
        descriptor_rows.append(html.Div([
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id={'type': 'base-descriptor-select', 'index': row_id},
                        options=[{"label": d, "value": d} for d in COMMON_BASE_DESCRIPTORS],
                        value=descriptor,
                        placeholder="Select descriptor",
                        clearable=True,
                        style={"fontSize": "0.875rem"}
                    )
                ], width=10),
                dbc.Col([
                    dbc.Button(
                        html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                        id={'type': 'delete-base-descriptor-row', 'index': row_id},
                        color="danger",
                        outline=True,
                        size="sm",
                        style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                    )
                ], width=2),
            ], className="mb-2 align-items-center"),
        ], id={'type': 'base-descriptor-row', 'index': row_id}))
    
    # If no descriptors, add empty row
    if not descriptor_rows:
        row_id = str(uuid.uuid4())
        descriptor_rows = [create_base_descriptor_row(row_id)]
    
    return True, base_rows, descriptor_rows
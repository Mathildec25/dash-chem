"""
Solvents and descriptors configuration callbacks
Handles solvent selection modal and related functionality
"""

from dash import callback, Input, Output, State, ALL, ctx, html, dcc, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid


# Common solvents list (mutable to allow adding custom solvents)
COMMON_SOLVENTS = [
    "Water", "Methanol", "Ethanol", "Acetone", "DMSO", "DMF", 
    "Acetonitrile", "THF", "Dichloromethane", "Chloroform",
    "Toluene", "Hexane", "Diethyl ether", "Ethyl acetate"
]

# Common descriptors list
COMMON_DESCRIPTORS = [
    "Polarity", "Boiling point", "Viscosity", "Dielectric constant",
    "Dipole moment", "Hydrogen bond donor", "Hydrogen bond acceptor",
    "Surface tension", "Refractive index", "Density"
]

# Store custom solvents with their SMILES
CUSTOM_SOLVENTS = {}


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


def create_descriptor_row(row_id):
    """Create a single descriptor selection row"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'descriptor-select', 'index': row_id},
                    options=[{"label": d, "value": d} for d in COMMON_DESCRIPTORS],
                    placeholder="Select descriptor",
                    clearable=True,
                    style={"fontSize": "0.875rem"}
                )
            ], width=10),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-descriptor-row', 'index': row_id},
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                )
            ], width=2),
        ], className="mb-2 align-items-center"),
    ], id={'type': 'descriptor-row', 'index': row_id})


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
    [Output("custom-solvent-collapse", "is_open"),
     Output("toggle-custom-solvent", "children")],
    Input("toggle-custom-solvent", "n_clicks"),
    State("custom-solvent-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_custom_solvent_collapse(n_clicks, is_open):
    """Toggle custom solvent form"""
    if n_clicks:
        new_state = not is_open
        button_text = [
            html.I(className="bi bi-flask me-2"),
            "Create Custom Solvent"
        ]
        return new_state, button_text
    raise PreventUpdate


# ===== ADD CUSTOM SOLVENT =====

@callback(
    [Output("solvent-rows-container", "children", allow_duplicate=True),
     Output({'type': 'solvent-select', 'index': ALL}, 'options'),
     Output("custom-solvent-name", "value"),
     Output("custom-solvent-smiles", "value"),
     Output("custom-solvent-collapse", "is_open", allow_duplicate=True),
     Output("toggle-custom-solvent", "children", allow_duplicate=True),
     Output("validation-alert", "children", allow_duplicate=True),
     Output("validation-alert", "is_open", allow_duplicate=True)],
    Input("confirm-custom-solvent-btn", "n_clicks"),
    [State("custom-solvent-name", "value"),
     State("custom-solvent-smiles", "value"),
     State("solvent-rows-container", "children"),
     State({'type': 'solvent-select', 'index': ALL}, 'options')],
    prevent_initial_call=True
)
def add_custom_solvent(n_clicks, name, smiles, current_rows, current_options):
    """Add a custom solvent to the list and create a new row with it selected"""
    if not n_clicks:
        raise PreventUpdate
    
    # Validate inputs
    if not name or not name.strip():
        alert = dbc.Alert("❌ Solvent name is required", color="danger")
        return no_update, no_update, no_update, no_update, no_update, no_update, alert, True
    
    if not smiles or not smiles.strip():
        alert = dbc.Alert("❌ SMILES is required", color="danger")
        return no_update, no_update, no_update, no_update, no_update, no_update, alert, True
    
    # Add to global lists
    solvent_name = name.strip()
    if solvent_name not in COMMON_SOLVENTS:
        COMMON_SOLVENTS.append(solvent_name)
        CUSTOM_SOLVENTS[solvent_name] = smiles.strip()
    
    # Update all dropdown options
    new_options = [{"label": s, "value": s} for s in COMMON_SOLVENTS]
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
        html.I(className="bi bi-flask me-2"),
        "Create Custom Solvent"
    ]
    
    alert = dbc.Alert([
        html.I(className="bi bi-check-circle-fill me-2"),
        f"✅ Added custom solvent: {solvent_name}"
    ], color="success")
    
    # Return: updated rows, updated options for ALL dropdowns, clear inputs, close collapse, reset button, show alert
    return updated_rows, updated_options, "", "", False, button_text, alert, True

# ===== INITIALIZE MODAL WITH DEFAULT ROWS =====

@callback(
    [Output("solvent-rows-container", "children"),
     Output("descriptor-rows-container", "children")],
    Input("solvent-modal", "is_open"),
    prevent_initial_call=True
)
def initialize_modal_content(is_open):
    """Initialize modal with one solvent row and one descriptor row when opened"""
    if is_open:
        solvent_id = str(uuid.uuid4())
        descriptor_id = str(uuid.uuid4())
        
        return [create_solvent_row(solvent_id)], [create_descriptor_row(descriptor_id)]
    
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
        # Add new solvent row
        if not add_clicks:
            raise PreventUpdate
        
        new_id = str(uuid.uuid4())
        new_row = create_solvent_row(new_id)
        return current_rows + [new_row]
    
    elif isinstance(triggered, dict) and triggered.get('type') == 'delete-solvent-row':
        # Delete solvent row
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
            new_rows = [create_solvent_row(new_id)]
        
        return new_rows
    
    raise PreventUpdate


# ===== MANAGE DESCRIPTOR ROWS =====

@callback(
    Output("descriptor-rows-container", "children", allow_duplicate=True),
    [Input("add-descriptor-row-btn", "n_clicks"),
     Input({'type': 'delete-descriptor-row', 'index': ALL}, 'n_clicks')],
    State("descriptor-rows-container", "children"),
    prevent_initial_call=True
)
def manage_descriptor_rows(add_clicks, delete_clicks, current_rows):
    """Handle adding and deleting descriptor rows"""
    triggered = ctx.triggered_id
    
    if triggered == "add-descriptor-row-btn":
        # Add new descriptor row
        if not add_clicks:
            raise PreventUpdate
        
        new_id = str(uuid.uuid4())
        new_row = create_descriptor_row(new_id)
        return current_rows + [new_row]
    
    elif isinstance(triggered, dict) and triggered.get('type') == 'delete-descriptor-row':
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
            new_rows = [create_descriptor_row(new_id)]
        
        return new_rows
    
    raise PreventUpdate


# ===== SAVE SOLVENT CONFIGURATION =====

@callback(
    [Output("validation-alert", "children", allow_duplicate=True),
     Output("validation-alert", "is_open", allow_duplicate=True)],
    Input("save-solvents-btn", "n_clicks"),
    [State({'type': 'solvent-select', 'index': ALL}, 'value'),
     State({'type': 'descriptor-select', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def save_solvent_configuration(n_clicks, solvents, descriptors):
    """Save the selected solvents and descriptors configuration"""
    if not n_clicks:
        raise PreventUpdate
    
    # Filter out None/empty values
    selected_solvents = [s for s in solvents if s]
    selected_descriptors = [d for d in descriptors if d]
    
    print(f"✅ Saved solvents: {selected_solvents}")
    print(f"✅ Saved descriptors: {selected_descriptors}")
    
    # Print SMILES for custom solvents
    for solvent in selected_solvents:
        if solvent in CUSTOM_SOLVENTS:
            print(f"   - {solvent}: {CUSTOM_SOLVENTS[solvent]}")
    
    # TODO: Store this configuration somewhere (could use dcc.Store or save to domain)
    
    alert = dbc.Alert([
        html.I(className="bi bi-check-circle-fill me-2"),
        f"Saved {len(selected_solvents)} solvent(s) and {len(selected_descriptors)} descriptor(s)"
    ], color="success")
    
    return alert, True
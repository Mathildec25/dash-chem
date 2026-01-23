"""
Constraints Card Component
Card for defining constraints in domain configuration
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_constraints_card():
    """
    Create the Constraints card component for domain configuration.
    
    This card appears when solvents are selected and allows defining
    constraints based on solvent boiling points.
    
    Returns:
        dbc.Card: The constraints card component
    """
    return dbc.Card([
        dbc.CardBody([
            # Header with title and add button
            html.Div([
                html.H5([
                    html.I(className="bi bi-sliders me-2", style={"color": "#6c757d"}),
                    "Constraints"
                ], className="mb-0", style={"fontWeight": "600", "display": "inline-block"}),
                dbc.Button([
                    html.I(className="bi bi-plus-lg me-1"),
                    "Add"
                ],
                id="add-constraint-btn",
                color="primary",
                size="sm",
                className="float-end",
                style={"borderRadius": "6px", "padding": "0.25rem 0.75rem"}
                ),
            ], className="mb-3"),
            
            # Info text
            html.P([
                html.I(className="bi bi-info-circle me-2"),
                "Define constraints to ensure parameters stay below solvent boiling points."
            ], className="text-muted small mb-3"),
            
            # Boiling point information display
            html.Div(id="bp-info-display", className="mb-3"),
            
            # Constraint type selector (for future expansion)
            html.Div([
                html.Label("Constraint Type", className="form-label small text-muted"),
                dcc.Dropdown(
                    id="constraint-type-select",
                    options=[
                        {"label": "Parameter < Minimum Boiling Point", "value": "less_than_min_bp"},
                    ],
                    value="less_than_min_bp",
                    clearable=False,
                    style={"fontSize": "0.875rem"},
                    disabled=True  # Only one type for now
                )
            ], className="mb-3"),
            
            # Constraints container
            html.Div(id="constraint-rows-container", children=[]),
            
            # Help text
            html.Div([
                html.Hr(className="my-3"),
                html.Small([
                    html.Strong("How it works: "),
                    "When you add a constraint, the selected parameter's upper bound will be ",
                    "automatically limited to the minimum boiling point of your selected solvents. ",
                    "This ensures the reaction temperature never exceeds the solvent's boiling point."
                ], className="text-muted")
            ])
        ], style={"padding": "1.25rem"})
    ], 
    id="constraints-card",
    style={
        "display": "none",  # Hidden by default, shown when solvents are configured
        "borderRadius": "12px",
        "border": "1px solid #e0e0e0",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
        "backgroundColor": "white",
        "marginTop": "1rem"
    })


def create_constraints_store():
    """
    Create the dcc.Store component for constraints data.
    
    Returns:
        dcc.Store: Store component for constraints
    """
    return dcc.Store(id='constraints-store', data=None, storage_type="session")

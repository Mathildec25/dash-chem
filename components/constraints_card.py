"""
Constraints Card Component
Card for defining constraints in domain configuration

UPDATED: Supports both boiling point (BP) and melting point (MP) constraints
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_constraints_card():
    """
    Create the Constraints card component for domain configuration.
    
    This card appears when solvents are selected and allows defining
    constraints based on solvent boiling points AND melting points.
    
    Returns:
        dbc.Card: The constraints card component
    """
    return dbc.Card([
        dbc.CardBody([
            # Header with title and add button
            html.Div([
                html.H5([
                    html.I(className="bi bi-sliders me-2", style={"color": "#6c757d"}),
                    "Phase Constraints"
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
                "Define constraints to ensure the solvent stays in liquid phase ",
                "(above melting point, below boiling point)."
            ], className="text-muted small mb-3"),
            
            # Boiling/Melting point information display
            html.Div(id="bp-info-display", className="mb-3"),
            
            # Constraints container
            html.Div(id="constraint-rows-container", children=[]),
            
            # Help text
            html.Div([
                html.Hr(className="my-3"),
                html.Small([
                    html.Strong("How it works: "),
                ], className="d-block mb-2"),
                html.Ul([
                    html.Li([
                        html.Strong("< Boiling Point: ", style={"color": "#dc3545"}),
                        "Prevents the solvent from boiling (too hot)"
                    ], className="small text-muted"),
                    html.Li([
                        html.Strong("> Melting Point: ", style={"color": "#0d6efd"}),
                        "Prevents the solvent from freezing (too cold)"
                    ], className="small text-muted"),
                ], className="mb-2", style={"paddingLeft": "1.2rem"}),
                html.Small([
                    html.I(className="bi bi-exclamation-triangle me-1", style={"color": "#ffc107"}),
                    "Note: Some solvents like DMSO (MP=18.5°C) and Water (MP=0°C) can freeze at common lab temperatures!"
                ], className="text-muted fst-italic")
            ], className="mt-3")
        ])
    ],
    id="constraints-card",
    style={
        "display": "none",  # Hidden by default, shown when solvents are configured
        "borderRadius": "12px",
        "border": "1px solid #e0e0e0",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
        "backgroundColor": "white"
    },
    className="mb-4"
    )
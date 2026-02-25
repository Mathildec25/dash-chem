"""
Constraints Card Component
Card for defining constraints in domain configuration

UPDATED: 
- Card is ALWAYS visible (not hidden by default)
- Phase constraints section (BP/MP) shown/hidden based on solvent config
- Linear constraints section always visible (inequality ≤ and equality =)
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_constraints_card():
    """
    Create the Constraints card component for domain configuration.
    
    This card is ALWAYS visible and contains two sections:
    1. Phase constraints (BP/MP) — shown only when solvents are configured
    2. Inter-parameter linear constraints — always available (≤ or =)
    
    Returns:
        dbc.Card: The constraints card component
    """
    return dbc.Card([
        dbc.CardBody([
            # ================================================================
            # CARD TITLE
            # ================================================================
            html.H5([
                html.I(className="bi bi-sliders me-2", style={"color": "#6c757d"}),
                "Constraints"
            ], className="mb-3", style={"fontWeight": "600"}),
            
            # ================================================================
            # SECTION 1: PHASE CONSTRAINTS (BP/MP) — conditionally visible
            # ================================================================
            html.Div([
                # Section header with add button
                html.Div([
                    html.H6([
                        html.I(className="bi bi-thermometer-half me-2", style={"color": "#dc3545"}),
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
                    "Ensure the solvent stays in liquid phase ",
                    "(above melting point, below boiling point)."
                ], className="text-muted small mb-3"),
                
                # Boiling/Melting point information display
                html.Div(id="bp-info-display", className="mb-3"),
                
                # Phase constraints container
                html.Div(id="constraint-rows-container", children=[]),
                
                # Help text for phase constraints
                html.Div([
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
                    ], className="mb-0", style={"paddingLeft": "1.2rem"}),
                ], className="mt-2"),
                
                html.Hr(className="my-4"),
            ],
            id="phase-constraints-section",
            style={"display": "none"}  # Hidden until solvents are configured
            ),
            
            # ================================================================
            # SECTION 2: INTER-PARAMETER LINEAR CONSTRAINTS — always visible
            # ================================================================
            
            # Section header with add button
            html.Div([
                html.H6([
                    html.I(className="bi bi-arrow-left-right me-2", style={"color": "#6c757d"}),
                    "Linear Constraints"
                ], className="mb-0", style={"fontWeight": "600", "display": "inline-block"}),
                dbc.Button([
                    html.I(className="bi bi-plus-lg me-1"),
                    "Add"
                ],
                id="add-ineq-constraint-btn",
                color="primary",
                outline=True,
                size="sm",
                className="float-end",
                style={"borderRadius": "6px", "padding": "0.25rem 0.75rem"}
                ),
            ], className="mb-3"),
            
            # Info text
            html.P([
                html.I(className="bi bi-info-circle me-2"),
                "Define relationships between two numerical parameters ",
                "(e.g., T\u2081 \u2264 T\u2082 + offset or C\u2081 = C\u2082 + offset)."
            ], className="text-muted small mb-3"),
            
            # Linear constraints container
            html.Div(id="ineq-constraint-rows-container", children=[]),
            
            # Help text for linear constraints
            html.Div([
                html.Small([
                    html.Strong("How it works: "),
                    "Choose ",
                    html.Code("\u2264",
                             style={"fontSize": "0.85rem", "backgroundColor": "#f0f0f0", 
                                    "padding": "2px 6px", "borderRadius": "3px"}),
                    " for inequality or ",
                    html.Code("=",
                             style={"fontSize": "0.85rem", "backgroundColor": "#f0f0f0", 
                                    "padding": "2px 6px", "borderRadius": "3px"}),
                    " for equality between ",
                    html.Code("Parameter A",
                             style={"fontSize": "0.8rem", "backgroundColor": "#f0f0f0", 
                                    "padding": "2px 4px", "borderRadius": "3px"}),
                    " and ",
                    html.Code("Parameter B + offset",
                             style={"fontSize": "0.8rem", "backgroundColor": "#f0f0f0", 
                                    "padding": "2px 4px", "borderRadius": "3px"}),
                    ". The offset can be 0 (strict) or any positive/negative value."
                ], className="text-muted")
            ], className="mt-2"),
        ])
    ],
    id="constraints-card",
    style={
        "borderRadius": "12px",
        "border": "1px solid #e0e0e0",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
        "backgroundColor": "white"
    },
    className="mb-4"
    )
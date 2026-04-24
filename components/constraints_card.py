"""Constraints card used in the domain-configuration page."""

import dash_bootstrap_components as dbc
from dash import html


def create_constraints_card():
    """
    Build the constraints card.

    The card is always visible and contains two sections:

    - Phase constraints (BP/MP) — hidden until solvents are configured.
    - Inter-parameter linear constraints (``<=`` / ``=``) — always visible.
    """
    return dbc.Card([
        dbc.CardBody([
            html.H5([
                html.I(className="bi bi-sliders me-2", style={"color": "#6c757d"}),
                "Constraints"
            ], className="mb-3", style={"fontWeight": "600"}),
            
            # Section 1: Phase constraints (BP/MP) - conditionally visible
            html.Div([
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
                
                html.P([
                    html.I(className="bi bi-info-circle me-2"),
                    "Ensure the solvent stays in liquid phase ",
                    "(above melting point, below boiling point)."
                ], className="text-muted small mb-3"),

                html.Div(id="bp-info-display", className="mb-3"),
                html.Div(id="constraint-rows-container", children=[]),

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
            style={"display": "none"},
            ),

            # Section 2: Inter-parameter linear constraints (always visible)
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

            html.P([
                html.I(className="bi bi-info-circle me-2"),
                "Define relationships between two numerical parameters ",
                "(e.g., T\u2081 \u2264 T\u2082 + offset or C\u2081 = C\u2082 + offset)."
            ], className="text-muted small mb-3"),

            html.Div(id="ineq-constraint-rows-container", children=[]),

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
"""
Layout for Run Optimization page
Displays editable experiment table and BO controls
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
from components.advanced_bo_settings import create_advanced_bo_settings


def create_opti_run_layout():
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                dcc.Link(
                    html.I(className="bi bi-arrow-left", style={"fontSize": "1.5rem", "color": "#6c757d"}),
                    href="/Opt-param",
                    style={"textDecoration": "none"}
                )
            ], width="auto"),
            dbc.Col([
                html.H1("Run Optimization", 
                       style={
                           "color": "#1a1a1a", 
                           "fontWeight": "600",
                           "fontSize": "2rem",
                           "letterSpacing": "-0.02em",
                           "marginBottom": "0.25rem"
                       }),
                html.P("Enter experiment results and run Bayesian optimization",
                      style={
                          "fontSize": "1rem",
                          "color": "#6c757d",
                          "marginBottom": "0"
                      })
            ], width=True),
            dbc.Col([
                html.Div(id="auto-save-indicator")
            ], width="auto", className="text-end")
        ], className="mb-4 align-items-center"),
        
        # Status Alert
        dbc.Row([
            dbc.Col([
                dbc.Alert(
                    id="run-status-alert",
                    is_open=False,
                    dismissable=True,
                    className="mb-3"
                )
            ], md=12)
        ]),
        
        # Table Card
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5("Experiments", className="mb-0", style={"fontWeight": "600"})
                            ]),
                            dbc.Col([
                                dbc.ButtonGroup([
                                    dbc.Button([
                                        html.I(className="bi bi-plus-lg me-1"),
                                        "Row"
                                    ],
                                    id="add-row-btn",
                                    color="primary",
                                    outline=True,
                                    size="sm"
                                    ),
                                    dbc.Button([
                                        html.I(className="bi bi-plus-lg me-1"),
                                        "Column"
                                    ],
                                    id="add-column-btn",
                                    color="secondary",
                                    outline=True,
                                    size="sm"
                                    ),
                                    dbc.Button([
                                        html.I(className="bi bi-trash me-1"),
                                        "Column"
                                    ],
                                    id="delete-column-btn",
                                    color="danger",
                                    outline=True,
                                    size="sm"
                                    ),
                                    dbc.Button([
                                        html.I(className="bi bi-save me-1"),
                                        "Save"
                                    ],
                                    id="save-table-btn",
                                    color="success",
                                    outline=True,
                                    size="sm"
                                    ),
                                ])
                            ], width="auto")
                        ], align="center")
                    ], style={"backgroundColor": "#f8f9fa", "padding": "1rem"}),
                    
                    dbc.CardBody([
                        html.Div(id="experiment-table-container", children=[
                            html.P("Loading experiments...", className="text-muted text-center py-5")
                        ])
                    ], style={"padding": "0"})
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
                    "backgroundColor": "white"
                })
            ], md=12, className="mb-3")
        ]),
        
        # Save Status
        dbc.Row([
            dbc.Col([
                dbc.Alert(
                    id="save-status",
                    is_open=False,
                    dismissable=True,
                    duration=3000,
                    className="mb-3"
                )
            ], md=12)
        ]),
        
        # Legend
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span([
                        html.Span(style={
                            "display": "inline-block",
                            "width": "12px",
                            "height": "12px",
                            "backgroundColor": "rgba(0, 123, 255, 0.3)",
                            "marginRight": "6px",
                            "borderRadius": "2px"
                        }),
                        "Parameters"
                    ], className="me-4"),
                    html.Span([
                        html.Span(style={
                            "display": "inline-block",
                            "width": "12px",
                            "height": "12px",
                            "backgroundColor": "rgba(40, 167, 69, 0.3)",
                            "marginRight": "6px",
                            "borderRadius": "2px"
                        }),
                        "Objectives"
                    ], className="me-4"),
                    html.Span([
                        html.Span(style={
                            "display": "inline-block",
                            "width": "12px",
                            "height": "12px",
                            "backgroundColor": "rgba(255, 193, 7, 0.3)",
                            "marginRight": "6px",
                            "borderRadius": "2px",
                            "border": "2px solid #ffc107"
                        }),
                        "Needs Result"
                    ])
                ], className="text-muted small")
            ], md=12, className="mb-3")
        ]),
        
        # Optimization Controls
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Bayesian Optimization", className="mb-3", style={"fontWeight": "600"}),
                        
                        # Boutons BO + Paramètres
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-lightning-charge me-2"),
                                    "Get New Experiment"
                                ],
                                id="run-bo-btn",
                                color="success",
                                size="lg",
                                className="w-100",
                                disabled=True,
                                style={
                                    "borderRadius": "8px",
                                    "fontWeight": "500"
                                })
                            ], md=9),
                            dbc.Col([
                                create_advanced_bo_settings()
                            ], md=3, className="d-flex align-items-center")
                        ])
                    ], style={"padding": "1.25rem"})
                ], style={
                    "borderRadius": "12px",
                    "border": "1px solid #e0e0e0",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
                    "backgroundColor": "white"
                })
            ], md=12, className="mb-3")
        ]),
        
        # ===== PARAMÈTRES AVANCÉS BO =====
        # (Le bouton et modal sont déjà dans la section au-dessus)
        
        # Store pour les paramètres avancés (valeurs par défaut)
        dcc.Store(id='advanced-bo-settings-store', data={
            'acquisition_function': 'qLogNEI (default)',
            'n_candidates': 1
        }),
        
        # BO Result Alert
        dbc.Row([
            dbc.Col([
                dbc.Alert(
                    id="bo-result-alert",
                    is_open=False,
                    dismissable=True,
                    className="mb-3"
                )
            ], md=12)
        ]),
        
        # Modals for column management
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Add New Column")),
            dbc.ModalBody([
                dbc.Label("Column Name:"),
                dbc.Input(id="opti-new-column-name", type="text", placeholder="Enter column name"),
                dbc.Label("Default Value (optional):", className="mt-3"),
                dbc.Input(id="opti-new-column-default", type="text", placeholder="Leave empty for blank cells")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="opti-cancel-add-column", color="secondary", outline=True),
                dbc.Button("Add Column", id="opti-confirm-add-column", color="primary")
            ])
        ], id="opti-add-column-modal", is_open=False),
        
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Delete Column")),
            dbc.ModalBody([
                dbc.Label("Select column to delete:"),
                dcc.Dropdown(id="opti-column-to-delete", placeholder="Choose a column...")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="opti-cancel-delete-column", color="secondary", outline=True),
                dbc.Button("Delete", id="opti-confirm-delete-column", color="danger")
            ])
        ], id="opti-delete-column-modal", is_open=False),
        
        # Navigation
        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Link(
                        dbc.Button([
                            html.I(className="bi bi-arrow-left me-2"),
                            "Back to Parameters"
                        ], color="secondary", outline=True, className="me-2"),
                        href="/Opt-param"
                    ),
                    dcc.Link(
                        dbc.Button([
                            "View Results & Analysis",
                            html.I(className="bi bi-arrow-right ms-2")
                        ], color="primary"),
                        href="/Opt-results"
                    )
                ], className="d-flex justify-content-between")
            ], md=12)
        ], className="mt-4")
        
    ], fluid=True, style={"maxWidth": "1400px", "paddingTop": "2rem", "paddingBottom": "3rem"})
"""
Improved Optimization Run Layout with configurable Bayesian Optimization parameters
"""

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import dcc, html
from components.advanced_bo_settings import create_advanced_bo_settings

import uuid

def create_opti_run_layout():
    """Create the experiment management and optimization layout with BO configuration"""
    
    return dbc.Container([
        # Header with project info
        dbc.Row([
            dbc.Col([
                html.H2("Experiment Manager", className="mb-2", style={"fontWeight": "700", "color": "#1e293b"}),
                html.P("Run experiments and optimize with AI", className="text-muted mb-4")
            ], md=12)
        ]),
        
        # Status Alert
        dbc.Row([
            dbc.Col([
                dbc.Alert(
                    id="opti-run-status-alert",
                    is_open=False,
                    dismissable=True,
                    className="mb-3"
                )
            ], md=12)
        ]),
        
        # Table Controls Row
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="bi bi-plus-circle me-2"),
                        "Add Row"
                    ], id="add-row-btn-opti", outline=True, color="primary", size="sm"),
                    dbc.Button([
                        html.I(className="bi bi-plus-square me-2"),
                        "Add Column"
                    ], id="opti-add-column-btn", outline=True, color="secondary", size="sm"),
                    dbc.Button([
                        html.I(className="bi bi-trash me-2"),
                        "Delete Column"
                    ], id="opti-delete-column-btn", outline=True, color="danger", size="sm"),
                ], className="mb-3")
            ], md=6),
            dbc.Col([
                dbc.Button([
                    html.I(className="bi bi-save me-2"),
                    "Save Changes"
                ], id="save-table-btn-opti", color="success", size="sm", className="float-end mb-3")
            ], md=6),
        ]),
        
        # Experiments Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Experiments", className="mb-0", style={"fontWeight": "600"})
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        html.Div(id="opti-table-container", style={"overflowX": "auto"}),
                        html.Div([
                            html.Span([
                                html.Span(style={
                                    "display": "inline-block",
                                    "width": "12px",
                                    "height": "12px",
                                    "backgroundColor": "rgba(99, 102, 241, 0.3)",
                                    "marginRight": "6px",
                                    "borderRadius": "2px",
                                    "border": "2px solid #6366f1"
                                }),
                                "Parameters"
                            ], className="me-4"),
                            html.Span([
                                html.Span(style={
                                    "display": "inline-block",
                                    "width": "12px",
                                    "height": "12px",
                                    "backgroundColor": "rgba(16, 185, 129, 0.3)",
                                    "marginRight": "6px",
                                    "borderRadius": "2px",
                                    "border": "2px solid #10b981"
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
                        ], className="text-muted small mt-2")
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=12, className="mb-3")
        ]),
        
        # Optimization Controls
        # ============================================
        # BAYESIAN OPTIMIZATION CONFIGURATION CARD
        # ============================================
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(className="bi bi-gear-fill me-2", style={"color": "#6366f1"}),
                            html.H5("Bayesian Optimization Configuration", className="d-inline mb-0", style={"fontWeight": "600"}),
                        ])
                    ], style={"backgroundColor": "#f8f9fa"}),
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
                        # Basic Settings
                        dbc.Row([
                            dbc.Col([
                                html.Label("Number of Suggestions", className="form-label small fw-bold text-muted mb-2"),
                                dbc.Input(
                                    id="bo-n-candidates",
                                    type="number",
                                    value=1,
                                    min=1,
                                    max=10,
                                    size="sm",
                                    style={"borderRadius": "6px"}
                                ),
                                html.Small("How many experiments to suggest per iteration", className="text-muted")
                            ], md=4, className="mb-3"),
                            
                            dbc.Col([
                                html.Label("Acquisition Function", className="form-label small fw-bold text-muted mb-2"),
                                dcc.Dropdown(
                                    id="bo-acquisition-function",
                                    options=[
                                        {"label": "qLogNEI (Recommended)", "value": "qLogNEI"},
                                        {"label": "qLogNEHVI (Multi-objective)", "value": "qLogNEHVI"},
                                        {"label": "qEI (Expected Improvement)", "value": "qEI"},
                                        {"label": "qUCB (Upper Confidence Bound)", "value": "qUCB"},
                                    ],
                                    value="qLogNEI",
                                    clearable=False,
                                    style={"fontSize": "0.875rem"}
                                ),
                                html.Small("Strategy for selecting next experiments", className="text-muted")
                            ], md=4, className="mb-3"),
                            
                            dbc.Col([
                                html.Label("Optimization Strategy", className="form-label small fw-bold text-muted mb-2"),
                                dcc.Dropdown(
                                    id="bo-strategy-type",
                                    options=[
                                        {"label": "Auto (Recommended)", "value": "auto"},
                                        {"label": "SOBO (Single Objective)", "value": "sobo"},
                                        {"label": "MOBO (Multi Objective)", "value": "mobo"},
                                    ],
                                    value="auto",
                                    clearable=False,
                                    style={"fontSize": "0.875rem"}
                                ),
                                html.Small("Automatically selected based on objectives", className="text-muted")
                            ], md=4, className="mb-3"),
                        ]),
                        
                        # Advanced Settings (Collapsible)
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-sliders me-2"),
                                    "Advanced Settings"
                                ],
                                id="toggle-bo-advanced",
                                outline=True,
                                color="secondary",
                                size="sm",
                                className="mb-3",
                                style={"borderRadius": "6px"}
                                ),
                                
                                dbc.Collapse([
                                    dbc.Card([
                                        dbc.CardBody([
                                            dbc.Row([
                                                dbc.Col([
                                                    html.Label("UCB Beta", className="form-label small fw-bold text-muted mb-2"),
                                                    dbc.Input(
                                                        id="bo-ucb-beta",
                                                        type="number",
                                                        value=2.0,
                                                        step=0.1,
                                                        size="sm",
                                                        style={"borderRadius": "6px"}
                                                    ),
                                                    html.Small("Exploration-exploitation trade-off (only for UCB)", className="text-muted")
                                                ], md=6, className="mb-3"),
                                                
                                                dbc.Col([
                                                    html.Label("Num Restarts", className="form-label small fw-bold text-muted mb-2"),
                                                    dbc.Input(
                                                        id="bo-num-restarts",
                                                        type="number",
                                                        value=20,
                                                        min=1,
                                                        max=100,
                                                        size="sm",
                                                        style={"borderRadius": "6px"}
                                                    ),
                                                    html.Small("Number of optimization restarts", className="text-muted")
                                                ], md=6, className="mb-3"),
                                            ]),
                                            
                                            dbc.Row([
                                                dbc.Col([
                                                    html.Label("Raw Samples", className="form-label small fw-bold text-muted mb-2"),
                                                    dbc.Input(
                                                        id="bo-raw-samples",
                                                        type="number",
                                                        value=512,
                                                        min=128,
                                                        max=2048,
                                                        step=128,
                                                        size="sm",
                                                        style={"borderRadius": "6px"}
                                                    ),
                                                    html.Small("Initial samples for acquisition optimization", className="text-muted")
                                                ], md=6, className="mb-3"),
                                                
                                                dbc.Col([
                                                    dbc.Checklist(
                                                        options=[
                                                            {"label": " Use sequential optimization", "value": "sequential"}
                                                        ],
                                                        value=[],
                                                        id="bo-sequential",
                                                        className="mt-4"
                                                    ),
                                                ], md=6),
                                            ]),
                                        ], style={"backgroundColor": "#f8f9fa", "padding": "1rem"})
                                    ], style={"border": "1px solid #e0e0e0", "borderRadius": "8px"})
                                ], id="bo-advanced-collapse", is_open=False),
                            ], md=12)
                        ]),
                        
                        # Run BO Button
                        html.Hr(className="my-3"),
                        dbc.Button([
                            html.I(className="bi bi-lightning-charge me-2"),
                            "Generate AI Suggestions"
                        ],
                        id="run-bo-btn",
                        color="success",
                        size="lg",
                        className="w-100",
                        disabled=True,
                        style={
                            "borderRadius": "8px",
                            "fontWeight": "600",
                            "boxShadow": "0 2px 8px rgba(16, 185, 129, 0.2)"
                        }
                        ),
                        
                        # Info text
                        html.Div([
                            html.I(className="bi bi-info-circle me-2", style={"color": "#6366f1"}),
                            html.Small("Complete at least 2 experiments with results to enable optimization", 
                                      className="text-muted")
                        ], className="mt-3 text-center")
                        
                    ], style={"padding": "1.5rem"})
                ], style={
                    "borderRadius": "12px",
                    "border": "2px solid #6366f1",
                    "boxShadow": "0 4px 12px rgba(99, 102, 241, 0.15)"
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
        # Navigation buttons
        dbc.Row([
            dbc.Col([
                dcc.Link(
                    dbc.Button([
                        html.I(className="bi bi-graph-up me-2"),
                        "View Results & Analysis"
                    ],
                    color="primary",
                    outline=True,
                    className="w-100",
                    style={"borderRadius": "8px"}
                    ),
                    href="/Opt-results"
                )
            ], md=6, className="mx-auto")
        ], className="mt-4"),
        
        # Modals for adding/deleting columns
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
        # Hidden store for BO configuration
        dcc.Store(id='bo-config-store', storage_type='session'),
        
    ], fluid=True, style={
        "maxWidth": "1400px",
        "backgroundColor": "#f8f9fa",
        "minHeight": "100vh",
        "paddingTop": "2rem",
        "paddingBottom": "4rem"
    })
"""
Layout for the Sensitivity Screen page.
Accessed from the Opt-run page via a button.
Inspired by Glorius et al. (Angew. Chem. Int. Ed. 2019, Chem. Sci. 2024).

The table is automatically pre-filled on page load with the best BO point.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


ACCENT = "#6366f1"
SUCCESS = "#10b981"


def create_sensitivity_layout():
    return dbc.Container([

        # Hidden stores
        dcc.Store(id="sensitivity-experiments-store", storage_type="session"),
        dcc.Store(id="sensitivity-reference-store", storage_type="session"),

        # ===== HEADER =====
        dbc.Row([
            dbc.Col([
                dcc.Link(
                    html.I(className="bi bi-arrow-left",
                           style={"fontSize": "1.5rem", "color": "#6c757d"}),
                    href="/Opt-run",
                    style={"textDecoration": "none"}
                )
            ], width="auto"),
            dbc.Col([
                html.H1("Sensitivity Screen",
                         style={"color": "#1a1a1a", "fontWeight": "600",
                                "fontSize": "2rem", "letterSpacing": "-0.02em",
                                "marginBottom": "0.25rem"}),
                html.P([
                    "Assess the robustness of your optimum — inspired by ",
                    html.A("Glorius et al.",
                           href="https://doi.org/10.1002/anie.201901935",
                           target="_blank",
                           style={"color": ACCENT}),
                    " (±50 % OFAT perturbation)"
                ], style={"fontSize": "1rem", "color": "#6c757d",
                          "marginBottom": "0"})
            ], width=True),
        ], className="mb-4 align-items-center"),

        # ===== STATUS ALERT =====
        dbc.Row([
            dbc.Col([
                dbc.Alert(id="sensitivity-status-alert", is_open=False,
                          dismissable=True, className="mb-3")
            ])
        ]),

        # ===== BEST EXPERIMENT SUMMARY CARD =====
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="bi bi-trophy me-2",
                                   style={"color": SUCCESS}),
                            "Reference Experiment (Best from BO)"
                        ], className="mb-0", style={"fontWeight": "600"})
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody(id="sensitivity-best-summary",
                                 children=html.Div([
                                     dbc.Spinner(size="sm", color="primary"),
                                     html.Span("Loading best experiment...", className="text-muted ms-2")
                                 ], className="text-center py-3"))
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=12, className="mb-3"),
        ]),

        # ===== EDITABLE TABLE (auto-filled on load) =====
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5([
                                    html.I(className="bi bi-table me-2"),
                                    "Sensitivity Experiments"
                                ], className="mb-0", style={"fontWeight": "600"})
                            ]),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-save me-2"),
                                    "Save Results"
                                ],
                                    id="save-sensitivity-btn",
                                    color="success",
                                    size="sm",
                                    style={"borderRadius": "6px"})
                            ], width="auto")
                        ], align="center")
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        html.Div(id="sensitivity-table-container",
                                 children=html.Div([
                                     dbc.Spinner(size="sm", color="primary"),
                                     html.Span("Generating sensitivity experiments...",
                                               className="text-muted ms-2")
                                 ], className="text-center py-4"))
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=12, className="mb-4"),
        ]),

        # ===== RADAR DIAGRAM =====
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="bi bi-bullseye me-2",
                                   style={"color": ACCENT}),
                            "Sensitivity Radar Diagram"
                        ], className="mb-0", style={"fontWeight": "600"})
                    ], style={"backgroundColor": "#f8f9fa"}),
                    dbc.CardBody([
                        dcc.Graph(id="sensitivity-radar-plot",
                                  config={"displayModeBar": True,
                                          "toImageButtonOptions": {
                                              "format": "svg",
                                              "filename": "sensitivity_radar"
                                          }})
                    ])
                ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0"})
            ], md=7, className="mb-4"),

            
        ]),

        # ===== NAVIGATION =====
        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Link(
                        dbc.Button([
                            html.I(className="bi bi-arrow-left me-2"),
                            "Back to Run Optimization"
                        ], color="secondary", outline=True),
                        href="/Opt-run"
                    ),
                ], className="d-flex justify-content-start")
            ], md=12)
        ], className="mt-2 mb-4"),

    ], fluid=True, className="p-3")
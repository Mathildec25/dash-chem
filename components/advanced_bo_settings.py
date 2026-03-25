"""
Advanced Bayesian Optimization Settings Component
Provides UI for customizing BO parameters, including outcome constraints for MOBO.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc


def create_advanced_bo_settings():
    """
    Create a button that opens a modal for advanced BO settings.

    Returns:
        html.Div: Button + Modal
    """

    button = dbc.Button(
        [html.I(className="bi bi-gear me-2"), "Advanced Settings"],
        id="open-advanced-bo-modal",
        color="secondary",
        outline=True,
        size="sm",
        style={"fontWeight": "500"}
    )

    modal = dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle([
                html.I(className="bi bi-gear-fill me-2"),
                "Optimization Settings"
            ]),
            close_button=True
        ),
        dbc.ModalBody([

            # ── Optimization type (read-only) ─────────────────────────────
            dbc.Row([
                dbc.Col([
                    html.Label("Optimization type:", className="text-muted small mb-1"),
                    dbc.Badge(
                        "SOBO",
                        id="bo-type-indicator",
                        color="primary",
                        className="d-block text-start px-3 py-2",
                        style={"fontSize": "0.9rem"}
                    )
                ], width=12, className="mb-3")
            ]),

            html.Hr(className="my-3"),

            # ── Acquisition function ──────────────────────────────────────
            dbc.Row([
                dbc.Col([
                    html.Label("Acquisition function:", className="fw-bold mb-2"),
                    dcc.Dropdown(
                        id='acquisition-function-dropdown',
                        options=[
                            {'label': 'qLogNEI (default)', 'value': 'qLogNEI (default)'}
                        ],
                        value='qLogNEI (default)',
                        clearable=False,
                        style={"fontSize": "0.9rem"}
                    )
                ], width=12, className="mb-3")
            ]),

            # ── Number of candidates ──────────────────────────────────────
            dbc.Row([
                dbc.Col([
                    html.Label("Number of experiments to suggest:", className="fw-bold mb-2"),
                    dbc.Input(
                        id='n-candidates-input',
                        type='number',
                        min=1,
                        max=20,
                        step=1,
                        value=1,
                        style={"fontSize": "0.9rem"}
                    )
                ], md=12, className="mb-3")
            ]),

            # ── Outcome Constraint (MOBO only) ────────────────────────────
            html.Div(
                id="outcome-constraint-section",
                style={"display": "none"},
                children=[
                    html.Hr(className="my-3"),

                    html.Div([
                        html.H6([
                            html.I(className="bi bi-funnel me-2", style={"color": "#6366f1"}),
                            "Outcome Constraint",
                            dbc.Badge("MOBO", color="success", className="ms-2",
                                      style={"fontSize": "0.7rem", "verticalAlign": "middle"})
                        ], className="mb-1", style={"fontWeight": "600"}),
                        html.P(
                            "Restrict the search to regions where a chosen objective "
                            "satisfies a threshold (e.g. Yield ≥ 60%). "
                            "Uses a dedicated GP trained on the constraint value — "
                            "identical to the BoTorch constrained MOBO tutorial.",
                            className="text-muted small mb-3"
                        ),
                    ]),

                    # Enable / disable switch
                    dbc.Row([
                        dbc.Col([
                            dbc.Switch(
                                id="enable-outcome-constraint-switch",
                                label="Enable outcome constraint",
                                value=False,
                                className="mb-3"
                            )
                        ], width=12)
                    ]),

                    # Constraint parameters (shown when switch is ON)
                    html.Div(
                        id="outcome-constraint-params",
                        children=[
                            dbc.Row([
                                # Objective to constrain
                                dbc.Col([
                                    html.Label("Objective:", className="fw-bold mb-1 small"),
                                    dcc.Dropdown(
                                        id='constraint-objective-dropdown',
                                        options=[],
                                        placeholder="Select objective…",
                                        clearable=False,
                                        style={"fontSize": "0.875rem"}
                                    )
                                ], md=5, className="mb-2"),

                                # Direction
                                dbc.Col([
                                    html.Label("Direction:", className="fw-bold mb-1 small"),
                                    dcc.Dropdown(
                                        id='constraint-direction-dropdown',
                                        options=[
                                            {"label": "≥  (minimum threshold)", "value": ">="},
                                            {"label": "≤  (maximum threshold)", "value": "<="},
                                        ],
                                        value=">=",
                                        clearable=False,
                                        style={"fontSize": "0.875rem"}
                                    )
                                ], md=3, className="mb-2"),

                                # Threshold
                                dbc.Col([
                                    html.Label("Threshold:", className="fw-bold mb-1 small"),
                                    dbc.Input(
                                        id='constraint-threshold-input',
                                        type='number',
                                        placeholder="e.g. 60",
                                        step="any",
                                        style={"fontSize": "0.875rem"}
                                    )
                                ], md=4, className="mb-2"),
                            ]),

                            dbc.Alert([
                                html.I(className="bi bi-info-circle me-2"),
                                "Enter the threshold in the same units as your experimental data "
                                "(e.g. if Yield is recorded as % enter 60, not 0.60)."
                            ], color="info", className="py-2 mt-2",
                               style={"fontSize": "0.8rem"}),
                        ]
                    )
                ]
            )

        ], style={"padding": "1.5rem"}),

        dbc.ModalFooter([
            dbc.Button(
                "Cancel",
                id="cancel-advanced-bo-modal",
                color="secondary",
                outline=True,
                size="sm"
            ),
            dbc.Button(
                [html.I(className="bi bi-check-lg me-2"), "Apply"],
                id="apply-advanced-bo-settings",
                color="primary",
                size="sm"
            )
        ])
    ], id="advanced-bo-modal", size="md", is_open=False)

    return html.Div([button, modal])


def get_acquisition_function_options(is_multi_objective=False):
    """
    Get dropdown options for acquisition functions based on optimization type.
    """
    if is_multi_objective:
        return [
            {'label': 'qLogNEHVI (par défaut) - Log Hypervolume', 'value': 'qLogNEHVI (default)'},
        ]
    else:
        return [
            {'label': 'qLogNEI (par défaut) - Log Noisy Expected Improvement', 'value': 'qLogNEI (default)'},
            {'label': 'qEI - Expected Improvement',                             'value': 'qEI (Expected Improvement)'},
            {'label': 'qNEI - Noisy Expected Improvement',                      'value': 'qNEI (Noisy Expected Improvement)'},
            {'label': 'qPI - Probability of Improvement',                       'value': 'qPI (Probability of Improvement)'},
            {'label': 'qUCB - Upper Confidence Bound',                          'value': 'qUCB (Upper Confidence Bound)'},
            {'label': 'qSR - Simple Regret',                                    'value': 'qSR (Simple Regret)'},
        ]
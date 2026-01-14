"""
Advanced Bayesian Optimization Settings Component
Provides UI for customizing BO parameters
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
            # Optimization type (read-only)
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
            
            # Acquisition function
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
            
            # Number of candidates
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
            ])
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
    
    Args:
        is_multi_objective: Boolean indicating if multi-objective
    
    Returns:
        list: List of dicts for dropdown options
    """
    if is_multi_objective:
        return [
            {'label': 'qLogNEHVI (par défaut) - Log Hypervolume', 'value': 'qLogNEHVI (default)'},
        ]
    else:
        return [
            {'label': 'qLogNEI (par défaut) - Log Noisy Expected Improvement', 'value': 'qLogNEI (default)'},
            {'label': 'qEI - Expected Improvement', 'value': 'qEI (Expected Improvement)'},
            {'label': 'qNEI - Noisy Expected Improvement', 'value': 'qNEI (Noisy Expected Improvement)'},
            {'label': 'qPI - Probability of Improvement', 'value': 'qPI (Probability of Improvement)'},
            {'label': 'qUCB - Upper Confidence Bound', 'value': 'qUCB (Upper Confidence Bound)'},
            {'label': 'qSR - Simple Regret', 'value': 'qSR (Simple Regret)'},
        ]
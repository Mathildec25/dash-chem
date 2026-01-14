"""
Bayesian Optimization Configuration Callbacks
Manages BO parameters and updates the optimization execution
"""

from dash import callback, Input, Output, State, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import html


# ============================================
# TOGGLE ADVANCED SETTINGS
# ============================================

@callback(
    Output("bo-advanced-collapse", "is_open"),
    Input("toggle-bo-advanced", "n_clicks"),
    State("bo-advanced-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_bo_advanced_settings(n_clicks, is_open):
    """Toggle advanced BO settings collapse"""
    if n_clicks:
        return not is_open
    return is_open


# ============================================
# UPDATE BO CONFIG STORE
# ============================================

@callback(
    Output('bo-config-store', 'data'),
    [Input('bo-n-candidates', 'value'),
     Input('bo-acquisition-function', 'value'),
     Input('bo-strategy-type', 'value'),
     Input('bo-ucb-beta', 'value'),
     Input('bo-num-restarts', 'value'),
     Input('bo-raw-samples', 'value'),
     Input('bo-sequential', 'value')],
    prevent_initial_call=False
)
def update_bo_config(n_candidates, acq_func, strategy, ucb_beta, num_restarts, raw_samples, sequential):
    """
    Save BO configuration to store whenever parameters change
    """
    config = {
        'n_candidates': n_candidates or 1,
        'acquisition_function': acq_func or 'qLogNEI',
        'strategy_type': strategy or 'auto',
        'ucb_beta': ucb_beta if ucb_beta is not None else 2.0,
        'num_restarts': num_restarts or 20,
        'raw_samples': raw_samples or 512,
        'sequential': 'sequential' in (sequential or [])
    }
    return config


# ============================================
# AUTO-ADJUST ACQUISITION FUNCTION
# ============================================

@callback(
    [Output('bo-acquisition-function', 'options'),
     Output('bo-acquisition-function', 'value')],
    [Input('current-excel-file', 'data'),
     Input('bo-strategy-type', 'value')],
    State('bo-acquisition-function', 'value'),
    prevent_initial_call=True
)
def update_acquisition_options(excel_file, strategy_type, current_acq):
    """
    Update acquisition function options based on strategy type
    Automatically adjusts when switching between SOBO and MOBO
    """
    if not excel_file:
        raise PreventUpdate
    
    # Try to load domain to determine number of objectives
    try:
        from domain_storage import DomainStorage
        domain_data = DomainStorage.load_domain(excel_file)
        
        if domain_data:
            n_obj = len(domain_data.get('objectives', []))
        else:
            n_obj = 1
    except:
        n_obj = 1
    
    # Determine strategy based on objectives if auto
    if strategy_type == 'auto':
        effective_strategy = 'sobo' if n_obj == 1 else 'mobo'
    else:
        effective_strategy = strategy_type
    
    # Define options based on strategy
    if effective_strategy == 'sobo':
        options = [
            {"label": "qLogNEI (Recommended)", "value": "qLogNEI"},
            {"label": "qEI (Expected Improvement)", "value": "qEI"},
            {"label": "qUCB (Upper Confidence Bound)", "value": "qUCB"},
        ]
        # Default for single objective
        default_value = "qLogNEI"
    else:  # mobo
        options = [
            {"label": "qLogNEHVI (Recommended)", "value": "qLogNEHVI"},
            {"label": "qNEHVI (Noisy EHVI)", "value": "qNEHVI"},
        ]
        # Default for multi-objective
        default_value = "qLogNEHVI"
    
    # Check if current acquisition is valid for new strategy
    valid_values = [opt['value'] for opt in options]
    
    if current_acq in valid_values:
        return options, current_acq
    else:
        return options, default_value


# ============================================
# DISABLE/ENABLE UCB BETA BASED ON ACQ FUNCTION
# ============================================

@callback(
    Output('bo-ucb-beta', 'disabled'),
    Input('bo-acquisition-function', 'value'),
    prevent_initial_call=True
)
def toggle_ucb_beta(acq_func):
    """Enable UCB beta input only when qUCB is selected"""
    return acq_func != 'qUCB'


# ============================================
# DISPLAY BO CONFIGURATION INFO
# ============================================

@callback(
    Output('bo-result-alert', 'children'),
    Output('bo-result-alert', 'is_open'),
    Output('bo-result-alert', 'color'),
    Input('run-bo-btn', 'n_clicks'),
    [State('bo-config-store', 'data'),
     State('current-excel-file', 'data')],
    prevent_initial_call=True
)
def show_bo_config_info(n_clicks, bo_config, excel_file):
    """
    Display information about the BO configuration being used
    This is called BEFORE the actual BO execution
    """
    if not n_clicks or not bo_config:
        raise PreventUpdate
    
    config_summary = html.Div([
        html.H6("🎯 Optimization Configuration:", className="mb-2"),
        html.Ul([
            html.Li(f"Candidates: {bo_config['n_candidates']}"),
            html.Li(f"Strategy: {bo_config['strategy_type'].upper()}"),
            html.Li(f"Acquisition: {bo_config['acquisition_function']}"),
            html.Li(f"Restarts: {bo_config['num_restarts']}"),
            html.Li(f"Raw Samples: {bo_config['raw_samples']}"),
        ], className="mb-0")
    ])
    
    return config_summary, True, "info"
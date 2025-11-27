"""
Callbacks for Advanced Bayesian Optimization Settings
Handles UI interactions and settings updates
"""

import dash
from dash import callback, Input, Output, State, html, dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from components.advanced_bo_settings import get_acquisition_function_options
from domain_storage import DomainStorage


# ==============================================
# TOGGLE MODAL + LOAD VALUES
# ==============================================

@callback(
    [Output("advanced-bo-modal", "is_open"),
     Output('bo-type-indicator', 'children'),
     Output('bo-type-indicator', 'color'),
     Output('acquisition-function-dropdown', 'options'),
     Output('acquisition-function-dropdown', 'value'),
     Output('n-candidates-input', 'value')],
    [Input("open-advanced-bo-modal", "n_clicks"),
     Input("cancel-advanced-bo-modal", "n_clicks"),
     Input("apply-advanced-bo-settings", "n_clicks")],
    [State("advanced-bo-modal", "is_open"),
     State('current-excel-file', 'data'),
     State('advanced-bo-settings-store', 'data')],
    prevent_initial_call=True
)
def toggle_and_load_modal(open_clicks, cancel_clicks, apply_clicks, is_open, excel_file, current_settings):
    """Toggle modal and load current values when opening"""
    
    triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    
    # Close modal
    if triggered_id in ['cancel-advanced-bo-modal', 'apply-advanced-bo-settings']:
        return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Open modal and load values
    if triggered_id == 'open-advanced-bo-modal':
        # Load domain from file
        domain_data = DomainStorage.load_domain(excel_file) if excel_file else None
        
        if not domain_data:
            return True, "No objectives", "warning", [], None, 1
        
        objectives = domain_data.get('objectives', [])
        n_objectives = len(objectives)
        
        if n_objectives == 0:
            return True, "No objectives", "warning", [], None, 1
        
        is_multi_objective = n_objectives >= 2
        
        if n_objectives == 1:
            bo_type_text = "SOBO (1 objective)"
            badge_color = "primary"
        else:
            bo_type_text = f"MOBO ({n_objectives} objectives)"
            badge_color = "success"
        
        acq_options = get_acquisition_function_options(is_multi_objective)
        default_acq = 'qLogNEHVI (default)' if is_multi_objective else 'qLogNEI (default)'
        
        # Load current values from store or use defaults
        current_acq = current_settings.get('acquisition_function', default_acq) if current_settings else default_acq
        current_n_candidates = current_settings.get('n_candidates', 1) if current_settings else 1
        
        return True, bo_type_text, badge_color, acq_options, current_acq, current_n_candidates
    
    return is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


# ==============================================
# STORE SETTINGS WHEN APPLYING
# ==============================================

@callback(
    Output('advanced-bo-settings-store', 'data'),
    Input('apply-advanced-bo-settings', 'n_clicks'),
    [State('acquisition-function-dropdown', 'value'),
     State('n-candidates-input', 'value')],
    prevent_initial_call=True
)
def store_settings_on_apply(n_clicks, acq_func, n_candidates):
    """Store settings only when user clicks Apply"""
    if not n_clicks:
        raise PreventUpdate
    
    return {
        'acquisition_function': acq_func or 'qLogNEI (default)',
        'n_candidates': n_candidates or 1
    }
"""
Callbacks for Advanced Bayesian Optimization Settings
Settings are persisted per project in the domain metadata JSON.
"""

import os
import dash
from dash import callback, Input, Output, State, html, dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from components.advanced_bo_settings import get_acquisition_function_options
from domain_storage import DomainStorage
from config_path import EXCEL_FOLDER

_METADATA_KEY = 'advanced_bo_settings'


# =============================================================================
# HELPER — LIST AVAILABLE CAMPAIGNS FOR TRANSFER LEARNING
# =============================================================================

def _get_available_campaigns(current_excel_file=None):
    """
    Scan EXCEL_FOLDER for past campaigns to use as TL source.
    Excludes the current campaign.

    Returns:
        list of {'label': project_name, 'value': excel_filename}
    """
    campaigns = []
    try:
        for fname in sorted(os.listdir(EXCEL_FOLDER)):
            if not fname.endswith('.xlsx'):
                continue
            if fname == current_excel_file:
                continue
            domain_data = DomainStorage.load_domain(fname)
            if not domain_data:
                continue
            project_name = (
                domain_data.get('metadata', {}).get('project_name')
                or fname.replace('.xlsx', '')
            )
            campaigns.append({'label': project_name, 'value': fname})
    except Exception as e:
        print(f"Could not list campaigns: {e}")
    return campaigns


def _check_domain_compatibility(source_excel, target_domain_data):
    """
    Check if the source campaign domain is compatible with the current campaign.
    Compatible = same parameter names, types, and objective names.

    Returns:
        (bool, str) — (is_compatible, message)
    """
    source_data = DomainStorage.load_domain(source_excel)
    if not source_data:
        return False, "Could not load source campaign"

    source_params  = {p['name']: p for p in source_data.get('parameters', [])}
    target_params  = {p['name']: p for p in target_domain_data.get('parameters', [])}

    if set(source_params.keys()) != set(target_params.keys()):
        missing = set(target_params.keys()) - set(source_params.keys())
        extra   = set(source_params.keys()) - set(target_params.keys())
        msg = []
        if missing:
            msg.append(f"missing in source: {missing}")
        if extra:
            msg.append(f"extra in source: {extra}")
        return False, "Different parameters — " + ", ".join(msg)

    for name, tp in target_params.items():
        sp = source_params[name]
        if tp.get('type') != sp.get('type'):
            return False, f"Type mismatch for '{name}': {sp.get('type')} vs {tp.get('type')}"

    source_obj_names = {o['name'] for o in source_data.get('objectives', [])}
    target_obj_names = {o['name'] for o in target_domain_data.get('objectives', [])}
    if source_obj_names != target_obj_names:
        return False, f"Different objectives: source={source_obj_names}, target={target_obj_names}"

    # Count source experiments
    try:
        import pandas as pd
        source_path = os.path.join(EXCEL_FOLDER, source_excel)
        df = pd.read_excel(source_path, engine='openpyxl')
        obj_names = list(source_obj_names)
        n_complete = df.dropna(subset=obj_names).shape[0]
        return True, f"Compatible ({n_complete} experiments available)"
    except Exception:
        return True, "Compatible"


# =============================================================================
# AUTO-LOAD SETTINGS FROM PROJECT METADATA INTO STORE ON PAGE LOAD
# =============================================================================

@callback(
    Output('advanced-bo-settings-store', 'data', allow_duplicate=True),
    Input('current-excel-file', 'data'),
    State('advanced-bo-settings-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_settings_from_metadata(excel_file, current_store):
    """
    When the active project changes (or on page reload), populate the store
    from the project metadata so that run_optimization.py always reads
    up-to-date settings — even if the user never opens the modal.
    """
    if not excel_file:
        raise PreventUpdate

    domain_data = DomainStorage.load_domain(excel_file)
    if not domain_data:
        raise PreventUpdate

    saved = domain_data.get(_METADATA_KEY)
    if not saved:
        raise PreventUpdate

    print(f"Auto-loaded BO settings from project metadata: {saved}")
    return saved


# =============================================================================
# TOGGLE MODAL + LOAD VALUES (from project metadata)
# =============================================================================

@callback(
    [Output("advanced-bo-modal", "is_open"),
     Output('bo-type-indicator', 'children'),
     Output('bo-type-indicator', 'color'),
     Output('acquisition-function-dropdown', 'options'),
     Output('acquisition-function-dropdown', 'value'),
     Output('n-candidates-input', 'value'),
     # Outcome constraint section
     Output('outcome-constraint-section', 'style'),
     Output('constraint-objective-dropdown', 'options'),
     Output('constraint-objective-dropdown', 'value'),
     Output('constraint-direction-dropdown', 'value'),
     Output('constraint-threshold-input', 'value'),
     Output('enable-outcome-constraint-switch', 'value'),
     # Transfer Learning section
     Output('tl-section', 'style'),
     Output('tl-source-campaign-dropdown', 'options'),
     Output('tl-source-campaign-dropdown', 'value'),
     Output('enable-tl-switch', 'value')],
    [Input("open-advanced-bo-modal", "n_clicks"),
     Input("cancel-advanced-bo-modal", "n_clicks"),
     Input("apply-advanced-bo-settings", "n_clicks")],
    [State("advanced-bo-modal", "is_open"),
     State('current-excel-file', 'data'),
     State('advanced-bo-settings-store', 'data')],
    prevent_initial_call=True
)
def toggle_and_load_modal(open_clicks, cancel_clicks, apply_clicks,
                          is_open, excel_file, store_settings):
    """Toggle modal. On open, load settings from project metadata (DomainStorage)."""

    triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]

    # ── Close modal ────────────────────────────────────────────────────────
    if triggered_id in ['cancel-advanced-bo-modal', 'apply-advanced-bo-settings']:
        return (False,) + (dash.no_update,) * 15

    # ── Open modal ─────────────────────────────────────────────────────────
    if triggered_id != 'open-advanced-bo-modal':
        return (is_open,) + (dash.no_update,) * 15

    domain_data = DomainStorage.load_domain(excel_file) if excel_file else None

    if not domain_data:
        return (True, "No objectives", "warning", [], None, 1,
                {"display": "none"}, [], None, ">=", None, False,
                {"display": "none"}, [], None, False)

    objectives   = domain_data.get('objectives', [])
    n_objectives = len(objectives)
    if n_objectives == 0:
        return (True, "No objectives", "warning", [], None, 1,
                {"display": "none"}, [], None, ">=", None, False,
                {"display": "none"}, [], None, False)

    is_multi_objective = n_objectives >= 2

    # ── Type badge ─────────────────────────────────────────────────────────
    if n_objectives == 1:
        bo_type_text = "SOBO (1 objective)"
        badge_color  = "primary"
    else:
        bo_type_text = f"MOBO ({n_objectives} objectives)"
        badge_color  = "success"

    # ── Acquisition function options ───────────────────────────────────────
    acq_options = get_acquisition_function_options(is_multi_objective)
    default_acq = 'qLogNEHVI (default)' if is_multi_objective else 'qLogNEI (default)'

    # ── Load saved settings ────────────────────────────────────────────────
    saved = domain_data.get(_METADATA_KEY) or store_settings or {}

    current_acq          = saved.get('acquisition_function', default_acq)
    current_n_candidates = saved.get('n_candidates', 1)

    # ── Outcome constraint section (MOBO only) ─────────────────────────────
    constraint_section_style = {"display": "block"} if is_multi_objective else {"display": "none"}
    obj_names   = [o.get('name', '') for o in objectives if o.get('name')]
    obj_options = [{'label': name, 'value': name} for name in obj_names]

    oc           = saved.get('outcome_constraint') or {}
    oc_enabled   = oc.get('enabled', False)
    oc_objective = oc.get('objective', obj_names[0] if obj_names else None)
    oc_direction = oc.get('direction', '>=')
    oc_threshold = oc.get('threshold', None)

    # ── Transfer Learning section (SOBO only) ──────────────────────────────
    tl_section_style = {"display": "block"} if not is_multi_objective else {"display": "none"}

    tl_campaigns = _get_available_campaigns(current_excel_file=excel_file)

    tl_config      = saved.get('transfer_learning') or {}
    tl_enabled     = tl_config.get('enabled', False)
    tl_source      = tl_config.get('source_campaign', None)

    # Validate that the saved source campaign still exists
    available_values = [c['value'] for c in tl_campaigns]
    if tl_source and tl_source not in available_values:
        tl_source  = None
        tl_enabled = False

    return (True, bo_type_text, badge_color,
            acq_options, current_acq, current_n_candidates,
            constraint_section_style,
            obj_options, oc_objective, oc_direction, oc_threshold, oc_enabled,
            tl_section_style, tl_campaigns, tl_source, tl_enabled)


# =============================================================================
# SHOW / HIDE CONSTRAINT PARAMETERS BASED ON SWITCH
# =============================================================================

@callback(
    Output('outcome-constraint-params', 'style'),
    Input('enable-outcome-constraint-switch', 'value'),
    prevent_initial_call=True
)
def toggle_constraint_params(enabled):
    """Show/hide constraint parameter inputs when switch changes."""
    return {"display": "block"} if enabled else {"display": "none"}


# =============================================================================
# SHOW / HIDE TL SOURCE SECTION BASED ON SWITCH
# =============================================================================

@callback(
    Output('tl-source-section', 'style'),
    Input('enable-tl-switch', 'value'),
    prevent_initial_call=True
)
def toggle_tl_source_section(enabled):
    """Show/hide source campaign dropdown when TL switch changes."""
    return {"display": "block"} if enabled else {"display": "none"}


# =============================================================================
# CHECK DOMAIN COMPATIBILITY ON SOURCE CAMPAIGN SELECTION
# =============================================================================

@callback(
    Output('tl-compatibility-badge', 'children'),
    Input('tl-source-campaign-dropdown', 'value'),
    State('current-excel-file', 'data'),
    prevent_initial_call=True
)
def check_tl_compatibility(source_excel, current_excel_file):
    """Check and display domain compatibility when source campaign is selected."""
    if not source_excel or not current_excel_file:
        return html.Span()

    target_domain_data = DomainStorage.load_domain(current_excel_file)
    if not target_domain_data:
        return dbc.Alert("Could not load current campaign", color="danger",
                         className="py-1 px-2", style={"fontSize": "0.8rem"})

    is_compatible, message = _check_domain_compatibility(source_excel, target_domain_data)

    if is_compatible:
        return dbc.Alert(
            [html.I(className="bi bi-check-circle me-2"), message],
            color="success", className="py-1 px-2 mb-0",
            style={"fontSize": "0.8rem"}
        )
    else:
        return dbc.Alert(
            [html.I(className="bi bi-x-circle me-2"), f"Incompatible — {message}"],
            color="danger", className="py-1 px-2 mb-0",
            style={"fontSize": "0.8rem"}
        )


# =============================================================================
# SAVE SETTINGS TO PROJECT METADATA + STORE
# =============================================================================

@callback(
    Output('advanced-bo-settings-store', 'data'),
    Input('apply-advanced-bo-settings', 'n_clicks'),
    [State('acquisition-function-dropdown', 'value'),
     State('n-candidates-input', 'value'),
     State('enable-outcome-constraint-switch', 'value'),
     State('constraint-objective-dropdown', 'value'),
     State('constraint-direction-dropdown', 'value'),
     State('constraint-threshold-input', 'value'),
     State('enable-tl-switch', 'value'),
     State('tl-source-campaign-dropdown', 'value'),
     State('current-excel-file', 'data')],
    prevent_initial_call=True
)
def store_settings_on_apply(n_clicks, acq_func, n_candidates,
                             enable_constraint, constraint_obj,
                             constraint_direction, constraint_threshold,
                             enable_tl, tl_source_campaign,
                             excel_file):
    """
    Save settings both to the in-memory store AND to the project metadata JSON.
    The project metadata ensures settings survive page reloads.
    """
    if not n_clicks:
        raise PreventUpdate

    settings = {
        'acquisition_function': acq_func or 'qLogNEI (default)',
        'n_candidates': n_candidates or 1,
        'outcome_constraint': {
            'enabled':   bool(enable_constraint),
            'objective': constraint_obj,
            'direction': constraint_direction or '>=',
            'threshold': float(constraint_threshold) if constraint_threshold is not None else None,
        },
        'transfer_learning': {
            'enabled':         bool(enable_tl),
            'source_campaign': tl_source_campaign if enable_tl else None,
        }
    }

    # ── Persist to project metadata (survives page reload) ────────────────
    if excel_file:
        success, msg = DomainStorage.update_metadata(excel_file, _METADATA_KEY, settings)
        if success:
            print(f"Advanced BO settings saved to project metadata: {settings}")
        else:
            print(f"Could not save to project metadata: {msg}")

    return settings
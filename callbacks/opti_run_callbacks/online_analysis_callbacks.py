"""
Online Analysis Callbacks
Handles file monitoring, auto-fill of results, and automatic BO triggering.

Fully generic — works with any number of objectives. The user maps file keys
to domain objectives via dropdowns before starting monitoring.

Workflow:
1. User enters file path and clicks "Detect File Keys"
2. Parser reads the file and shows which keys are present
3. User maps each file key to a domain objective (via dropdowns)
4. User toggles ON → monitoring starts with dcc.Interval
5. New experiment blocks are detected, mapped, and filled into the table
6. When init is complete → BO triggers automatically
7. BO suggestion added → monitoring continues → loop
"""

import os
import json
from datetime import datetime

from dash import callback, Input, Output, State, html, no_update, ctx, dcc, ALL, MATCH
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np

from utils.online_analysis import (
    parse_result_file,
    get_file_keys,
    get_new_results,
    validate_result_file,
    get_file_modification_time,
    map_results_to_objectives
)
from domain_storage import DomainStorage
from config_path import EXCEL_FOLDER
from utils.BoFire import (
    create_bofire_domain_from_store,
    bayesian_optimization,
    get_optimization_type
)
from callbacks.opti_param_callbacks.constraints_callbacks import validate_and_adjust_suggestion


# =============================================================================
# HELPER
# =============================================================================

def add_log_entry(state: dict, message: str) -> dict:
    """Add a timestamped entry to the activity log."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    
    log_entries = state.get("log_entries", [])
    log_entries.append(entry)
    
    # Keep last 50 entries
    if len(log_entries) > 50:
        log_entries = log_entries[-50:]
    
    state["log_entries"] = log_entries
    return state


# =============================================================================
# 1. DETECT FILE KEYS & SHOW MAPPING UI
# =============================================================================

@callback(
    [Output("online-analysis-validation-msg", "children"),
     Output("online-analysis-mapping-section", "children"),
     Output("online-analysis-detected-keys", "data")],
    Input("online-analysis-validate-btn", "n_clicks"),
    [State("online-analysis-filepath", "value"),
     State("current-excel-file", "data")],
    prevent_initial_call=True
)
def detect_keys_and_build_mapping(n_clicks, filepath, excel_file):
    """
    Read the result file, detect keys, and build the mapping UI.
    Each detected key gets a dropdown to map it to a domain objective.
    """
    if not n_clicks:
        raise PreventUpdate
    
    if not filepath or not filepath.strip():
        return (
            dbc.Alert("Please enter a file path.", color="warning",
                     className="mb-0 py-1 px-2", style={"fontSize": "0.8rem"}),
            no_update,
            no_update
        )
    
    filepath = filepath.strip()
    info = validate_result_file(filepath)
    
    # File not found
    if not info['exists']:
        return (
            dbc.Alert([
                html.I(className="bi bi-exclamation-triangle me-2"),
                f"File not found: {filepath}"
            ], color="danger", className="py-1 px-2", style={"fontSize": "0.8rem"}),
            no_update,
            no_update
        )
    
    detected_keys = info.get('keys', [])
    
    # File exists but no keys detected (empty or wrong format)
    if not detected_keys:
        return (
            dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                "File exists but no key=value blocks found. "
                "Expected format: 'Yield = 78.5' with blocks separated by blank lines. "
                "Monitoring will start and detect keys when data appears."
            ], color="info", className="py-1 px-2", style={"fontSize": "0.8rem"}),
            no_update,
            []
        )
    
    # Get domain objectives for dropdown options
    obj_options = []
    if excel_file:
        domain_data = DomainStorage.load_domain(excel_file)
        if domain_data:
            obj_names = domain_data.get('metadata', {}).get('objective_names', [])
            obj_options = [{"label": name, "value": name} for name in obj_names]
    
    # Success message
    keys_str = ', '.join(detected_keys)
    validation_msg = dbc.Alert([
        html.I(className="bi bi-check-circle me-2"),
        f"✅ {info['n_results']} experiment(s) found — keys: ",
        html.Strong(keys_str)
    ], color="success", className="py-1 px-2", style={"fontSize": "0.8rem"})
    
    # Build mapping UI: one row per detected key with a dropdown
    mapping_rows = []
    
    for i, key in enumerate(detected_keys):
        # Try to auto-match: if key name matches an objective name, pre-select it
        default_value = None
        for opt in obj_options:
            if opt['value'].lower() == key.lower():
                default_value = opt['value']
                break
        
        mapping_rows.append(
            dbc.Row([
                dbc.Col([
                    html.Div([
                        dbc.Badge(key, color="dark", className="me-2",
                                 style={"fontSize": "0.8rem", "fontFamily": "monospace"}),
                        html.Span("→", className="text-muted me-2")
                    ], className="d-flex align-items-center h-100")
                ], width=4),
                dbc.Col([
                    dcc.Dropdown(
                        id={"type": "online-analysis-mapping-dropdown", "index": i},
                        options=obj_options,
                        value=default_value,
                        placeholder="Select objective...",
                        clearable=True,
                        style={"fontSize": "0.8rem"}
                    )
                ], width=8),
            ], className="mb-2 align-items-center")
        )
    
    mapping_section = html.Div([
        html.Hr(className="my-2"),
        dbc.Label("Map file keys to objectives", className="fw-bold mb-2",
                 style={"fontSize": "0.85rem"}),
        html.Div(mapping_rows),
        html.Small(
            "Each key in the result file must be mapped to one of your domain objectives. "
            "Unmapped keys will be ignored.",
            className="text-muted",
            style={"fontSize": "0.75rem"}
        )
    ])
    
    return validation_msg, mapping_section, detected_keys


# =============================================================================
# 2. COLLECT MAPPING FROM DROPDOWNS → STORE
# =============================================================================

@callback(
    Output("online-analysis-key-mapping", "data"),
    Input({"type": "online-analysis-mapping-dropdown", "index": ALL}, "value"),
    State("online-analysis-detected-keys", "data"),
    prevent_initial_call=True
)
def collect_key_mapping(dropdown_values, detected_keys):
    """
    Collect the mapping from all dropdowns into a single dict.
    {file_key: objective_name} for all mapped keys.
    """
    if not detected_keys:
        raise PreventUpdate
    
    mapping = {}
    for i, key in enumerate(detected_keys):
        if i < len(dropdown_values) and dropdown_values[i]:
            mapping[key] = dropdown_values[i]
    
    return mapping


# =============================================================================
# 3. TOGGLE ON/OFF
# =============================================================================

@callback(
    [Output("online-analysis-config", "style"),
     Output("online-analysis-monitor", "style"),
     Output("online-analysis-interval-component", "disabled"),
     Output("online-analysis-interval-component", "interval"),
     Output("online-analysis-state", "data", allow_duplicate=True),
     Output("online-analysis-toggle", "value", allow_duplicate=True),
     Output("online-analysis-active-mapping", "children")],
    [Input("online-analysis-toggle", "value"),
     Input("online-analysis-stop-btn", "n_clicks")],
    [State("online-analysis-filepath", "value"),
     State("online-analysis-interval", "value"),
     State("online-analysis-state", "data"),
     State("online-analysis-key-mapping", "data"),
     State("online-analysis-detected-keys", "data"),
     State("current-excel-file", "data")],
    prevent_initial_call=True
)
def toggle_online_analysis(toggle_value, stop_clicks, filepath, interval_secs,
                           state, key_mapping, detected_keys, excel_file):
    """Toggle online analysis monitoring on/off."""
    
    triggered = ctx.triggered_id
    
    # Stop button
    if triggered == "online-analysis-stop-btn":
        state = state or {}
        state["enabled"] = False
        state = add_log_entry(state, "⏹ Monitoring stopped by user")
        
        return (
            {"display": "block"}, {"display": "none"},
            True, no_update, state, False, no_update
        )
    
    # Toggle ON
    if toggle_value:
        # Validate prerequisites
        if not filepath or not filepath.strip():
            return ({"display": "block"}, {"display": "none"},
                    True, no_update, no_update, False, no_update)
        
        if not key_mapping:
            return ({"display": "block"}, {"display": "none"},
                    True, no_update, no_update, False, no_update)
        
        filepath = filepath.strip()
        
        # Count init experiments
        total_init = 0
        if excel_file:
            try:
                file_path = os.path.join(EXCEL_FOLDER, excel_file)
                df = pd.read_excel(file_path, engine='openpyxl')
                total_init = len(df)
            except:
                pass
        
        interval_ms = max(2, int(interval_secs or 5)) * 1000
        
        # Initialize state
        state = {
            "enabled": True,
            "filepath": filepath,
            "key_mapping": key_mapping,
            "phase": "initialization",
            "results_processed": 0,
            "total_init_experiments": total_init,
            "log_entries": [],
            "last_file_mtime": None,
            "bo_iteration": 0,
        }
        
        state = add_log_entry(state, "▶ Monitoring started")
        state = add_log_entry(state, f"  File: {filepath}")
        state = add_log_entry(state, f"  Polling: every {interval_ms // 1000}s")
        state = add_log_entry(state, f"  Init experiments: {total_init}")
        
        for fk, obj in key_mapping.items():
            state = add_log_entry(state, f"  Mapping: {fk} → {obj}")
        
        # Build active mapping display
        mapping_badges = []
        for fk, obj in key_mapping.items():
            mapping_badges.append(
                html.Span([
                    dbc.Badge(fk, color="dark", className="me-1",
                             style={"fontSize": "0.7rem", "fontFamily": "monospace"}),
                    html.Span("→ ", className="text-muted", style={"fontSize": "0.75rem"}),
                    dbc.Badge(obj, color="success", className="me-3",
                             style={"fontSize": "0.7rem"}),
                ])
            )
        
        active_mapping = html.Div([
            html.Small("Mapping: ", className="fw-bold", style={"fontSize": "0.8rem"}),
            *mapping_badges
        ])
        
        return (
            {"display": "none"}, {"display": "block"},
            False, interval_ms, state, True, active_mapping
        )
    
    # Toggle OFF
    else:
        state = state or {}
        state["enabled"] = False
        return (
            {"display": "block"}, {"display": "none"},
            True, no_update, state, False, no_update
        )


# =============================================================================
# 4. MAIN POLLING CALLBACK
# =============================================================================

@callback(
    [Output("experiment-datatable", "data", allow_duplicate=True),
     Output("online-analysis-state", "data", allow_duplicate=True),
     Output("online-analysis-log", "children"),
     Output("online-analysis-phase-badge", "children"),
     Output("online-analysis-phase-badge", "color"),
     Output("online-analysis-status-badge", "children"),
     Output("online-analysis-status-badge", "color"),
     Output("online-analysis-progress-text", "children"),
     Output("online-analysis-progress-bar", "value"),
     Output("bo-result-alert", "children", allow_duplicate=True),
     Output("bo-result-alert", "is_open", allow_duplicate=True),
     Output("bo-result-alert", "color", allow_duplicate=True)],
    Input("online-analysis-interval-component", "n_intervals"),
    [State("online-analysis-state", "data"),
     State("experiment-datatable", "data"),
     State("current-excel-file", "data"),
     State("advanced-bo-settings-store", "data")],
    prevent_initial_call=True
)
def poll_for_results(n_intervals, state, table_data, excel_file, advanced_settings):
    """
    Main polling callback — fires every N seconds when monitoring is active.
    
    1. Checks if the result file has been modified
    2. Parses new experiment blocks and maps keys to objectives
    3. Fills objective values into the next empty rows
    4. When init phase is complete → runs BO automatically
    5. When BO suggestion gets results → runs next BO iteration
    """
    
    if not state or not state.get("enabled"):
        raise PreventUpdate
    
    filepath = state.get("filepath", "")
    key_mapping = state.get("key_mapping", {})
    
    if not filepath or not key_mapping:
        raise PreventUpdate
    
    # --- Check file modification ---
    current_mtime = get_file_modification_time(filepath)
    last_mtime = state.get("last_file_mtime")
    
    if current_mtime is None:
        state = add_log_entry(state, "⚠ File not found, waiting...")
        return _build_outputs(state, table_data=no_update,
                              status_text="File not found", status_color="danger")
    
    # No modification → just refresh UI
    if last_mtime is not None and current_mtime <= last_mtime:
        return _build_outputs(state, table_data=no_update,
                              status_text="Polling...", status_color="warning")
    
    # --- File modified → check for new results ---
    state["last_file_mtime"] = current_mtime
    results_processed = state.get("results_processed", 0)
    
    new_results = get_new_results(filepath, results_processed, key_mapping)
    
    if not new_results:
        return _build_outputs(state, table_data=no_update,
                              status_text="Polling...", status_color="warning")
    
    # === NEW RESULTS FOUND ===
    state = add_log_entry(state, f"📥 {len(new_results)} new result(s) detected")
    
    if not table_data or not excel_file:
        state = add_log_entry(state, "⚠ No table data available")
        return _build_outputs(state, table_data=no_update,
                              status_text="Error: no table", status_color="danger")
    
    # Load domain
    domain_data = DomainStorage.load_domain(excel_file)
    if not domain_data:
        state = add_log_entry(state, "⚠ Domain not found")
        return _build_outputs(state, table_data=no_update,
                              status_text="Error: no domain", status_color="danger")
    
    obj_names = domain_data.get('metadata', {}).get('objective_names', [])
    
    # Fill results into table
    updated_data = list(table_data)
    current_row_idx = results_processed
    
    for result in new_results:
        if current_row_idx >= len(updated_data):
            state = add_log_entry(state, f"⚠ Result received but no empty row at index {current_row_idx + 1}")
            break
        
        # Fill each mapped objective
        filled_parts = []
        for obj_name in obj_names:
            if obj_name in result:
                updated_data[current_row_idx][obj_name] = result[obj_name]
                filled_parts.append(f"{obj_name}={result[obj_name]}")
        
        if filled_parts:
            state = add_log_entry(state, f"  ✅ Row {current_row_idx + 1}: {', '.join(filled_parts)}")
        
        current_row_idx += 1
        state["results_processed"] = current_row_idx
    
    # Save to Excel
    _save_table(updated_data, excel_file, state)
    
    # === CHECK PHASE TRANSITION ===
    bo_alert_msg = no_update
    bo_alert_open = no_update
    bo_alert_color = no_update
    
    phase = state.get("phase", "initialization")
    total_init = state.get("total_init_experiments", 0)
    results_count = state.get("results_processed", 0)
    
    if phase == "initialization" and results_count >= total_init and total_init > 0:
        # === INIT COMPLETE → FIRST BO ===
        state["phase"] = "optimization"
        state = add_log_entry(state, "🎯 Initialization complete! Launching Bayesian Optimization...")
        
        updated_data, state, bo_alert_msg, bo_alert_open, bo_alert_color = _run_bo_iteration(
            updated_data, state, domain_data, obj_names, advanced_settings
        )
    
    elif phase == "optimization":
        # === IN OPTIMIZATION: check if latest suggestion has results ===
        if _last_row_is_complete(updated_data, obj_names):
            state = add_log_entry(state, "📥 BO experiment result received, running next iteration...")
            
            updated_data, state, bo_alert_msg, bo_alert_open, bo_alert_color = _run_bo_iteration(
                updated_data, state, domain_data, obj_names, advanced_settings
            )
    
    return _build_outputs(
        state, table_data=updated_data,
        bo_alert_msg=bo_alert_msg, bo_alert_open=bo_alert_open, bo_alert_color=bo_alert_color
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _save_table(table_data, excel_file, state):
    """Save table data to Excel file."""
    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.DataFrame(table_data)
        df.to_excel(file_path, index=False, engine='openpyxl')
        state = add_log_entry(state, "  💾 Table auto-saved")
    except Exception as e:
        state = add_log_entry(state, f"  ⚠ Save error: {e}")


def _last_row_is_complete(table_data, obj_names):
    """Check if the last row in the table has all objective values filled."""
    if not table_data:
        return False
    
    last_row = table_data[-1]
    for obj in obj_names:
        val = last_row.get(obj)
        if val is None or val == '' or (isinstance(val, float) and np.isnan(val)):
            return False
    return True


def _run_bo_iteration(updated_data, state, domain_data, obj_names, advanced_settings):
    """
    Run one Bayesian Optimization iteration.
    
    Returns:
        (updated_data, state, bo_alert_msg, bo_alert_open, bo_alert_color)
    """
    bo_alert_msg = no_update
    bo_alert_open = no_update
    bo_alert_color = no_update
    
    try:
        domain = create_bofire_domain_from_store(domain_data)
        
        if domain is None:
            state = add_log_entry(state, "❌ Failed to create BO domain")
            return updated_data, state, "❌ Failed to create domain", True, "danger"
        
        # Prepare experiments DataFrame with numeric objectives
        df_experiments = pd.DataFrame(updated_data)
        for obj in obj_names:
            if obj in df_experiments.columns:
                df_experiments[obj] = pd.to_numeric(df_experiments[obj], errors='coerce')
        
        df_complete = df_experiments.dropna(subset=obj_names)
        
        # Run BO
        advanced_settings = advanced_settings or {}
        n_suggestions = advanced_settings.get('n_candidates', 1)
        
        new_candidates = bayesian_optimization(
            domain, df_complete, n_candidates=n_suggestions
        )
        
        if new_candidates is None or new_candidates.empty:
            state = add_log_entry(state, "❌ BO failed to generate candidates")
            return updated_data, state, "❌ BO failed to generate candidates", True, "danger"
        
        # Apply constraints if configured
        constraints_config = domain_data.get('metadata', {}).get('constraints_config')
        if constraints_config:
            for idx in range(len(new_candidates)):
                row = new_candidates.iloc[idx]
                adjusted = validate_and_adjust_suggestion(
                    row.to_dict(), constraints_config, domain_data
                )
                for k, v in adjusted.items():
                    new_candidates.at[new_candidates.index[idx], k] = v
        
        # Add suggestion rows to table
        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        
        for _, candidate in new_candidates.iterrows():
            new_row = {col: '' for col in updated_data[0].keys()}
            new_row['Point type'] = 'BO suggestion'
            
            for param in param_names:
                if param in candidate:
                    new_row[param] = candidate[param]
            
            updated_data.append(new_row)
        
        state["bo_iteration"] = state.get("bo_iteration", 0) + 1
        n_added = len(new_candidates)
        state = add_log_entry(state, f"🤖 BO iteration {state['bo_iteration']}: {n_added} experiment(s) suggested")
        
        # Save with BO suggestions
        excel_file = state.get("filepath", "").replace(os.sep, "/")
        # We need to save via the correct path — caller should handle this
        # For now, the main callback saves after this returns
        
        bo_alert_msg = f"🤖 Online BO iteration {state['bo_iteration']}: {n_added} new experiment(s) suggested. Waiting for results..."
        bo_alert_open = True
        bo_alert_color = "info"
        
    except Exception as e:
        state = add_log_entry(state, f"❌ BO error: {e}")
        bo_alert_msg = f"❌ BO error: {str(e)}"
        bo_alert_open = True
        bo_alert_color = "danger"
    
    return updated_data, state, bo_alert_msg, bo_alert_open, bo_alert_color


def _build_outputs(state, table_data=no_update,
                   status_text=None, status_color=None,
                   bo_alert_msg=no_update, bo_alert_open=no_update, bo_alert_color=no_update):
    """
    Build the standard 12-element output tuple for the polling callback.
    Centralizes all UI state computation.
    """
    phase = state.get("phase", "initialization")
    results_count = state.get("results_processed", 0)
    total_init = state.get("total_init_experiments", 0)
    bo_iter = state.get("bo_iteration", 0)
    
    if phase == "initialization":
        progress = (results_count / total_init * 100) if total_init > 0 else 0
        progress_text = f"{results_count} / {total_init} init results received"
        phase_badge = "Initialization"
        phase_color = "info"
        if status_text is None:
            status_text = "Receiving results..." if results_count > 0 else "Waiting for first result..."
        if status_color is None:
            status_color = "success" if results_count > 0 else "warning"
    else:
        progress = 100
        progress_text = f"BO iteration {bo_iter} — {results_count} total results"
        phase_badge = "Optimization"
        phase_color = "primary"
        if status_text is None:
            status_text = f"BO active (iter {bo_iter})"
        if status_color is None:
            status_color = "success"
    
    log_text = "\n".join(state.get("log_entries", []))
    
    return (
        table_data,
        state,
        log_text,
        phase_badge,
        phase_color,
        status_text,
        status_color,
        progress_text,
        min(progress, 100),
        bo_alert_msg,
        bo_alert_open,
        bo_alert_color
    )
"""
Sensitivity Screen Callbacks
Auto-generates OFAT experiments on page load and renders radar diagram live.
"""

from dash import callback, Input, Output, State, html, no_update, ctx, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

from domain_storage import DomainStorage
from config_path import EXCEL_FOLDER
from utils.sensitivity_screen import (
    generate_sensitivity_experiments,
    find_best_experiment,
    create_sensitivity_radar
)


# ============================================================================
# HELPER: build the DataTable component
# ============================================================================

def _build_sensitivity_datatable(data, param_names, obj_names):
    """Return a DataTable for the sensitivity experiments."""
    columns = [
        {'name': 'Parameter', 'id': '_sensitivity_param', 'editable': False, 'type': 'text'},
        {'name': 'Variation', 'id': '_sensitivity_direction', 'editable': False, 'type': 'text'},
    ]
    for p in param_names:
        columns.append({'name': p, 'id': p, 'editable': False, 'type': 'numeric'})
    for o in obj_names:
        columns.append({'name': f"✏️ {o}", 'id': o, 'editable': True, 'type': 'numeric'})

    return dash_table.DataTable(
        id='sensitivity-datatable',
        columns=columns,
        data=data,
        editable=True,
        row_selectable=False,
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': '600',
            'fontSize': '12px',
            'borderBottom': '2px solid #dee2e6',
            'textAlign': 'center',
        },
        style_cell={
            'textAlign': 'center',
            'padding': '8px 12px',
            'fontSize': '13px',
            'fontFamily': 'Inter, -apple-system, sans-serif',
            'minWidth': '80px',
        },
        style_data_conditional=[
            # Reference row
            {
                'if': {'filter_query': '{_sensitivity_direction} = "ref"'},
                'backgroundColor': '#e8f5e9',
                'fontWeight': '600',
            },
            # Editable objective columns
            {
                'if': {'column_id': obj_names},
                'backgroundColor': '#fff8e1',
                'border': '1px solid #ffc107',
            },
            # -50% rows
            {
                'if': {'filter_query': '{_sensitivity_direction} = "-50%"'},
                'backgroundColor': '#fff3e0',
            },
            # +50% rows
            {
                'if': {'filter_query': '{_sensitivity_direction} = "+50%"'},
                'backgroundColor': '#e3f2fd',
            },
        ],
    )


# ============================================================================
# 1. PAGE LOAD → show best experiment + auto-generate table
#    Pattern copied from results_analysis.py initialize_results_page
# ============================================================================

@callback(
    [Output('sensitivity-best-summary', 'children'),
     Output('sensitivity-table-container', 'children'),
     Output('sensitivity-experiments-store', 'data'),
     Output('sensitivity-reference-store', 'data'),
     Output('sensitivity-status-alert', 'children'),
     Output('sensitivity-status-alert', 'is_open'),
     Output('sensitivity-status-alert', 'color')],
    [Input('current-excel-file', 'data'),
     Input('url', 'pathname')]
)
def initialize_sensitivity_page(excel_file, pathname):
    """Load best experiment and auto-generate sensitivity table on page load."""

    empty_summary = html.P("No data available", className="text-muted text-center")
    empty_table = html.P("No experiments to display", className="text-muted text-center py-4")

    if pathname != '/sensitivity' or not excel_file:
        raise PreventUpdate

    print(f"Sensitivity page loading for: {excel_file}")

    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df = pd.read_excel(file_path, engine='openpyxl')

        storage = DomainStorage()
        domain_data = storage.load_domain(excel_file)
        if not domain_data:
            return (empty_summary, empty_table, None, None,
                    "Domain configuration not found.", True, "danger")

        param_names = domain_data.get('metadata', {}).get('parameter_names', [])
        obj_names = domain_data.get('metadata', {}).get('objective_names', [])
        objectives = domain_data.get('objectives', [])
        parameters = domain_data.get('parameters', [])

        # ---- Find best experiment (same logic as convergence plot) ----
        best = find_best_experiment(df, param_names, obj_names, objectives)
        if not best:
            return (empty_summary, empty_table, None, None,
                    "No completed experiments found.", True, "warning")

        print(f"🏆 Best experiment: {best}")

        # ---- Build summary cards ----
        cards = []
        for p in param_names:
            val = best.get(p, 'N/A')
            if isinstance(val, (float, np.floating)):
                val = f"{val:.4g}"
            cards.append(
                dbc.Col([
                    html.Div([
                        html.Small(p, className="text-muted"),
                        html.Div(html.Strong(str(val)), style={"fontSize": "1.1rem"})
                    ], className="text-center p-2",
                       style={"backgroundColor": "#f0f0f0", "borderRadius": "8px"})
                ], md=True, className="mb-2")
            )
        for o in obj_names:
            val = best.get(o, 'N/A')
            if isinstance(val, (float, np.floating)):
                val = f"{val:.4g}"
            cards.append(
                dbc.Col([
                    html.Div([
                        html.Small(o, className="text-muted"),
                        html.Div(html.Strong(str(val)),
                                 style={"fontSize": "1.1rem", "color": "#10b981"})
                    ], className="text-center p-2",
                       style={"backgroundColor": "#e8f5e9", "borderRadius": "8px"})
                ], md=True, className="mb-2")
            )
        summary = dbc.Row(cards)

        # ---- Generate sensitivity experiments ----
        sens_df = generate_sensitivity_experiments(
            best, parameters, objectives, variation_pct=0.50
        )

        display_cols = ['_sensitivity_param', '_sensitivity_direction'] + param_names + obj_names
        data = sens_df[display_cols].to_dict('records')
        table = _build_sensitivity_datatable(data, param_names, obj_names)

        # ---- Store reference data ----
        ref_data = {
            'best_experiment': {
                k: (float(v) if isinstance(v, (np.integer, np.floating)) else v)
                for k, v in best.items()
            },
            'param_names': param_names,
            'obj_names': obj_names,
        }

        n_exp = len(sens_df)
        n_varied = len(sens_df[sens_df['_sensitivity_param'] != 'Reference']['_sensitivity_param'].unique())

        return (
            summary,
            table,
            data,
            ref_data,
            f"✅ {n_exp} sensitivity experiments generated "
            f"({n_varied} parameters varied ±50 %). "
            f"Fill in the objective values after running the experiments.",
            True, "success"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return (empty_summary, empty_table, None, None,
                f"Error: {e}", True, "danger")


# ============================================================================
# 2. SAVE RESULTS TO EXCEL
# ============================================================================

@callback(
    [Output('sensitivity-status-alert', 'children', allow_duplicate=True),
     Output('sensitivity-status-alert', 'is_open', allow_duplicate=True),
     Output('sensitivity-status-alert', 'color', allow_duplicate=True)],
    Input('save-sensitivity-btn', 'n_clicks'),
    [State('sensitivity-datatable', 'data'),
     State('current-excel-file', 'data')],
    prevent_initial_call=True
)
def save_sensitivity_results(n_clicks, table_data, excel_file):
    """Append sensitivity experiments to the main Excel file."""

    if not n_clicks or not table_data or not excel_file:
        raise PreventUpdate

    try:
        file_path = os.path.join(EXCEL_FOLDER, excel_file)
        df_existing = pd.read_excel(file_path, engine='openpyxl')

        df_sens = pd.DataFrame(table_data)

        # Only keep columns that exist in the main file + Point type
        keep_cols = [c for c in df_existing.columns if c in df_sens.columns]
        if 'Point type' not in keep_cols and 'Point type' in df_sens.columns:
            keep_cols.append('Point type')

        df_to_append = df_sens[keep_cols].copy()

        # Remove existing sensitivity rows to avoid duplicates
        if 'Point type' in df_existing.columns:
            df_existing = df_existing[df_existing['Point type'] != 'Sensitivity']

        df_combined = pd.concat([df_existing, df_to_append], ignore_index=True)
        df_combined.to_excel(file_path, index=False, engine='openpyxl')

        return (f"💾 Saved {len(df_to_append)} sensitivity experiments to {excel_file}",
                True, "success")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error saving: {e}", True, "danger"


# ============================================================================
# 3. LIVE UPDATE RADAR + BAR CHARTS
# ============================================================================

@callback(
    Output('sensitivity-radar-plot', 'figure'),
    Input('sensitivity-datatable', 'data'),
    State('sensitivity-reference-store', 'data'),
    prevent_initial_call=True
)
def update_sensitivity_plots(table_data, ref_data):
    """Regenerate radar and bar charts when table data changes."""

    empty = go.Figure()
    empty.update_layout(
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        annotations=[dict(text="Fill in objective values to see the radar diagram",
                          xref="paper", yref="paper", x=0.5, y=0.5,
                          showarrow=False, font=dict(size=14, color="#6c757d"))],
        plot_bgcolor='white', paper_bgcolor='white'
    )

    if not table_data or not ref_data:
        return empty

    obj_names = ref_data.get('obj_names', [])
    if not obj_names:
        return empty

    obj_name = obj_names[0]
    df = pd.DataFrame(table_data)

    # Get reference yield
    ref_rows = df[df['_sensitivity_direction'] == 'ref']
    if len(ref_rows) == 0:
        return empty

    ref_yield = pd.to_numeric(ref_rows.iloc[0].get(obj_name, np.nan), errors='coerce')

    # Fallback: use best experiment yield from store
    if pd.isna(ref_yield):
        best_exp = ref_data.get('best_experiment', {})
        ref_yield = best_exp.get(obj_name)
        if ref_yield is not None:
            ref_yield = float(ref_yield)

    if ref_yield is None or pd.isna(ref_yield) or ref_yield == 0:
        return empty

    # Check if any non-reference values are filled
    non_ref = df[df['_sensitivity_direction'] != 'ref']
    obj_vals = pd.to_numeric(non_ref[obj_name], errors='coerce')
    if obj_vals.notna().sum() == 0:
        return empty

    radar = create_sensitivity_radar(df, obj_name, ref_yield)

    return radar
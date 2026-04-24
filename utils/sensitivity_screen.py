"""
OFAT sensitivity screen around an optimum, rendered as a Glorius-style radar.

References:
    Pitzer, Schäfers & Glorius, Angew. Chem. Int. Ed. 2019, 58, 8572-8576
    Schäfer, Lückemeier & Glorius, Chem. Sci. 2024, 15, 14548-14555

Radar convention (faithful to Glorius):
    - Center (+50%) = improvement over reference → robust
    - Edge (-100%)  = total loss of yield        → sensitive
    - Concentric colored zones: blue (robust) → white (moderate) → orange/red
    - Black polygon traces the actual yield deviations
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def _yield_to_color(ratio):
    """Traffic-light RGBA fill for a yield ratio (unused publicly, kept for reuse)."""
    if ratio >= 0.90:
        return "rgba(16, 185, 129, 0.85)"
    if ratio >= 0.70:
        return "rgba(251, 191, 36, 0.85)"
    return "rgba(239, 68, 68, 0.85)"


def _sensitivity_label(ratio):
    """Return a Robust / Moderate / Sensitive label for a yield ratio."""
    if ratio >= 0.90:
        return "Robust"
    if ratio >= 0.70:
        return "Moderate"
    return "Sensitive"


def _glorius_gradient_bands():
    """Concentric ``(radius, rgba)`` bands used to paint the radar background."""
    return [
        (150, "rgba(198, 80, 30, 1.0)"),
        (140, "rgba(212, 100, 42, 1.0)"),
        (130, "rgba(226, 120, 55, 1.0)"),
        (119, "rgba(236, 142, 70, 1.0)"),
        (108, "rgba(243, 162, 90, 1.0)"),
        (97,  "rgba(248, 182, 115, 1.0)"),
        (87,  "rgba(252, 200, 145, 1.0)"),
        (77,  "rgba(254, 222, 185, 1.0)"),
        (66,  "rgba(250, 235, 220, 1.0)"),
        (56,  "rgba(240, 240, 245, 1.0)"),
        (45,  "rgba(200, 225, 245, 1.0)"),
        (36,  "rgba(165, 210, 240, 1.0)"),
        (27,  "rgba(130, 195, 235, 1.0)"),
        (18,  "rgba(100, 180, 225, 1.0)"),
        (10,  "rgba(75, 165, 218, 1.0)"),
    ]


def generate_sensitivity_experiments(best_experiment: dict,
                                     parameters: list,
                                     objectives: list,
                                     variation_pct: float = 0.50) -> pd.DataFrame:
    """
    Build an OFAT perturbation batch around ``best_experiment``.

    For every numeric parameter, two new rows are produced (``-variation_pct``
    and ``+variation_pct`` relative to the reference), clipped to the
    parameter bounds and snapped to the parameter step when available.
    Categorical parameters are skipped.
    """
    obj_names = [o['name'] for o in objectives]
    param_names = [p['name'] for p in parameters]
    rows = []

    ref_row = {p: best_experiment.get(p, '') for p in param_names}
    for o in obj_names:
        ref_row[o] = ''
    ref_row['Point type'] = 'Sensitivity'
    ref_row['_sensitivity_param'] = 'Reference'
    ref_row['_sensitivity_direction'] = 'ref'
    rows.append(ref_row)

    for param in parameters:
        name = param['name']
        ptype = param.get('type')

        if ptype == 'cat':
            continue

        best_val = best_experiment.get(name)
        if best_val is None or best_val == '':
            continue

        best_val = float(best_val)

        type_info = param.get('type_info', {})
        if ptype == 'float':
            bounds = type_info.get('range', [None, None])
            lb, ub = (float(bounds[0]) if bounds[0] is not None else None,
                      float(bounds[1]) if bounds[1] is not None else None)
            step = type_info.get('step')
        elif ptype == 'int':
            values = type_info.get('range', [])
            if values:
                lb, ub = min(values), max(values)
            else:
                lb, ub = None, None
            step = None
        else:
            continue

        delta = abs(best_val) * variation_pct
        if delta == 0:
            if lb is not None and ub is not None:
                delta = (ub - lb) * variation_pct
            else:
                continue

        for direction, sign in [('-50%', -1), ('+50%', +1)]:
            new_val = best_val + sign * delta

            if lb is not None:
                new_val = max(new_val, lb)
            if ub is not None:
                new_val = min(new_val, ub)

            if step and step > 0:
                new_val = round(round(new_val / step) * step, 6)
            elif ptype == 'int' and values:
                new_val = min(values, key=lambda v: abs(v - new_val))

            if ptype == 'float' and step is None:
                new_val = round(new_val, 4)

            row = {p: best_experiment.get(p, '') for p in param_names}
            row[name] = new_val
            for o in obj_names:
                row[o] = ''
            row['Point type'] = 'Sensitivity'
            row['_sensitivity_param'] = name
            row['_sensitivity_direction'] = direction
            rows.append(row)

    return pd.DataFrame(rows)


def find_best_experiment(df: pd.DataFrame,
                         param_names: list,
                         obj_names: list,
                         objectives: list) -> dict:
    """
    Return the best row of ``df`` as a ``{param/obj: value}`` dict.

    "Best" is determined by the first objective in ``obj_names`` and its
    ``direction`` (``'min'`` or ``'max'``) looked up in ``objectives``. Rows
    with NaN objective values are ignored.
    """
    df_complete = df.copy()
    for obj in obj_names:
        if obj in df_complete.columns:
            df_complete[obj] = pd.to_numeric(df_complete[obj], errors='coerce')
            df_complete = df_complete[df_complete[obj].notna()]

    if len(df_complete) == 0:
        return {}

    obj_col = obj_names[0]
    direction = 'min'
    for obj in objectives:
        if obj.get('name') == obj_col:
            direction = obj.get('direction', 'min')
            break

    if direction == 'min':
        best_idx = df_complete[obj_col].idxmin()
    else:
        best_idx = df_complete[obj_col].idxmax()

    best_row = df_complete.loc[best_idx]
    result = {}
    for p in param_names:
        if p in best_row.index:
            result[p] = best_row[p]
    for o in obj_names:
        if o in best_row.index:
            result[o] = best_row[o]

    return result


def create_sensitivity_radar(sensitivity_df: pd.DataFrame,
                             obj_name: str,
                             reference_yield: float) -> go.Figure:
    """
    Render a Glorius-style radar of sensitivity perturbations.

    Each spoke is one ``(parameter, direction)`` pair. The black polygon
    connects the relative deviation of ``obj_name`` from ``reference_yield``.
    """
    if reference_yield is None or reference_yield == 0:
        fig = go.Figure()
        fig.update_layout(title="Cannot create radar: reference yield is 0 or missing")
        return fig

    # 1. Collect yield deviations per perturbation
    params_data = {}

    for _, row in sensitivity_df.iterrows():
        param = row.get('_sensitivity_param', '')
        direction = row.get('_sensitivity_direction', '')
        if param == 'Reference' or param == '' or direction == 'ref':
            continue

        val = pd.to_numeric(row.get(obj_name, np.nan), errors='coerce')
        if pd.isna(val):
            continue

        deviation_pct = (val - reference_yield) / reference_yield * 100
        deviation_pct = max(-100, min(deviation_pct, 50))

        if param not in params_data:
            params_data[param] = {}
        params_data[param][direction] = deviation_pct

    if not params_data:
        fig = go.Figure()
        fig.update_layout(title="No sensitivity data available yet")
        return fig

    # 2. Build spoke labels and radar values
    # Mapping: r_plotly = 50 - deviation_pct
    #   +50% → r=0 (center), 0% → r=50, -50% → r=100, -100% → r=150

    categories = []
    r_values = []
    deviation_values = []
    hover_texts = []

    for param in params_data:
        data = params_data[param]
        for direction in ['-50%', '+50%']:
            if direction in data:
                dev = data[direction]

                label = f"{param} ({direction})"
                categories.append(label)

                r = 50.0 - dev
                r = max(0, min(r, 150))
                r_values.append(r)
                deviation_values.append(dev)

                sens = _sensitivity_label((100 + dev) / 100)
                hover_texts.append(
                    f"<b>{param} {direction}</b><br>"
                    f"Yield deviation: {dev:+.1f}%<br>"
                    f"Absolute yield: {reference_yield * (1 + dev/100):.4g}<br>"
                    f"Sensitivity: {sens}"
                )

    if len(categories) == 0:
        fig = go.Figure()
        fig.update_layout(title="No sensitivity data available yet")
        return fig

    categories_closed = categories + [categories[0]]
    r_values_closed = r_values + [r_values[0]]
    hover_texts_closed = hover_texts + [hover_texts[0]]

    # 3. Glorius-style concentric color gradient
    fig = go.Figure()
    theta_fill = categories + [categories[0]]

    for zone_r, zone_color in _glorius_gradient_bands():
        fig.add_trace(go.Scatterpolar(
            r=[zone_r] * len(theta_fill), theta=theta_fill,
            fill='toself', fillcolor=zone_color,
            line=dict(color='rgba(0,0,0,0)', width=0),
            hoverinfo='skip', showlegend=False,
        ))

    # 4. Grid circles
    for thresh in [25, 50, 75, 100, 125]:
        fig.add_trace(go.Scatterpolar(
            r=[thresh] * len(theta_fill), theta=theta_fill,
            line=dict(color='rgba(0,0,0,0.15)', width=0.8),
            hoverinfo='skip', showlegend=False,
        ))

    # 5. Black data polygon
    fig.add_trace(go.Scatterpolar(
        r=r_values_closed, theta=categories_closed,
        fill='toself', fillcolor='rgba(0, 0, 0, 0.08)',
        line=dict(color='black', width=3),
        marker=dict(size=10, color='black', line=dict(width=1.5, color='white')),
        name=f'Deviation of {obj_name} from<br>standard conditions (%)',
        hovertext=hover_texts_closed, hoverinfo='text',
    ))

    # 6. Layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 155],
                tickvals=[0, 25, 50, 75, 100, 125, 150],
                ticktext=['50', '25', '0', '−25', '−50', '−75', '−100'],
                tickfont=dict(size=11, color='rgba(0,0,0,0.6)', family="Arial, sans-serif"),
                gridcolor='rgba(0,0,0,0)', linecolor='rgba(0,0,0,0)', showline=False,
            ),
            angularaxis=dict(
                tickfont=dict(size=12, family="Arial, sans-serif", color='#222'),
                gridcolor='rgba(0,0,0,0.12)', linecolor='rgba(0,0,0,0.15)',
                rotation=90, direction='clockwise',
            ),
            bgcolor='rgba(0,0,0,0)',
        ),
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.05, xanchor='center', x=0.5,
                    font=dict(size=11), itemsizing='constant'),
        title=dict(
            text=(f"<b>Reaction-condition sensitivity analysis</b><br>"
                  f"<sup>Reference {obj_name}: {reference_yield:.4g} "
                  f"| Center = robust (0%), Edge = sensitive (−100%)</sup>"),
            font=dict(size=15, family="Arial, sans-serif"), x=0.5,
        ),
        font=dict(family="Arial, sans-serif"),
        paper_bgcolor='white', plot_bgcolor='white',
        margin=dict(t=100, b=80, l=80, r=80), height=650,
    )

    return fig
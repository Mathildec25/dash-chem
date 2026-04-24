"""
Shared layout builders used by both page layouts and callback modules.

Living in ``components/`` (not ``callbacks/``) so that layout and callback
modules can both depend on it without creating a circular import.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

from utils.descriptor_data import get_available_descriptors


def make_objective_row(row_id: str) -> html.Div:
    """Row of inputs used to define one objective (name / direction / bounds)."""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Input(
                    id={"type": "objective-name", "index": row_id},
                    placeholder="Objective name", size="sm",
                    style={"borderRadius": "6px"},
                ),
            ], width=4),
            dbc.Col([
                dcc.Dropdown(
                    id={"type": "objective-direction", "index": row_id},
                    options=[
                        {"label": "Minimize", "value": "min"},
                        {"label": "Maximize", "value": "max"},
                    ],
                    placeholder="Direction", clearable=False,
                    style={"fontSize": "0.875rem"},
                ),
            ], width=2),
            dbc.Col([
                dbc.Input(
                    id={"type": "objective-lower", "index": row_id},
                    placeholder="Min", type="number", step="any", size="sm",
                    style={"borderRadius": "6px"},
                ),
            ], width=2),
            dbc.Col([
                dbc.Input(
                    id={"type": "objective-upper", "index": row_id},
                    placeholder="Max", type="number", step="any", size="sm",
                    style={"borderRadius": "6px"},
                ),
            ], width=2),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={"type": "delete-objective", "index": row_id},
                    color="danger", outline=True, size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"},
                ),
            ], width=2),
        ], className="mb-1 align-items-center"),
    ], id={"type": "objective-row", "index": row_id})


def _build_custom_descriptor_form(
    kind: str,
    collapse_id: str,
    name_input_id: str,
    desc_input_type: str,
    save_button_id: str,
    save_button_label: str,
) -> html.Div:
    """Shared implementation for the custom-solvent / custom-base forms."""
    descriptor_keys = get_available_descriptors(kind)

    descriptor_inputs = [
        dbc.Row([
            dbc.Col([dbc.Label(desc_key, className="small mb-0")], width=4),
            dbc.Col([
                dbc.Input(
                    id={"type": desc_input_type, "index": desc_key},
                    type="number",
                    placeholder=f"Value for {desc_key}",
                    size="sm",
                    style={"borderRadius": "6px"},
                ),
            ], width=8),
        ], className="mb-2 align-items-center")
        for desc_key in descriptor_keys
    ]

    return html.Div([
        html.Div([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(
                            [dbc.Label(f"{kind.capitalize()} Name", className="small mb-0 fw-bold")],
                            width=4,
                        ),
                        dbc.Col([
                            dbc.Input(
                                id=name_input_id,
                                type="text",
                                placeholder=f"e.g. My Custom {kind.capitalize()}",
                                size="sm",
                                style={"borderRadius": "6px"},
                            ),
                        ], width=8),
                    ], className="mb-3 align-items-center"),

                    html.Hr(className="my-2"),
                    html.P(
                        "Descriptor values:",
                        className="small fw-bold mb-2 text-muted",
                    ),

                    *descriptor_inputs,

                    html.Hr(className="my-2"),

                    dbc.Button(
                        [html.I(className="bi bi-check-circle me-2"), save_button_label],
                        id=save_button_id,
                        color="success",
                        size="sm",
                        className="w-100",
                    ),
                ]),
            ], className="border-info"),
        ], id=collapse_id, style={"display": "none"}),
    ])


def create_custom_solvent_form() -> html.Div:
    """Collapsible form for adding a custom solvent + all its descriptor values."""
    return _build_custom_descriptor_form(
        kind="solvent",
        collapse_id="custom-solvent-collapse",
        name_input_id="custom-solvent-name",
        desc_input_type="custom-solvent-desc",
        save_button_id="confirm-custom-solvent-btn",
        save_button_label="Save Custom Solvent",
    )


def create_custom_base_form() -> html.Div:
    """Collapsible form for adding a custom base + all its descriptor values."""
    return _build_custom_descriptor_form(
        kind="base",
        collapse_id="custom-base-collapse",
        name_input_id="custom-base-name",
        desc_input_type="custom-base-desc",
        save_button_id="confirm-custom-base-btn",
        save_button_label="Save Custom Base",
    )

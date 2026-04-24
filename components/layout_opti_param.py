"""Layout for the domain parameterization page."""

import uuid

import dash_bootstrap_components as dbc
from dash import dcc, html

from callbacks.opti_param_callbacks.base_callbacks import create_custom_base_form
from callbacks.opti_param_callbacks.solvents_callbacks import create_custom_solvent_form
from components.constraints_card import create_constraints_card

initial_id = str(uuid.uuid4())
initial_objective_id = str(uuid.uuid4())


def _make_objective_row(row_id: str) -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Input(
                    id={'type': 'objective-name', 'index': row_id},
                    placeholder="Objective name", size="sm",
                    style={"borderRadius": "6px"})
            ], width=4),
            dbc.Col([
                dcc.Dropdown(
                    id={'type': 'objective-direction', 'index': row_id},
                    options=[
                        {"label": "Minimize", "value": "min"},
                        {"label": "Maximize", "value": "max"},
                    ],
                    placeholder="Direction", clearable=False,
                    style={"fontSize": "0.875rem"})
            ], width=2),
            dbc.Col([
                dbc.Input(
                    id={'type': 'objective-lower', 'index': row_id},
                    placeholder="Min", type="number", step="any", size="sm",
                    style={"borderRadius": "6px"})
            ], width=2),
            dbc.Col([
                dbc.Input(
                    id={'type': 'objective-upper', 'index': row_id},
                    placeholder="Max", type="number", step="any", size="sm",
                    style={"borderRadius": "6px"})
            ], width=2),
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash", style={"fontSize": "0.875rem"}),
                    id={'type': 'delete-objective', 'index': row_id},
                    color="danger", outline=True, size="sm",
                    style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"})
            ], width=2),
        ], className="mb-1 align-items-center"),
    ], id={'type': 'objective-row', 'index': row_id})


def create_opti_param_layout():
    return dbc.Container([

        # ── Header ────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dcc.Link(
                    html.I(className="bi bi-arrow-left",
                           style={"fontSize": "1.5rem", "color": "#6c757d"}),
                    href="/Opt-home", style={"textDecoration": "none"})
            ], width="auto"),
            dbc.Col([
                html.H1("Domain Configuration",
                        style={"color": "#1a1a1a", "fontWeight": "600", "fontSize": "2rem",
                               "letterSpacing": "-0.02em", "marginBottom": "0.25rem"}),
                html.P("Define your optimization space parameters and objectives",
                       style={"fontSize": "1rem", "color": "#6c757d", "marginBottom": "0"})
            ], width=True)
        ], className="mb-4 align-items-center"),

        # ── Validation alert ──────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Alert(id="validation-alert", is_open=False, dismissable=True, className="mb-3")
            ], md=12)
        ]),

        # ══════════════════════════════════════════════════════════════════
        #  TRANSFER LEARNING — compact strip at the very top
        # ══════════════════════════════════════════════════════════════════
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            # Switch
                            dbc.Col([
                                dbc.Switch(
                                    id="tl-domain-switch",
                                    label=html.Span([
                                        html.I(className="bi bi-arrow-left-right me-1",
                                               style={"color": "#2a9d8f"}),
                                        html.Strong("Transfer Learning"),
                                        html.Span(
                                            " — reuse data from a past campaign (same domain)",
                                            className="text-muted ms-1",
                                            style={"fontWeight": "400", "fontSize": "0.85rem"}
                                        )
                                    ]),
                                    value=False,
                                    className="mb-0"
                                )
                            ], width="auto", className="d-flex align-items-center"),

                            # Source dropdown (shown when switch ON)
                            dbc.Col([
                                html.Div(
                                    id="tl-domain-source-section",
                                    style={"display": "none"},
                                    children=[
                                        dbc.Row([
                                            dbc.Col([
                                                dcc.Dropdown(
                                                    id="tl-domain-source-dropdown",
                                                    options=[],
                                                    placeholder="Select source campaign…",
                                                    clearable=True,
                                                    style={"fontSize": "0.875rem"}
                                                )
                                            ], width=8),
                                            dbc.Col([
                                                html.Div(id="tl-domain-compatibility-badge")
                                            ], width=4, className="d-flex align-items-center")
                                        ], align="center")
                                    ]
                                )
                            ], width=True),
                        ], align="center"),

                        # Info banner (visible when TL active + source confirmed)
                        html.Div(
                            id="tl-best-point-info",
                            style={"display": "none"},
                            children=[
                                dbc.Alert([
                                    html.I(className="bi bi-lightning-charge-fill me-2",
                                           style={"color": "#2a9d8f"}),
                                    html.Strong("Parameters locked"),
                                    " — imported from source campaign.  ",
                                    html.Strong("First experiment: "),
                                    "the best-performing condition from the source campaign "
                                    "(Summit strategy, 1 init point)."
                                ], color="success", className="py-2 mb-0 mt-2",
                                   style={"fontSize": "0.8rem"})
                            ]
                        )
                    ], style={"padding": "0.75rem 1.25rem"})
                ], style={
                    "borderRadius": "10px",
                    "border": "1px solid #d0f0ec",
                    "backgroundColor": "#f4fdfb"
                })
            ], md=12, className="mb-3")
        ]),
        # ══════════════════════════════════════════════════════════════════

        # ── Parameters + Objectives ───────────────────────────────────────
        dbc.Row([
            # Parameters Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5("Parameters", className="mb-0",
                                    style={"fontWeight": "600", "display": "inline-block"}),
                            # Buttons hidden by TL callback when source selected
                            html.Div(
                                id="param-action-buttons",
                                className="float-end",
                                children=[
                                    dbc.Button("Solvant", id="add-solvent-button",
                                               color="secondary", outline=True, size="sm",
                                               className="me-2",
                                               style={"borderRadius": "6px",
                                                      "padding": "0.25rem 0.75rem"}),
                                    dbc.Button("Base", id="add-base-button",
                                               color="secondary", outline=True, size="sm",
                                               className="me-2",
                                               style={"borderRadius": "6px",
                                                      "padding": "0.25rem 0.75rem"}),
                                    dbc.Button(html.I(className="bi bi-plus-lg"),
                                               id="add-para-button", color="primary", size="sm",
                                               style={"borderRadius": "6px",
                                                      "padding": "0.25rem 0.5rem"}),
                                ]
                            ),
                        ], className="mb-3"),

                        html.Div(id="parameter-container", children=[
                            html.Div([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Input(
                                            id={'type': 'parameter-name', 'index': initial_id},
                                            placeholder="Parameter name", size="sm",
                                            style={"borderRadius": "6px"})
                                    ], width=3),
                                    dbc.Col([
                                        dcc.Dropdown(
                                            id={'type': 'parameter-type', 'index': initial_id},
                                            options=[
                                                {"label": "Continuous", "value": "float"},
                                                {"label": "Discrete",   "value": "int"},
                                                {"label": "Categorical","value": "cat"},
                                            ],
                                            value="float", clearable=False,
                                            style={"fontSize": "0.875rem"})
                                    ], width=2),
                                    dbc.Col([
                                        html.Div(
                                            id={'type': 'parameter-inputs',
                                                'index': initial_id},
                                            children=[
                                                dbc.Row([
                                                    dbc.Col(dbc.Input(
                                                        id={'type': 'parameter-min',
                                                            'index': initial_id},
                                                        placeholder="Min", type="number",
                                                        step="any", size="sm",
                                                        style={"borderRadius": "6px"}),
                                                        width=4),
                                                    dbc.Col(dbc.Input(
                                                        id={'type': 'parameter-max',
                                                            'index': initial_id},
                                                        placeholder="Max", type="number",
                                                        step="any", size="sm",
                                                        style={"borderRadius": "6px"}),
                                                        width=4),
                                                    dbc.Col(dbc.Input(
                                                        id={'type': 'parameter-step',
                                                            'index': initial_id},
                                                        placeholder="Step", type="number",
                                                        step="any", size="sm",
                                                        style={"borderRadius": "6px"}),
                                                        width=4),
                                                ])
                                            ])
                                    ], width=5),
                                    dbc.Col([
                                        html.Div(
                                            id={'type': 'parameter-categories',
                                                'index': initial_id},
                                            style={"display": "none"})
                                    ], width=0),
                                    dbc.Col([
                                        dbc.Button(
                                            html.I(className="bi bi-trash",
                                                   style={"fontSize": "0.875rem"}),
                                            id={'type': 'delete-parameter',
                                                'index': initial_id},
                                            color="danger", outline=True, size="sm",
                                            style={"borderRadius": "6px",
                                                   "padding": "0.25rem 0.5rem"})
                                    ], width=1),
                                ], className="mb-2 align-items-center"),
                            ], id={'type': 'parameter-row', 'index': initial_id})
                        ]),
                    ], style={"padding": "1.25rem"})
                ], style={
                    "borderRadius": "12px", "border": "1px solid #e0e0e0",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
                    "backgroundColor": "white", "height": "100%"
                })
            ], md=6, className="mb-3"),

            # Objectives Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5("Objectives", className="mb-0",
                                    style={"fontWeight": "600", "display": "inline-block"}),
                            dbc.Button(
                                html.I(className="bi bi-plus-lg"),
                                id="add-objective-button",
                                color="success", size="sm", className="float-end",
                                style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}
                            ),
                        ], className="mb-3"),
                        html.Div(id="objective-container", children=[
                            _make_objective_row(initial_objective_id)
                        ]),
                    ], style={"padding": "1.25rem"})
                ], style={
                    "borderRadius": "12px", "border": "1px solid #e0e0e0",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
                    "backgroundColor": "white", "height": "100%"
                })
            ], md=6, className="mb-3"),
        ]),

        # ── Constraints ───────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([create_constraints_card()], md=12)
        ], className="mb-3"),

        # ── Extra Columns (collapsible) ───────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Button([html.I(className="bi bi-plus-square me-2"),
                            "Add Extra Columns (Optional)"],
                           id="toggle-extra-columns", outline=True, color="secondary",
                           size="sm", className="mb-3", style={"borderRadius": "6px"}),
                dbc.Collapse([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Extra Columns", className="mb-3",
                                    style={"fontWeight": "600"}),
                            html.Div(id="extra-column-container", children=[]),
                            dbc.Button([html.I(className="bi bi-plus me-2"), "Add Column"],
                                       id="add-extra-column-button", outline=True,
                                       color="secondary", size="sm",
                                       style={"borderRadius": "6px"}),
                        ], style={"padding": "1rem"})
                    ], style={"borderRadius": "12px", "border": "1px solid #e0e0e0",
                              "backgroundColor": "white"})
                ], id="extra-columns-collapse", is_open=False),
            ], md=12, className="mb-3")
        ]),

        # ── Sampling (hidden when TL active) ─────────────────────────────
        html.Div(
            id="sampling-config-row",
            className="mb-3",
            children=[
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Initial Sampling", className="mb-3",
                                style={"fontWeight": "600"}),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Method", className="form-label small text-muted"),
                                dcc.Dropdown(
                                    id="starting-sampling-DD",
                                    options=[
                                        {"label": "None",              "value": "none"},
                                        {"label": "Random",            "value": "random"},
                                        {"label": "Latin Hypercube",   "value": "latin_hypercube"},
                                        {"label": "Sobol",             "value": "sobol"},
                                        {"label": "k-Means (constrained)", "value": "kmeans"},
                                    ],
                                    value="kmeans", clearable=False,
                                    style={"fontSize": "0.875rem"}),
                            ], md=6),
                            dbc.Col([
                                html.Label("Points", className="form-label small text-muted"),
                                dbc.Input(id="nb-sampling-points", type="number", value=10,
                                          min=1, size="sm", style={"borderRadius": "6px"}),
                            ], md=6)
                        ])
                    ], style={"padding": "1.25rem"})
                ], style={
                    "borderRadius": "12px", "border": "1px solid #e0e0e0",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.06)", "backgroundColor": "white"
                })
            ]
        ),

        # ── Continue Button ───────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Button([html.I(className="bi bi-arrow-right-circle me-2"),
                            "Continue to Experiments"],
                           id="create-domain-btn", color="primary", size="lg",
                           className="w-100", disabled=True,
                           style={
                               "backgroundColor": "#6366f1", "border": "none",
                               "borderRadius": "8px", "padding": "0.75rem",
                               "fontSize": "1rem", "fontWeight": "500",
                               "boxShadow": "0 2px 8px rgba(99, 102, 241, 0.2)"
                           })
            ], md=6, className="mx-auto")
        ]),

        # ── Solvent Modal ─────────────────────────────────────────────────
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Solvent Configuration")),
            dbc.ModalBody([
                html.Div([
                    html.H6("Choose Solvents", className="mb-0",
                            style={"fontWeight": "600", "display": "inline-block"}),
                    html.Div([
                        dbc.Button(html.I(className="bi bi-plus-lg"),
                                   id="add-solvent-row-btn", color="primary", size="sm",
                                   style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}),
                    ], className="float-end"),
                ], className="mb-3"),
                html.Div(id="solvent-rows-container", children=[]),
                html.Hr(className="my-3"),
                create_custom_solvent_form(),
                html.Hr(className="my-3"),
                html.Div([
                    html.I(className="bi bi-info-circle me-2", style={"color": "#6c757d"}),
                    html.Small("Descriptors: ε, μ, HBA, HBD, AN, DN (auto-selected)",
                               className="text-muted")
                ], className="mb-3"),
                html.Div(id="descriptor-rows-container", children=[], style={"display": "none"}),
            ]),
            dbc.ModalFooter([
                dbc.Button([html.I(className="bi bi-plus-circle me-1",
                                   style={"fontSize": "0.75rem"}), "Create Custom"],
                           id="toggle-custom-solvent-btn", color="secondary", outline=True,
                           size="sm", className="me-auto",
                           style={"borderRadius": "6px", "padding": "0.25rem 0.75rem",
                                  "fontSize": "0.85rem"}),
                dbc.Button("Save", id="save-solvents-btn", color="primary", size="sm",
                           style={"borderRadius": "6px"})
            ]),
        ], id="solvent-modal", size="lg", is_open=False),

        # ── Base Modal ────────────────────────────────────────────────────
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Base Configuration")),
            dbc.ModalBody([
                html.Div([
                    html.H6("Choose Bases", className="mb-0",
                            style={"fontWeight": "600", "display": "inline-block"}),
                    html.Div([
                        dbc.Button(html.I(className="bi bi-plus-lg"),
                                   id="add-base-row-btn", color="primary", size="sm",
                                   style={"borderRadius": "6px", "padding": "0.25rem 0.5rem"}),
                    ], className="float-end"),
                ], className="mb-3"),
                html.Div(id="base-rows-container", children=[]),
                html.Hr(className="my-3"),
                create_custom_base_form(),
                html.Hr(className="my-3"),
                html.Div([
                    html.I(className="bi bi-info-circle me-2", style={"color": "#6c757d"}),
                    html.Small("Descriptors: pKa_DMSO, MW (auto-selected)",
                               className="text-muted")
                ], className="mb-3"),
                html.Div(id="base-descriptor-rows-container", children=[],
                         style={"display": "none"}),
            ]),
            dbc.ModalFooter([
                dbc.Button([html.I(className="bi bi-plus-circle me-1",
                                   style={"fontSize": "0.75rem"}), "Create Custom"],
                           id="toggle-custom-base-btn", color="secondary", outline=True,
                           size="sm", className="me-auto",
                           style={"borderRadius": "6px", "padding": "0.25rem 0.75rem",
                                  "fontSize": "0.85rem"}),
                dbc.Button("Save", id="save-bases-btn", color="primary", size="sm",
                           style={"borderRadius": "6px"})
            ]),
        ], id="base-modal", size="lg", is_open=False),

        # ── Stores ────────────────────────────────────────────────────────
        dcc.Store(id='solvent-config-store', data=None),
        dcc.Store(id='base-config-store',    data=None),
        dcc.Store(id='tl-domain-store',      data=None),

    ], fluid=True, style={
        "maxWidth": "1400px",
        "backgroundColor": "#f8f9fa",
        "minHeight": "100vh",
        "paddingTop": "2rem",
        "paddingBottom": "4rem"
    })
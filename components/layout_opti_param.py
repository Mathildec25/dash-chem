import dash_bootstrap_components as dbc
from dash import dcc, html
import uuid

initial_id = str(uuid.uuid4())
initial_objective_id = str(uuid.uuid4())
initial_extra_col_id = str(uuid.uuid4())

def create_opti_param_layout():
    return dbc.Container([
        # Header simplifié
        dbc.Row([
            dbc.Col([
                html.H1("Configure Your Experiment", 
                       className="text-center mb-2",
                       style={"color": "#2c3e50", "fontWeight": "bold"}),
                html.P("Define what you can change and what you want to optimize",
                      className="text-center text-muted mb-4",
                      style={"fontSize": "16px"})
            ], width=12)
        ], className="mt-4"),

        # Progress indicators - simplifié
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="bi bi-sliders", style={"fontSize": "24px", "color": "#007bff"}),
                    html.Small("Parameters", className="d-block mt-1")
                ], className="text-center")
            ], md=3),
            dbc.Col([
                html.Div([
                    html.I(className="bi bi-bullseye", style={"fontSize": "24px", "color": "#28a745"}),
                    html.Small("Objectives", className="d-block mt-1")
                ], className="text-center")
            ], md=3),
            dbc.Col([
                html.Div([
                    html.I(className="bi bi-table", style={"fontSize": "24px", "color": "#6c757d"}),
                    html.Small("Extra Data", className="d-block mt-1")
                ], className="text-center")
            ], md=3),
            dbc.Col([
                html.Div([
                    html.I(className="bi bi-gear-fill", style={"fontSize": "24px", "color": "#ffc107"}),
                    html.Small("Launch", className="d-block mt-1")
                ], className="text-center")
            ], md=3),
        ], className="mb-4"),

        # Configuration Accordion - simplifié
        dbc.Card([
            dbc.CardBody([
                dbc.Accordion([
                    # 1. Parameters
                    dbc.AccordionItem([
                        html.Div(id="parameter-container", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row(
                                        id={'type': 'parameter-block', 'index': initial_id},
                                        children=[
                                            dbc.Col([
                                                dbc.Label("Name", className="fw-bold"),
                                                dbc.Input(  
                                                    id={'type': 'parameter-name', 'index': initial_id},
                                                    placeholder="e.g., Temperature",
                                                    type="text",
                                                    size="md"
                                                ),
                                            ], width=5),
                                            dbc.Col([
                                                html.Div(id={'type': 'parameter-type-container', 'index': initial_id})
                                            ], width=5),
                                            dbc.Col([
                                                dbc.Label("✕", className="fw-bold"),
                                                dbc.Button(
                                                    "✕", 
                                                    id={'type': 'delete-parameter', 'index': initial_id}, 
                                                    color="outline-danger", 
                                                    size="sm",
                                                    className="w-100"
                                                ),
                                            ], width=2)
                                        ],
                                        className="align-items-end mb-2"
                                    ),
                                    html.Div(id={'type': 'parameter-type-specific-container', 'index': initial_id}),
                                ])
                            ], className="mb-2 shadow-sm")
                        ]),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-plus me-2"),
                                    "Add"
                                ],
                                id="add-para-button",
                                color="primary",
                                className="me-2"
                                ),
                                dbc.Button([
                                    html.I(className="bi bi-check me-2"),
                                    "Save"
                                ], 
                                id="save-parameters-btn", 
                                color="success"
                                ),
                            ])
                        ], className="mb-2"),
                        
                        dbc.Card([
                            dbc.CardBody([
                                html.Div(
                                    id="parameter-display", 
                                    children=[html.P("No parameters yet", className="text-muted small")],
                                    style={"maxHeight": "200px", "overflowY": "auto"}
                                )
                            ])
                        ], className="mt-2")
                    ], 
                    title="1. Parameters",
                    item_id="item-parameters"),
                    
                    # 2. Objectives
                    dbc.AccordionItem([
                        html.Div(id="objective-container", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row(
                                        id={'type': 'objective-block', 'index': initial_objective_id},
                                        children=[
                                            dbc.Col([
                                                dbc.Label("Name", className="fw-bold"),
                                                dbc.Input(
                                                    id={'type': 'objective-name', 'index': initial_objective_id},
                                                    placeholder="e.g., Yield",
                                                    type="text",
                                                    size="md"
                                                ),
                                            ], width=3),
                                            dbc.Col([
                                                html.Div(id={'type': 'objective-direction-container', 'index': initial_objective_id})
                                            ], width=3),
                                            dbc.Col([
                                                html.Div(id={'type': 'objective-bounds-container', 'index': initial_objective_id})
                                            ], width=4),
                                            dbc.Col([
                                                dbc.Label("✕", className="fw-bold"),
                                                dbc.Button(
                                                    "✕",
                                                    id={'type': 'delete-objective-btn', 'index': initial_objective_id},
                                                    color="outline-danger",
                                                    size="sm",
                                                    className="w-100"
                                                )
                                            ], width=2),
                                        ],
                                        className="align-items-end mb-2"
                                    )
                                ])
                            ], className="mb-2 shadow-sm")
                        ]),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-plus me-2"),
                                    "Add"
                                ],
                                id="add-objective-button",
                                color="primary",
                                className="me-2"
                                ),
                                dbc.Button([
                                    html.I(className="bi bi-check me-2"),
                                    "Save"
                                ],
                                id="save-objectives-btn",
                                color="success"
                                )
                            ])
                        ], className="mb-2"),
                        
                        dbc.Card([
                            dbc.CardBody([
                                html.Div(
                                    id="objective-display",
                                    children=[html.P("No objectives yet", className="text-muted small")], 
                                    style={"maxHeight": "200px", "overflowY": "auto"}
                                )
                            ])
                        ], className="mt-2")
                    ], 
                    title="2. Objectives",
                    item_id="item-objectives"),
                    
                    # 3. Extra Columns (collapsed by default)
                    dbc.AccordionItem([
                        html.Div(id="extra-column-container", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row(
                                        id={'type': 'extra-column-block', 'index': initial_extra_col_id},
                                        children=[
                                            dbc.Col([
                                                dbc.Label("Name", className="fw-bold"),
                                                dbc.Input(
                                                    id={'type': 'extra-column-name', 'index': initial_extra_col_id},
                                                    placeholder="e.g., Batch_ID",
                                                    type="text",
                                                    size="md"
                                                ),
                                            ], width=10),
                                            dbc.Col([
                                                dbc.Label("✕", className="fw-bold"),
                                                dbc.Button(
                                                    "✕",
                                                    id={'type': 'delete-extra-column-btn', 'index': initial_extra_col_id},
                                                    color="outline-danger",
                                                    size="sm",
                                                    className="w-100"
                                                )
                                            ], width=2),
                                        ],
                                        className="align-items-end mb-2"
                                    )
                                ])
                            ], className="mb-2 shadow-sm")
                        ]),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-plus me-2"),
                                    "Add"
                                ],
                                id="add-extra-column-button",
                                color="primary",
                                className="me-2"
                                ),
                                dbc.Button([
                                    html.I(className="bi bi-check me-2"),
                                    "Save"
                                ],
                                id="save-extra-columns-btn",
                                color="success"
                                ),
                            ])
                        ], className="mb-2"),
                        
                        dbc.Card([
                            dbc.CardBody([
                                html.Div(
                                    id="extra-columns-display",
                                    children=[html.P("No extra columns", className="text-muted small")],
                                    style={"maxHeight": "150px", "overflowY": "auto"}
                                )
                            ])
                        ], className="mt-2")
                    ], 
                    title="3. Extra Data (Optional)",
                    item_id="item-extra"),
                    
                    # 4. Launch
                    dbc.AccordionItem([
                        dbc.Alert([
                            html.I(className="bi bi-info-circle me-2"),
                            "Initial sampling creates the first points to train the AI"
                        ], color="info", className="mb-3 small"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Sampling Method", className="fw-bold mb-2"),
                                dcc.Dropdown(
                                    id="starting-sampling-DD",
                                    options=[
                                        {"label": "None", "value": "none"},
                                        {"label": "Random", "value": "random"},
                                        {"label": "Latin Hypercube ⭐", "value": "latin_hypercube"},
                                        {"label": "Sobol", "value": "sobol"},
                                    ],
                                    value="latin_hypercube",
                                    className="mb-2"
                                ),
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Number of Points", className="fw-bold mb-2"),
                                dbc.Input(
                                    id="nb-sampling-points",
                                    type="number",
                                    value=10,
                                    min=1,
                                    className="mb-2"
                                ),
                                html.Small("Tip: 2× parameters", className="text-muted")
                            ], width=6)
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                dcc.Link(
                                    dbc.Button([
                                        html.I(className="bi bi-rocket-takeoff me-2"),
                                        "Create & Start"
                                    ],
                                    id="create-domain-btn",
                                    color="success",
                                    size="lg",
                                    className="w-100"
                                    ), 
                                    href="/Opt-run"
                                )
                            ], md=6, className="mx-auto")
                        ])
                    ], 
                    title="4. Launch",
                    item_id="item-launch"),
                ], 
                id="accordion", 
                active_item="item-parameters",
                className="mb-3")
            ])
        ], className="shadow"),
        
    ], fluid=True, style={"maxWidth": "1200px"})
import dash_bootstrap_components as dbc
from dash import dcc, html
import uuid

# For the solvent part
solvents = [
    'Acetonitrile', 'Methanol', 'Butanol', 'THF', 'DMSO', 'Water', 'Ethanol', 'Cyclohexane', 'Toluene', 'Isopropyl alcohol',
    'Acetone', 'Hexane', 'Dichloromethane', 'DMF', 'Benzene', 'Chloroform', 'Heptane', 'Acetic acid', 'Diethyl ether', 'Chlorobenzene'
]

# ID to match in AccordionItems
initial_id = str(uuid.uuid4()) # For the parameters part
initial_objective_id = str(uuid.uuid4()) # For the objectives part
initial_extra_col_id = str(uuid.uuid4()) # For the extra columns part

def chunk_list(lst, chunk_size):
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

chunks = chunk_list(solvents, 5)

def create_opti_param_layout():
    return dbc.Container([
        # Header Section
        dbc.Row([
            dbc.Col([
                html.H1("Domain Configuration", 
                       className="text-center mb-2",
                       style={"color": "#2c3e50", "fontWeight": "bold"}),
                html.P("Define your experimental space for Bayesian Optimization",
                      className="text-center text-muted mb-4",
                      style={"fontSize": "18px"})
            ], width=12)
        ], className="mt-4"),
        
        # Process Overview Alert
        dbc.Alert([
            html.I(className="bi bi-lightbulb-fill me-2"),
            html.Strong("Domain Setup Process: "),
            "Parameters (what you can control) → Objectives (what you want to optimize) → "
            "Additional Data → Sampling Strategy → Domain Creation"
        ], color="info", className="mb-4"),

        # Main Configuration Accordion
        dbc.Card([
            dbc.CardBody([
                dbc.Accordion([
                    # Parameters Section
                    dbc.AccordionItem([
                        # Header explanation
                        dbc.Alert([
                            html.I(className="bi bi-lightbulb-fill me-2"),
                            html.Strong("Parameters "),
                            "are the experimental variables you can control (temperature, concentration, time, etc.). "
                            "Define their types and valid ranges."
                        ], color="info", className="mb-4"),
                        
                        # Parameter container
                        html.Div(id="parameter-container", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row(
                                        id={'type': 'parameter-block', 'index': initial_id},
                                        children=[
                                            dbc.Col([
                                                dbc.Label("Parameter Name", className="fw-bold"),
                                                dbc.Input(  
                                                    id={'type': 'parameter-name', 'index': initial_id},
                                                    placeholder="e.g., Temperature, Concentration...",
                                                    type="text",
                                                    size="md",
                                                    style={"fontSize": "16px"}
                                                ),
                                            ], width=5),
                                            dbc.Col([
                                                dbc.Label("Parameter Type", className="fw-bold"),
                                                html.Div(id={'type': 'parameter-type-container', 'index': initial_id})
                                            ], width=5),
                                            dbc.Col([
                                                dbc.Label("Delete", className="fw-bold"),
                                                dbc.Button(
                                                    "✕", 
                                                    id={'type': 'delete-parameter', 'index': initial_id}, 
                                                    color="outline-danger", 
                                                    size="sm",
                                                    className="w-100"
                                                ),
                                            ], width=2)
                                        ],
                                        className="align-items-end mb-3"
                                    ),
                                    # Type-specific configuration area
                                    html.Div(id={'type': 'parameter-type-specific-container', 'index': initial_id}),
                                ])
                            ], className="mb-3 shadow-sm")
                        ]),
                        
                        # Action buttons
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-plus-circle me-2"),
                                    "Add Parameter"
                                ],
                                id="add-para-button",
                                color="primary",
                                size="lg",
                                className="me-3"
                                ),
                                dbc.Button([
                                    html.I(className="bi bi-floppy me-2"),
                                    "Save Parameters"
                                ], 
                                id="save-parameters-btn", 
                                color="success", 
                                size="lg"
                                ),
                            ], className="text-center")
                        ], className="mb-3"),
                        
                        # Parameter display
                        dbc.Card([
                            dbc.CardHeader([
                                html.H6([
                                    html.I(className="bi bi-list-check me-2"),
                                    "Current Parameters"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                html.Div(
                                    id="parameter-display", 
                                    children=[html.P("No parameters defined yet", className="text-muted")],
                                    style={"fontSize": "14px", "maxHeight": "300px", "overflowY": "auto"}
                                )
                            ])
                        ], className="mt-3")
                    ], 
                    title=[
                        html.I(className="bi bi-sliders me-2"),
                        "Step 1: Define Parameters"
                    ],
                    item_id="item-parameters"),
                    
                    # Objectives Section
                    dbc.AccordionItem([
                        # Header explanation
                        dbc.Alert([
                            html.I(className="bi bi-lightbulb-fill me-2"),
                            html.Strong("Objectives "),
                            "are the goals you want to optimize (yield, purity, cost, etc.). "
                            "Specify whether to minimize or maximize each one."
                        ], color="info", className="mb-4"),
                        
                        html.Div(id="objective-container", children=[
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row(
                                        id={'type': 'objective-block', 'index': initial_objective_id},
                                        children=[
                                            dbc.Col([
                                                dbc.Label("Objective Name", className="fw-bold"),
                                                dbc.Input(
                                                    id={'type': 'objective-name', 'index': initial_objective_id},
                                                    placeholder="e.g., Yield, Purity, Cost...",
                                                    type="text",
                                                    size="md",
                                                    style={"fontSize": "16px"}
                                                ),
                                            ], width=3),
                                            dbc.Col([
                                                dbc.Label("Optimization Direction", className="fw-bold"),
                                                html.Div(id={'type': 'objective-direction-container', 'index': initial_objective_id})
                                            ], width=3),
                                            dbc.Col([
                                                dbc.Label("Bounds", className="fw-bold"),
                                                html.Div(id={'type': 'objective-bounds-container', 'index': initial_objective_id})
                                            ], width=4),
                                            dbc.Col([
                                                dbc.Label("Delete", className="fw-bold"),
                                                dbc.Button(
                                                    "✕",
                                                    id={'type': 'delete-objective-btn', 'index': initial_objective_id},
                                                    color="outline-danger",
                                                    size="sm",
                                                    className="w-100"
                                                )
                                            ], width=2),
                                        ],
                                        className="align-items-end mb-3"
                                    )
                                ])
                            ], className="mb-3 shadow-sm")
                        ]),
                        
                        # Action buttons
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="bi bi-plus-circle me-2"),
                                    "Add Objective"
                                ],
                                id="add-objective-button",
                                color="primary",
                                size="lg",
                                className="me-3"
                                ),
                                dbc.Button([
                                    html.I(className="bi bi-floppy me-2"),
                                    "Save Objectives"
                                ],
                                id="save-objectives-btn",
                                color="success",
                                size="lg"
                                )
                            ], className="text-center")
                        ], className="mb-3"),
                        
                        # Objectives display
                        dbc.Card([
                            dbc.CardHeader([
                                html.H6([
                                    html.I(className="bi bi-bullseye me-2"),
                                    "Current Objectives"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                html.Div(
                                    id="objective-display",
                                    children=[html.P("No objectives defined yet", className="text-muted")], 
                                    style={"fontSize": "14px", "maxHeight": "300px", "overflowY": "auto"}
                                )
                            ])
                        ], className="mt-3")
                    ], 
                    title=[
                        html.I(className="bi bi-bullseye me-2"),
                        "Step 2: Define Objectives"
                    ],
                    item_id="item-objectives"),
                    
                    # Extra Columns Section
                    dbc.AccordionItem([
                        # Header explanation
                        dbc.Alert([
                            html.I(className="bi bi-lightbulb-fill me-2"),
                            html.Strong("Additional Columns "),
                            "are for tracking extra information not used in optimization "
                            "(batch ID, notes, operator, etc.). These help with data organization."
                        ], color="info", className="mb-4"),
                        
                        dbc.Row([
                            dbc.Col([
                                html.Div(id="extra-column-container", children=[
                                    dbc.Card([
                                        dbc.CardBody([
                                            dbc.Row(
                                                id={'type': 'extra-column-block', 'index': initial_extra_col_id},
                                                children=[
                                                    dbc.Col([
                                                        dbc.Label("Column Name", className="fw-bold"),
                                                        dbc.Input(
                                                            id={'type': 'extra-column-name', 'index': initial_extra_col_id},
                                                            placeholder="e.g., Batch_ID, Operator, Notes...",
                                                            type="text",
                                                            size="md",
                                                            style={"fontSize": "16px"}
                                                        ),
                                                    ], width=10),
                                                    dbc.Col([
                                                        dbc.Label("Delete", className="fw-bold"),
                                                        dbc.Button(
                                                            "✕",
                                                            id={'type': 'delete-extra-column-btn', 'index': initial_extra_col_id},
                                                            color="outline-danger",
                                                            size="sm",
                                                            className="w-100"
                                                        )
                                                    ], width=2),
                                                ],
                                                className="align-items-end mb-3"
                                            )
                                        ])
                                    ], className="mb-3 shadow-sm")
                                ]),
                                
                                # Action buttons
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button([
                                            html.I(className="bi bi-plus-circle me-2"),
                                            "Add Column"
                                        ],
                                        id="add-extra-column-button",
                                        color="primary",
                                        size="lg",
                                        className="me-3"
                                        ),
                                        dbc.Button([
                                            html.I(className="bi bi-floppy me-2"),
                                            "Save Columns"
                                        ],
                                        id="save-extra-columns-btn",
                                        color="success",
                                        size="lg"
                                        ),
                                    ], className="text-center")
                                ], className="mb-3"),
                                
                                # Extra columns display
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.H6([
                                            html.I(className="bi bi-table me-2"),
                                            "Additional Columns"
                                        ], className="mb-0")
                                    ]),
                                    dbc.CardBody([
                                        html.Div(
                                            id="extra-columns-display",
                                            children=[html.P("No additional columns defined", className="text-muted")],
                                            style={"fontSize": "14px", "maxHeight": "200px", "overflowY": "auto"}
                                        )
                                    ])
                                ], className="mt-3")
                            ], width=12)
                        ])
                    ], 
                    title=[
                        html.I(className="bi bi-table me-2"),
                        "Step 3: Additional Columns (Optional)"
                    ],
                    item_id="item-extra"),
                    
                    # Sampling and Launch Section
                    dbc.AccordionItem([
                        # Header explanation
                        dbc.Alert([
                            html.I(className="bi bi-lightbulb-fill me-2"),
                            html.Strong("Initial Sampling "),
                            "generates the first experimental points to train the AI model. "
                            "More points = better initial model, fewer points = faster start."
                        ], color="info", className="mb-4"),
                        
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="bi bi-gear me-2"),
                                    "Sampling Configuration"
                                ], className="mb-0 text-primary")
                            ]),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Sampling Strategy", className="fw-bold mb-2"),
                                        dcc.Dropdown(
                                            id="starting-sampling-DD",
                                            options=[
                                                {"label": "None (Manual Start)", "value": "none"},
                                                {"label": "Random Sampling", "value": "random"},
                                                {"label": "Latin Hypercube (Recommended)", "value": "latin_hypercube"},
                                                {"label": "Sobol Sequence", "value": "sobol"},
                                            ],
                                            placeholder="Select sampling method...",
                                            value="latin_hypercube",  # Default to recommended
                                            style={"fontSize": "16px"},
                                            className="mb-2"
                                        ),
                                    ], width=6),
                                    dbc.Col([
                                        dbc.Label("Number of Initial Points", className="fw-bold mb-2"),
                                        dbc.Input(
                                            id="nb-sampling-points",
                                            type="number",
                                            placeholder="e.g., 10, 20, 50...",
                                            value=10,  # Default value
                                            min=1,
                                            style={"fontSize": "16px"},
                                            className="mb-2"
                                        ),
                                        html.Small([
                                            html.I(className="bi bi-calculator text-info me-1"),
                                            "Recommendation: 2 × number of parameters"
                                        ], className="text-muted")
                                    ], width=6)
                                ], className="mb-4"),
                                
                                # Summary section
                                dbc.Alert([
                                    html.H6("Ready to Create Domain?", className="alert-heading"),
                                    html.P("Make sure you have defined:", className="mb-2"),
                                    html.Ul([
                                        html.Li("At least one parameter with valid bounds"),
                                        html.Li("At least one objective with direction"),
                                        html.Li("Sampling strategy (if desired) with a number of points")
                                    ], className="mb-3"),
                                ], color="light", className="border border-primary"),
                                
                                # Launch button
                                dbc.Row([
                                    dbc.Col([
                                        dcc.Link(
                                            dbc.Button([
                                                html.I(className="bi bi-rocket-takeoff me-2"),
                                                "Create Domain & Start Optimization"
                                            ],
                                            id="create-domain-btn",
                                            color="success",
                                            size="lg",
                                            className="w-100",
                                            style={"fontSize": "18px", "padding": "12px"}
                                            ), 
                                            href="/Opt-run"
                                        )
                                    ], md=6, className="mx-auto")
                                ], className="mt-4")
                            ])
                        ], className="shadow-sm")
                    ], 
                    title=[
                        html.I(className="bi bi-gear-fill me-2"),
                        "Step 4: Configure & Launch"
                    ],
                    item_id="item-launch"),
                ], 
                id="accordion", 
                active_item="item-parameters",
                className="mb-4")
            ])
        ], className="shadow"),
        
        # Help Section
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H6([
                        html.I(className="bi bi-question-circle me-2"),
                        "Domain Configuration Guide"
                    ], className="alert-heading"),
                    html.Hr(),
                    html.P([
                        html.Strong("Parameter Types: "),
                        "• Continuous (decimals) • Discrete (specific numbers) • Categorical (text options)"
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Objectives: "),
                        "• Minimize • Maximize • Bounds help the AI"
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Sampling: "),
                        "• Latin Hypercube: Best space coverage • Random: Simple but less efficient • "
                        "Sobol: Quasi-random, good for many parameters"
                    ], className="mb-0"),
                ], color="light", className="border")
            ], width=12)
        ], className="mt-4")
    ], fluid=True, style={"maxWidth": "1400px"})

#===============================================
# OTHER PARTS REMOVED BUT COULD BE ADDED LATER
#===============================================

 # First part to selct Batch/Flow
                            # dbc.AccordionItem(
                            #     children=[
                            #         dcc.RadioItems(
                            #             options=[
                            #                 {'label': 'Batch', 'value': 'Batch'},
                            #                 {'label': 'Flow', 'value': 'Flow'},
                            #                 {'label': "Don't know", 'value': "Don't know"},
                            #             ],
                            #             inline=True,
                            #             labelStyle={'marginLeft': '200px', 'fontSize': '20px', 'display': 'inline-block'},
                            #             inputStyle={'marginRight': '5px'},
                            #         )
                            #     ],
                            #     title="Batch/Flow", 
                            #     item_id="item-1",
                            # ),
                            # # Second part to select Solvent
                            # dbc.AccordionItem(
                            #     children=[
                            #         dbc.Row([
                            #             dbc.Col([
                            #                 dcc.Checklist(
                            #                     options=[{'label': item, 'value': item} for item in chunk],
                            #                     labelStyle={'fontSize': '18px', 'display': 'block'},
                            #                     inputStyle={'marginRight': '5px'},
                            #                     id=f'checklist-col-{i}'
                            #                 )
                            #             ], width='auto', style={"marginLeft":"20px"}) for i, chunk in enumerate(chunks)
                            #         ], justify='center'),
                            #     ],
                            #     title="Solvent",
                            #     item_id="item-2",
                            # ),
                            # # Third part to draw Reactants and gather their SMILES
                            # dbc.AccordionItem(
                            #     children=[
                            #         dbc.Row([
                            #             html.Iframe(
                            #                 id='ketcher-frame',
                            #                 src="/ketcher/index.html",
                            #                 style={'width': '100%', 'height': '400px', 'border': '1px solid #ccc'},
                            #             )
                            #         ]),
                            #         dbc.Row([
                            #             dbc.Col([
                            #                 html.Div([
                            #                     dbc.Button(
                            #                         " Collect SMILES",
                            #                         id="collect-smiles-btn",
                            #                         color="primary",
                            #                         style={"fontSize": "18px", "marginTop": "12px"},
                            #                         n_clicks=0
                            #                     )
                            #                 ]),
                            #                 dcc.Store(id="smiles-store", data=[], storage_type='session'),
                            #                 html.Div(id="smiles-output", style={"marginTop": "12px"}),
                            #             ])
                            #         ])
                            #     ],
                            #     title="Reactants",
                            #     item_id="item-3",
                            # ),

# # Seventh part to select specifications about BO algorithm
                            # dbc.AccordionItem(
                            #     children=[
                            #         # html.Hr(),
                            #         # dbc.Row([
                            #         #     dbc.Col([
                            #         #             html.H6("Scalarization techniques", style={"textAlign": "center", "fontSize": "20px"}),
                            #         #             dcc.Dropdown(
                            #         #                 id="scalarization-technique-DD",
                            #         #                 options=[
                            #         #                     {"label": "None", "value": "none"},
                            #         #                     {"label": "Tchebychev", "value": "TCH"},
                            #         #                     {"label": "Lexicographical/Chimera", "value": "chimera"},
                            #         #                     {"label": "Weighted sum", "value": "weighted_sum"},
                            #         #                 ],
                            #         #                 style={"marginBottom": "10px", "marginTop": "10px"},
                            #         #             ),
                            #         #     ], width=12)
                            #         # ]),
                            #         html.Hr(),
                            #         dbc.Row([
                            #             dbc.Col([
                            #                     html.H6("Surrogate models", style={"textAlign": "center", "fontSize": "20px"}),
                            #                     dcc.Dropdown(
                            #                         id="surrogate-model-DD",
                            #                         options=[
                            #                             {"label": "BoTorch/Gaussian Process (GP)", "value": "botorch"},
                            #                             {"label": "Gryffin/Bayesian Neural Network (BNN)", "value": "gryffin"},
                            #                             {"label": "Smac/Random Forest (RF)", "value": "smac"},
                            #                             {"label": "Grid search", "value": "grid"},
                            #                             {"label": "Random sampling", "value": "random"},
                            #                         ],
                            #                         style={"marginBottom": "10px", "marginTop": "10px"},
                            #                     ),
                            #             ], width=12)
                            #         ]),
                            #         html.Hr(),
                            #         dbc.Row([
                            #             dbc.Col([
                            #                     html.H6("Acquisition functions", style={"textAlign": "center", "fontSize": "20px"}),
                            #                     dcc.Dropdown(
                            #                         id="acquisition-function-DD",
                            #                         options=[
                            #                             {"label": "Expected Improvement (EI)", "value": "EI"},
                            #                             {"label": "Expected HyperVolume Improvement (EHVI)", "value": "EHVI"},
                            #                             {"label": "Genetic", "value": "genetic"},
                            #                             {"label": "qNEHVI", "value": "qNEHVI"},
                            #                             {"label": "Probability of Improvement (PI)", "value": "PI"},
                            #                         ],
                            #                         style={"marginBottom": "10px", "marginTop": "10px"},
                            #                     ),
                            #             ], width=12)
                            #         ]),
                            #         # html.Hr(),
                            #         # dbc.Row([
                            #         #     dbc.Col([
                            #         #             html.H6("Ending conditions", style={"textAlign": "center", "fontSize": "20px"}),
                            #         #             dcc.Dropdown(
                            #         #                 id="ending-condition-DD",
                            #         #                 options=[
                            #         #                     {"label": "None", "value": "none"},
                            #         #                     {"label": "Iterations", "value": "iterations"},
                            #         #                     {"label": "No more improvement", "value": "no_improvement"},
                            #         #                     {"label": "Goal", "value": "goal"},
                            #         #                 ],
                            #         #                 style={"marginBottom": "10px", "marginTop": "10px"},
                            #         #             ),
                            #         #     ], width=12)
                            #         # ])
                            #     ],
                            #     title="Algorithm Specifications",
                            #     item_id="item-7",
                            # ),
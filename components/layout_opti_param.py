import dash_bootstrap_components as dbc
from dash import dcc, html
import uuid


# For the solvent part
solvents = [
    'Acetonitrile', 'Methanol', 'Butanol', 'THF', 'DMSO', 'Water', 'Ethanol', 'Cyclohexane', 'Toluene', 'Isopropyl alcohol',
    'Acetone', 'Hexane', 'Dichloromethane', 'DMF', 'Benzene', 'Chloroform', 'Heptane', 'Acetic acid', 'Diethyl ether', 'Chlorobenzene'
]

# ID to match in AccodionItems
initial_id = str(uuid.uuid4()) # For the parameters part
initial_objective_id = str(uuid.uuid4()) # For the objectives part
initial_extra_col_id = str(uuid.uuid4()) # For the extra columns part

def chunk_list(lst, chunk_size):
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

chunks = chunk_list(solvents, 5)

# This function creates the layout for the dashboard page 
def create_opti_param_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Location(id="url"),
                html.H2("Optimization Parameterization part", className="display-4", style={"textAlign": "center","marginTop":"5px", "marginBottom": "20px"}),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Accordion([
                            # First part to selct Batch/Flow
                            dbc.AccordionItem(
                                children=[
                                    dcc.RadioItems(
                                        options=[
                                            {'label': 'Batch', 'value': 'Batch'},
                                            {'label': 'Flow', 'value': 'Flow'},
                                            {'label': "Don't know", 'value': "Don't know"},
                                        ],
                                        inline=True,
                                        labelStyle={'marginLeft': '200px', 'fontSize': '20px', 'display': 'inline-block'},
                                        inputStyle={'marginRight': '5px'},
                                    )
                                ],
                                title="Batch/Flow", 
                                item_id="item-1",
                            ),
                            # Second part to select Solvent
                            dbc.AccordionItem(
                                children=[
                                    dbc.Row([
                                        dbc.Col([
                                            dcc.Checklist(
                                                options=[{'label': item, 'value': item} for item in chunk],
                                                labelStyle={'fontSize': '18px', 'display': 'block'},
                                                inputStyle={'marginRight': '5px'},
                                                id=f'checklist-col-{i}'
                                            )
                                        ], width='auto', style={"marginLeft":"20px"}) for i, chunk in enumerate(chunks)
                                    ], justify='center'),
                                ],
                                title="Solvent",
                                item_id="item-2",
                            ),
                            # Third part to draw Reactants and gather their SMILES
                            dbc.AccordionItem(
                                children=[
                                    dbc.Row([
                                        html.Iframe(
                                            id='ketcher-frame',
                                            src="/ketcher/index.html",
                                            style={'width': '100%', 'height': '400px', 'border': '1px solid #ccc'},
                                        )
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.Div([
                                                dbc.Button(
                                                    " Collect SMILES",
                                                    id="collect-smiles-btn",
                                                    color="primary",
                                                    style={"fontSize": "18px", "marginTop": "12px"},
                                                    n_clicks=0
                                                )
                                            ]),
                                            dcc.Store(id="smiles-store", data=[], storage_type='session'),
                                            html.Div(id="smiles-output", style={"marginTop": "12px"}),
                                        ])
                                    ])
                                ],
                                title="Reactants",
                                item_id="item-3",
                            ),
                            # Fourth part to select Parameters/Variables
                            dbc.AccordionItem(
                                children=[
                                    dcc.Store(id='parameter-store', data=[]),
                                    html.Div(id="parameter-container", children=[
                                        dbc.Row(
                                            id={'type': 'parameter-block', 'index': initial_id},
                                            children=[
                                                dbc.Col([
                                                    dbc.Label("Name of the parameter"),
                                                    dbc.Input(
                                                        id={'type': 'parameter-name', 'index': initial_id},
                                                        placeholder="Type here...",
                                                        type="text",
                                                        size="sm",
                                                        style={"fontSize": "18px"}
                                                    ),
                                                ], width=5),
                                                dbc.Col([
                                                    html.Div(id={'type': 'parameter-type-container', 'index': initial_id})
                                                ], width=5),
                                                dbc.Col([
                                                    dbc.Button(
                                                        "✕", 
                                                        id={'type': 'delete-parameter', 'index': initial_id}, 
                                                        color="danger", 
                                                        size="sm"
                                                    ),
                                                ], width=2)
                                            ],
                                            style={"marginBottom": "10px"}
                                        ),
                                        # Add a row below with the placeholder for type-specific component:
                                        html.Div(id={'type': 'parameter-type-specific-container', 'index': initial_id}),
                                    ]),
                                    html.Div(
                                        children=[
                                            dbc.Row([
                                                dbc.Col([
                                                    dbc.Button(
                                                        " Add a parameter",
                                                        id="add-para-button",
                                                        color="primary",
                                                        className="bi bi-plus-square",
                                                        style={"marginTop": "12px"}
                                                    ),
                                                    dbc.Button(
                                                        " Save Parameters", 
                                                        id="save-parameters-btn", 
                                                        color="success", 
                                                        className="bi bi-floppy",
                                                        style={"marginTop": "12px", "marginLeft": "10px"}
                                                    ),
                                                ])
                                            ]),
                                        ]
                                    ), 
                                    html.Div(
                                        id="parameter-display", 
                                        style={"marginTop": "15px", "fontSize": "16px"}
                                    ),
                                ],
                                title="Parameters",
                                item_id="item-4",
                            ),
                            # Fifth part to select Objctives
                            dbc.AccordionItem(
                                children=[
                                    dcc.Store(id='objective-store', data=[]),
                                    html.Div(id="objective-container", 
                                        children=[
                                            dbc.Row(
                                                id={'type': 'objective-block', 'index': initial_objective_id},
                                                children=[
                                                    dbc.Col([
                                                        dbc.Label("Name of the objective"),
                                                        dbc.Input(
                                                            id={'type': 'objective-name', 'index': initial_objective_id},
                                                            placeholder="Type here...",
                                                            type="text",
                                                            size="sm",
                                                            style={"fontSize": "18px"}
                                                        ),
                                                    ], width=5),
                                                    dbc.Col([
                                                        html.Div(id={'type': 'objective-direction-container', 'index': initial_objective_id})
                                                    ], width=5),
                                                    dbc.Col([
                                                        dbc.Button(
                                                            "✕",
                                                            id={'type': 'delete-objective-btn', 'index': initial_objective_id},
                                                            color="danger",
                                                            size="sm",
                                                        )
                                                    ], width=2),
                                                ],
                                                style={"marginBottom": "10px"}
                                            )
                                        ],
                                    ),
                                    html.Div(
                                        children=[
                                            dbc.Row([
                                                dbc.Col([
                                                    dbc.Button(
                                                        " Add an objective",
                                                        id="add-objective-button",
                                                        color="primary",
                                                        className="bi bi-plus-square",
                                                        style={"marginTop": "12px"}
                                                    ),
                                                    dbc.Button(
                                                        " Save Objectives",
                                                        id="save-objectives-btn",
                                                        color="success",
                                                        className="bi bi-floppy",
                                                        style={"marginTop": "12px", "marginLeft": "10px"}
                                                    )
                                                ])
                                            ]),
                                        ]
                                    ),
                                    html.Div(id="objective-display", style={"marginTop": "15px", "fontSize": "16px"}), 
                                ],
                                title="Objectives",
                                item_id="item-5",
                            ),
                           # Sixth part to choose Excel name + Other columns
                            dbc.AccordionItem(
                                children=[
                                    dcc.Store(id="extra-columns-store", data=[]),
                                    dcc.Store(id="excel-name-store", data=""),
                                    dbc.Row([
                                        # LEFT SIDE: Extra column names
                                        dbc.Col([
                                            html.Div(id="extra-column-container", children=[
                                                dbc.Row(
                                                    id={'type': 'extra-column-block', 'index': initial_extra_col_id},
                                                    children=[
                                                        dbc.Col([
                                                            dbc.Label("Column name"),
                                                            dbc.Input(
                                                                id={'type': 'extra-column-name', 'index': initial_extra_col_id},
                                                                placeholder="Enter column name...",
                                                                type="text",
                                                                size="sm",
                                                                style={"fontSize": "16px"}
                                                            ),
                                                        ], width=10),
                                                        dbc.Col([
                                                            dbc.Button(
                                                                "✕",
                                                                id={'type': 'delete-extra-column-btn', 'index': initial_extra_col_id},
                                                                color="danger",
                                                                size="sm",
                                                            )
                                                        ], width=2),
                                                    ],
                                                    style={"marginBottom": "10px"}
                                                )
                                            ]),
                                            html.Div(
                                                children=[
                                                    dbc.Row([
                                                        dbc.Col([
                                                            dbc.Button(
                                                                " Add a column",
                                                                id="add-extra-column-button",
                                                                color="primary",
                                                                className="bi bi-plus-square",
                                                                style={"marginTop": "12px"}
                                                            ),
                                                            dbc.Button(
                                                                " Save Columns",
                                                                id="save-extra-columns-btn",
                                                                color="success",
                                                                className="bi bi-floppy",
                                                                style={"marginTop": "12px", "marginLeft": "8px"}
                                                            ),
                                                        ])
                                                    ]),
                                                ]
                                            ),
                                            html.Div(id="extra-columns-display", style={"marginTop": "15px", "fontSize": "14px"})
                                        ], width=6, style={"borderRight": "1px solid #ddd"}),

                                        # RIGHT SIDE: Excel name input
                                        dbc.Col([
                                            html.H6("Excel File Name"),
                                            dbc.Input(
                                                id="excel-name-input",
                                                placeholder="e.g. my_parameters.xlsx",
                                                type="text",
                                                style={"marginBottom": "8px"}
                                            ),
                                            dbc.Button(
                                                " Save Excel Name",
                                                id="save-excel-name-btn",
                                                color="success",
                                                className="bi bi-floppy",
                                                style={"marginTop": "12px"}
                                            ),
                                            html.Div(
                                                id="create-excel-btn-container",
                                                children=[
                                                    dbc.Button(
                                                    " Create the Excel",
                                                    id="create-excel-btn",
                                                    color="primary",
                                                    className="bi bi-file-earmark-plus",
                                                    style={"marginTop": "12px"}
                                                    ),
                                                ], 
                                                style={"display": "none"}
                                            ),    
                                            html.Div(id="excel-confirmation", style={"marginTop": "10px", "fontSize": "14px"}),
                                            html.Div(id="excel-create-message", style={"marginTop": "10px", "fontSize": "14px"}),
                                        ], width=6),
                                    ])
                                ],
                                title="Other Columns & Excel Name",
                                item_id="item-6",
                            ),
                            # Seventh part to select specifications about BO algorithm
                            dbc.AccordionItem(
                                children=[
                                    dbc.Row([
                                        dbc.Col([
                                                html.H6("Starting sampling options", style={"textAlign": "center", "fontSize": "20px"}),
                                                dcc.Dropdown(
                                                    id="starting-sampling-DD",
                                                    options=[
                                                        {"label": "None", "value": "none"},
                                                        {"label": "Random", "value": "random"},
                                                        {"label": "Latin Hypercube", "value": "latin_hypercube"},
                                                        {"label": "Sobol", "value": "sobol"},
                                                    ],
                                                    style={"marginBottom": "10px", "marginTop": "10px"},
                                                ),
                                        ], width=12)
                                    ]),
                                    html.Hr(),
                                    dbc.Row([
                                        dbc.Col([
                                                html.H6("Scalarization techniques", style={"textAlign": "center", "fontSize": "20px"}),
                                                dcc.Dropdown(
                                                    id="scalarization-technique-DD",
                                                    options=[
                                                        {"label": "None", "value": "none"},
                                                        {"label": "Tchebychev", "value": "TCH"},
                                                        {"label": "Lexicographical/Chimera", "value": "chimera"},
                                                        {"label": "Weighted sum", "value": "weighted_sum"},
                                                    ],
                                                    style={"marginBottom": "10px", "marginTop": "10px"},
                                                ),
                                        ], width=12)
                                    ]),
                                    html.Hr(),
                                    dbc.Row([
                                        dbc.Col([
                                                html.H6("Surrogate models", style={"textAlign": "center", "fontSize": "20px"}),
                                                dcc.Dropdown(
                                                    id="surrogate-model-DD",
                                                    options=[
                                                        {"label": "BoTorch/Gaussian Process (GP)", "value": "botorch"},
                                                        {"label": "Gryffin/Bayesian Neural Network (BNN)", "value": "gryffin"},
                                                        {"label": "Smac/Random Forest (RF)", "value": "smac"},
                                                        {"label": "Grid search", "value": "grid"},
                                                        {"label": "Random sampling", "value": "random"},
                                                    ],
                                                    style={"marginBottom": "10px", "marginTop": "10px"},
                                                ),
                                        ], width=12)
                                    ]),
                                    html.Hr(),
                                    dbc.Row([
                                        dbc.Col([
                                                html.H6("Acquisition functions", style={"textAlign": "center", "fontSize": "20px"}),
                                                dcc.Dropdown(
                                                    id="acquisition-function-DD",
                                                    options=[
                                                        {"label": "Expected Improvement (EI)", "value": "EI"},
                                                        {"label": "Expected HyperVolume Improvement (EHVI)", "value": "EHVI"},
                                                        {"label": "Genetic", "value": "genetic"},
                                                        {"label": "qNEHVI", "value": "qNEHVI"},
                                                        {"label": "Probability of Improvement (PI)", "value": "PI"},
                                                    ],
                                                    style={"marginBottom": "10px", "marginTop": "10px"},
                                                ),
                                        ], width=12)
                                    ]),
                                    html.Hr(),
                                    dbc.Row([
                                        dbc.Col([
                                                html.H6("Ending conditions", style={"textAlign": "center", "fontSize": "20px"}),
                                                dcc.Dropdown(
                                                    id="ending-condition-DD",
                                                    options=[
                                                        {"label": "None", "value": "none"},
                                                        {"label": "Iterations", "value": "iterations"},
                                                        {"label": "No more improvement", "value": "no_improvement"},
                                                        {"label": "Goal", "value": "goal"},
                                                    ],
                                                    style={"marginBottom": "10px", "marginTop": "10px"},
                                                ),
                                        ], width=12)
                                    ])
                                ],
                                title="Algorithm Specifications",
                                item_id="item-7",
                            ),
                            # Eighth part to launch the optimization
                            dbc.AccordionItem(
                                children=[
                                    dbc.Row([
                                        dbc.Col([
                                            html.H6("Are you ready?", style={"textAlign": "center", "fontSize": "20px"}),
                                            html.Div([
                                                dbc.Button(
                                                    " Give next conditions",
                                                    id="run-BO-btn",
                                                    color="primary",
                                                    className="bi bi-rocket-takeoff",
                                                    style={"marginTop": "12px", "fontSize": "30px"}
                                                    ),
                                            ],
                                            style={"textAlign": "center"}
                                            ),
                                        ]),
                                    ]),
                                ],
                                title="Run the optimization",
                                item_id="item-8",
                            ),
                            # Ninth part to display the results
                            dbc.AccordionItem(
                                children=[
                                    dbc.Row([
                                        dbc.Col([
                                            html.H6("Graph to be added", style={"textAlign": "center", "fontSize": "20px"}),
                                        ]),
                                    ]),
                                ],
                                title="Visualizations",
                                item_id="item-9",
                            ),    
                    ], id="accordion", active_item="item-1"),
                ]),
            ], width=12),        
        ]),
    ])

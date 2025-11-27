import dash_bootstrap_components as dbc
from dash import dcc, html

# This function creates the layout for the dashboard page 
def create_dashboard_layout():
    return dbc.Container([
        # Header Section - Compact
        dbc.Row([
            dbc.Col([
                html.H2("Dashboard", 
                       className="mb-2",
                       style={"color": "#2c3e50", "fontWeight": "bold"}),
                html.P("Edit directly in the table • Right-click column headers to rename",
                      className="text-muted mb-3",
                      style={"fontSize": "14px"})
            ], width=12)
        ], className="mt-3"),
        
        # Toolbar - Une seule ligne compacte
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="bi bi-plus-square me-1"),
                        "Add Row"
                    ], 
                    id="editing-rows-button", 
                    color="success",
                    size="sm",
                    n_clicks=0
                    ),
                    dbc.Button([
                        html.I(className="bi bi-plus-circle me-1"),
                        "Add Column"
                    ],
                    id="quick-add-column-btn",
                    color="info",
                    size="sm"
                    ),
                    dbc.Button([
                        html.I(className="bi bi-save me-1"),
                        "Save"
                    ], 
                    id="save-button", 
                    color="primary",
                    size="sm",
                    n_clicks=0
                    ),
                ], size="sm")
            ], width="auto"),
            
            dbc.Col([
                html.Div(id="save-status-inline", className="text-muted small")
            ], width="auto", className="d-flex align-items-center"),
            
            dbc.Col([
                dcc.Dropdown(
                    id="column-dropdown",
                    options=[],
                    value=[],
                    multi=True,
                    placeholder="🔍 Hide/Show columns...",
                    style={"minWidth": "250px", "fontSize": "14px"},
                    className="dash-bootstrap"
                ),
            ], className="ms-auto"),
        ], className="mb-3 align-items-center"),
        
        # Table Section - Plein écran
        dbc.Card([
            dbc.CardBody([
                dcc.Loading(
                    id="loading-table",
                    type="circle",
                    children=[
                        html.Div(id="main-content-dashboard")
                    ]
                )
            ], className="p-1")
        ], className="shadow-sm"),
        
        # Modal pour ajouter une colonne
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Add New Column")),
            dbc.ModalBody([
                dbc.Label("Column Name", className="fw-bold"),
                dbc.Input(
                    id="new-column-name-modal",
                    placeholder="e.g., Temperature, pH, Yield...",
                    type="text",
                    autoFocus=True
                ),
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="cancel-add-column", color="secondary", size="sm"),
                dbc.Button("Add Column", id="confirm-add-column", color="success", size="sm"),
            ])
        ], id="add-column-modal", is_open=False),
        
        # Modal pour renommer une colonne
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Rename Column")),
            dbc.ModalBody([
                dbc.Label("Current Name", className="fw-bold"),
                dbc.Input(
                    id="current-column-name-display",
                    type="text",
                    disabled=True,
                    className="mb-2"
                ),
                dbc.Label("New Name", className="fw-bold"),
                dbc.Input(
                    id="new-column-name-modal-rename",
                    placeholder="Enter new column name...",
                    type="text",
                    autoFocus=True
                ),
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="cancel-rename-column", color="secondary", size="sm"),
                dbc.Button("Rename", id="confirm-rename-column", color="warning", size="sm"),
            ])
        ], id="rename-column-modal", is_open=False),
        
        # Store pour la colonne à renommer
        dcc.Store(id="column-to-rename-store"),
        
    ], fluid=True, style={"maxWidth": "100%", "padding": "10px"})
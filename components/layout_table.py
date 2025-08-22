import dash_bootstrap_components as dbc
from dash import dcc, html

# This function creates the layout for the dashboard page 
def create_dashboard_layout():
    return dbc.Container([
        # Header Section
        dbc.Row([
            dbc.Col([
                html.H1("Data Dashboard", 
                       className="text-center mb-2",
                       style={"color": "#2c3e50", "fontWeight": "bold"}),
                html.P("View, edit, and manage your experimental data in real-time",
                      className="text-center text-muted mb-4",
                      style={"fontSize": "18px"})
            ], width=12)
        ], className="mt-4"),
        
        # Info Alert
        dbc.Alert([
            html.I(className="bi bi-info-circle-fill me-2"),
            html.Strong("Dashboard Features: "),
            "Edit cells directly by clicking on them • Add new data rows • Filter and sort columns • "
            "Select which columns to display • Save changes back to your Excel file",
        ], color="info", className="mb-4"),
        
        # Column Selection Section
        dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="bi bi-columns-gap me-2"),
                    "Column Selection"
                ], className="text-primary mb-0"),
                html.P("Choose which columns to display in your data table", 
                      className="text-muted mb-0 small mt-1")
            ]),
            dbc.CardBody([
                dbc.Accordion([
                    dbc.AccordionItem([
                        dcc.Dropdown(
                            id="column-dropdown",
                            options=[],
                            value=[],
                            multi=True,
                            placeholder="🔍 Search and select columns to display...",
                            style={"width": "100%"}
                        ),
                    ], title="📋 Configure Visible Columns")
                ], start_collapsed=True, className="mb-0")
            ])
        ], className="mb-4 shadow-sm"),
        
        # Data Table Section
        dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.H5([
                        html.I(className="bi bi-table me-2"),
                        "Data Table"
                    ], className="text-success mb-0 d-inline"),
                    html.Small("Interactive spreadsheet view of your data", 
                              className="text-muted ms-3")
                ])
            ]),
            dbc.CardBody([
                dcc.Loading(
                    id="loading-table",
                    type="circle",
                    children=[
                        html.Div(id="main-content-dashboard", className="table-responsive")
                    ]
                )
            ], className="p-2")
        ], className="mb-4 shadow-sm"),
        
        # Action Buttons Section
        dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="bi bi-gear me-2"),
                    "Data Management Actions"
                ], className="text-warning mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button([
                            html.I(className="bi bi-plus-circle me-2"),
                            "Add New Row"
                        ], 
                        id="editing-rows-button", 
                        color="success",
                        size="lg",
                        n_clicks=0,
                        className="w-100 mb-2"
                        ),
                        html.Small("Adds a new empty row at the top of the table",
                                  className="text-muted")
                    ], md=6, className="mb-3"),
                    
                    dbc.Col([
                        dbc.Button([
                            html.I(className="bi bi-floppy me-2"),
                            "Save Changes"
                        ], 
                        id="save-button", 
                        color="primary",
                        size="lg",
                        n_clicks=0,
                        className="w-100 mb-2"
                        ),
                        html.Small("Saves all modifications to your Excel file",
                                  className="text-muted")
                    ], md=6, className="mb-3"),
                ], justify="center"),
                
                # Warning Alert
                dbc.Alert([
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    html.Strong("Important: "),
                    "Changes are only temporary until you click 'Save Changes'. "
                    "Make sure to save your work before navigating away from this page.",
                ], color="warning", className="mt-3 mb-0")
            ])
        ], className="mb-4 shadow-sm"),
        
        # Help Section
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H6([
                        html.I(className="bi bi-question-circle me-2"),
                        "Quick Help"
                    ], className="alert-heading"),
                    html.Hr(),
                    html.P([
                        html.Strong("Editing: "),
                        "Click any cell to edit its value. Press Enter to confirm changes."
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Filtering: "),
                        "Use the filter boxes under column headers to search specific values."
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Sorting: "),
                        "Click column headers to sort data in ascending/descending order."
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Navigation: "),
                        "Use your mouse wheel or scrollbars to navigate large datasets."
                    ], className="mb-0"),
                ], color="light", className="border")
            ], width=12)
        ])
    ], fluid=True, style={"maxWidth": "1400px"})
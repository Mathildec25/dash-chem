"""
Layout for Tutorial page
"""

import dash_bootstrap_components as dbc
from dash import html


def create_tutorial_layout():
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("REACTO Tutorial", className="mb-4 mt-4",
                       style={"color": "#219ebc", "fontWeight": "bold"}),
                html.Hr(style={"borderTop": "3px solid #219ebc", "width": "100px"}),
            ], md=12)
        ]),
        
        # Introduction
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.I(className="bi bi-lightbulb-fill me-2"),
                    "This tutorial will guide you through the complete workflow of using REACTO ",
                    "for your chemical synthesis optimization projects."
                ], color="info", className="mb-4")
            ], md=12)
        ]),
        
        # Tutorial steps
        dbc.Row([
            dbc.Col([
                # Step 1
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.Span("1", className="badge bg-primary me-3",
                                     style={"borderRadius": "50%", "padding": "0.6rem 0.9rem", 
                                           "fontSize": "1.2rem"}),
                            html.Strong("Creating a New Project", style={"fontSize": "1.3rem"})
                        ], style={"display": "flex", "alignItems": "center"})
                    ], style={"backgroundColor": "#f0f7ff"}),
                    dbc.CardBody([
                        html.P([
                            html.Strong("Navigate to the Optimization page"),
                            " and click on ",
                            html.Strong("'New Project'"),
                            "."
                        ]),
                        html.Ul([
                            html.Li("Enter a descriptive project name"),
                            html.Li("The system will create a dedicated Excel file for your project"),
                            html.Li("This file will track all experiments and results"),
                        ]),
                        dbc.Alert([
                            html.I(className="bi bi-info-circle me-2"),
                            "Pro tip: Use clear, descriptive names for easy project identification later."
                        ], color="light", className="mb-0 mt-2")
                    ])
                ], className="mb-4 shadow-sm"),
                
                # Step 2
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.Span("2", className="badge bg-primary me-3",
                                     style={"borderRadius": "50%", "padding": "0.6rem 0.9rem", 
                                           "fontSize": "1.2rem"}),
                            html.Strong("Defining Parameters and Objectives", style={"fontSize": "1.3rem"})
                        ], style={"display": "flex", "alignItems": "center"})
                    ], style={"backgroundColor": "#f0f7ff"}),
                    dbc.CardBody([
                        html.P("Once your project is created, you'll be directed to the parameterization page:"),
                        
                        html.H6("Parameters (Input Variables):", className="mt-3 mb-2",
                               style={"color": "#219ebc"}),
                        html.Ul([
                            html.Li("Add all variables you want to optimize (temperature, concentration, time, etc.)"),
                            html.Li("Specify the range for each parameter (min/max values)"),
                            html.Li("Choose the parameter type (continuous, discrete, categorical)"),
                        ]),
                        
                        html.H6("Objectives (Output Metrics):", className="mt-3 mb-2",
                               style={"color": "#219ebc"}),
                        html.Ul([
                            html.Li("Define what you want to optimize (yield, purity, cost, etc.)"),
                            html.Li("Specify if you want to maximize or minimize each objective"),
                            html.Li("Add target values or constraints if needed"),
                        ]),
                        
                        html.H6("Extra Columns (Optional):", className="mt-3 mb-2",
                               style={"color": "#219ebc"}),
                        html.Ul([
                            html.Li("Add any additional data you want to track"),
                            html.Li("These won't be optimized but will be recorded with results"),
                        ]),
                    ])
                ], className="mb-4 shadow-sm"),
                
                # Step 3
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.Span("3", className="badge bg-primary me-3",
                                     style={"borderRadius": "50%", "padding": "0.6rem 0.9rem", 
                                           "fontSize": "1.2rem"}),
                            html.Strong("Initial Sampling", style={"fontSize": "1.3rem"})
                        ], style={"display": "flex", "alignItems": "center"})
                    ], style={"backgroundColor": "#f0f7ff"}),
                    dbc.CardBody([
                        html.P("Generate your first batch of experiments:"),
                        html.Ul([
                            html.Li("Choose the number of initial experiments (typically 5-10)"),
                            html.Li("The system uses a sampling strategy to explore the parameter space"),
                            html.Li("These experiments provide initial data for the optimization algorithm"),
                        ]),
                        dbc.Alert([
                            html.I(className="bi bi-lightbulb me-2"),
                            "More initial experiments = better initial understanding, but more lab work upfront."
                        ], color="light", className="mb-0 mt-2")
                    ])
                ], className="mb-4 shadow-sm"),
                
                # Step 4
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.Span("4", className="badge bg-primary me-3",
                                     style={"borderRadius": "50%", "padding": "0.6rem 0.9rem", 
                                           "fontSize": "1.2rem"}),
                            html.Strong("Running Experiments", style={"fontSize": "1.3rem"})
                        ], style={"display": "flex", "alignItems": "center"})
                    ], style={"backgroundColor": "#f0f7ff"}),
                    dbc.CardBody([
                        html.P("Execute your experiments and record results:"),
                        html.Ul([
                            html.Li("Download the generated experiment file"),
                            html.Li("Perform the suggested experiments in the lab"),
                            html.Li("Record results in the Excel file or use the auto-fill feature"),
                        ]),
                        
                        html.H6("Auto-Fill Feature:", className="mt-3 mb-2",
                               style={"color": "#219ebc"}),
                        html.P("If your colleagues generate result files automatically:"),
                        html.Ul([
                            html.Li("The system can detect and import results automatically"),
                            html.Li("Uses intelligent keyword matching to find the right data"),
                            html.Li("Saves time and reduces manual data entry errors"),
                        ]),
                    ])
                ], className="mb-4 shadow-sm"),
                
                # Step 5
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.Span("5", className="badge bg-success me-3",
                                     style={"borderRadius": "50%", "padding": "0.6rem 0.9rem", 
                                           "fontSize": "1.2rem"}),
                            html.Strong("Bayesian Optimization", style={"fontSize": "1.3rem"})
                        ], style={"display": "flex", "alignItems": "center"})
                    ], style={"backgroundColor": "#f0fff4"}),
                    dbc.CardBody([
                        html.P("Let REACTO suggest your next experiments:"),
                        html.Ul([
                            html.Li("Upload your results file with completed experiments"),
                            html.Li("Choose the number of new experiments to generate"),
                            html.Li("The algorithm suggests optimal next experiments based on current data"),
                            html.Li("Repeat steps 4-5 until you reach your optimization goals"),
                        ]),
                        
                        html.H6("Advanced Settings:", className="mt-3 mb-2",
                               style={"color": "#219ebc"}),
                        html.Ul([
                            html.Li("Customize acquisition function (confidence vs exploration)"),
                            html.Li("Adjust optimization strategy parameters"),
                            html.Li("Configure surrogate model settings"),
                        ]),
                    ])
                ], className="mb-4 shadow-sm"),
                
                # Step 6
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.Span("6", className="badge bg-success me-3",
                                     style={"borderRadius": "50%", "padding": "0.6rem 0.9rem", 
                                           "fontSize": "1.2rem"}),
                            html.Strong("Results & Analysis", style={"fontSize": "1.3rem"})
                        ], style={"display": "flex", "alignItems": "center"})
                    ], style={"backgroundColor": "#f0fff4"}),
                    dbc.CardBody([
                        html.P("Visualize and export your results:"),
                        html.Ul([
                            html.Li("View interactive plots of your optimization progress"),
                            html.Li("Analyze parameter importance and correlations"),
                            html.Li("Identify optimal operating conditions"),
                            html.Li("Generate professional Word reports with all results"),
                        ]),
                    ])
                ], className="mb-4 shadow-sm"),
                
            ], md=10)
        ], justify="center"),
        
        # Tips section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="bi bi-star-fill me-2", style={"color": "#ffc107"}),
                        html.Strong("Best Practices")
                    ], style={"backgroundColor": "#fffbf0"}),
                    dbc.CardBody([
                        html.Ul([
                            html.Li("Start with a reasonable number of parameters (3-6 is typical)"),
                            html.Li("Define realistic parameter ranges based on chemical constraints"),
                            html.Li("Run at least 5-10 initial experiments for good coverage"),
                            html.Li("Check data quality before running optimization"),
                            html.Li("Use the auto-fill feature to reduce manual work"),
                            html.Li("Review suggested experiments before running them"),
                            html.Li("Document any deviations from suggested conditions"),
                        ], className="mb-0")
                    ])
                ], className="shadow-sm")
            ], md=10)
        ], justify="center", className="mt-4 mb-5"),
        
    ], fluid=True, style={
        "maxWidth": "1200px",
        "marginTop": "2rem",
        "paddingBottom": "3rem"
    })
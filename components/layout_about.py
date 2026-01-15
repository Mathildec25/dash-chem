"""
Layout for About page
"""

import dash_bootstrap_components as dbc
from dash import html


def create_about_layout():
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("About REACTO", className="mb-4 mt-4",
                       style={"color": "#219ebc", "fontWeight": "bold"}),
                html.Hr(style={"borderTop": "3px solid #219ebc", "width": "100px"}),
            ], md=12)
        ]),
        
        # Main content
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("What is REACTO?", className="mb-3",
                               style={"color": "#219ebc"}),
                        html.P([
                            "REACTO (Reaction + Optimization) is a comprehensive graphical user interface ",
                            "for multi-objective Bayesian optimization in chemical synthesis. ",
                            "It provides researchers with an intuitive platform to design, execute, ",
                            "and analyze chemical optimization experiments."
                        ], className="lead"),
                        
                        html.Hr(),
                        
                        html.H4("Key Features", className="mb-3 mt-4",
                               style={"color": "#219ebc"}),
                        html.Ul([
                            html.Li([
                                html.Strong("Multi-objective Optimization: "),
                                "Optimize multiple reaction parameters simultaneously"
                            ], className="mb-2"),
                            html.Li([
                                html.Strong("Bayesian Optimization: "),
                                "Leverage advanced machine learning algorithms (BoFire) for efficient experimentation"
                            ], className="mb-2"),
                            html.Li([
                                html.Strong("Automated Result Import: "),
                                "Intelligent auto-fill system for seamless data integration"
                            ], className="mb-2"),
                            html.Li([
                                html.Strong("Professional Reporting: "),
                                "Generate comprehensive Word documents with results and visualizations"
                            ], className="mb-2"),
                            html.Li([
                                html.Strong("Real-time Collaboration: "),
                                "Work with colleagues for experiment execution and analysis"
                            ], className="mb-2"),
                        ], style={"fontSize": "1.05rem"}),
                        
                        html.Hr(),
                        
                        html.H4("Technology Stack", className="mb-3 mt-4",
                               style={"color": "#219ebc"}),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.I(className="bi bi-check-circle-fill me-2",
                                          style={"color": "#28a745"}),
                                    html.Span("Python & Dash for the interface")
                                ], className="mb-2")
                            ], md=6),
                            dbc.Col([
                                html.Div([
                                    html.I(className="bi bi-check-circle-fill me-2",
                                          style={"color": "#28a745"}),
                                    html.Span("BoFire for Bayesian optimization")
                                ], className="mb-2")
                            ], md=6),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.I(className="bi bi-check-circle-fill me-2",
                                          style={"color": "#28a745"}),
                                    html.Span("Plotly for interactive visualizations")
                                ], className="mb-2")
                            ], md=6),
                            dbc.Col([
                                html.Div([
                                    html.I(className="bi bi-check-circle-fill me-2",
                                          style={"color": "#28a745"}),
                                    html.Span("Bootstrap for responsive design")
                                ], className="mb-2")
                            ], md=6),
                        ]),
                        
                        html.Hr(),
                        
                        html.H4("Development Team", className="mb-3 mt-4",
                               style={"color": "#219ebc"}),
                        html.P([
                            "REACTO is developed at the University of Liège as part of ongoing research ",
                            "in chemical synthesis optimization and artificial intelligence applications ",
                            "in chemistry."
                        ]),
                        
                    ])
                ], className="shadow-sm")
            ], md=10)
        ], justify="center"),
        
        # Version info
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Small([
                        html.I(className="bi bi-info-circle me-2"),
                        "For questions or support, please contact the development team."
                    ], className="text-muted")
                ], className="text-center mt-4 mb-4")
            ], md=12)
        ])
        
    ], fluid=True, style={
        "maxWidth": "1200px",
        "marginTop": "2rem",
        "paddingBottom": "3rem"
    })
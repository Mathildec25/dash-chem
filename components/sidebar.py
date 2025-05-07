import dash_bootstrap_components as dbc
from dash import dcc, html
from dash import page_registry

def generate_sidebar(sheet_names):
    nav_links = [
        html.Div(
            id="dropdown-container",
            children=[
                dcc.Dropdown(
                    id="sheet-dropdown",
                    options=[{"label": name, "value": name} for name in sheet_names],
                    placeholder="Select a sheet",
                    style={"margin-top": "5px"}
                ),
            ]
        )
    ]

    for page in page_registry.values():
        nav_links.append(
            dbc.NavLink(
                [html.Div(page["name"], className="ms-2")],
                href=page["path"],
                active="exact"
            )
        )

    sidebar = dbc.Collapse(
        html.Div(
            [
                html.H2("<3||^^", className="display-3", style={"textAlign": "center"}),
                html.Hr(),
                dbc.Nav(
                    children=nav_links,
                    vertical=True,
                    pills=True,
                    className="bg-light"
                )
            ],
            style={
                "padding": "1rem",
                "background-color": "#f3fcff",
                "height": "300vh"
            }
        ),
        id="collapse-sidebar",
        is_open=True
    )

    return sidebar

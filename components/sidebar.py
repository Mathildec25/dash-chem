import dash_bootstrap_components as dbc
from dash import dcc, html
from dash import page_registry

# Define and return the sidebar layout
def generate_sidebar(sheet_names):
    nav_links = [
        html.Div(
            id="dropdown-container",
            children=[
                dcc.Dropdown(       # To select the sheet to display
                    id="sheet-dropdown",
                    options=[{"label": name, "value": name} for name in sheet_names],
                    placeholder="Select a sheet",
                    style={"margin-top": "5px"}
                ),
            ]
        )
    ]

    for page in page_registry.values():     # Add all files in the pages folder as links in the sidebar
        nav_links.append(
            dbc.NavLink(
                [html.Div(page["name"], className="ms-2")],
                href=page["path"],
                active="exact"
            )
        )

    sidebar = dbc.Collapse(     # Sidebar content in collapse to be able to hide it
        html.Div(
            [
                html.H2("MET", className="display-2", style={"textAlign": "center"}),
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
                "background-color": "#ebbfbb",
                "height": "300vh"
            }
        ),
        id="collapse-sidebar",
        is_open=True
    )

    return sidebar

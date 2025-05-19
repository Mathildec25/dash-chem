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
                [
                    html.I(className="bi bi-house-door me-2"),  # Icône Bootstrap
                    html.Span(page["name"], className="link-text")  # texte masqué si besoin
                ],
                href=page["path"],
                active="exact"
            )
        )

    sidebar = html.Div(
        [
            html.Div("MET", className="sidebar-logo"),
            html.Hr(),
            dbc.Nav(
                children=nav_links,
                vertical=True,
                pills=True,
                className="sidebar-nav"
            )
        ],
        className="sidebar"
    )

    return sidebar
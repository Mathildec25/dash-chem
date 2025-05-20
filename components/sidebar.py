import dash_bootstrap_components as dbc
from dash import dcc, html
from dash import page_registry

icon_map = {
    "Home": "bi-house-door",
    "Dashboard": "bi-table",
    "Visualization": "bi-graph-up",
    "Caracterization": "bi-gear",
    "Bayesian-Optimization": "bi-calculator",
}

def generate_sidebar(sheet_names):
    nav_links = [
        html.Div(
            id="dropdown-container",
            children=[
                dcc.Dropdown(
                    id="sheet-dropdown",
                    options=[{"label": name, "value": name} for name in sheet_names],
                    placeholder="Select a sheet",
                    clearable = False,
                    style={"background-color": "#ff9e3d"}
                ),
            ]
        )
    ]

    for page in page_registry.values():
        icon_class = icon_map.get(page["name"], "bi-circle") 
        nav_links.append(
            dbc.NavLink(
                [
                    html.I(className=f"bi {icon_class} me-2", style={"font-size": "1.2rem"}),  # Icône Bootstrap
                    html.Span(page["name"], className="link-text")  # texte masqué si besoin
                ],
                href=page["path"],
                active="exact"
            )
        )

    sidebar = html.Div([
        html.Div(
            [
            html.I(className="bi bi-menu-button icon-logo", style={"font-size": "2rem"}),
            html.Span("MET", className="text-logo")
            ], 
        className="sidebar-logo"
        ),
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
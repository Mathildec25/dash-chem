import dash_bootstrap_components as dbc
from dash import dcc, html
from dash import page_registry

# 
icon_map = {
    "Home": "bi-house-door",
    "Dashboard": "bi-table",
    "Visualization": "bi-graph-up",
    "Caracterization": "bi-gear",
    "Bayesian-Optimization": "bi-calculator",
}

def generate_sidebar():
    nav_links = []
    for page in page_registry.values():
        icon_class = icon_map.get(page["name"], "bi-circle") 
        nav_links.append(
            dbc.NavLink(
                [
                    html.I(className=f"bi {icon_class} me-2", style={"font-size": "1.2rem"}),  # Bootstrap icon
                    html.Span(page["name"], className="link-text")  # hidden text if needed
                ],
                href=page["path"],
                active="exact"
            )
        )

    sidebar = html.Div([
        html.Div(
            [
            html.Img(src="/assets/Logo.svg", className="icon-logo"),
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
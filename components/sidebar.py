import dash_bootstrap_components as dbc
from dash import dcc, html
from dash import page_registry

# 
icon_map = {
    "Home": "bi-house-door",
    "Dashboard": "bi-table",
    "Visualization": "bi-bar-chart-line",
    "Caracterization": "bi-gear",
    "Optimization": "/assets/BO_icon.svg",
}

def generate_sidebar():
    nav_links = []
    for page in page_registry.values():
        if page["name"] not in ["Opti parameterization", "Opti run", "Results & Analysis", "Caracterization"]:
            icon_entry = icon_map.get(page["name"], "bi-circle")

            # If it's an SVG path, render with html.Img
            if icon_entry.endswith(".svg"):
                icon_component = html.Img(
                    src=icon_entry,
                    className="sidebar-icon",
                )
            else:
                # Otherwise use Bootstrap icon
                icon_component = html.I(
                    className=f"bi {icon_entry} me-2",
                    style={"fontSize": "1.2rem"}
                )

            nav_links.append(
                dbc.NavLink(
                    [
                        icon_component,
                        html.Span(page["name"], className="link-text"),
                    ],
                    href=page["path"],
                    active="exact",
                )
            )

    sidebar = html.Div(
        [
            html.Div(
                [
                    html.Img(src="/assets/Logo.svg", className="icon-logo"),
                    html.Span("MET", className="text-logo"),
                ],
                className="sidebar-logo",
            ),
            dbc.Nav(
                children=nav_links,
                vertical=True,
                pills=True,
                className="sidebar-nav",
            ),
        ],
        className="sidebar",
    )

    return sidebar
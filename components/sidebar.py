import dash_bootstrap_components as dbc
from dash import html
from dash import page_registry

# Icon mapping for each page
ICON_MAP = {
    "Optimization": "/assets/BO_icon.svg",
    "Tutorial": "bi-book",
    "About": "bi-info-circle",
}

# Pages to exclude from sidebar
EXCLUDED_PAGES = {"Opti parameterization", "Opti run", "Results & Analysis"}

# Display order for sidebar pages
PAGE_ORDER = ["Optimization", "Tutorial", "About"]

# Default icon for pages without specific mapping
DEFAULT_ICON = "bi-circle"


def create_icon_component(icon_entry):
    """
    Create an icon component from either an SVG path or Bootstrap icon class.
    
    Args:
        icon_entry (str): Either a path to SVG file or Bootstrap icon class name
        
    Returns:
        dash component: Icon component (html.Img or html.I)
    """
    if icon_entry.endswith(".svg"):
        return html.Img(src=icon_entry, className="sidebar-icon")
    
    return html.I(className=f"bi {icon_entry} me-2", style={"fontSize": "1.2rem"})


def generate_sidebar():
    """
    Generate the sidebar navigation component with logo and page links.
    
    Returns:
        html.Div: Complete sidebar component
    """
    # Filter out excluded pages and sort according to PAGE_ORDER
    pages = sorted(
        [page for page in page_registry.values() if page["name"] not in EXCLUDED_PAGES],
        key=lambda p: PAGE_ORDER.index(p["name"]) if p["name"] in PAGE_ORDER else 999
    )
    
    nav_links = [
        dbc.NavLink(
            [
                create_icon_component(ICON_MAP.get(page["name"], DEFAULT_ICON)),
                html.Span(page["name"], className="link-text"),
            ],
            href=page["path"],
            active="exact",
        )
        for page in pages
    ]

    return html.Div(
        [
            html.Div(
                [
                    html.Img(src="/assets/REACTO_logo.png", className="icon-logo"),
                ],
                className="sidebar-logo",
            ),
            dbc.Nav(nav_links, vertical=True, pills=True, className="sidebar-nav"),
        ],
        className="sidebar",
    )
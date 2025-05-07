import dash
from components.layout_display import create_dashboard_layout

dash.register_page(__name__, name="Dashboard", path="/")

layout = create_dashboard_layout()

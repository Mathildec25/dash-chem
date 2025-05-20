import dash
from components.layout_dashboard import create_dashboard_layout

# Include this file as a page in the Dash app
dash.register_page(__name__, name="Dashboard", path="/table", order=2)

# Define the layout of the page using the function from layout_display.py
layout = create_dashboard_layout()

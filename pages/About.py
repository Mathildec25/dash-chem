import dash
from components.layout_about import create_about_layout

# Include this file as a page in the Dash app
dash.register_page(__name__, name="About", path="/about", order=1)

# Define the layout of the page using the function from layout_about.py
layout = create_about_layout()
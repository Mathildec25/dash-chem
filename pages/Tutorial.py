import dash
from components.layout_tutorial import create_tutorial_layout

# Include this file as a page in the Dash app
dash.register_page(__name__, name="Tutorial", path="/tutorial", order=2)

# Define the layout of the page using the function from layout_tutorial.py
layout = create_tutorial_layout()
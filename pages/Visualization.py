import dash
from components.layout_visu import create_visu_layout

# Include this file as a page in the Dash app
dash.register_page(__name__, name="Visualization", path="/visu", order=3)

# Define the layout of the page using the function from layout_display.py
layout = create_visu_layout()
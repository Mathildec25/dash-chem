import dash
from components.layout_opti_home import create_opti_home_layout

# Include this file as a page in the Dash app
dash.register_page(__name__, name="Optimization", path="/", order=5)

# Define the layout of the page using the function from layout_display.py
layout = create_opti_home_layout()




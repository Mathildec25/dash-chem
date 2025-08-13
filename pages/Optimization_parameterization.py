import dash
from components.layout_opti_param import create_opti_param_layout

# Include this file as a page in the Dash app
dash.register_page(__name__, name="Opti parameterization", path="/Opt-param", order=6)

# Define the layout of the page using the function from layout_display.py
layout = create_opti_param_layout()




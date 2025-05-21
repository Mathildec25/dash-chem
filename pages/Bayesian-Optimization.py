import dash
from components.layout_optimization import create_optimization_layout

# Include this file as a page in the Dash app
dash.register_page(__name__, name="Bayesian-Optimization", path="/Bay-Opt", order=5)

# Define the layout of the page using the function from layout_display.py
layout = create_optimization_layout()




import dash
from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update, MATCH, ALL, ctx
import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
from components.layout_home import create_home_layout

# Include this file as a page in the Dash app
dash.register_page(__name__, name="Home", path="/", order=1)

# Define the layout of the page using the function from layout_display.py
layout = create_home_layout()
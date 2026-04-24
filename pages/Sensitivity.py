import dash

from components.layout_sensitivity import create_sensitivity_layout

dash.register_page(__name__, path="/sensitivity", name="Sensitivity Screen")

layout = create_sensitivity_layout()

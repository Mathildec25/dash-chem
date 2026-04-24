import dash

from components.layout_opti_home import create_opti_home_layout

dash.register_page(__name__, name="Optimization", path="/", order=5)

layout = create_opti_home_layout()

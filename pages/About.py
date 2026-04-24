import dash

from components.layout_about import create_about_layout

dash.register_page(__name__, name="About", path="/about", order=1)

layout = create_about_layout()

import dash

from components.layout_tutorial import create_tutorial_layout

dash.register_page(__name__, name="Tutorial", path="/tutorial", order=2)

layout = create_tutorial_layout()

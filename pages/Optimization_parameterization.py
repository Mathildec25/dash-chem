import dash

from components.layout_opti_param import create_opti_param_layout

dash.register_page(__name__, name="Opti parameterization", path="/Opt-param", order=6)

layout = create_opti_param_layout()

import dash

from components.layout_opti_run import create_opti_run_layout

dash.register_page(__name__, name="Opti run", path="/Opt-run", order=6)

layout = create_opti_run_layout()

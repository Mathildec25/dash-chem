import dash

from components.layout_opti_results import create_opti_results_layout

dash.register_page(__name__, path="/Opt-results", name="Results & Analysis")

layout = create_opti_results_layout()

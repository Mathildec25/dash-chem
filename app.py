import os

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from flask import send_from_directory

from components.sidebar import generate_sidebar
from callbacks.app_callbacks import register_app_callbacks

# Imported for their side-effects: each module registers its @callback handlers.
from callbacks import advanced_bo_callbacks, sensitivity_callbacks  # noqa: F401
from callbacks.opti_home_callbacks import already_created_callbacks, new_proj_callbacks  # noqa: F401
from callbacks.opti_param_callbacks import (  # noqa: F401
    base_callbacks,
    constraints_callbacks,
    domain_creation,
    parameter_part,
    solvents_callbacks,
)
from callbacks.opti_results_callbacks import results_analysis  # noqa: F401
from callbacks.opti_run_callbacks import online_analysis_callbacks, run_optimization  # noqa: F401


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.icons.BOOTSTRAP],
    use_pages=True,
    suppress_callback_exceptions=True,
)
server = app.server


@server.route("/ketcher/<path:filename>")
def serve_ketcher(filename):
    return send_from_directory(os.path.join("public", "ketcher"), filename)


sidebar = generate_sidebar()
register_app_callbacks(app)


app.layout = html.Div([
    dcc.Store(id="selected-excel-store", storage_type="session"),
    dcc.Store(id="selected-sheet-store", storage_type="session"),
    dcc.Store(id="parameter-store", data=[], storage_type="session"),
    dcc.Store(id="objective-store", data=[], storage_type="session"),
    dcc.Store(id="extra-columns-store", data=[], storage_type="session"),
    dcc.Store(id="project-name-store", storage_type="session"),
    dcc.Store(id="constraints-store", data=None, storage_type="session"),
    dcc.Store(id="selected-file-store", storage_type="session"),
    dcc.Store(id="current-excel-file", storage_type="session"),
    dcc.Store(id="current-domain", storage_type="session"),
    dcc.Location(id="url", refresh="callback-nav"),
    sidebar,
    html.Div(
        id="main-content",
        className="main-content",
        children=[dash.page_container],
        style={"marginLeft": "68px"},
    ),
])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088, debug=True)

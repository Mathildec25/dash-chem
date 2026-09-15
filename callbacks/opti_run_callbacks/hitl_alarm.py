# -*- coding: utf-8 -*-
"""The human-in-the-loop alarm on the Run page.

When a project was created with "Human in the loop" switched on, every change
of the experiment table is read by hitl_bench.alarm: if the frozen trigger
fires at the last completed experiment and that alert has not been answered,
a panel appears - the same three answers as on the HITL live page - and the
"Get New Experiment" button waits for the answer.

Answers are appended to the project's metadata under `hitl_log`, with the
experiment number, P* at that moment, the reason, and the time. "Stop" keeps
the button disabled for good; "propose" appends an empty row marked "Chemist"
to the table (and to the Excel file) for the user to fill in.
"""

import os

from dash import Input, Output, State, callback, html, no_update
import dash_bootstrap_components as dbc
import pandas as pd

from config_path import EXCEL_FOLDER
from domain_storage import DomainStorage
from hitl_bench import alarm
from utils.safe_excel import safe_excel_save

RED = "#c1121f"


def _project(excel_file):
    """(objectives, hitl config, log) of the project, or None when it has no alarm."""
    if not excel_file:
        return None
    domain_data = DomainStorage.load_domain(excel_file)
    if not domain_data:
        return None
    config = domain_data.get("metadata", {}).get("hitl") or {}
    if not config.get("enabled"):
        return None
    return domain_data.get("objectives", []), config, domain_data.get("hitl_log") or []


def alarm_state(excel_file, table_data):
    """The alarm's view of the project, or None when the project has no alarm."""
    project = _project(excel_file)
    if project is None or not table_data:
        return None
    objectives, config, log = project
    return alarm.state(table_data, objectives, log)


def _panel(st):
    n = st["pending"]
    return dbc.Card(dbc.CardBody([
        html.H5([html.I(className="bi bi-pause-circle me-2"),
                 "The campaign pauses at experiment %d" % n], style={"color": RED}),
        html.P("The optimiser is progressing much more slowly than it has so far. "
               "What happens next is your call.", className="mb-3"),
        dbc.RadioItems(id="hitl-choice", value=None, className="mb-2", options=[
            {"label": "Let the optimiser continue — ask it for the next experiment as usual",
             "value": "continue"},
            {"label": "Propose the next experiment myself — an empty row marked \"Chemist\" is added "
                      "to the table for my conditions; run it and fill in the result",
             "value": "chemist"},
            {"label": "Stop the campaign here", "value": "stop"},
        ]),
        dbc.Label("Why? (required)", className="fw-bold"),
        dbc.Textarea(id="hitl-why", rows=2, className="mb-2",
                     placeholder="One sentence is enough."),
        dbc.Button("Submit", id="hitl-submit", color="danger"),
        html.Div(id="hitl-feedback", className="mt-2"),
    ]), className="mb-3", style={"borderRadius": "12px", "border": "2px solid %s" % RED})


def _stopped_banner(log):
    entry = next(e for e in log if e.get("choice") == "stop")
    return dbc.Alert([html.B("Campaign stopped at experiment %d. " % entry["experiment"]),
                      html.Span(entry.get("why", ""), className="fst-italic")],
                     color="secondary", className="mb-3")


@callback(
    Output("hitl-alarm-container", "children"),
    Input("experiment-datatable", "data"),
    Input("hitl-tick", "data"),
    State("current-excel-file", "data"),
    prevent_initial_call=True,
)
def show_alarm(table_data, tick, excel_file):
    project = _project(excel_file)
    if project is None or not table_data:
        return html.Div()
    objectives, config, log = project
    st = alarm.state(table_data, objectives, log)
    if st["stopped"]:
        return _stopped_banner(log)
    if st["pending"]:
        return _panel(st)
    return html.Div()


@callback(
    Output("hitl-feedback", "children"),
    Output("hitl-tick", "data"),
    Output("experiment-datatable", "data", allow_duplicate=True),
    Input("hitl-submit", "n_clicks"),
    State("hitl-choice", "value"),
    State("hitl-why", "value"),
    State("experiment-datatable", "data"),
    State("experiment-datatable", "columns"),
    State("current-excel-file", "data"),
    State("hitl-tick", "data"),
    prevent_initial_call=True,
)
def answer_alarm(n_clicks, choice, why, table_data, columns, excel_file, tick):
    if not n_clicks:
        return no_update, no_update, no_update
    project = _project(excel_file)
    if project is None:
        return dbc.Alert("This project has no alarm.", color="secondary"), no_update, no_update
    objectives, config, log = project
    st = alarm.state(table_data, objectives, log)
    if not st["pending"]:
        return dbc.Alert("No pause is pending.", color="secondary"), no_update, no_update
    if choice is None:
        return dbc.Alert("Choose one of the three options.", color="warning"), no_update, no_update
    why = (why or "").strip()
    if len(why) < 3:
        return dbc.Alert("Please write why, in a sentence — it matters as much as the choice.",
                         color="warning"), no_update, no_update
    log = log + [alarm.log_entry(st["pending"], choice, why, st["p_star"])]
    ok, message = DomainStorage.update_metadata(excel_file, "hitl_log", log)
    if not ok:
        return dbc.Alert("Could not save the answer: %s" % message, color="danger"), no_update, no_update

    new_data = no_update
    if choice == "chemist":
        # the chemist's experiment: an empty row to fill in, already marked as theirs
        row = {c["id"]: ("Chemist" if c["id"] == "Point type" else "") for c in columns}
        new_data = list(table_data) + [row]
        df = pd.DataFrame(new_data)
        saved, message = safe_excel_save(os.path.join(EXCEL_FOLDER, excel_file),
                                         lambda path: df.to_excel(path, index=False, engine="openpyxl"))
        if not saved:
            return dbc.Alert("Answer saved, but the new row could not be written: %s" % message,
                             color="danger"), (tick or 0) + 1, no_update
    return dbc.Alert("Saved.", color="success", className="py-1"), (tick or 0) + 1, new_data

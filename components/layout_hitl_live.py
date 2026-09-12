# -*- coding: utf-8 -*-
"""Layout for the live HITL page: a chemist drives a campaign, one experiment at a time.

Everything that decides what happens lives in hitl_bench/live.py; this file only
draws. It follows the Results page - same cards, same KPI tiles, same colour -
so a chemist who has seen REACTO recognises it, and it never names the optimiser's
internals: no hypervolume, no acquisition, no front. The plots show what a
chemist would look at during a real campaign, which is the point of the study.
"""

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html

from hitl_bench import live

BLUE = "#219ebc"
GREY = "#8b93a1"
RED = "#c1121f"
GREEN = "#10b981"
TO_CHOOSE = "— choose —"


# --- the page --------------------------------------------------------------
def create_hitl_live_layout():
    return html.Div([
        dbc.Row(dbc.Col([
            html.H1("Optimisation with a chemist in the loop", className="mb-2 mt-4",
                    style={"color": BLUE, "fontWeight": "bold"}),
            html.Hr(style={"borderTop": "3px solid %s" % BLUE, "width": "100px"}),
        ])),

        # --- identity ---------------------------------------------------------
        dbc.Card(dbc.CardBody([
            html.H5("Who are you?", style={"color": BLUE}),
            dbc.Row([
                dbc.Col([dbc.Label("Name or initials", className="fw-bold small"),
                         dbc.Input(id="hl-name", placeholder="e.g. MC")], md=4),
                dbc.Col([dbc.Label("Field", className="fw-bold small"),
                         dbc.Input(id="hl-field",
                                   placeholder="catalysis, flow chemistry, process...")], md=5),
                dbc.Col([dbc.Label(" ", className="small"),
                         dbc.Button("Start", id="hl-start", color="primary",
                                    className="w-100")], md=3),
            ]),
            html.Div("Your answers are saved under this name. Always use the same one "
                     "to resume a campaign in progress.",
                     className="text-muted small mt-2"),
        ]), className="mb-3", style={"borderRadius": "12px"}),

        html.Div(id="hl-campaigns"),        # the list of campaigns, once named
        html.Div(id="hl-view"),             # the running campaign
        dcc.Store(id="hl-session"),         # {chemist, field, benchmark, seed}
        dcc.Store(id="hl-tick", data=0),
        dcc.Interval(id="hl-interval", interval=900, disabled=True),
    ], style={"maxWidth": "68rem", "margin": "0 auto", "padding": "0 1rem 4rem"})


def campaign_list(chemist, field):
    """The three campaigns a chemist is given, with what is done."""
    items = live.campaigns_for(chemist)
    if not items:
        return dbc.Alert("No campaign is available yet.", color="warning")
    buttons = []
    for name, seed, done in items:
        pres = live.presentation(name)
        buttons.append(dbc.ListGroupItem([
            html.Div([
                html.B(pres["title"]),
                html.Span(" — campaign %d" % seed, className="text-muted"),
            ]),
            dbc.Badge("finished", color="success", className="me-2") if done
            else dbc.Button("Open", id={"type": "hl-open", "b": name, "s": seed},
                            size="sm", color="primary", outline=True),
        ], className="d-flex justify-content-between align-items-center"))
    return dbc.Card(dbc.CardBody([
        html.H5("Your campaigns", style={"color": BLUE}),
        html.P("Three reactions, one campaign each. Do them in whichever order you "
               "like; each takes ten to fifteen minutes.", className="small"),
        dbc.ListGroup(buttons, flush=True),
    ]), className="mb-3", style={"borderRadius": "12px"})


# --- the campaign view --------------------------------------------------------
def _kpi(icon, value, title, colour):
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.I(className="bi %s" % icon, style={"fontSize": "1.4rem", "color": colour}),
        html.H4(value, className="mb-0 mt-1", style={"fontWeight": 700}),
        html.P(title, className="text-muted mb-0 small"),
    ], className="text-center"), style={"borderRadius": "12px"}), md=3, className="mb-2")


def _with_unit(entry):
    """'Temperature (°C)' from ('Temperature', '°C'); no parentheses without a unit."""
    return entry[0] + ((" (%s)" % entry[1]) if entry[1] else "")


def _table(c):
    keys = c.benchmark.parameter_keys
    objs = c.benchmark.objectives
    head = [html.Th("#"), html.Th("")]
    head += [html.Th(_with_unit(c.pres["params"].get(k, (k, "")))) for k in keys]
    head += [html.Th(_with_unit(c.pres["objectives"].get(o, (o, "", "")))) for o in objs]
    rows = []
    for r in c.experiments:
        badge = {"lhs": ("start", "secondary"), "bo": ("algorithm", "info"),
                 "chemist": ("you", "danger")}[r["phase"]]
        cells = [html.Td(r["experiment"]),
                 html.Td(dbc.Badge(badge[0], color=badge[1], className="small"))]
        cells += [html.Td(live.label(c.benchmark, k, r[k])) for k in keys]
        cells += [html.Td(live.number(r[o], 4), style={"textAlign": "right"}) for o in objs]
        rows.append(html.Tr(cells))
    return html.Div(dbc.Table([html.Thead(html.Tr(head)), html.Tbody(rows)],
                              size="sm", hover=True, responsive=True),
                    style={"maxHeight": "22rem", "overflowY": "auto"})


def _scatter(c):
    """The objectives against each other, best trade-offs outlined."""
    objs = c.benchmark.objectives
    o1, o2 = objs[0], objs[1] if len(objs) > 1 else objs[0]
    t1 = c.pres["objectives"].get(o1, (o1, "", "max"))
    t2 = c.pres["objectives"].get(o2, (o2, "", "max"))
    fig = go.Figure()
    for phase, name, colour, symbol in (("lhs", "starting experiments", GREY, "circle"),
                                        ("bo", "algorithm", BLUE, "circle"),
                                        ("chemist", "you", RED, "star")):
        pts = [r for r in c.experiments if r["phase"] == phase]
        if not pts:
            continue
        fig.add_trace(go.Scatter(
            x=[r[o1] for r in pts], y=[r[o2] for r in pts], mode="markers", name=name,
            marker={"color": colour, "size": 11 if phase == "chemist" else 8,
                    "symbol": symbol, "line": {"width": 0.5, "color": "white"}},
            text=["experiment %d" % r["experiment"] for r in pts]))
    # outline the current best trade-offs, without naming them a front
    import numpy as np
    from hitl_bench import metrics
    raw = np.array([[r[o] for o in objs] for r in c.experiments], dtype=float)
    sign = np.array([1.0 if c.pres["objectives"].get(o, (o, "", "max"))[2] == "max"
                     else -1.0 for o in objs])
    mask = metrics.pareto_mask(raw * sign)
    best = sorted([c.experiments[i] for i in np.flatnonzero(mask)], key=lambda r: r[o1])
    fig.add_trace(go.Scatter(
        x=[r[o1] for r in best], y=[r[o2] for r in best], mode="lines+markers",
        name="best trade-offs", line={"color": GREEN, "width": 1.5, "dash": "dot"},
        marker={"color": GREEN, "size": 12, "symbol": "circle-open", "line": {"width": 2}}))
    fig.update_layout(
        xaxis_title=_with_unit(t1), yaxis_title=_with_unit(t2),
        margin={"l": 50, "r": 10, "t": 10, "b": 45}, height=340,
        legend={"orientation": "h", "y": 1.08}, template="plotly_white")
    return fig


def _progress(c):
    """Best value of each objective so far, experiment by experiment."""
    fig = go.Figure()
    for o in c.benchmark.objectives:
        t = c.pres["objectives"].get(o, (o, "", "max"))
        vals = [r[o] for r in c.experiments]
        best = []
        for i, v in enumerate(vals):
            best.append(max(vals[: i + 1]) if t[2] == "max" else min(vals[: i + 1]))
        fig.add_trace(go.Scatter(x=list(range(1, len(best) + 1)), y=best, mode="lines",
                                 name="best %s" % t[0].lower(), line={"width": 2}))
    fig.add_vline(x=c.n_init + 0.5, line={"color": GREY, "dash": "dot", "width": 1})
    for d in c.state["decisions"]:
        if d["choice"] == "chemist":
            fig.add_vline(x=d["at_experiment"] + 1, line={"color": RED, "width": 1.2})
    fig.update_layout(xaxis_title="experiment", margin={"l": 50, "r": 10, "t": 10, "b": 45},
                      height=340, legend={"orientation": "h", "y": 1.08},
                      template="plotly_white")
    return fig


def _alert_panel(c):
    alert = c.state["pending_alert"]
    keys = c.benchmark.parameter_keys
    proposal = alert["proposal"]
    prop_txt = " · ".join("%s %s" % (c.pres["params"].get(k, (k, ""))[0],
                                     live.label(c.benchmark, k, proposal[k])) for k in keys)
    menus = [dbc.Col([
        dbc.Label(_with_unit(c.pres["params"].get(k, (k, ""))), className="fw-bold small"),
        dcc.Dropdown(id={"type": "hl-param", "key": k},
                     options=[{"label": n, "value": n} for n in live.levels(c.benchmark, k)],
                     placeholder=TO_CHOOSE, clearable=True),
    ], md=4, className="mb-2") for k in keys]

    return dbc.Card(dbc.CardBody([
        html.H5([html.I(className="bi bi-pause-circle me-2"),
                 "The campaign pauses at experiment %d" % alert["experiment"]],
                style={"color": RED}),
        html.P("The algorithm is progressing much more slowly than it has so far. "
               "What happens next is your call.", className="mb-3"),
        dbc.Label("What do you do?", className="fw-bold"),
        dbc.RadioItems(id="hl-choice", value=None, className="mb-2", options=[
            {"label": "Let the algorithm continue — its next experiment would be: %s"
                      % prop_txt, "value": "optimiser"},
            {"label": "Propose the next experiment myself", "value": "chemist"},
            {"label": "Stop the campaign here", "value": "stop"},
        ]),
        html.Div(id="hl-proposal", style={"display": "none"}, children=[
            dbc.Card(dbc.CardBody([html.P(html.B("Your conditions"), className="mb-2"),
                                   dbc.Row(menus)]), className="border-danger mb-2"),
        ]),
        dbc.Label("Why?", className="fw-bold"),
        dbc.Textarea(id="hl-why", rows=2, className="mb-2",
                     placeholder="One sentence is enough. Your reasoning matters as much as your choice."),
        dbc.Button("Submit", id="hl-submit", color="danger"),
        html.Div(id="hl-feedback", className="mt-2"),
    ]), className="mb-3", style={"borderRadius": "12px", "border": "2px solid %s" % RED})


def campaign_view(c):
    """The whole campaign screen, rebuilt on every tick."""
    n_bo = sum(1 for r in c.experiments if r["phase"] == "bo")
    n_you = sum(1 for r in c.experiments if r["phase"] == "chemist")
    objs = c.benchmark.objectives
    o1 = c.pres["objectives"].get(objs[0], (objs[0], "", "max"))
    vals = [r[objs[0]] for r in c.experiments]
    best1 = (max(vals) if o1[2] == "max" else min(vals)) if vals else 0

    if c.finished:
        status = dbc.Alert([html.B("Campaign finished. "),
                            "Thank you — your %d decisions are recorded." % len(c.state["decisions"]),
                            html.Br(), html.Span("You can open the next campaign in the "
                                                 "list above.", className="small")],
                           color="success")
        controls = html.Div()
    elif c.waiting:
        status = html.Div()
        controls = _alert_panel(c)
    elif c.n_done == c.n_init:
        status = dbc.Alert([html.B("Here are the %d starting experiments. " % c.n_init),
                            "They were drawn at random to cover the domain, not chosen "
                            "by the algorithm. Launch the optimisation once you have "
                            "looked at them."], color="light", className="border")
        controls = dbc.Button([html.I(className="bi bi-play-fill me-1"),
                               "Launch the optimisation"], id="hl-launch", color="primary",
                              size="lg", className="mb-3")
    else:
        status = dbc.Alert([dbc.Spinner(size="sm", color="primary"),
                            html.Span("  The algorithm is choosing and running experiments "
                                      "one by one… (%d / %d)" % (c.n_done, c.budget))],
                           color="light", className="border")
        controls = html.Div()

    return html.Div([
        html.H3(c.pres["title"], style={"color": BLUE}, className="mt-2"),
        html.P(c.pres["intro"]),
        dbc.Alert(c.pres["note"], color="secondary", className="small py-2"),
        dbc.Row([
            _kpi("bi-clipboard-data", "%d / %d" % (c.n_done, c.budget), "experiments", "#6366f1"),
            _kpi("bi-cpu", str(n_bo), "chosen by the algorithm", BLUE),
            _kpi("bi-person", str(n_you), "chosen by you", RED),
            _kpi("bi-trophy", live.number(best1, 3) + (" " + o1[1] if o1[1] else ""),
                 "best %s" % o1[0].lower(), GREEN),
        ]),
        status, controls,
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("The two objectives", className="text-muted"),
                dcc.Graph(figure=_scatter(c), config={"displayModeBar": False})]),
                style={"borderRadius": "12px"}), md=6, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Progress", className="text-muted"),
                dcc.Graph(figure=_progress(c), config={"displayModeBar": False})]),
                style={"borderRadius": "12px"}), md=6, className="mb-3"),
        ]),
        dbc.Card(dbc.CardBody([html.H6("All experiments", className="text-muted"),
                               _table(c)]), style={"borderRadius": "12px"}),
    ])

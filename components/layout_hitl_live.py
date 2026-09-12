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

BLEU = "#219ebc"
GRIS = "#8b93a1"
ROUGE = "#c1121f"
VERT = "#10b981"
A_CHOISIR = "— à choisir —"


# --- the page --------------------------------------------------------------
def create_hitl_live_layout():
    return html.Div([
        dbc.Row(dbc.Col([
            html.H1("Optimisation avec un chimiste dans la boucle", className="mb-2 mt-4",
                    style={"color": BLEU, "fontWeight": "bold"}),
            html.Hr(style={"borderTop": "3px solid %s" % BLEU, "width": "100px"}),
        ])),

        # --- identity ---------------------------------------------------------
        dbc.Card(dbc.CardBody([
            html.H5("Qui êtes-vous ?", style={"color": BLEU}),
            dbc.Row([
                dbc.Col([dbc.Label("Nom ou initiales", className="fw-bold small"),
                         dbc.Input(id="hl-nom", placeholder="ex. MC")], md=4),
                dbc.Col([dbc.Label("Domaine", className="fw-bold small"),
                         dbc.Input(id="hl-domaine",
                                   placeholder="catalyse, flux, procédés...")], md=5),
                dbc.Col([dbc.Label(" ", className="small"),
                         dbc.Button("Commencer", id="hl-commencer", color="primary",
                                    className="w-100")], md=3),
            ]),
            html.Div("Vos réponses sont enregistrées sous ce nom. Utilisez toujours le "
                     "même pour reprendre une campagne en cours.",
                     className="text-muted small mt-2"),
        ]), className="mb-3", style={"borderRadius": "12px"}),

        html.Div(id="hl-campagnes"),        # the list of campaigns, once named
        html.Div(id="hl-vue"),              # the running campaign
        dcc.Store(id="hl-session"),         # {chemist, domaine, benchmark, seed}
        dcc.Store(id="hl-tick", data=0),
        dcc.Interval(id="hl-interval", interval=900, disabled=True),
    ], style={"maxWidth": "68rem", "margin": "0 auto", "padding": "0 1rem 4rem"})


def campaign_list(chemist, domaine):
    """The three campaigns a chemist is given, with what is done."""
    items = live.campaigns_for(chemist)
    if not items:
        return dbc.Alert("Aucune campagne disponible pour l'instant.", color="warning")
    boutons = []
    for name, seed, done in items:
        pres = live.presentation(name)
        boutons.append(dbc.ListGroupItem([
            html.Div([
                html.B(pres["titre"]),
                html.Span(" — campagne %d" % seed, className="text-muted"),
            ]),
            dbc.Badge("terminée", color="success", className="me-2") if done
            else dbc.Button("Ouvrir", id={"type": "hl-ouvrir", "b": name, "s": seed},
                            size="sm", color="primary", outline=True),
        ], className="d-flex justify-content-between align-items-center"))
    return dbc.Card(dbc.CardBody([
        html.H5("Vos campagnes", style={"color": BLEU}),
        html.P("Trois réactions, une campagne chacune. Faites-les dans l'ordre qui vous "
               "convient ; chacune prend dix à quinze minutes.", className="small"),
        dbc.ListGroup(boutons, flush=True),
    ]), className="mb-3", style={"borderRadius": "12px"})


# --- the campaign view --------------------------------------------------------
def _kpi(icone, valeur, titre, couleur):
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.I(className="bi %s" % icone, style={"fontSize": "1.4rem", "color": couleur}),
        html.H4(valeur, className="mb-0 mt-1", style={"fontWeight": 700}),
        html.P(titre, className="text-muted mb-0 small"),
    ], className="text-center"), style={"borderRadius": "12px"}), md=3, className="mb-2")


def _table(c):
    keys = c.benchmark.parameter_keys
    objs = c.benchmark.objectives
    head = [html.Th("#"), html.Th("")]
    head += [html.Th(c.pres["params"].get(k, (k, ""))[0]
                     + ((" (%s)" % c.pres["params"][k][1]) if c.pres["params"].get(k, ("", ""))[1] else ""))
             for k in keys]
    head += [html.Th(c.pres["objectives"].get(o, (o, "", ""))[0]
                     + ((" (%s)" % c.pres["objectives"][o][1]) if c.pres["objectives"].get(o, ("", "", ""))[1] else ""))
             for o in objs]
    rows = []
    for r in c.experiments:
        badge = {"lhs": ("départ", "secondary"), "bo": ("algorithme", "info"),
                 "chemist": ("vous", "danger")}[r["phase"]]
        cells = [html.Td(r["experiment"]),
                 html.Td(dbc.Badge(badge[0], color=badge[1], className="small"))]
        cells += [html.Td(live.label(c.benchmark, k, r[k])) for k in keys]
        cells += [html.Td(live.french(r[o], 4), style={"textAlign": "right"}) for o in objs]
        rows.append(html.Tr(cells))
    return html.Div(dbc.Table([html.Thead(html.Tr(head)), html.Tbody(rows)],
                              size="sm", hover=True, responsive=True),
                    style={"maxHeight": "22rem", "overflowY": "auto"})


def _scatter(c):
    """The objectives against each other, best compromises outlined."""
    objs = c.benchmark.objectives
    o1, o2 = objs[0], objs[1] if len(objs) > 1 else objs[0]
    t1 = c.pres["objectives"].get(o1, (o1, "", "max"))
    t2 = c.pres["objectives"].get(o2, (o2, "", "max"))
    fig = go.Figure()
    for phase, nom, couleur, symbole in (("lhs", "départ", GRIS, "circle"),
                                          ("bo", "algorithme", BLEU, "circle"),
                                          ("chemist", "vous", ROUGE, "star")):
        pts = [r for r in c.experiments if r["phase"] == phase]
        if not pts:
            continue
        fig.add_trace(go.Scatter(
            x=[r[o1] for r in pts], y=[r[o2] for r in pts], mode="markers", name=nom,
            marker={"color": couleur, "size": 11 if phase == "chemist" else 8,
                    "symbol": symbole, "line": {"width": 0.5, "color": "white"}},
            text=["essai %d" % r["experiment"] for r in pts]))
    # outline the current best compromises, without naming them a front
    import numpy as np
    from hitl_bench import metrics
    raw = np.array([[r[o] for o in objs] for r in c.experiments], dtype=float)
    sign = np.array([1.0 if c.pres["objectives"].get(o, (o, "", "max"))[2] == "max"
                     else -1.0 for o in objs])
    mask = metrics.pareto_mask(raw * sign)
    best = sorted([c.experiments[i] for i in np.flatnonzero(mask)], key=lambda r: r[o1])
    fig.add_trace(go.Scatter(
        x=[r[o1] for r in best], y=[r[o2] for r in best], mode="lines+markers",
        name="meilleurs compromis", line={"color": VERT, "width": 1.5, "dash": "dot"},
        marker={"color": VERT, "size": 12, "symbol": "circle-open", "line": {"width": 2}}))
    fig.update_layout(
        xaxis_title="%s%s" % (t1[0], (" (%s)" % t1[1]) if t1[1] else ""),
        yaxis_title="%s%s" % (t2[0], (" (%s)" % t2[1]) if t2[1] else ""),
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
                                 name="meilleur %s" % t[0].lower(), line={"width": 2}))
    fig.add_vline(x=c.n_init + 0.5, line={"color": GRIS, "dash": "dot", "width": 1})
    for d in c.state["decisions"]:
        if d["choice"] == "chemist":
            fig.add_vline(x=d["at_experiment"] + 1, line={"color": ROUGE, "width": 1.2})
    fig.update_layout(xaxis_title="expérience", margin={"l": 50, "r": 10, "t": 10, "b": 45},
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
        dbc.Label(c.pres["params"].get(k, (k, ""))[0]
                  + ((" (%s)" % c.pres["params"][k][1]) if c.pres["params"].get(k, ("", ""))[1] else ""),
                  className="fw-bold small"),
        dcc.Dropdown(id={"type": "hl-param", "cle": k},
                     options=[{"label": n, "value": n} for n in live.levels(c.benchmark, k)],
                     placeholder=A_CHOISIR, clearable=True),
    ], md=4, className="mb-2") for k in keys]

    return dbc.Card(dbc.CardBody([
        html.H5([html.I(className="bi bi-pause-circle me-2"),
                 "La campagne marque une pause à l'essai %d" % alert["experiment"]],
                style={"color": ROUGE}),
        html.P("L'algorithme progresse nettement moins vite qu'il ne l'a fait jusqu'ici. "
               "C'est à vous de décider de la suite.", className="mb-3"),
        dbc.Label("Que faites-vous ?", className="fw-bold"),
        dbc.RadioItems(id="hl-choix", value=None, className="mb-2", options=[
            {"label": "Laisser l'algorithme continuer — son prochain essai serait : %s"
                      % prop_txt, "value": "optimiser"},
            {"label": "Proposer moi-même le prochain essai", "value": "chemist"},
            {"label": "Arrêter la campagne ici", "value": "stop"},
        ]),
        html.Div(id="hl-proposition", style={"display": "none"}, children=[
            dbc.Card(dbc.CardBody([html.P(html.B("Vos conditions"), className="mb-2"),
                                   dbc.Row(menus)]), className="border-danger mb-2"),
        ]),
        dbc.Label("Pourquoi ?", className="fw-bold"),
        dbc.Textarea(id="hl-pourquoi", rows=2, className="mb-2",
                     placeholder="Une phrase suffit. Le raisonnement compte autant que le choix."),
        dbc.Button("Valider", id="hl-valider", color="danger"),
        html.Div(id="hl-retour", className="mt-2"),
    ]), className="mb-3", style={"borderRadius": "12px", "border": "2px solid %s" % ROUGE})


def campaign_view(c):
    """The whole campaign screen, rebuilt on every tick."""
    n_bo = sum(1 for r in c.experiments if r["phase"] == "bo")
    n_you = sum(1 for r in c.experiments if r["phase"] == "chemist")
    objs = c.benchmark.objectives
    o1 = c.pres["objectives"].get(objs[0], (objs[0], "", "max"))
    vals = [r[objs[0]] for r in c.experiments]
    best1 = (max(vals) if o1[2] == "max" else min(vals)) if vals else 0

    if c.finished:
        statut = dbc.Alert([html.B("Campagne terminée. "),
                            "Merci — vos %d décisions sont enregistrées." % len(c.state["decisions"]),
                            html.Br(), html.Span("Vous pouvez ouvrir la campagne suivante "
                                                 "dans la liste ci-dessus.", className="small")],
                           color="success")
        commandes = html.Div()
    elif c.waiting:
        statut = html.Div()
        commandes = _alert_panel(c)
    elif c.n_done == c.n_init:
        statut = dbc.Alert([html.B("Voici les %d essais de départ. " % c.n_init),
                            "Ils ont été tirés au hasard pour couvrir le domaine, pas "
                            "choisis par l'algorithme. Lancez l'optimisation quand vous "
                            "les avez regardés."], color="light", className="border")
        commandes = dbc.Button([html.I(className="bi bi-play-fill me-1"),
                                "Lancer l'optimisation"], id="hl-lancer", color="primary",
                               size="lg", className="mb-3")
    else:
        statut = dbc.Alert([dbc.Spinner(size="sm", color="primary"),
                            html.Span("  L'algorithme choisit et teste les essais un par un… "
                                      "(%d / %d)" % (c.n_done, c.budget))],
                           color="light", className="border")
        commandes = html.Div()

    return html.Div([
        html.H3(c.pres["titre"], style={"color": BLEU}, className="mt-2"),
        html.P(c.pres["intro"]),
        dbc.Alert(c.pres["reserve"], color="secondary", className="small py-2"),
        dbc.Row([
            _kpi("bi-clipboard-data", "%d / %d" % (c.n_done, c.budget), "essais", "#6366f1"),
            _kpi("bi-cpu", str(n_bo), "choisis par l'algorithme", BLEU),
            _kpi("bi-person", str(n_you), "choisis par vous", ROUGE),
            _kpi("bi-trophy", live.french(best1, 3) + (" " + o1[1] if o1[1] else ""),
                 "meilleur %s" % o1[0].lower(), VERT),
        ]),
        statut, commandes,
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Les deux objectifs", className="text-muted"),
                dcc.Graph(figure=_scatter(c), config={"displayModeBar": False})]),
                style={"borderRadius": "12px"}), md=6, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Progression", className="text-muted"),
                dcc.Graph(figure=_progress(c), config={"displayModeBar": False})]),
                style={"borderRadius": "12px"}), md=6, className="mb-3"),
        ]),
        dbc.Card(dbc.CardBody([html.H6("Tous les essais", className="text-muted"),
                               _table(c)]), style={"borderRadius": "12px"}),
    ])

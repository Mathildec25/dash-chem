# -*- coding: utf-8 -*-
"""Layout for the Chemist input page.

A chemist is shown one campaign stopped mid-flight and asked what to do next.
Everything on this page is driven by a checkpoint file written by
hitl_bench/scripts/make_checkpoints.py, so adding a reaction or a campaign means
dropping a JSON in, never editing this file.

Three rules the page follows, each of which is a decision rather than a style:

- **No optimiser vocabulary.** No hypervolume, no acquisition function, no
  Pareto front. A participant who has to learn what those mean before answering
  is being tested on Bayesian optimisation, not on chemistry.
- **Nothing is pre-selected.** Every choice starts empty. A dropdown sitting on
  its first alphabetical value looks like an answer and would be recorded as
  one, and a campaign nobody thought about would enter the study as a
  suggestion.
- **The expected answer is not on the page.** It lives in a separate file that
  is never served here.
"""

import json
import os

import dash_bootstrap_components as dbc
from dash import dcc, html

BLEU = "#219ebc"
CHECKPOINTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "hitl_bench", "forms", "checkpoints")
REPONSES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "hitl_bench", "forms", "reponses")

A_CHOISIR = "— à choisir —"


def available_checkpoints():
    """Every checkpoint on disk, newest reaction first, as dropdown options."""
    if not os.path.isdir(CHECKPOINTS):
        return []
    options = []
    for name in sorted(os.listdir(CHECKPOINTS)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(CHECKPOINTS, name), encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception:
            continue
        options.append({
            "label": "%s — campagne %d, arrêtée à l'essai %d"
                     % (payload["titre"], payload["seed"], payload["stop_at"]),
            "value": payload["id"],
        })
    return options


def load_checkpoint(identifier):
    path = os.path.join(CHECKPOINTS, identifier + ".json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


# --- pieces of the page ----------------------------------------------------
def _experiments_table(payload):
    """The campaign as a chemist reads one: named reagents, real units, in order.

    A bar on the first objective, because a column of numbers hides a plateau
    that a chemist would spot instantly on a shape.
    """
    colonnes = [v["cle"] for v in payload["variables"]]
    objectifs = [o["cle"] for o in payload["objectifs"]]
    premier = objectifs[0]
    valeurs = [abs(float(str(r[premier]).replace(",", "."))) for r in payload["essais"]]
    echelle = max(valeurs) or 1.0

    entete = [html.Th("#")]
    entete += [html.Th(v["titre"] + (" (%s)" % v["unite"] if v["unite"] else ""))
               for v in payload["variables"]]
    entete += [html.Th(o["titre"] + (" (%s)" % o["unite"] if o["unite"] else ""))
               for o in payload["objectifs"]]
    entete += [html.Th("")]

    lignes = []
    for r, valeur in zip(payload["essais"], valeurs):
        cellules = [html.Td(r["n"], style={"textAlign": "right"})]
        cellules += [html.Td(r[c]) for c in colonnes]
        cellules += [html.Td(r[o], style={"textAlign": "right"}) for o in objectifs]
        cellules.append(html.Td(html.Div(style={
            "height": "0.55rem", "borderRadius": "2px", "background": BLEU,
            "width": "%.1f%%" % (100 * valeur / echelle), "minWidth": "2px"}),
            style={"width": "14%"}))
        style = {"background": "#f4f7f9"} if r["phase"] == "lhs" else {}
        lignes.append(html.Tr(cellules, style=style))

    return dbc.Card(dbc.CardBody([
        html.P([html.B("%d essais faits" % len(payload["essais"])),
                " sur %d prévus. Les %d premiers, sur fond gris, sont le tirage "
                "de départ : ils ont été choisis au hasard pour couvrir le domaine, "
                "pas par l'algorithme."
                % (payload["budget"], payload["n_init"])],
               className="mb-2"),
        html.Div(dbc.Table([html.Thead(html.Tr(entete)), html.Tbody(lignes)],
                           bordered=False, hover=True, size="sm", responsive=True),
                 style={"maxHeight": "26rem", "overflowY": "auto"}),
    ]), className="mb-3")


def _proposal_fields(payload):
    """One dropdown per variable, built from the grid so any answer is evaluable."""
    champs = []
    for v in payload["variables"]:
        champs.append(dbc.Col([
            dbc.Label(v["titre"] + (" (%s)" % v["unite"] if v["unite"] else ""),
                      className="fw-bold small"),
            dcc.Dropdown(id={"type": "ci-param", "cle": v["cle"]},
                         options=[{"label": n, "value": n} for n in v["niveaux"]],
                         placeholder=A_CHOISIR, clearable=True),
        ], md=4, className="mb-2"))
    return dbc.Row(champs)


def create_chemist_input_layout():
    options = available_checkpoints()
    return dbc.Container([
        dbc.Row(dbc.Col([
            html.H1("Votre avis de chimiste", className="mb-2 mt-4",
                    style={"color": BLEU, "fontWeight": "bold"}),
            html.Hr(style={"borderTop": "3px solid %s" % BLEU, "width": "100px"}),
        ])),

        dbc.Alert([
            html.P([html.B("Il n'y a pas de bonne réponse attendue."),
                    " Ce qui nous intéresse est votre raisonnement de chimiste, pas "
                    "de deviner ce que l'algorithme ferait."], className="mb-1"),
            html.P("Un montage automatisé teste des conditions une par une. Après "
                   "chaque essai, un programme choisit le suivant à partir de ce "
                   "qu'il a déjà vu. Il arrive qu'il s'enferme dans une zone qu'il "
                   "croit bonne. On cherche à savoir si un chimiste, à qui on montre "
                   "la campagne en cours, sait la remettre sur les rails.",
                   className="mb-0 small"),
        ], color="light", className="border"),

        dbc.Row(dbc.Col([
            dbc.Label("Quelle campagne examinez-vous ?", className="fw-bold"),
            dcc.Dropdown(id="ci-checkpoint", options=options,
                         placeholder="Choisissez la campagne qu'on vous a indiquée",
                         clearable=False),
        ], md=8), className="mb-4"),

        html.Div(id="ci-contenu"),
        dcc.Store(id="ci-payload"),
    ], fluid=False)


def checkpoint_block(payload):
    """The whole questionnaire for one checkpoint, rebuilt when it is chosen."""
    variables = html.Ul([
        html.Li([html.B(v["titre"]), " — ",
                 ", ".join(v["niveaux"]) if len(v["niveaux"]) <= 8
                 else "%s à %s, %d valeurs" % (v["niveaux"][0], v["niveaux"][-1],
                                               len(v["niveaux"]))])
        for v in payload["variables"]])
    objectifs = html.Ul([
        html.Li([html.B(o["titre"]), " — à ", o["sens"]]) for o in payload["objectifs"]])

    return html.Div([
        html.H3(payload["titre"], style={"color": BLEU}, className="mt-2"),
        *[html.P(p) for p in payload["intro"]],
        dbc.Alert(payload["reserve"], color="secondary", className="small py-2"),

        dbc.Row([
            dbc.Col([html.P(html.B("Ce que l'on peut régler")), variables], md=7),
            dbc.Col([html.P(html.B("Ce qui est mesuré")), objectifs], md=5),
        ], className="mt-2"),

        html.H4("Où en est la campagne", style={"color": BLEU}, className="mt-4"),
        _experiments_table(payload),

        html.H4("Vos réponses", style={"color": BLEU}, className="mt-4"),

        dbc.Label("1. Que pensez-vous de cette campagne ?", className="fw-bold"),
        html.Div("Va-t-elle dans la bonne direction ? Quelque chose vous gêne ?",
                 className="text-muted small mb-1"),
        dbc.Textarea(id="ci-avis", rows=3, className="mb-3"),

        dbc.Label("2. Que faut-il faire maintenant ?", className="fw-bold"),
        dbc.RadioItems(id="ci-decision", className="mb-2", value=None, options=[
            {"label": "Je propose un essai précis", "value": "propose"},
            {"label": "Laisser le programme continuer", "value": "continuer"},
            {"label": "Arrêter la campagne, il n'y a plus grand-chose à espérer",
             "value": "arreter"},
        ]),

        html.Div(id="ci-proposition", style={"display": "none"}, children=[
            dbc.Card(dbc.CardBody([
                html.P(html.B("Les conditions que vous proposez"), className="mb-2"),
                _proposal_fields(payload),
                dbc.Label("Pourquoi ces conditions ?", className="fw-bold mt-2"),
                html.Div("Le raisonnement nous intéresse autant que le point choisi.",
                         className="text-muted small mb-1"),
                dbc.Textarea(id="ci-pourquoi", rows=3),
            ]), className="mb-3 border-primary"),
        ]),

        dbc.Label("3. Aviez-vous reconnu cette réaction ?", className="fw-bold"),
        html.Div("Question de méthode, pas un examen : certaines de ces chimies sont "
                 "publiées, et il faut pouvoir distinguer un raisonnement d'un "
                 "souvenir. Répondre oui ne disqualifie rien.",
                 className="text-muted small mb-1"),
        dbc.RadioItems(id="ci-connue", className="mb-3", value=None, options=[
            {"label": "Non, je raisonne sur ce que je vois", "value": "non"},
            {"label": "Ça me dit quelque chose", "value": "vaguement"},
            {"label": "Oui, je connais son résultat publié", "value": "oui"},
        ]),

        dbc.Row([
            dbc.Col([dbc.Label("À quel point êtes-vous sûr ?", className="fw-bold"),
                     dcc.Dropdown(id="ci-surete", placeholder=A_CHOISIR, options=[
                         {"label": t, "value": t} for t in
                         ("pas du tout", "un peu", "moyennement", "assez",
                          "tout à fait")])], md=4),
            dbc.Col([dbc.Label("Vos initiales", className="fw-bold"),
                     dbc.Input(id="ci-qui", placeholder="ex. MC")], md=4),
            dbc.Col([dbc.Label("Votre domaine", className="fw-bold"),
                     dbc.Input(id="ci-domaine",
                               placeholder="catalyse, flux, procédés...")], md=4),
        ], className="mb-3"),

        dbc.Button("Enregistrer ma réponse", id="ci-envoyer", color="primary",
                   className="mt-2"),
        html.Div(id="ci-retour", className="mt-3"),
    ])

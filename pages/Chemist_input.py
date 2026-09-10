# -*- coding: utf-8 -*-
"""Chemist input page: show one campaign mid-flight, collect one suggestion.

The page itself is in components/layout_chemist_input.py; the callbacks live
here. A response is written as a JSON file under hitl_bench/forms/reponses, one
per answer, named after the checkpoint and the participant - so two chemists
answering the same checkpoint never overwrite each other, and collecting the
study's data is copying a directory.
"""

import datetime
import json
import os
import re

import dash
import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback, ctx, html, no_update

from components.layout_chemist_input import (
    REPONSES, checkpoint_block, create_chemist_input_layout, load_checkpoint,
)

dash.register_page(__name__, name="Chemist input", path="/chemist-input", order=7)

layout = create_chemist_input_layout()


@callback(
    Output("ci-contenu", "children"),
    Output("ci-payload", "data"),
    Input("ci-checkpoint", "value"),
    prevent_initial_call=True,
)
def afficher_checkpoint(identifier):
    if not identifier:
        return no_update, no_update
    payload = load_checkpoint(identifier)
    if payload is None:
        return dbc.Alert("Campagne introuvable.", color="danger"), None
    return checkpoint_block(payload), payload


@callback(
    Output("ci-proposition", "style"),
    Input("ci-decision", "value"),
    prevent_initial_call=True,
)
def basculer_proposition(decision):
    """The conditions only make sense if a suggestion is actually being made."""
    return {"display": "block"} if decision == "propose" else {"display": "none"}


def _nom_de_fichier(identifier, qui):
    propre = re.sub(r"[^A-Za-z0-9_-]", "", (qui or "anonyme"))[:20] or "anonyme"
    horodatage = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return "%s__%s__%s.json" % (identifier, propre, horodatage)


@callback(
    Output("ci-retour", "children"),
    Input("ci-envoyer", "n_clicks"),
    State("ci-payload", "data"),
    State("ci-avis", "value"),
    State("ci-decision", "value"),
    State({"type": "ci-param", "cle": ALL}, "value"),
    State({"type": "ci-param", "cle": ALL}, "id"),
    State("ci-pourquoi", "value"),
    State("ci-connue", "value"),
    State("ci-surete", "value"),
    State("ci-qui", "value"),
    State("ci-domaine", "value"),
    prevent_initial_call=True,
)
def enregistrer(n_clicks, payload, avis, decision, valeurs, identifiants,
                pourquoi, connue, surete, qui, domaine):
    if not n_clicks or not payload:
        return no_update

    # Rien n'est invente a la place du participant : une decision non prise reste
    # non prise, et une condition non choisie n'entre pas dans la proposition.
    if decision is None:
        return dbc.Alert("Merci de répondre à la question 2 avant d'enregistrer.",
                         color="warning")

    proposition = {}
    if decision == "propose":
        proposition = {i["cle"]: v for i, v in zip(identifiants, valeurs) if v}
        manquantes = [i["cle"] for i, v in zip(identifiants, valeurs) if not v]
        if manquantes:
            return dbc.Alert(
                "Il manque %d condition(s) pour que votre essai soit réalisable. "
                "Complétez-les, ou choisissez une autre option à la question 2."
                % len(manquantes), color="warning")

    reponse = {
        "checkpoint": payload["id"],
        "benchmark": payload["benchmark"],
        "seed": payload["seed"],
        "stop_at": payload["stop_at"],
        "date": datetime.datetime.now().isoformat(timespec="seconds"),
        "qui": (qui or "").strip() or "anonyme",
        "domaine": (domaine or "").strip(),
        "avis": (avis or "").strip(),
        "decision": decision,
        "proposition": proposition,
        "pourquoi": (pourquoi or "").strip(),
        "reaction_connue": connue,
        "surete": surete,
    }

    os.makedirs(REPONSES, exist_ok=True)
    chemin = os.path.join(REPONSES, _nom_de_fichier(payload["id"], qui))
    with open(chemin, "w", encoding="utf-8") as handle:
        json.dump(reponse, handle, ensure_ascii=False, indent=1)

    return dbc.Alert([
        html.B("Merci, votre réponse est enregistrée."),
        html.Br(),
        html.Span("Vous pouvez passer à la campagne suivante avec le menu du haut.",
                  className="small"),
    ], color="success")

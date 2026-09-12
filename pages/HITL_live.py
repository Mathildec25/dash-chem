# -*- coding: utf-8 -*-
"""Live HITL page: the callbacks. The screen is drawn by components/layout_hitl_live.py,
the campaign is driven by hitl_bench/live.py.

The rhythm of the page is an interval. When the chemist launches the campaign,
the interval starts ticking; every tick runs one optimiser experiment and
redraws. When the trigger fires, the engine sets a pending alert, the interval
stops, and the alert panel waits. The chemist's answer clears the alert and the
interval resumes. Replayed experiments take milliseconds, so the ticks are what
give the campaign a visible pace; a live experiment takes several seconds and
the tick simply waits for it.

Nothing is inferred from silence. A tick with no pending campaign does nothing,
a validation with no choice is refused, and an imposed point with a condition
left blank is refused with the count of what is missing.
"""

import dash
import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback, ctx, html, no_update

from components.layout_hitl_live import (
    A_CHOISIR, campaign_list, campaign_view, create_hitl_live_layout,
)
from hitl_bench import live

dash.register_page(__name__, name="HITL live", path="/hitl-live", order=8)

layout = create_hitl_live_layout()


def _open(session):
    if not session or not session.get("benchmark"):
        return None
    return live.LiveCampaign(session["chemist"], session["benchmark"],
                             session["seed"], session.get("domaine", ""))


# --- identity -> list of campaigns -------------------------------------------
@callback(
    Output("hl-campagnes", "children"),
    Output("hl-session", "data"),
    Input("hl-commencer", "n_clicks"),
    Input({"type": "hl-ouvrir", "b": ALL, "s": ALL}, "n_clicks"),
    State("hl-nom", "value"),
    State("hl-domaine", "value"),
    State("hl-session", "data"),
    prevent_initial_call=True,
)
def identite(n_clicks, ouvrir, nom, domaine, session):
    trigger = ctx.triggered_id
    if trigger == "hl-commencer":
        if not (nom or "").strip():
            return dbc.Alert("Indiquez votre nom ou vos initiales.", color="warning"), no_update
        session = {"chemist": live.slug(nom), "domaine": (domaine or "").strip(),
                   "benchmark": None, "seed": None}
        return campaign_list(session["chemist"], session["domaine"]), session
    if isinstance(trigger, dict) and trigger.get("type") == "hl-ouvrir":
        if not any(ouvrir or []):
            return no_update, no_update
        session = dict(session or {})
        session["benchmark"], session["seed"] = trigger["b"], trigger["s"]
        return campaign_list(session["chemist"], session.get("domaine", "")), session
    return no_update, no_update


# --- drawing the campaign, and ticking it --------------------------------------
@callback(
    Output("hl-vue", "children"),
    Output("hl-interval", "disabled"),
    Input("hl-session", "data"),
    Input("hl-interval", "n_intervals"),
    Input("hl-lancer", "n_clicks"),
    prevent_initial_call=True,
)
def avancer(session, n_intervals, lancer):
    campaign = _open(session)
    if campaign is None:
        return html.Div(), True

    trigger = ctx.triggered_id
    if trigger == "hl-lancer":
        # The chemist has looked at the initial design and starts the optimiser.
        campaign.step()
        return campaign_view(campaign), campaign.waiting or campaign.finished

    if trigger == "hl-interval":
        if campaign.waiting or campaign.finished:
            return campaign_view(campaign), True
        campaign.step()
        return campaign_view(campaign), campaign.waiting or campaign.finished

    # session changed: just draw where the campaign stands, ticking if it was mid-run
    en_cours = (campaign.n_done > campaign.n_init and not campaign.waiting
                and not campaign.finished)
    return campaign_view(campaign), not en_cours


@callback(
    Output("hl-proposition", "style"),
    Input("hl-choix", "value"),
    prevent_initial_call=True,
)
def montrer_menus(choix):
    return {"display": "block"} if choix == "chemist" else {"display": "none"}


# --- the chemist's answer at an alert --------------------------------------------
@callback(
    Output("hl-retour", "children"),
    Output("hl-tick", "data"),
    Input("hl-valider", "n_clicks"),
    State("hl-session", "data"),
    State("hl-choix", "value"),
    State({"type": "hl-param", "cle": ALL}, "value"),
    State({"type": "hl-param", "cle": ALL}, "id"),
    State("hl-pourquoi", "value"),
    State("hl-tick", "data"),
    prevent_initial_call=True,
)
def repondre(n_clicks, session, choix, valeurs, identifiants, pourquoi, tick):
    if not n_clicks:
        return no_update, no_update
    campaign = _open(session)
    if campaign is None or not campaign.waiting:
        return dbc.Alert("Aucune pause en attente.", color="secondary"), no_update
    if choix is None:
        return dbc.Alert("Choisissez une des trois options.", color="warning"), no_update

    why = (pourquoi or "").strip()
    if choix == "stop":
        campaign.stop(why=why)
    elif choix == "optimiser":
        campaign.take_proposal(why=why)
    else:
        point = {i["cle"]: v for i, v in zip(identifiants, valeurs) if v and v != A_CHOISIR}
        manquantes = [i["cle"] for i in identifiants if i["cle"] not in point]
        if manquantes:
            return dbc.Alert("Il manque %d condition(s) : votre essai n'est pas réalisable "
                             "tel quel." % len(manquantes), color="warning"), no_update
        try:
            campaign.impose(point, why=why)
        except KeyError as exc:
            return dbc.Alert("Conditions non reconnues : %s" % exc, color="danger"), no_update
    # bump the tick store so the drawing callback resumes
    return dbc.Alert("Enregistré.", color="success", className="py-1"), (tick or 0) + 1


@callback(
    Output("hl-session", "data", allow_duplicate=True),
    Input("hl-tick", "data"),
    State("hl-session", "data"),
    prevent_initial_call=True,
)
def reprendre(tick, session):
    """After an answer, re-emit the session so the campaign redraws and resumes."""
    if not tick or not session:
        return no_update
    return dict(session, tick=tick)

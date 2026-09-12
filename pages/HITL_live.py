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
a submission with no choice is refused, and an imposed point with a condition
left blank is refused with the count of what is missing.
"""

import threading

import dash
import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback, ctx, html, no_update

from components.layout_hitl_live import (
    TO_CHOOSE, campaign_list, campaign_view, create_hitl_live_layout,
)
from hitl_bench import live

dash.register_page(__name__, name="HITL live", path="/hitl-live", order=8)

layout = create_hitl_live_layout()


def _open(session):
    if not session or not session.get("benchmark"):
        return None
    return live.LiveCampaign(session["chemist"], session["benchmark"],
                             session["seed"], session.get("field", ""))


# One lock per campaign, so that two ticks never step the same campaign at once.
_locks, _locks_guard = {}, threading.Lock()


def _lock_for(session):
    key = ((session or {}).get("chemist"), (session or {}).get("benchmark"),
           (session or {}).get("seed"))
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


# --- identity -> list of campaigns -------------------------------------------
@callback(
    Output("hl-campaigns", "children"),
    Output("hl-session", "data"),
    Input("hl-start", "n_clicks"),
    Input({"type": "hl-open", "b": ALL, "s": ALL}, "n_clicks"),
    State("hl-name", "value"),
    State("hl-field", "value"),
    State("hl-session", "data"),
    prevent_initial_call=True,
)
def identify(n_clicks, opened, name, field, session):
    trigger = ctx.triggered_id
    if trigger == "hl-start":
        if not (name or "").strip():
            return dbc.Alert("Enter your name or initials.", color="warning"), no_update
        session = {"chemist": live.slug(name), "field": (field or "").strip(),
                   "benchmark": None, "seed": None}
        return campaign_list(session["chemist"], session["field"]), session
    if isinstance(trigger, dict) and trigger.get("type") == "hl-open":
        if not any(opened or []):
            return no_update, no_update
        session = dict(session or {})
        session["benchmark"], session["seed"] = trigger["b"], trigger["s"]
        return campaign_list(session["chemist"], session.get("field", "")), session
    return no_update, no_update


# --- drawing the campaign, and ticking it --------------------------------------
@callback(
    Output("hl-view", "children"),
    Output("hl-interval", "disabled"),
    Input("hl-session", "data"),
    Input("hl-interval", "n_intervals"),
    Input({"type": "hl-launch", "b": ALL, "s": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def advance(session, n_intervals, launch):
    trigger = ctx.triggered_id
    launched = isinstance(trigger, dict) and trigger.get("type") == "hl-launch"
    if launched and not any(launch or []):
        return no_update, no_update           # the button appeared, nobody clicked it
    if launched or trigger == "hl-interval":
        # A live experiment takes longer than one tick. If the previous tick is
        # still running its step, this one does nothing rather than run a second
        # step on the same state: two concurrent steps would each load the
        # campaign, each append an experiment, and the last save would win.
        lock = _lock_for(session)
        if not lock.acquire(blocking=False):
            return no_update, no_update
        try:
            campaign = _open(session)
            if campaign is None:
                return html.Div(), True
            if not launched and (campaign.waiting or campaign.finished):
                return campaign_view(campaign), True
            campaign.step()
            return campaign_view(campaign), campaign.waiting or campaign.finished
        finally:
            lock.release()

    campaign = _open(session)
    if campaign is None:
        return html.Div(), True
    # session changed: just draw where the campaign stands, ticking if it was mid-run
    running = (campaign.n_done > campaign.n_init and not campaign.waiting
               and not campaign.finished)
    return campaign_view(campaign), not running


@callback(
    Output("hl-proposal", "style"),
    Input("hl-choice", "value"),
    prevent_initial_call=True,
)
def show_menus(choice):
    return {"display": "block"} if choice == "chemist" else {"display": "none"}


# --- the chemist's answer at an alert --------------------------------------------
@callback(
    Output("hl-feedback", "children"),
    Output("hl-tick", "data"),
    Input("hl-submit", "n_clicks"),
    State("hl-session", "data"),
    State("hl-choice", "value"),
    State({"type": "hl-param", "key": ALL}, "value"),
    State({"type": "hl-param", "key": ALL}, "id"),
    State("hl-why", "value"),
    State("hl-tick", "data"),
    prevent_initial_call=True,
)
def answer(n_clicks, session, choice, values, identifiers, why, tick):
    if not n_clicks:
        return no_update, no_update
    campaign = _open(session)
    if campaign is None or not campaign.waiting:
        return dbc.Alert("No pause is pending.", color="secondary"), no_update
    if choice is None:
        return dbc.Alert("Choose one of the three options.", color="warning"), no_update

    why = (why or "").strip()
    if choice == "stop":
        campaign.stop(why=why)
    elif choice == "optimiser":
        campaign.take_proposal(why=why)
    else:
        point = {i["key"]: v for i, v in zip(identifiers, values) if v and v != TO_CHOOSE}
        missing = [i["key"] for i in identifiers if i["key"] not in point]
        if missing:
            return dbc.Alert("%d condition(s) missing: your experiment cannot be run "
                             "as it stands." % len(missing), color="warning"), no_update
        try:
            campaign.impose(point, why=why)
        except KeyError as exc:
            return dbc.Alert("Unrecognised conditions: %s" % exc, color="danger"), no_update
    # bump the tick store so the drawing callback resumes
    return dbc.Alert("Saved.", color="success", className="py-1"), (tick or 0) + 1


@callback(
    Output("hl-session", "data", allow_duplicate=True),
    Input("hl-tick", "data"),
    State("hl-session", "data"),
    prevent_initial_call=True,
)
def resume(tick, session):
    """After an answer, re-emit the session so the campaign redraws and resumes."""
    if not tick or not session:
        return no_update
    return dict(session, tick=tick)

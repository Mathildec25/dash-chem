r"""Draw where a stall trigger would have fired along saved campaigns.

Two figures, written to hitl_bench/figures:

  triggers_detail.png    two campaigns side by side, one that ends trapped and
                         one that ends on the global front, each with its
                         hypervolume curve above and the P* signal below.
  triggers_overview.png  all campaigns as small multiples.

P* compares the campaign's recent pace to its own average pace since the end of
the initial design, so it carries no units and means the same thing on a
reaction topping out at 44% yield and one at 91%. It equals 1 when a campaign
progresses steadily; the trigger fires when it drops below the threshold.

Run from the dash-chem directory; needs nothing but the saved logs:

    cd C:\Users\mathi\REACTO\dash-chem
    set MPLBACKEND=Agg
    .venv\Scripts\python.exe hitl_bench/scripts/plot_triggers.py --threshold 0.10
"""

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --- configuration ---------------------------------------------------------
WINDOW = 3            # experiments in the "recent pace" window
BURN_IN = 13          # no firing before this experiment
EPS = 1e-12
DETAIL = ("ii__no_hitl__seed05", "ii__no_hitl__seed02")

# Slots 1 to 3 of the reference categorical palette, the set documented as
# passing every check under the all-pairs list. Identity never rests on colour
# alone here: each mark also has a distinct shape and a direct label.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE = "#fcfcfb"
INK, INK_SOFT, INK_FAINT = "#0b0b0b", "#52514e", "#8a8880"

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
FIGURES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figures")


def p_star(hv, n_init, experiment):
    """Recent pace divided by the campaign's average pace since the initial design.

    A campaign that has gained nothing at all is the most stalled case there is,
    so it returns 0 rather than dividing by zero.
    """
    i = experiment - 1
    total = hv[i] - hv[n_init - 1]
    if total <= EPS:
        return 0.0
    recent = (hv[i] - hv[i - WINDOW]) / WINDOW
    average = total / (experiment - n_init)
    return recent / average


def load_campaigns():
    campaigns = []
    for path in sorted(glob.glob(os.path.join(RESULTS, "*no_hitl*.json"))):
        log = json.load(open(path, encoding="utf-8"))
        hv = log["curves"]["hypervolume"]
        n_init = log["config"]["n_init"]
        front = log["reference"]["front_ligands"]
        on_front = [r["experiment"] for r in log["experiments"]
                    if r["phase"] == "bo" and r["ligand"] in front]
        campaigns.append({
            "key": os.path.basename(path)[:-5],
            "label": "cas %s, graine %d" % (log["config"]["case"], log["config"]["seed"]),
            "hv": hv,
            "n_init": n_init,
            "signal": {e: p_star(hv, n_init, e) for e in range(BURN_IN, len(hv) + 1)},
            "final": log["analysis"]["hv_final_fraction"] * 100,
            "found": on_front[0] if on_front else None,
            "front": "/".join(front),
        })
    return campaigns


def fires(campaign, threshold):
    return [e for e, v in sorted(campaign["signal"].items()) if v < threshold]


def style(axis):
    axis.set_facecolor(SURFACE)
    axis.grid(True, color=INK_FAINT, alpha=0.22, linewidth=0.6)
    axis.set_axisbelow(True)
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_color(INK_FAINT)
        axis.spines[side].set_linewidth(0.8)
    axis.tick_params(colors=INK_SOFT, labelsize=8, length=3, width=0.8)


def draw_detail(campaigns, threshold):
    chosen = [c for key in DETAIL for c in campaigns if c["key"] == key]
    if len(chosen) < 2:
        chosen = sorted(campaigns, key=lambda c: c["final"])[:1] + \
                 sorted(campaigns, key=lambda c: -c["final"])[:1]

    figure, axes = plt.subplots(2, len(chosen), figsize=(11, 6.4), sharex=True,
                                gridspec_kw={"height_ratios": [1.35, 1]})
    figure.patch.set_facecolor(SURFACE)

    for column, campaign in enumerate(chosen):
        experiments = range(1, len(campaign["hv"]) + 1)
        firing = fires(campaign, threshold)

        top = axes[0][column]
        style(top)
        top.plot(experiments, campaign["hv"], color=BLUE, linewidth=2.0,
                 solid_capstyle="round", zorder=3)
        if campaign["found"]:
            top.axvline(campaign["found"], color=AQUA, linewidth=2.0, alpha=0.85, zorder=2)
            top.annotate("la BO adopte %s" % campaign["front"],
                         xy=(campaign["found"], 0.55),
                         xycoords=("data", "axes fraction"),
                         xytext=(5, 0), textcoords="offset points",
                         color=INK_SOFT, fontsize=8, rotation=90, va="center")
        for e in firing:
            top.axvline(e, color=ORANGE, linewidth=1.0, alpha=0.35, zorder=1)
        if firing:
            top.plot(firing, [campaign["hv"][e - 1] for e in firing], "v",
                     color=ORANGE, markersize=8, markeredgecolor=SURFACE,
                     markeredgewidth=1.2, zorder=4)
        top.set_title("%s  ·  %.1f %% du front global" % (campaign["label"], campaign["final"]),
                      color=INK, fontsize=10.5, pad=9, loc="left")
        if column == 0:
            top.set_ylabel("hypervolume", color=INK_SOFT, fontsize=9)

        bottom = axes[1][column]
        style(bottom)
        points = sorted(campaign["signal"].items())
        bottom.plot([e for e, _ in points], [v for _, v in points],
                    color=BLUE, linewidth=2.0, solid_capstyle="round", zorder=3)
        bottom.axhline(1.0, color=INK_FAINT, linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
        bottom.axhline(threshold, color=ORANGE, linewidth=1.4, linestyle=(0, (4, 3)), zorder=2)
        bottom.annotate("rythme habituel", xy=(len(campaign["hv"]), 1.0),
                        xytext=(-2, 4), textcoords="offset points", ha="right",
                        color=INK_SOFT, fontsize=8)
        bottom.annotate("seuil %.2f" % threshold, xy=(len(campaign["hv"]), threshold),
                        xytext=(-2, 6), textcoords="offset points", ha="right",
                        color=ORANGE, fontsize=8)
        if firing:
            bottom.plot(firing, [campaign["signal"][e] for e in firing], "v",
                        color=ORANGE, markersize=8, markeredgecolor=SURFACE,
                        markeredgewidth=1.2, zorder=4)
        bottom.set_ylim(-0.12, 2.3)
        bottom.set_xlabel("expérience", color=INK_SOFT, fontsize=9)
        if column == 0:
            bottom.set_ylabel("P*  (rythme récent / rythme moyen)", color=INK_SOFT, fontsize=9)

    handles = [
        plt.Line2D([], [], color=BLUE, linewidth=2.0, label="campagne"),
        plt.Line2D([], [], color=ORANGE, marker="v", linestyle="none", markersize=8,
                   label="le trigger se déclenche"),
        plt.Line2D([], [], color=AQUA, linewidth=2.0, label="la BO adopte le bon ligand"),
    ]
    figure.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
                  fontsize=9, labelcolor=INK_SOFT, bbox_to_anchor=(0.5, -0.015))
    figure.suptitle("Où le trigger se déclencherait, sur une campagne piégée et une campagne réussie",
                    color=INK, fontsize=12.5, x=0.012, ha="left", y=0.985)
    figure.tight_layout(rect=(0, 0.045, 1, 0.955))
    path = os.path.join(FIGURES, "triggers_detail.png")
    figure.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(figure)
    return path


def draw_overview(campaigns, threshold):
    ordered = sorted(campaigns, key=lambda c: c["final"])
    columns = 3
    rows = (len(ordered) + columns - 1) // columns
    figure, axes = plt.subplots(rows, columns, figsize=(11, 2.5 * rows),
                               sharex=True, sharey=True)
    figure.patch.set_facecolor(SURFACE)
    flat = axes.ravel() if hasattr(axes, "ravel") else [axes]

    for panel, campaign in zip(flat, ordered):
        style(panel)
        experiments = range(1, len(campaign["hv"]) + 1)
        firing = fires(campaign, threshold)
        panel.plot(experiments, campaign["hv"], color=BLUE, linewidth=1.8,
                   solid_capstyle="round", zorder=3)
        if campaign["found"]:
            panel.axvline(campaign["found"], color=AQUA, linewidth=1.8, alpha=0.85, zorder=2)
        for e in firing:
            panel.axvline(e, color=ORANGE, linewidth=1.0, alpha=0.32, zorder=1)
        if firing:
            panel.plot(firing, [campaign["hv"][e - 1] for e in firing], "v",
                       color=ORANGE, markersize=6, markeredgecolor=SURFACE,
                       markeredgewidth=1.0, zorder=4)
        panel.set_title("%s  ·  %.1f %%  ·  %d déclenchements"
                        % (campaign["label"], campaign["final"], len(firing)),
                        color=INK, fontsize=9, pad=6, loc="left")
    for panel in flat[len(ordered):]:
        panel.set_visible(False)

    handles = [
        plt.Line2D([], [], color=BLUE, linewidth=2.0, label="hypervolume"),
        plt.Line2D([], [], color=ORANGE, marker="v", linestyle="none", markersize=7,
                   label="le trigger se déclenche"),
        plt.Line2D([], [], color=AQUA, linewidth=2.0, label="la BO adopte le bon ligand"),
    ]
    figure.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
                  fontsize=9, labelcolor=INK_SOFT, bbox_to_anchor=(0.5, -0.008))
    figure.suptitle("Les campagnes sans intervention, de la plus piégée à la plus réussie  (seuil %.2f)"
                    % threshold, color=INK, fontsize=12.5, x=0.012, ha="left", y=0.995)
    figure.tight_layout(rect=(0, 0.035, 1, 0.96))
    path = os.path.join(FIGURES, "triggers_overview.png")
    figure.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(figure)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=float, default=0.10)
    args = parser.parse_args()

    os.makedirs(FIGURES, exist_ok=True)
    campaigns = load_campaigns()
    if not campaigns:
        parser.error("no no_hitl campaign in %s" % RESULTS)

    print("%d campagnes, seuil %.2f\n" % (len(campaigns), args.threshold))
    print("%-22s %8s %8s  %s" % ("campagne", "final", "nb", "expériences"))
    for campaign in sorted(campaigns, key=lambda c: c["final"]):
        firing = fires(campaign, args.threshold)
        print("%-22s %7.1f%% %8d  %s"
              % (campaign["label"], campaign["final"], len(firing),
                 " ".join(str(e) for e in firing) if firing else "aucune"))

    for path in (draw_detail(campaigns, args.threshold),
                 draw_overview(campaigns, args.threshold)):
        print("\necrit : %s" % path)


if __name__ == "__main__":
    main()

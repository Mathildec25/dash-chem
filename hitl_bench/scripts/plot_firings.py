# -*- coding: utf-8 -*-
r"""Where the trigger fires along every saved campaign, benchmark by benchmark.

One small multiple per seed: the hypervolume curve as a fraction of the global
front, the experiments at which the trigger would have fired, and the 90% line
that separates a success from a failure under the study's definition.

Two rules this file follows on purpose.

It calls `triggers.firing_times` rather than recomputing the signal. An earlier
plotting script carried its own copy of P*, which is how a figure drifts away
from the trigger it claims to show.

It colours a campaign by its **outcome**, not by its seed. The question a reader
should be able to answer at a glance is not "what did seed 7 do" but "does the
trigger fire on the campaigns that needed help?" - so failures and successes
have to be distinguishable without reading the titles.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/plot_firings.py --benchmarks ii i edbo_ch_arylation
"""

import argparse
import functools
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from hitl_bench import triggers  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")
FIGURES = os.path.join(HERE, "figures")

SUCCESS = 0.90
ECHEC, REUSSITE, ALERTE = "#eb6834", "#2a78d6", "#c1121f"


def load(stem):
    out = []
    for path in sorted(glob.glob(os.path.join(RESULTS, "%s__no_hitl__seed*.json" % stem))):
        with open(path, encoding="utf-8") as handle:
            out.append((os.path.basename(path)[:-5].split("__")[-1], json.load(handle)))
    return out


# Chaque signal vient avec sa valeur, son seuil et son nom d'axe. Le seuil de
# l'original est dix fois plus bas que celui de P*, donc l'echelle verticale ne
# peut pas etre commune : elle est calee sur le seuil du signal trace.
SIGNAUX = {
    # Le seuil vient du trigger lui-meme : le recopier ici, c'est se preparer
    # a tracer un seuil different de celui qui declenche.
    "pace_ratio": (triggers.pace_ratio, triggers.pace_ratio_value,
                   triggers.THRESHOLD, "P*"),
    "original_ratio": (triggers.original_ratio, triggers.original_ratio_value, 0.05,
                       "P (original)"),
}


def draw(stem, campaigns, window, cooldown, suffix="", nom_signal="pace_ratio",
         seuil=None):
    """Deux lignes par campagne : l'hypervolume, puis le signal P* qui le suit.

    P* seul ne dit rien - il faut voir a quel endroit de la courbe il
    s'effondre - donc les deux panneaux partagent l'axe des experiences et
    portent les memes marqueurs de declenchement."""
    fonction, valeur, defaut, etiquette = SIGNAUX[nom_signal]
    SEUIL_P = defaut if seuil is None else seuil
    P_MAX = max(1.0, 4 * SEUIL_P)
    n = len(campaigns)
    cols = min(6, n)
    blocs = (n + cols - 1) // cols
    rows = 2 * blocs
    fig, axes = plt.subplots(rows, cols, figsize=(2.5 * cols, 2.9 * blocs),
                             sharex=True, squeeze=False,
                             gridspec_kw={"height_ratios": [2, 1] * blocs})

    burn_in = None
    for index, (name, log) in enumerate(campaigns):
        bloc, col = index // cols, index % cols
        axis = axes[2 * bloc][col]
        bas = axes[2 * bloc + 1][col]
        records = log["experiments"]
        n_init = log["config"]["n_init"]
        budget = len(records)
        reference = log["reference"]["max_hypervolume"]
        curve = [v / reference for v in log["curves"]["hypervolume"]]
        x = [r["experiment"] for r in records]
        final = curve[-1]
        colour = REUSSITE if final >= SUCCESS else ECHEC

        burn_in = n_init + triggers._window(budget, window)
        axis.axhline(SUCCESS, color="#8b93a1", ls="--", lw=0.9)
        axis.axvline(n_init + 0.5, color="#c9ced6", lw=0.9)
        axis.axvspan(0, burn_in, color="#f2f4f7", zorder=0)   # trigger muet ici
        axis.plot(x, curve, color=colour, lw=1.8)

        signal = functools.partial(fonction, fraction=window, threshold=SEUIL_P)
        fired = triggers.firing_times(signal, records, n_init, budget)
        for rank, experiment in enumerate(fired):
            axis.plot(experiment, curve[experiment - 1], marker="v",
                      ms=9 if rank == 0 else 6, color=ALERTE,
                      mec="white", mew=0.8, zorder=5)

        axis.set_title("%s  %.0f%%%s" % (name, 100 * final,
                                         "" if fired else "  (muet)"),
                       fontsize=9, color="black" if fired else ALERTE)
        axis.set_ylim(0, 1.05)
        axis.set_xlim(0, budget + 1)
        axis.grid(alpha=0.25, lw=0.5)
        axis.tick_params(labelbottom=False)

        # --- P*, lu depuis triggers.py, jamais recalcule ici ---------------
        xs, ps, hauts = [], [], []
        for position in range(len(records)):
            value = valeur(records[: position + 1], budget, window)
            if value is None:
                continue
            xs.append(records[position]["experiment"])
            ps.append(min(value, P_MAX))
            if value > P_MAX:
                hauts.append(records[position]["experiment"])
        bas.axvspan(0, burn_in, color="#f2f4f7", zorder=0)
        bas.axhline(SEUIL_P, color=ALERTE, ls="--", lw=0.9)
        bas.plot(xs, ps, color="#5b6472", lw=1.2)
        bas.fill_between(xs, 0, ps, where=[v < SEUIL_P for v in ps],
                         color=ALERTE, alpha=0.55)
        for experiment in hauts:                      # valeurs ecretees
            bas.plot(experiment, P_MAX, marker="^", ms=3, color="#5b6472")
        for rank, experiment in enumerate(fired):
            bas.axvline(experiment, color=ALERTE, lw=1.2 if rank == 0 else 0.7,
                        alpha=0.7, zorder=1)
        bas.set_ylim(0, P_MAX * 1.05)
        # 0 et 0,10 se chevauchent a cette hauteur de panneau : on ne garde
        # que le seuil et le repere 1, qui sont les deux valeurs a lire.
        bas.set_yticks([SEUIL_P, P_MAX])
        bas.set_yticklabels(["%.2f" % SEUIL_P, "%.1f" % P_MAX], fontsize=7)
        bas.grid(alpha=0.25, lw=0.5)

    for index in range(n, blocs * cols):
        axes[2 * (index // cols)][index % cols].axis("off")
        axes[2 * (index // cols) + 1][index % cols].axis("off")
    for bloc in range(blocs):
        axes[2 * bloc][0].set_ylabel("fraction du front", fontsize=8)
        axes[2 * bloc + 1][0].set_ylabel(etiquette, fontsize=8)
    for c in range(cols):
        axes[rows - 1][c].set_xlabel("expérience")

    # Deux lignes plutot qu'une : sur trois panneaux, un titre d'une ligne
    # deborde la figure et se fait rogner aux deux bouts.
    fig.suptitle("%s — %d campagnes  |  bleu ≥ 90%% du front, orange < 90%%\n"
                 "%s : ▼ déclenchement (W=%d, burn-in=%d, cooldown=%d), "
                 "le premier en gros ; zone grise = trigger muet ; signal sous le seuil en rouge"
                 % (stem, n, etiquette, triggers._window(40, window, 3),
                    burn_in or 0, triggers._window(40, cooldown)),
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95 if rows > 2 else (0.90 if rows > 1 else 0.80)))
    os.makedirs(FIGURES, exist_ok=True)
    path = os.path.join(FIGURES, "firings_%s%s.png" % (stem, suffix))
    fig.savefig(path, dpi=145)
    plt.close(fig)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmarks", nargs="*", default=["ii", "i", "edbo_ch_arylation"])
    parser.add_argument("--window", type=int, default=3, help="W, en experiences")
    parser.add_argument("--cooldown", type=int, default=5, help="cooldown, en experiences")
    parser.add_argument("--budget", type=int, default=40)
    parser.add_argument("--signal", default="pace_ratio", choices=sorted(SIGNAUX))
    parser.add_argument("--threshold", type=float, default=None,
                        help="seuil du signal ; defaut = celui du signal")
    args = parser.parse_args()

    # Les reglages sont donnes en experiences et convertis en fractions du
    # budget, qui est ce que le trigger manipule.
    window = args.window / args.budget
    cooldown = args.cooldown / args.budget
    # firing_times lit le burn-in dans WINDOW_FRACTION du module : ne regler
    # que le cooldown laissait le burn-in a sa valeur par defaut, donc les
    # figures W=3 s'affichaient avec un burn-in de 13 mais en appliquaient 15.
    triggers.WINDOW_FRACTION = window
    triggers.COOLDOWN_FRACTION = cooldown
    seuil = args.threshold if args.threshold is not None else SIGNAUX[args.signal][2]
    suffix = "_%s_W%d_cd%d_s%03d" % (args.signal, args.window, args.cooldown,
                                     round(100 * seuil))

    for stem in args.benchmarks:
        campaigns = load(stem)
        if not campaigns:
            print("%s : aucune campagne" % stem)
            continue
        signal = functools.partial(SIGNAUX[args.signal][0], fraction=window,
                                   threshold=seuil)
        fired = [triggers.firing_times(signal, log["experiments"],
                                       log["config"]["n_init"], len(log["experiments"]))
                 for _, log in campaigns]
        muettes = sum(1 for f in fired if not f)
        print("%-20s W=%d cd=%d seuil=%.2f | %.1f alertes/campagne | %d muette(s) -> %s"
              % (stem, args.window, args.cooldown, seuil,
                 sum(len(f) for f in fired) / len(fired), muettes,
                 draw(stem, campaigns, window, cooldown, suffix, args.signal, seuil)))


if __name__ == "__main__":
    main()

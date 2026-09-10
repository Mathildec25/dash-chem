# -*- coding: utf-8 -*-
r"""Build one Google Colab notebook holding every checkpoint a chemist is asked about.

Why a notebook rather than the standalone HTML pages of make_chemist_form.py:
a Colab link is never stripped by a mail server, it opens on a phone, there is
nothing to download or install, and the notebook lives in the repository, so
whoever takes this over reopens the exact page the participants saw.

Three things this file gets deliberately right, each of them a mistake made once:

**Titles are literal text, never HTML entities.** A `#@title` is not rendered as
HTML: Colab prints it verbatim, so `&eacute;` appears as `&eacute;` and the
notebook looks broken. Write the accented characters and the emoji directly.

**The form is built from ipywidgets, so the notebook is run once.** The obvious
design uses `#@param`, but editing a `#@param` rewrites the cell's source without
re-running it, which forces a second "Tout executer" and, worse, makes the first
one print "reponse enregistree" under every campaign before the participant has
typed anything. Widgets hold their value live, so the send button reads what is
on screen at the moment it is clicked.

**Dropdowns come from the benchmark grid, not from the campaign log.** A campaign
of 40 experiments touches a handful of levels; offering only those would silently
forbid asking for 1.0 mol% on the Suzuki grid, which is exactly the kind of
suggestion the study exists to collect. It also guarantees every proposal is a
grid point we can evaluate by table lookup.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/make_colab_notebook.py
"""

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hitl_bench.scripts.make_chemist_form import (  # noqa: E402
    PRESENTATION, SKIP, catalyst_names, label_value, presentation_for,
)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
RESULTS = os.path.join(HERE, "results")
FORMS = os.path.join(HERE, "forms")

# Where a participant's answers are sent. Here rather than buried in the
# notebook text so a successor changes it in one place.
CONTACT = "mathilde.croissant@uliege.be"

# The four checkpoints, each stopped where the trigger actually fires. Two need
# an intervention, one is a campaign that looks bad and recovers on its own, one
# has nothing left to find. Without the last two we could not tell a chemist who
# reasons from a chemist who always says "intervene".
CHECKPOINTS = [
    ("ii__no_hitl__seed03", 16),
    ("edbo_ch_arylation__no_hitl__seed02", 16),
    ("ii__no_hitl__seed04", 15),
    ("snar__no_hitl__seed01", 14),
]


def french(value, digits=6):
    """A number as a French reader writes it, keeping enough digits to be exact."""
    return (("%." + str(digits) + "g") % float(value)).replace(".", ",")


def load(stem, stop_at):
    with open(os.path.join(RESULTS, stem + ".json"), encoding="utf-8") as handle:
        log = json.load(handle)
    name = log["config"].get("benchmark") or log["config"].get("case")
    presentation = presentation_for(name)
    names = catalyst_names() if presentation is PRESENTATION["suzuki"] else None
    objectives = [o for o in log["config"]["objectives"] if o in log["experiments"][0]]
    params = [k for k in log["experiments"][0] if k not in SKIP and k not in objectives]
    return {"stem": stem, "stop_at": stop_at, "name": name, "log": log,
            "pres": presentation, "names": names, "objectives": objectives,
            "params": params, "records": log["experiments"][:stop_at]}


def grid_path(name):
    if name in ("i", "ii", "iii", "iv"):
        return os.path.join(DATA, "suzuki_%s.csv" % name)
    return os.path.join(DATA, "other", "%s.csv" % name)


def grid_levels(case):
    """Every level of every variable, read from the grid, labelled for a chemist.

    The Suzuki grids store the catalyst one-hot across columns L0..L6; the other
    grids keep it as a plain column. Read with csv so that generating the
    notebook needs nothing beyond the standard library.
    """
    with open(grid_path(case["name"]), newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    columns = list(rows[0].keys())

    levels = {}
    for parameter in case["params"]:
        if parameter in columns:
            values = sorted({row[parameter] for row in rows},
                            key=lambda v: (_is_text(v), _as_number(v), v))
            levels[parameter] = [(v if _is_text(v) else french(v)) for v in values]
        else:
            codes = [c for c in columns if c.startswith("L") and c[1:].isdigit()]
            levels[parameter] = [label_value(parameter, c, case["names"])
                                 for c in sorted(codes)]
    return levels


def _is_text(value):
    try:
        float(value)
        return False
    except (TypeError, ValueError):
        return True


def _as_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def table_payload(case):
    rows = []
    for record in case["records"]:
        row = {"n": record["experiment"]}
        for key in case["params"]:
            value = record[key]
            row[key] = (label_value(key, value, case["names"])
                        if isinstance(value, str) else french(value, 4))
        for objective in case["objectives"]:
            row[objective] = french(record[objective], 4)
            row["_" + objective] = abs(float(record[objective]))
        rows.append(row)
    return rows


def headers(case):
    out = {}
    for key in case["params"]:
        label, unit = case["pres"]["params"].get(key, (key, ""))[:2]
        out[key] = label + ((" (%s)" % unit) if unit else "")
    for objective in case["objectives"]:
        label, unit = case["pres"]["objectives"].get(objective, (objective, "", "haut"))[:2]
        out[objective] = label + ((" (%s)" % unit) if unit else "")
    return out


def markdown(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.split("\n")}


def code(source, title):
    """A Colab form cell: source hidden, only the title bar and widgets show.

    The title is printed verbatim by Colab, so it carries real accents and real
    emoji - never HTML entities.
    """
    body = '#@title %s {display-mode:"form"}\n' % title + source
    return {"cell_type": "code", "execution_count": None, "outputs": [],
            "metadata": {"cellView": "form"}, "source": body.split("\n")}


SETUP = r'''
import json, urllib.parse
import ipywidgets as widgets
from IPython.display import HTML, display

DONNEES = json.loads(r"""__PAYLOAD__""")
CONTACT = "__CONTACT__"
CHAMPS = {}

STYLE = """<style>
 .hb{font:15px/1.55 "Segoe UI",system-ui,sans-serif;color:#16181d;max-width:62rem}
 .hb h3{margin:0 0 .3rem;font-size:1.05rem}
 .hb table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}
 .hb th,.hb td{padding:.35rem .55rem;border-bottom:1px solid #dfe3e9;text-align:left}
 .hb th{font-size:.68rem;letter-spacing:.05em;text-transform:uppercase;color:#8b93a1}
 .hb td.n{text-align:right;font-variant-numeric:tabular-nums}
 .hb .bar span{display:block;height:.55rem;border-radius:2px;background:#1f5f8b;min-width:2px}
 .hb .note{background:#e6eef5;border-left:3px solid #1f5f8b;padding:.7rem .9rem;
           border-radius:0 5px 5px 0;margin:.7rem 0}
</style>"""

LARGE = widgets.Layout(width="46rem", max_width="98%")
ETIQUETTE = {"description_width": "14rem"}


def _tableau(c):
    reglages = "".join("<li><b>%s</b> : %s</li>" % (t, v) for t, v in c["reglages"])
    mesures = "".join("<li><b>%s</b>, à rendre %s</li>" % (t, s) for t, s in c["mesures"])
    colonnes = c["colonnes"]
    tete = "".join("<th>%s</th>" % c["entetes"][k] for k in colonnes)
    premier = "_" + c["objectifs"][0]
    echelle = max(r[premier] for r in c["lignes"]) or 1.0
    lignes = []
    for r in c["lignes"]:
        cases = "".join('<td class="%s">%s</td>'
                        % ("n" if k in c["objectifs"] else "", r[k]) for k in colonnes)
        lignes.append('<tr><td class="n">%d</td>%s<td class="bar">'
                      '<span style="width:%.1f%%"></span></td></tr>'
                      % (r["n"], cases, 100 * r[premier] / echelle))
    return STYLE + """<div class="hb">
<h3>%s</h3><p>%s</p>
<p><b>Ce que l'on peut régler</b></p><ul>%s</ul>
<p><b>Ce qui est mesuré à chaque essai</b></p><ul>%s</ul>
<p><b>%d essais faits sur %d prévus.</b> Voici tout ce qui a été testé, dans l'ordre.</p>
<table><thead><tr><th>#</th>%s<th></th></tr></thead><tbody>%s</tbody></table>
</div>""" % (c["titre"], c["intro"], reglages, mesures, len(c["lignes"]),
             c["budget"], tete, "".join(lignes))


# Shown as the first entry of every dropdown and as the unselected state of
# every choice. Nothing a participant did not touch may leave this notebook
# looking like an answer: a campaign they skipped must read as skipped, never as
# "propose CsOAc, BrettPhos, BuCN" because those happen to sort first.
A_CHOISIR = "— à choisir —"


def campagne(cle):
    """Affiche une campagne et les champs de réponse. Rien à valider :
    ce qui est à l'écran au moment de l'envoi est ce qui sera envoyé."""
    c = DONNEES[cle]
    display(HTML(_tableau(c)))

    avis = widgets.Textarea(
        description="Votre avis", placeholder="Va-t-elle dans la bonne direction ? "
        "Quelque chose vous gêne ? Quelques phrases suffisent.",
        layout=widgets.Layout(width="46rem", max_width="98%", height="5rem"),
        style=ETIQUETTE)
    decision = widgets.RadioButtons(
        description="Que faire ?", style=ETIQUETTE, layout=LARGE,
        options=["Je propose un essai",
                 "Laisser le programme continuer",
                 "Arrêter la campagne"])
    decision.index = None                      # aucune case cochée au départ

    proposition, boites = {}, []
    for titre, options in c["niveaux"]:
        boites.append(widgets.Dropdown(description=titre, options=[A_CHOISIR] + options,
                                       style=ETIQUETTE, layout=LARGE))
        proposition[titre] = boites[-1]
    pourquoi = widgets.Textarea(
        description="Pourquoi ?", placeholder="Le raisonnement nous intéresse "
        "autant que le point choisi.",
        layout=widgets.Layout(width="46rem", max_width="98%", height="4rem"),
        style=ETIQUETTE)
    essai = widgets.VBox(boites + [pourquoi])
    essai.layout.display = "none"              # n'apparaît que si on propose

    def bascule(evenement):
        essai.layout.display = None if evenement["new"] == "Je propose un essai" else "none"
    decision.observe(bascule, names="value")

    connu = widgets.RadioButtons(
        description="Aviez-vous reconnu cette réaction ?", style=ETIQUETTE, layout=LARGE,
        options=["Non, je raisonne sur ce que je vois",
                 "Ça me dit quelque chose", "Oui, je connais son résultat publié"])
    connu.index = None
    surete = widgets.Dropdown(
        description="À quel point êtes-vous sûr ?", style=ETIQUETTE, layout=LARGE,
        options=[A_CHOISIR, "pas du tout", "un peu", "moyennement", "assez", "tout à fait"])

    CHAMPS[cle] = {"avis": avis, "decision": decision, "proposition": proposition,
                   "pourquoi": pourquoi, "connu": connu, "surete": surete}
    display(widgets.VBox([avis, decision, essai, connu, surete]))


def _court(valeur):
    """Le mail doit rester court : mailto tronque au-dela de ~2000 caracteres."""
    return {"Non, je raisonne sur ce que je vois": "non",
            "Ça me dit quelque chose": "vaguement",
            "Oui, je connais son résultat publié": "oui",
            "Je propose un essai": "propose",
            "Laisser le programme continuer": "continuer",
            "Arrêter la campagne": "arreter"}.get(valeur, valeur)


def _reponses(qui, domaine):
    """Le texte envoye, et la liste des campagnes restees sans reponse."""
    lignes = ["Etude BO - reponses de %s (%s)" % (qui or "anonyme", domaine or "-"), ""]
    sautees = []
    for cle, c in DONNEES.items():
        w = CHAMPS.get(cle)
        if not w:
            continue
        avis = w["avis"].value.strip()
        if w["decision"].value is None and not avis:
            sautees.append(c["titre"])
            continue                            # rien de ce que la personne n'a pas dit
        lignes.append("[%s] %s" % (cle, c["titre"]))
        if avis:
            lignes.append("Avis: " + avis)
        lignes.append("Decision: " + (_court(w["decision"].value) or "non repondu"))
        if w["decision"].value == "Je propose un essai":
            choisis = ["%s=%s" % (t.split(" (")[0], b.value)
                       for t, b in w["proposition"].items() if b.value != A_CHOISIR]
            lignes.append("Essai: " + (" ; ".join(choisis) if choisis
                                       else "aucune condition choisie"))
            if w["pourquoi"].value.strip():
                lignes.append("Pourquoi: " + w["pourquoi"].value.strip())
        if w["connu"].value is not None:
            lignes.append("Reconnue: " + _court(w["connu"].value))
        if w["surete"].value != A_CHOISIR:
            lignes.append("Sur: " + w["surete"].value)
        lignes.append("")
    return "\n".join(lignes), sautees


def envoi():
    """Le bouton final : il lit les champs tels qu'ils sont à cet instant."""
    qui = widgets.Text(description="Vos initiales", style=ETIQUETTE, layout=LARGE,
                       placeholder="ex. MC")
    domaine = widgets.Text(
        description="Votre domaine", style=ETIQUETTE, layout=LARGE,
        placeholder="catalyse organométallique, chimie en flux, procédés...")
    bouton = widgets.Button(description="Voir mes réponses", button_style="primary",
                            icon="envelope", layout=widgets.Layout(width="16rem"))
    sortie = widgets.Output()

    def clic(_):
        corps, sautees = _reponses(qui.value.strip(), domaine.value.strip())
        lien = ("mailto:" + CONTACT + "?subject="
                + urllib.parse.quote("Reponses etude BO - " + (qui.value.strip() or "anonyme"))
                + "&body=" + urllib.parse.quote(corps))
        avertissement = ""
        if sautees:
            avertissement += ('<div class="note">Rien n\'a été répondu pour : <b>'
                              + ", ".join(sautees)
                              + "</b>. Ces campagnes ne seront pas dans le mail. "
                                "Remontez les remplir puis recliquez, ou envoyez "
                                "tel quel.</div>")
        # Un lien mailto complet depasse ce qu'Outlook accepte des qu'on repond
        # vraiment aux quatre campagnes, et il tronque sans rien dire. Le bouton
        # Copier est donc le chemin principal ; le lien mail n'est propose que
        # quand il tient.
        mail = ""
        if len(lien) <= 1900:
            mail = ('<p style="margin:.2rem 0 0"><a href="%s" style="color:#1f5f8b;'
                    'font-size:.9rem">ou ouvrir directement mon logiciel de mail</a>'
                    '</p>' % lien)
        with sortie:
            sortie.clear_output()
            display(HTML(STYLE + """<div class="hb">%s
<p><b>Vos réponses sont prêtes.</b> Cliquez sur Copier, puis collez-les dans un
mail adressé à <b>%s</b>.</p>
<textarea id="hbtexte" readonly style="width:100%%;height:14rem;font-family:
 ui-monospace,Consolas,monospace;font-size:.78rem;padding:.7rem;border:1px solid
 #dfe3e9;border-radius:5px;background:#e6eef5">%s</textarea>
<p style="margin:.7rem 0 0"><button id="hbcopie" style="background:#1f5f8b;
 color:#fff;border:0;border-radius:5px;padding:.7rem 1.3rem;font:inherit;
 font-weight:600;cursor:pointer">Copier mes réponses</button>
 <span id="hbdit" style="margin-left:.7rem;color:#1baf7a;font-weight:600"></span></p>
%s</div>
<script>
 document.getElementById("hbcopie").onclick = function () {
   var z = document.getElementById("hbtexte");
   z.select(); z.setSelectionRange(0, 999999);
   var ok = false;
   try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
   document.getElementById("hbdit").textContent =
     ok ? "copié !" : "sélectionnez le texte puis Ctrl+C";
 };
</script>""" % (avertissement, CONTACT, corps, mail)))

    bouton.on_click(clic)
    display(widgets.VBox([qui, domaine, bouton, sortie]))
'''.strip()


COVER = """# Un algorithme optimise une réaction. À quel moment faut-il un chimiste ?

Merci d'avoir accepté. **Vous n'avez rien à installer et rien à coder.**

Un montage automatisé teste des conditions de réaction une par une. Après chaque
essai, un programme choisit la suivante à partir de ce qu'il a déjà vu. C'est
efficace, mais il arrive qu'il s'enferme : il tourne autour d'une zone qu'il
croit bonne et n'en sort plus, alors qu'un chimiste qui regarde le tableau voit
tout de suite ce qui cloche.

**Ce qu'on cherche à savoir :** est-ce qu'un chimiste, à qui on montre une
campagne en cours, arrive à la remettre sur les rails ? Et peut-on repérer à
l'avance le moment où il vaut la peine de le déranger ?

Les quatre campagnes ci-dessous sont réelles, et toutes leurs conditions ont déjà
été mesurées et publiées. On saura donc exactement ce que votre proposition
aurait donné, sans que personne retourne à la paillasse.

> **Il n'y a pas de bonne réponse attendue.** Ce qui nous intéresse est votre
> raisonnement de chimiste, pas de deviner ce que l'algorithme ferait.

---

### Comment faire

Dans le menu tout en haut, cliquez sur **Exécution → Tout exécuter**, une seule
fois. Acceptez l'avertissement de Google, il apparaît pour n'importe quel
notebook. Les tableaux et les questions s'affichent.

Ensuite, descendez, lisez, répondez, et cliquez sur le bouton d'envoi tout en
bas. Comptez vingt minutes.

Rien à valider en cours de route : ce qui est à l'écran au moment où vous
cliquez est ce qui sera envoyé.

Une question revient à chaque campagne : **aviez-vous reconnu cette réaction ?**
C'est une question de méthode et pas un examen. Certaines de ces chimies sont
publiées, et il faut pouvoir faire la différence entre un raisonnement et un
souvenir. Répondre oui ne disqualifie rien."""


CLOSING = """---

## C'est fini

Deux dernières cases, puis le bouton."""


def build(checkpoints):
    cases = [load(stem, stop) for stem, stop in checkpoints]
    payload = {}
    for index, case in enumerate(cases, 1):
        presentation, log = case["pres"], case["log"]
        levels = grid_levels(case)
        head = headers(case)
        payload["c%d" % index] = {
            "titre": presentation["title"],
            "intro": presentation["intro"],
            "budget": log["config"]["n_init"] + log["config"]["n_iterations"],
            "colonnes": case["params"] + case["objectives"],
            "objectifs": case["objectives"],
            "entetes": head,
            "lignes": table_payload(case),
            "niveaux": [[head[p], levels[p]] for p in case["params"]],
            "reglages": [(head[p], _summarise(levels[p])) for p in case["params"]],
            "mesures": [(presentation["objectives"].get(o, (o, "", "haut"))[0],
                         presentation["objectives"].get(o, (o, "", "haut"))[2])
                        for o in case["objectives"]],
        }

    setup = (SETUP.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False))
                  .replace("__CONTACT__", CONTACT))
    cells = [markdown(COVER), code(setup, "▶️ Préparation — rien à faire ici")]
    for index, case in enumerate(cases, 1):
        heading = "## Campagne %d sur %d" % (index, len(cases))
        if any(other["pres"] is case["pres"] for other in cases[:index - 1]):
            heading += ("\n\nMême chimie que plus haut, mais **une autre campagne** : "
                        "elle est partie sur d'autres essais de départ.")
        cells.append(markdown(heading))
        cells.append(code('campagne("c%d")' % index,
                          "📊 Campagne %d — le tableau et vos réponses" % index))
    cells.append(markdown(CLOSING))
    cells.append(code("envoi()", "📧 Vos coordonnées, puis envoi"))

    return {"nbformat": 4, "nbformat_minor": 0,
            "metadata": {"colab": {"provenance": [], "toc_visible": True},
                         "kernelspec": {"name": "python3", "display_name": "Python 3"},
                         "language_info": {"name": "python"}},
            "cells": cells}


def _summarise(texts, limit=8):
    """Long ladders of numbers read as a range, not as a list."""
    if len(texts) <= limit:
        return ", ".join(texts)
    return "%s à %s, %d valeurs" % (texts[0], texts[-1], len(texts))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=os.path.join(FORMS, "campagnes_chimistes.ipynb"))
    args = parser.parse_args()

    os.makedirs(FORMS, exist_ok=True)
    notebook = build(CHECKPOINTS)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(notebook, handle, ensure_ascii=False, indent=1)
    print("ecrit : %s (%d cellules)" % (args.out, len(notebook["cells"])))


if __name__ == "__main__":
    main()

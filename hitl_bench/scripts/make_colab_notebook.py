# -*- coding: utf-8 -*-
r"""Build one Google Colab notebook holding every checkpoint a chemist is asked about.

Why a notebook rather than the standalone HTML pages of make_chemist_form.py:
a Colab link is never stripped by a mail server, it opens on a phone, there is
nothing to download or install, and the notebook lives in the repository, so
whoever takes this over reopens the exact page the participants saw.

The participant must never see code. Every code cell carries `cellView: "form"`,
which is Colab's own way of hiding a cell's source and showing only its
`#@param` widgets, so the notebook reads as text, dropdowns and text boxes.

Dropdowns are built from the **benchmark grid**, never from the campaign's own
history. A campaign of 40 experiments touches a handful of levels, so offering
only those would silently forbid a chemist from asking for 1.0 mol% - a
perfectly valid condition that this campaign happens not to have tried. The
whole point is to let them ask for what the optimiser did not.

Three gestures for the participant, and no notion of a cell is required:

    1. Execution > Tout executer          (renders the campaign tables)
    2. fill the boxes
    3. Execution > Tout executer again, then click the mail link at the bottom

Step 3 is what makes it reliable: editing a `#@param` widget rewrites the cell's
source but does not re-run it, so a full re-run is the one gesture that captures
every answer without explaining cells to anyone.

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
    text = ("%." + str(digits) + "g") % float(value)
    return text.replace(".", ",")


def load(stem, stop_at):
    with open(os.path.join(RESULTS, stem + ".json"), encoding="utf-8") as handle:
        log = json.load(handle)
    name = log["config"].get("benchmark") or log["config"].get("case")
    presentation = presentation_for(name)
    names = catalyst_names() if presentation is PRESENTATION["suzuki"] else None
    objectives = [o for o in log["config"]["objectives"] if o in log["experiments"][0]]
    params = [k for k in log["experiments"][0] if k not in SKIP and k not in objectives]
    return {
        "stem": stem, "stop_at": stop_at, "name": name, "log": log,
        "pres": presentation, "names": names,
        "objectives": objectives, "params": params,
        "records": log["experiments"][:stop_at],
    }


def grid_path(name):
    if name in ("i", "ii", "iii", "iv"):
        return os.path.join(DATA, "suzuki_%s.csv" % name)
    return os.path.join(DATA, "other", "%s.csv" % name)


def grid_levels(case):
    """Every level of every variable, from the grid rather than from the campaign.

    The Suzuki grids store the catalyst one-hot across columns L0..L6; the other
    grids keep it as a plain column. Read with csv rather than pandas so that
    generating the notebook needs nothing beyond the standard library.
    """
    with open(grid_path(case["name"]), newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    columns = rows[0].keys()

    levels = {}
    for parameter in case["params"]:
        if parameter in columns:
            seen = sorted({row[parameter] for row in rows},
                          key=lambda v: (_is_text(v), _as_number(v), v))
            levels[parameter] = [(french(v) if not _is_text(v) else v, v) for v in seen]
        else:
            # one-hot: the levels are the column names that are not something else
            codes = [c for c in columns
                     if c not in case["params"] and c not in case["objectives"]
                     and c.startswith("L")]
            levels[parameter] = [(label_value(parameter, code, case["names"]), code)
                                 for code in sorted(codes)]
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
            row[key] = (label_value(key, value, case["names"]) if isinstance(value, str)
                        else french(value, 4))
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


def code(source, title=None):
    body = source if not title else '#@title %s {display-mode: "form"}\n' % title + source
    return {"cell_type": "code", "execution_count": None, "outputs": [],
            "metadata": {"cellView": "form"}, "source": body.split("\n")}


SETUP = r'''
import json
from IPython.display import HTML, display

DONNEES = json.loads(r"""%(payload)s""")
REPONSES = {}

STYLE = """<style>
 .hb{font:15px/1.55 "Segoe UI",system-ui,sans-serif;color:#16181d;max-width:62rem}
 .hb h3{margin:0 0 .3rem;font-size:1.05rem}
 .hb table{border-collapse:collapse;width:100%%;font-size:.9rem;margin:.6rem 0}
 .hb th,.hb td{padding:.35rem .55rem;border-bottom:1px solid #dfe3e9;text-align:left}
 .hb th{font-size:.68rem;letter-spacing:.05em;text-transform:uppercase;color:#8b93a1}
 .hb td.n{text-align:right;font-variant-numeric:tabular-nums}
 .hb .bar span{display:block;height:.55rem;border-radius:2px;background:#1f5f8b;min-width:2px}
 .hb .note{background:#e6eef5;border-left:3px solid #1f5f8b;padding:.7rem .9rem;
           border-radius:0 5px 5px 0;margin:.7rem 0}
</style>"""


def montrer(cle):
    """Affiche une campagne : ce qu'on peut regler, ce qu'on mesure, les essais faits."""
    c = DONNEES[cle]
    reglages = "".join("<li><b>%%s</b> : %%s</li>" %% (t, v) for t, v in c["reglages"])
    mesures = "".join("<li><b>%%s</b>, \u00e0 rendre %%s</li>" %% (t, s) for t, s in c["mesures"])
    colonnes = c["colonnes"]
    tete = "".join("<th>%%s</th>" %% c["entetes"][k] for k in colonnes)
    premier = "_" + c["objectifs"][0]
    echelle = max(r[premier] for r in c["lignes"]) or 1.0
    lignes = []
    for r in c["lignes"]:
        cases = "".join('<td class="%%s">%%s</td>'
                        %% ("n" if k in c["objectifs"] else "", r[k]) for k in colonnes)
        lignes.append('<tr><td class="n">%%d</td>%%s<td class="bar"><span style="width:%%.1f%%%%">'
                      '</span></td></tr>' %% (r["n"], cases, 100 * r[premier] / echelle))
    display(HTML(STYLE + """<div class="hb">
<h3>%%s</h3><p>%%s</p>
<p><b>Ce que l'on peut r\u00e9gler</b></p><ul>%%s</ul>
<p><b>Ce qui est mesur\u00e9 \u00e0 chaque essai</b></p><ul>%%s</ul>
<p><b>%%d essais faits sur %%d pr\u00e9vus.</b> Voici tout ce qui a \u00e9t\u00e9 test\u00e9,
dans l'ordre.</p>
<table><thead><tr><th>#</th>%%s<th></th></tr></thead><tbody>%%s</tbody></table>
</div>""" %% (c["titre"], c["intro"], reglages, mesures, len(c["lignes"]),
              c["budget"], tete, "".join(lignes))))


def enregistrer(cle, **champs):
    REPONSES[cle] = champs
    display(HTML(STYLE + '<div class="hb"><div class="note">R\u00e9ponse enregistr\u00e9e '
                 'pour <b>%%s</b>. Passez \u00e0 la suite.</div></div>'
                 %% DONNEES[cle]["titre"]))
'''.strip()


SEND = r'''
import urllib.parse
from IPython.display import HTML, display

lignes = ["Etude BO - reponses de %%s (%%s)" %% (qui or "anonyme", domaine or "-"), ""]
for cle, c in DONNEES.items():
    r = REPONSES.get(cle)
    if not r:
        continue
    lignes.append("[%%s] %%s" %% (cle, c["titre"]))
    lignes.append("Avis: " + (r["reponse"] or "-"))
    lignes.append("Decision: " + r["decision"])
    if r["decision"].startswith("je propose"):
        lignes.append("Proposition: " + " ; ".join(
            "%%s=%%s" %% (k, v) for k, v in r["proposition"].items()))
        lignes.append("Pourquoi: " + (r["pourquoi"] or "-"))
    lignes.append("Confiance: %%s | Deja vu: %%s" %% (r["confiance"], r["deja_vu"]))
    lignes.append("")
corps = "\n".join(lignes)

lien = ("mailto:%(contact)s?subject="
        + urllib.parse.quote("Reponses etude BO - " + (qui or "anonyme"))
        + "&body=" + urllib.parse.quote(corps))

manquantes = [c["titre"] for k, c in DONNEES.items() if k not in REPONSES]
alerte = ""
if len(lien) > 1900:
    alerte += ('<div class="note">Vos réponses sont détaillées, et '
               'certains logiciels de mail coupent les liens trop longs. '
               '<b>Préférez le copier-coller du texte ci-dessous</b> '
               'plutôt que le bouton.</div>')
if manquantes:
    alerte = ('<div class="note"><b>Attention</b> : rien n\'est enregistr\u00e9 pour '
              + ", ".join(manquantes) + '. Remplissez ces sections, puis relancez '
              '<b>Ex\u00e9cution &gt; Tout ex\u00e9cuter</b>.</div>')

display(HTML(STYLE + """<div class="hb">%%s
<p style="margin:1rem 0"><a href="%%s" style="background:#1f5f8b;color:#fff;
 text-decoration:none;padding:.75rem 1.4rem;border-radius:5px;font-weight:600;
 display:inline-block">Envoyer mes r\u00e9ponses par mail</a></p>
<p style="color:#5b6472;font-size:.9rem">Le lien ouvre votre logiciel de mail avec
tout d\u00e9j\u00e0 rempli : il ne reste qu'\u00e0 cliquer Envoyer. S'il ne s'ouvre pas,
copiez le texte ci-dessous et envoyez-le \u00e0 %(contact)s.</p>
<pre style="background:#e6eef5;padding:.8rem;border-radius:5px;font-size:.78rem;
 white-space:pre-wrap">%%s</pre></div>""" %% (alerte, lien, corps)))
'''.strip()


def answer_cell(case, index, levels):
    key = "c%d" % index
    lines = ['reponse = "" #@param {type:"string"}',
             'decision = "je propose un essai" '
             '#@param ["je propose un essai", "laisser le programme continuer", '
             '"arreter la campagne"]']
    proposal = []
    for parameter in case["params"]:
        label = case["pres"]["params"].get(parameter, (parameter, ""))[0]
        unit = case["pres"]["params"].get(parameter, (parameter, ""))[1]
        variable = _identifier(label + ("_" + unit if unit else ""))
        options = [text for text, _ in levels[parameter]]
        lines.append("%s = %s #@param %s" % (
            variable, json.dumps(options[0], ensure_ascii=False),
            json.dumps(options, ensure_ascii=False)))
        proposal.append('"%s": %s' % (label + ((" (%s)" % unit) if unit else ""), variable))
    lines += ['pourquoi = "" #@param {type:"string"}',
              'confiance = "3 - moyennement" #@param ["1 - pas du tout", "2", '
              '"3 - moyennement", "4", "5 - tout a fait"]',
              'deja_vu = "non" #@param ["non", "ca me dit quelque chose", "oui"]',
              '',
              'enregistrer("%s", reponse=reponse, decision=decision,' % key,
              '            pourquoi=pourquoi, confiance=confiance, deja_vu=deja_vu,',
              '            proposition={%s})' % ", ".join(proposal)]
    return code("\n".join(lines), "&#9997;&#65039; Vos r&eacute;ponses")


def _identifier(label):
    """Colab shows a form field's *variable name* as its label, so it is the text
    the chemist reads: plain ASCII, no doubled underscores, units spelled out."""
    table = str.maketrans("àâäéèêëîïôöùûüçÀÂÉÈÊÎÔÙÛÇ", "aaaeeeeiioouuucAAEEEIOUUC")
    cleaned = label.translate(table).replace("%", "pct").replace("°", "")
    kept = "".join(c if c.isalnum() else "_" for c in cleaned)
    while "__" in kept:
        kept = kept.replace("__", "_")
    return kept.strip("_")


def build(checkpoints):
    cases = [load(stem, stop) for stem, stop in checkpoints]
    payload, all_levels = {}, []
    for index, case in enumerate(cases, 1):
        presentation, log = case["pres"], case["log"]
        levels = grid_levels(case)
        all_levels.append(levels)
        payload["c%d" % index] = {
            "titre": presentation["title"],
            "intro": presentation["intro"],
            "budget": log["config"]["n_init"] + log["config"]["n_iterations"],
            "colonnes": case["params"] + case["objectives"],
            "objectifs": case["objectives"],
            "entetes": headers(case),
            "lignes": table_payload(case),
            "reglages": [(headers(case)[p], _summarise([t for t, _ in levels[p]]))
                         for p in case["params"]],
            "mesures": [(presentation["objectives"].get(o, (o, "", "haut"))[0],
                         presentation["objectives"].get(o, (o, "", "haut"))[2])
                        for o in case["objectives"]],
        }

    cells = [markdown(COVER),
             code(SETUP % {"payload": json.dumps(payload, ensure_ascii=False)},
                  "&#9654;&#65039; Pr&eacute;paration (rien &agrave; faire ici)")]
    for index, case in enumerate(cases, 1):
        heading = "## Campagne %d sur %d" % (index, len(cases))
        if any(other["pres"] is case["pres"] for other in cases[:index - 1]):
            heading += ("\n\nMême chimie que plus haut, mais **une autre campagne** : "
                        "elle est partie sur d'autres essais de départ.")
        cells.append(markdown(heading))
        cells.append(code('montrer("c%d")' % index, "&#128202; La campagne %d" % index))
        cells.append(answer_cell(case, index, all_levels[index - 1]))

    cells.append(markdown(CLOSING))
    cells.append(code('qui = "" #@param {type:"string"}\n'
                      'domaine = "" #@param {type:"string"}\n\n' + SEND % {"contact": CONTACT},
                      "&#128231; Vos coordonn&eacute;es, puis envoi"))

    return {
        "nbformat": 4, "nbformat_minor": 0,
        "metadata": {
            "colab": {"provenance": [], "toc_visible": True},
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "language_info": {"name": "python"},
        },
        "cells": cells,
    }


def _summarise(texts, limit=8):
    """Long ladders of numbers are read as a range, not as a list."""
    if len(texts) <= limit:
        return ", ".join(texts)
    return "%s à %s, %d valeurs" % (texts[0], texts[-1], len(texts))


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

Les campagnes ci-dessous sont réelles et toutes leurs conditions ont déjà été
mesurées et publiées. On saura donc exactement ce que votre proposition aurait
donné, sans que personne retourne à la paillasse.

> **Il n'y a pas de bonne réponse attendue.** Ce qui nous intéresse est votre
> raisonnement de chimiste, pas de deviner ce que l'algorithme ferait.

---

### Comment faire, en trois gestes

1. Dans le menu tout en haut, **Exécution → Tout exécuter**. Acceptez
   l'avertissement de Google, il apparaît pour n'importe quel notebook. Les
   tableaux s'affichent.
2. **Remplissez les champs** de chaque section. Comptez vingt minutes.
3. Refaites **Exécution → Tout exécuter**, puis cliquez sur le bouton d'envoi
   tout en bas.

Le deuxième « Tout exécuter » n'est pas une coquetterie : c'est lui qui
enregistre ce que vous avez tapé.

Une question revient à chaque campagne : **aviez-vous reconnu cette réaction ?**
C'est une question de méthode et pas un examen. Certaines de ces chimies sont
publiées, et il faut pouvoir faire la différence entre un raisonnement et un
souvenir. Répondre oui ne disqualifie rien."""


CLOSING = """---

## Envoi

Encore deux champs, et c'est fini."""


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

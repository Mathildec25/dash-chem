# -*- coding: utf-8 -*-
r"""Build the page a chemist receives *first*, before any campaign is shown.

make_chemist_form.py builds the checkpoint pages: one campaign, three questions.
Those are the experiment. This script builds what comes before it - the document
that explains what we are asking, presents the candidate reactions in the terms
a bench chemist uses, and lets each participant say which ones they are willing
to reason about and which ones they already know.

Why it matters that they answer before seeing any campaign: a participant who
recognises the Reizman Suzuki work knows its published conclusion, PCy3 at
110 C, and would recite it rather than reason. Asking afterwards invites them to
under-report. Asking first, with nothing at stake, does not.

Nothing here mentions Bayesian optimisation, hypervolume or Pareto fronts. Every
level quoted is read from the grids themselves, so the page cannot drift away
from what the campaigns actually run.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/make_chemist_invitation.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
OTHER = os.path.join(DATA, "other")
FORMS = os.path.join(HERE, "forms")

# What a participant is actually asked for: four checkpoint pages, about five
# minutes each on the pages as generated.
N_CHECKPOINTS = 4
MINUTES = 20


def number(value, fmt="%g"):
    """A number as a French reader expects it: comma decimal, thin thousands space."""
    text = fmt % value
    if "." in text:
        whole, decimals = text.split(".")
        text = whole + "," + decimals
    if len(text.split(",")[0]) > 4:                 # 11560 -> 11 560
        whole = text.split(",")[0]
        grouped = " ".join(
            [whole[max(0, i - 3):i] for i in range(len(whole) % 3 or 3, len(whole) + 1, 3)])
        text = grouped + text[len(whole):]
    return text


def ligand_names():
    """The Suzuki catalysts, named where the mapping establishes a name.

    Two of the seven are deliberately left as their precatalyst-ligand code:
    the accessible text of the Reizman paper names five, and a guessed name
    shown to a chemist would corrupt the study. The page says so rather than
    dropping an unexplained 'P1-L6' into a list of phosphines.
    """
    with open(os.path.join(DATA, "catalyst_names.json"), encoding="utf-8") as handle:
        mapping = json.load(handle)["mapping"]
    named, unnamed = [], []
    for code in sorted(mapping):
        entry = mapping[code]
        (named if entry.get("ligand") else unnamed).append(
            entry["ligand"] or entry["pair"])
    text = "%d possibilités : %s" % (len(named) + len(unnamed), ", ".join(named))
    if unnamed:
        text += ", plus %d paire%s dont le nom n'est pas publié (%s)" % (
            len(unnamed), "s" if len(unnamed) > 1 else "", ", ".join(unnamed))
    return text


def levels(frame, column, fmt="%g"):
    """The column's levels as strings. Text columns are already readable."""
    values = sorted(frame[column].unique())
    if not pd.api.types.is_numeric_dtype(frame[column]):
        return [str(value) for value in values]
    return [number(value, fmt) for value in values]


def listing(frame, column, unit=""):
    """Levels as one readable line.

    Numeric levels are separated by semicolons: French writes decimals with a
    comma, so a comma-separated list of them cannot be parsed by eye.
    """
    separator = ", " if not pd.api.types.is_numeric_dtype(frame[column]) else " ; "
    return separator.join(levels(frame, column)) + unit


def span(frame, column, unit=""):
    """A regular ladder of levels reads better as a range than as a list."""
    values = levels(frame, column)
    numbers = [float(v.replace(" ", "").replace(",", ".")) for v in values]
    steps = {round(b - a, 6) for a, b in zip(numbers, numbers[1:])}
    if len(steps) == 1 and len(numbers) > 3:
        return "de %s à %s%s, par pas de %s" % (
            number(numbers[0]), number(numbers[-1]), unit, number(steps.pop()))
    return listing(frame, column, unit)


def reactions():
    """The three reactions, described from the grids the campaigns actually use."""
    suzuki = pd.read_csv(os.path.join(DATA, "suzuki_ii.csv"))
    edbo = pd.read_csv(os.path.join(OTHER, "edbo_ch_arylation.csv"))
    snar = pd.read_csv(os.path.join(OTHER, "snar.csv"))

    return [
        {
            "key": "suzuki",
            "title": "Couplage de Suzuki-Miyaura, en flux continu",
            "what": "Un montage en flux teste une condition à la fois. On cherche "
                    "à la fois un bon rendement et à ne pas gaspiller le palladium.",
            "size": len(suzuki),
            "knobs": [
                ("Paire précatalyseur–ligand", ligand_names()),
                ("Temps de séjour", span(suzuki, "res_time", " s")),
                ("Température", span(suzuki, "temperature", " °C")),
                ("Charge en Pd", span(suzuki, "catalyst_loading", " mol%")),
            ],
            "goals": [
                ("Rendement", "à maximiser ; il va de 0 à %s %% sur cette chimie"
                 % number(suzuki["yield"].max(), "%.1f")),
                ("TON (rotations par Pd)", "à maximiser ; de 0 à %s"
                 % number(suzuki["turnover"].max(), "%.0f")),
            ],
            "note": "Le rendement plafonne bas sur ce substrat : %s %% est le "
                    "maximum atteignable, ce n'est pas le signe d'une campagne qui "
                    "se passe mal." % number(suzuki["yield"].max(), "%.1f"),
        },
        {
            "key": "arylation",
            "title": "Arylation C–H",
            "what": "Même principe, mais l'arbitrage est différent : on veut un bon "
                    "rendement sans faire exploser le coût des réactifs, et les deux "
                    "ne vont pas ensemble.",
            "size": len(edbo),
            "knobs": [
                ("Ligand", "12 possibilités : " + listing(edbo, "ligand")),
                ("Base", listing(edbo, "base")),
                ("Solvant", listing(edbo, "solvent")),
                ("Concentration", listing(edbo, "concentration", " M")),
                ("Température", listing(edbo, "temperature", " °C")),
            ],
            "goals": [
                ("Rendement", "à maximiser ; de 0 à 100 %"),
                ("Coût des réactifs", "à minimiser ; il varie d'un facteur 20 entre "
                                      "le moins cher et le plus cher"),
            ],
            "note": "C'est la réaction où le choix du ligand pèse le plus lourd : "
                    "entre le meilleur et le pire, le rendement moyen passe de 53 % "
                    "à 0,3 %.",
        },
        {
            "key": "snar",
            "title": "Substitution nucléophile aromatique, en flux continu",
            "what": "Aucun catalyseur ici, seulement des conditions de procédé. On "
                    "veut produire beaucoup et jeter peu.",
            "size": len(snar),
            "knobs": [
                ("Temps de séjour", listing(snar, "tau", " min")),
                ("Équivalents de pyrrolidine", listing(snar, "equiv_pldn")),
                ("Concentration en DFNB", listing(snar, "conc_dfnb", " M")),
                ("Température", listing(snar, "temperature", " °C")),
            ],
            "goals": [
                ("Productivité (STY)", "à maximiser ; de %s à %s kg·m⁻³·h⁻¹"
                 % (number(snar["sty"].min(), "%.0f"),
                    number(snar["sty"].max(), "%.0f"))),
                ("Facteur E (déchets)", "à minimiser ; de %s à %s kg de déchets "
                 "par kg de produit" % (number(snar["e_factor"].min(), "%.0f"),
                                        number(snar["e_factor"].max(), "%.0f"))),
            ],
            "note": "Pas de catalyseur à choisir : si vous êtes plus à l'aise avec "
                    "le procédé qu'avec l'organométallique, c'est celle-là.",
        },
    ]


def render_reaction(index, reaction):
    knobs = "".join("<li><b>%s</b> — %s</li>" % pair for pair in reaction["knobs"])
    goals = "".join("<li><b>%s</b> — %s</li>" % pair for pair in reaction["goals"])
    return """
<div class="card">
<h3>%(n)d. %(title)s</h3>
<p>%(what)s</p>
<p class="hint">%(size)s combinaisons possibles au total.</p>
<p><b>Ce que vous pouvez régler</b></p><ul>%(knobs)s</ul>
<p><b>Ce qui est mesuré à chaque essai</b></p><ul>%(goals)s</ul>
<p class="note">%(note)s</p>
</div>""" % {"n": index, "title": reaction["title"], "what": reaction["what"],
             "size": "{:,}".format(reaction["size"]).replace(",", "\u202f"),
             "knobs": knobs, "goals": goals, "note": reaction["note"]}


def render_choices(reaction_list):
    return "".join(
        '<tr><td>%s</td>'
        '<td><input type="checkbox" name="volontaire_%s"></td>'
        '<td><select name="connait_%s"><option value="">—</option>'
        '<option>oui</option><option>peut-être</option><option>non</option>'
        '</select></td></tr>' % (reaction["title"], reaction["key"], reaction["key"])
        for reaction in reaction_list)


PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Optimisation de réactions — votre avis de chimiste</title>
<style>
 :root{--ink:#16181d;--soft:#5b6472;--faint:#8b93a1;--rule:#dfe3e9;--paper:#f7f8fa;
       --card:#fff;--accent:#1f5f8b;--accent-soft:#e6eef5}
 *{box-sizing:border-box}
 body{margin:0;background:var(--paper);color:var(--ink);
      font:16px/1.6 "Segoe UI",system-ui,sans-serif}
 .wrap{max-width:62rem;margin:0 auto;padding:2rem 1.5rem 5rem}
 h1{font-size:1.7rem;margin:0 0 .3rem;line-height:1.2}
 h2{font-size:1.15rem;margin:2.2rem 0 .8rem;padding-bottom:.4rem;
    border-bottom:1px solid var(--rule)}
 h3{font-size:1.02rem;margin:0 0 .5rem}
 p{margin:.6rem 0;max-width:62ch}
 .lede{color:var(--soft);font-size:1.05rem;max-width:60ch}
 .card{background:var(--card);border:1px solid var(--rule);border-radius:6px;
       padding:1.1rem 1.3rem;margin:1rem 0}
 ul{margin:.4rem 0;padding-left:1.2rem} li{margin:.25rem 0}
 ol{padding-left:1.2rem} ol li{margin:.35rem 0}
 table{border-collapse:collapse;width:100%%;font-size:.92rem}
 th,td{padding:.5rem .6rem;border-bottom:1px solid var(--rule);text-align:left}
 th{font-size:.7rem;letter-spacing:.05em;text-transform:uppercase;color:var(--faint);
    font-weight:600}
 .scroll{overflow-x:auto}
 label{display:block;margin:.9rem 0 .25rem;font-weight:600;font-size:.95rem}
 .hint{font-weight:400;color:var(--soft);font-size:.88rem}
 textarea,select,input[type=text]{width:100%%;padding:.5rem .6rem;
        border:1px solid var(--rule);border-radius:4px;font:inherit;background:#fff;
        color:var(--ink)}
 textarea{min-height:4.5rem;resize:vertical}
 td select{max-width:11rem} td input[type=checkbox]{width:auto}
 button{background:var(--accent);color:#fff;border:0;border-radius:5px;
        padding:.7rem 1.2rem;font:inherit;font-weight:600;cursor:pointer}
 button.ghost{background:#fff;color:var(--accent);border:1px solid var(--accent)}
 .actions{display:flex;gap:.7rem;flex-wrap:wrap;margin-top:1.2rem}
 #out{margin-top:1rem;white-space:pre-wrap;font-family:ui-monospace,Consolas,monospace;
      font-size:.82rem;background:var(--accent-soft);border-radius:5px;padding:.9rem;
      display:none}
 .note{background:var(--accent-soft);border-left:3px solid var(--accent);
       padding:.8rem 1rem;border-radius:0 5px 5px 0;font-size:.95rem}
</style></head><body><div class="wrap">

<h1>Un algorithme optimise une réaction.<br>À quel moment faut-il un chimiste ?</h1>
<p class="lede">Rien à installer, rien à coder, et il n'y a pas de bonne réponse
attendue.</p>

<h2>De quoi il s'agit</h2>
<p>Un montage automatisé teste des conditions de réaction une par une. Après
chaque essai, un programme choisit le suivant à partir de ce qu'il a déjà vu.
C'est efficace, mais il arrive que le programme s'enferme : il tourne autour
d'une zone qu'il croit bonne et n'en sort plus, alors qu'un chimiste qui regarde
le tableau d'essais voit tout de suite ce qui cloche.</p>

<p><b>Ce qu'on cherche à savoir :</b> est-ce qu'un chimiste, à qui on montre une
campagne en cours, arrive à la remettre sur les rails ? Et peut-on repérer
<i>à l'avance</i> le moment où il vaut la peine de le déranger ?</p>

<p>Les campagnes qu'on vous montrera sont réelles, et toutes leurs conditions ont
déjà été mesurées et publiées. On saura donc exactement ce que votre proposition
aurait donné, sans que personne retourne à la paillasse.</p>

<h2>Ce qu'on vous demande</h2>
<ol>
<li>Répondre à ce questionnaire, cinq minutes.</li>
<li>Recevoir ensuite %(n_checkpoints)d pages du même genre. Chacune montre une
campagne arrêtée en cours de route : le tableau de tous les essais déjà faits,
avec les vrais réactifs et les vraies unités.</li>
<li>Pour chacune, dire ce que vous en pensez, puis choisir entre proposer
vous-même le prochain essai, laisser le programme continuer, ou arrêter la
campagne.</li>
</ol>
<p>Comptez <b>%(minutes)d minutes en tout</b>. Chaque page est un fichier à ouvrir
dans votre navigateur ; à la fin, un bouton copie vos réponses et vous les collez
dans un mail. Rien ne part tout seul.</p>

<div class="note">On vous demandera à chaque fois si vous aviez reconnu la
réaction. C'est une question de méthode et pas un examen : certaines de ces
chimies sont publiées, et il faut pouvoir faire la différence entre un
raisonnement et un souvenir. Répondre « oui » ne disqualifie rien.</div>

<h2>Les réactions envisagées</h2>
<p>Trois candidates. Vous n'avez pas besoin de les connaître pour participer :
tout ce qui est nécessaire figurera sur la page.</p>
%(reactions)s

<h2>Vos réponses</h2>
<form id="f">

<label>1. Sur lesquelles accepteriez-vous de vous prononcer ?
<span class="hint">Cochez celles où vous vous sentez à l'aise, et dites-nous
franchement si vous connaissez déjà le système. C'est utile, pas gênant.</span></label>
<div class="card scroll" style="margin-top:.5rem">
<table><thead><tr><th>Réaction</th><th>Je veux bien</th>
<th>Je connais déjà ce système</th></tr></thead>
<tbody>%(choices)s</tbody></table></div>

<label>2. Quand vous regardez une série d'essais qui n'avance plus, qu'est-ce qui
vous met la puce à l'oreille ?
<span class="hint">C'est le cœur de l'étude : on essaie de reproduire ce
jugement-là automatiquement. Dites-le avec vos mots.</span></label>
<textarea name="signaux" placeholder="Par exemple : toujours le même catalyseur, un solvant jamais testé, une température jamais poussée..."></textarea>

<label>3. Dans votre pratique, après combien d'essais décevants de suite
arrêteriez-vous une campagne ?</label>
<input type="text" name="patience" placeholder="Un nombre, ou &laquo;&nbsp;ça dépend de...&nbsp;&raquo;">

<label>4. Quelque chose à redire sur la façon dont c'est présenté ?
<span class="hint">Si une page est illisible ou un mot mal choisi, c'est le
moment de le dire.</span></label>
<textarea name="remarques" placeholder="Facultatif."></textarea>

<label>Votre nom ou vos initiales
<span class="hint">pour relier vos réponses entre les pages</span></label>
<input type="text" name="qui" placeholder="ex. MC">

<label>Votre domaine principal
<span class="hint">catalyse organométallique, chimie en flux, procédés, formulation...</span></label>
<input type="text" name="domaine" placeholder="En quelques mots">

<div class="actions">
 <button type="button" onclick="show()">Voir mes réponses</button>
 <button type="button" class="ghost" onclick="copyIt()">Copier mes réponses</button>
 <button type="button" class="ghost" onclick="save()">Enregistrer un fichier</button>
</div>
<p class="hint">Collez vos réponses dans un mail, ou enregistrez le fichier et
renvoyez-le. Rien n'est envoyé automatiquement.</p>
<div id="out"></div>
</form>

<script>
 function answer() {
   var d = {formulaire: "invitation", date: new Date().toISOString()};
   document.querySelectorAll('#f input[type=checkbox]').forEach(function (c) {
     d[c.name] = c.checked ? 'oui' : 'non';
   });
   new FormData(document.getElementById('f')).forEach(function (v, k) {
     if (!(k in d)) { d[k] = v; }
   });
   return JSON.stringify(d, null, 2);
 }
 function show() {
   var o = document.getElementById('out');
   o.textContent = answer(); o.style.display = 'block';
 }
 function copyIt() {
   navigator.clipboard.writeText(answer()).then(
     function () { alert('Réponses copiées. Collez-les dans votre mail.'); },
     function () { show(); alert('Copie impossible : sélectionnez le texte affiché.'); });
 }
 function save() {
   var b = new Blob([answer()], {type: 'application/json'});
   var a = document.createElement('a');
   a.href = URL.createObjectURL(b);
   a.download = 'reponse_invitation.json';
   a.click();
 }
</script>
</div></body></html>
"""


def main():
    os.makedirs(FORMS, exist_ok=True)
    reaction_list = reactions()
    html = PAGE % {
        "n_checkpoints": N_CHECKPOINTS,
        "minutes": MINUTES,
        "reactions": "".join(render_reaction(i + 1, r)
                             for i, r in enumerate(reaction_list)),
        "choices": render_choices(reaction_list),
    }
    target = os.path.join(FORMS, "00_invitation_chimistes.html")
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(html)
    print("ecrit : %s" % target)


if __name__ == "__main__":
    main()

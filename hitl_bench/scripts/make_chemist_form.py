r"""Build the page a chemist is shown at a checkpoint, as a standalone HTML file.

The chemist does not code and may not know what Bayesian optimisation is. So the
page shows the campaign the way a chemist reads one - a table of experiments with
named reagents and real units - and never mentions hypervolume, acquisition
functions or Pareto fronts. It asks three things: what they make of the campaign,
what they want to do about it, and whether they recognised the system.

That last question is not optional. The Reizman work is published and its
conclusion, PCy3 at 110 C, is in the abstract. A participant who recognises the
system recites rather than reasons, and without asking you cannot tell the two
apart afterwards.

Works on both kinds of log: the Suzuki campaigns written by hitl_bench.campaign,
and the other benchmarks written by run_other_benchmarks.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/make_chemist_form.py --list
    .venv\Scripts\python.exe hitl_bench/scripts/make_chemist_form.py ^
        --log ii__no_hitl__seed03 --stop-at 16
"""

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")
DATA = os.path.join(HERE, "data")
FORMS = os.path.join(HERE, "forms")

# How each reaction is introduced, and how each quantity is labelled. Everything
# a chemist reads comes from here; nothing is generated from variable names.
PRESENTATION = {
    "suzuki": {
        "title": "Couplage de Suzuki-Miyaura en flux continu",
        "intro": "Un robot de chimie en flux teste des conditions une par une. Après "
                 "chaque essai, un algorithme choisit la suivante. La campagne "
                 "ci-dessous est en cours.",
        "params": {"ligand": ("Catalyseur", ""), "res_time": ("Temps de séjour", "s"),
                   "temperature": ("Température", "°C"),
                   "catalyst_loading": ("Charge en Pd", "mol%")},
        "objectives": {"yield": ("Rendement", "%", "haut"),
                       "turnover": ("TON", "", "haut")},
    },
    "edbo_ch_arylation": {
        "title": "Arylation C–H",
        "intro": "Une campagne d'optimisation teste des conditions une par une : un "
                 "algorithme choisit chaque essai à partir des précédents. On cherche "
                 "un bon rendement sans faire exploser le coût des réactifs.",
        "params": {"ligand": ("Ligand", ""), "base": ("Base", ""),
                   "solvent": ("Solvant", ""), "concentration": ("Concentration", "M"),
                   "temperature": ("Température", "°C")},
        "objectives": {"yield": ("Rendement", "%", "haut"),
                       "cost": ("Coût des réactifs", "", "bas")},
    },
    "snar": {
        "title": "Substitution nucléophile aromatique en flux",
        "intro": "Une campagne d'optimisation en flux continu. On cherche à produire "
                 "beaucoup tout en produisant peu de déchets — les deux tirent en sens "
                 "contraire.",
        "params": {"tau": ("Temps de séjour", "min"),
                   "equiv_pldn": ("Équivalents de pyrrolidine", ""),
                   "conc_dfnb": ("Concentration en DFNB", "M"),
                   "temperature": ("Température", "°C")},
        "objectives": {"sty": ("Productivité", "kg·m⁻³·h⁻¹", "haut"),
                       "e_factor": ("Facteur E (déchets)", "", "bas")},
    },
    "buchwald": {
        "title": "Couplage de Buchwald-Hartwig",
        "intro": "Une campagne d'optimisation teste des conditions une par une : un "
                 "algorithme choisit chaque essai à partir des précédents.",
        "params": {"aryl_halide": ("Halogénure d'aryle", ""), "additive": ("Additif", ""),
                   "base": ("Base", ""), "ligand": ("Ligand", "")},
        "objectives": {"yield": ("Rendement", "%", "haut")},
    },
    "lnp3": {
        "title": "Formulation de nanoparticules lipidiques",
        "intro": "Une campagne d'optimisation de formulation. On veut charger un "
                 "maximum de principe actif, l'encapsuler efficacement, et obtenir des "
                 "particules petites.",
        "params": {"drug_input": ("Principe actif", "mg"),
                   "solid_lipid": ("Lipide solide", ""),
                   "solid_lipid_input": ("Lipide solide", "mg"),
                   "liquid_lipid_input": ("Lipide liquide", "mg"),
                   "surfractant_input": ("Tensioactif", "")},
        "objectives": {"drug_loading": ("Charge en principe actif", "", "haut"),
                       "encap_efficiency": ("Efficacité d'encapsulation", "", "haut"),
                       "particle_diameter": ("Diamètre des particules", "", "bas")},
    },
}
SKIP = {"experiment", "phase", "iteration", "seconds", "hypervolume", "igd_plus", "model"}


def presentation_for(name):
    if name.startswith("buchwald"):
        return PRESENTATION["buchwald"]
    if name in PRESENTATION:
        return PRESENTATION[name]
    if name in ("i", "ii", "iii", "iv"):
        return PRESENTATION["suzuki"]
    raise SystemExit("aucune presentation pour %r; ajoutez-la dans PRESENTATION" % name)


def catalyst_names():
    path = os.path.join(DATA, "catalyst_names.json")
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def label_value(key, value, names):
    """A chemist reads names, not codes. L4 becomes PCy3 (P1-L5)."""
    if key == "ligand" and names and str(value) in names["mapping"]:
        entry = names["mapping"][str(value)]
        return ("%s (%s)" % (entry["ligand"], entry["pair"])) if entry.get("ligand") \
            else entry["pair"]
    if isinstance(value, float):
        return ("%.3g" % value)
    return str(value)


def build(stem, stop_at):
    log = json.load(open(os.path.join(RESULTS, stem + ".json"), encoding="utf-8"))
    config = log["config"]
    name = config.get("benchmark") or config.get("case")
    pres = presentation_for(name)
    names = catalyst_names() if pres is PRESENTATION["suzuki"] else None

    objectives = [o for o in (config.get("objectives") or []) if o in log["experiments"][0]]
    params = [k for k in log["experiments"][0] if k not in SKIP and k not in objectives]
    records = log["experiments"][:stop_at]

    # a bar next to each experiment, scaled on the first objective
    first = objectives[0]
    span = max(abs(r[first]) for r in records) or 1.0

    head = "".join("<th>%s%s</th>" % (pres["params"].get(p, (p, ""))[0],
                                      _unit(pres["params"].get(p, (p, ""))[1]))
                   for p in params)
    head += "".join("<th>%s%s</th>" % (pres["objectives"].get(o, (o, "", ""))[0],
                                       _unit(pres["objectives"].get(o, (o, "", ""))[1]))
                    for o in objectives)

    rows = []
    for r in records:
        cells = "".join("<td>%s</td>" % label_value(p, r[p], names) for p in params)
        cells += "".join('<td class=n>%.3g</td>' % r[o] for o in objectives)
        rows.append("<tr><td class=n>%d</td>%s<td class=bar><span style=\"width:%.1f%%\">"
                    "</span></td></tr>" % (r["experiment"], cells,
                                           100.0 * abs(r[first]) / span))

    # a per-level summary on the first categorical, which is what a chemist scans
    cat = next((p for p in params if isinstance(records[0][p], str)), None)
    summary_block = ""
    if cat:
        groups = {}
        for r in records:
            groups.setdefault(label_value(cat, r[cat], names), []).append(r[first])
        body = "".join("<tr><td>%s</td><td class=n>%d</td><td class=n>%.3g</td>"
                       "<td class=n>%.3g</td></tr>"
                       % (k, len(v), max(v), sum(v) / len(v))
                       for k, v in sorted(groups.items(), key=lambda kv: -max(kv[1])))
        summary_block = SUMMARY % {
            "what": pres["params"].get(cat, (cat, ""))[0],
            "metric": pres["objectives"].get(first, (first, "", ""))[0], "rows": body}

    goals = "".join("<li><b>%s</b> — à rendre %s</li>"
                    % (pres["objectives"].get(o, (o, "", "haut"))[0],
                       pres["objectives"].get(o, (o, "", "haut"))[2]) for o in objectives)
    variables = "".join("<li><b>%s</b> — %s</li>"
                        % (pres["params"].get(p, (p, ""))[0], _choices(log, p, names))
                        for p in params)
    fields = "".join(_field(log, p, pres, names) for p in params)

    html = PAGE % {
        "title": pres["title"], "intro": pres["intro"], "n": len(records),
        "budget": config["n_init"] + config["n_iterations"],
        "head": head, "rows": "\n".join(rows), "summary": summary_block,
        "goals": goals, "variables": variables, "fields": fields,
        "campaign_id": "%s-exp%02d" % (stem, stop_at),
    }
    os.makedirs(FORMS, exist_ok=True)
    path = os.path.join(FORMS, "%s_exp%02d.html" % (stem, stop_at))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(html)
    return path


def _unit(unit):
    return (" (%s)" % unit) if unit else ""


def _levels(log, key):
    return sorted({r[key] for r in log["experiments"]},
                  key=lambda v: (isinstance(v, str), v))


def _choices(log, key, names):
    values = _levels(log, key)
    if isinstance(values[0], str):
        return ", ".join(label_value(key, v, names) for v in values)
    return "de %.3g à %.3g" % (min(values), max(values))


def _field(log, key, pres, names):
    label = pres["params"].get(key, (key, ""))[0]
    unit = _unit(pres["params"].get(key, (key, ""))[1])
    values = _levels(log, key)
    if isinstance(values[0], str):
        options = "".join("<option>%s</option>" % label_value(key, v, names) for v in values)
        control = '<select name="%s">%s</select>' % (key, options)
    else:
        control = ('<input name="%s" type="number" step="any" min="%.4g" max="%.4g" '
                   'value="%.4g">' % (key, min(values), max(values), max(values)))
    return '<div><label class="hint">%s%s</label>%s</div>' % (label, unit, control)


SUMMARY = """<div class="card scroll">
<p style="margin-top:0"><b>Résumé par %(what)s</b></p>
<table><thead><tr><th>%(what)s</th><th>Essais</th><th>Meilleur %(metric)s</th>
<th>%(metric)s moyen</th></tr></thead><tbody>%(rows)s</tbody></table></div>"""


PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s — votre avis</title>
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
 p{margin:.6rem 0;max-width:62ch}
 .lede{color:var(--soft);font-size:1.05rem;max-width:60ch}
 .card{background:var(--card);border:1px solid var(--rule);border-radius:6px;
       padding:1.1rem 1.3rem;margin:1rem 0}
 ul{margin:.4rem 0;padding-left:1.2rem} li{margin:.2rem 0}
 table{border-collapse:collapse;width:100%%;font-size:.92rem}
 th,td{padding:.4rem .6rem;border-bottom:1px solid var(--rule);text-align:left}
 th{font-size:.7rem;letter-spacing:.05em;text-transform:uppercase;color:var(--faint);
    font-weight:600}
 td.n{text-align:right;font-variant-numeric:tabular-nums}
 td.bar{width:16%%;padding-right:0}
 td.bar span{display:block;height:.6rem;border-radius:2px;background:var(--accent);
             min-width:2px}
 .scroll{overflow-x:auto}
 label{display:block;margin:.9rem 0 .25rem;font-weight:600;font-size:.95rem}
 .hint{font-weight:400;color:var(--soft);font-size:.88rem}
 textarea,select,input{width:100%%;padding:.5rem .6rem;border:1px solid var(--rule);
        border-radius:4px;font:inherit;background:#fff;color:var(--ink)}
 textarea{min-height:5.5rem;resize:vertical}
 .choices{display:flex;flex-direction:column;gap:.5rem;margin-top:.5rem}
 .choice{display:flex;gap:.6rem;align-items:flex-start;padding:.7rem .9rem;
         border:1px solid var(--rule);border-radius:5px;background:#fff;cursor:pointer}
 .choice:hover{border-color:var(--accent)}
 .choice input{width:auto;margin-top:.25rem}
 .choice b{display:block} .choice span{color:var(--soft);font-size:.9rem}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));gap:.8rem}
 #proposal{display:none;margin-top:.8rem;padding-top:.8rem;border-top:1px dashed var(--rule)}
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

<h1>%(title)s</h1>
<p class="lede">%(intro)s</p>
<div class="note">Il n'y a pas de bonne réponse attendue. Ce qui nous intéresse est
votre raisonnement de chimiste, pas de deviner ce que l'algorithme ferait.</div>

<h2>La réaction</h2>
<p>Ce qui peut être réglé :</p>
<ul>%(variables)s</ul>
<p>Ce qui est mesuré à chaque essai :</p>
<ul>%(goals)s</ul>

<h2>Où en est la campagne</h2>
<p><b>%(n)d essais faits sur %(budget)d prévus.</b> Voici tout ce qui a été testé,
dans l'ordre.</p>
<div class="card scroll">
<table><thead><tr><th>#</th>%(head)s<th></th></tr></thead>
<tbody>%(rows)s</tbody></table></div>
%(summary)s

<h2>Vos réponses</h2>
<form id="f">
<label>1. Que pensez-vous de cette campagne ?
<span class="hint">Va-t-elle dans la bonne direction ? Quelque chose vous gêne ?</span></label>
<textarea name="reading" placeholder="Quelques phrases suffisent."></textarea>

<label>2. Que faut-il faire maintenant ?</label>
<div class="choices">
 <label class="choice"><input type="radio" name="decision" value="proposer">
  <span><b>Je propose un essai</b><span>Vous choisissez les conditions du prochain
  essai, puis l'algorithme reprend la main.</span></span></label>
 <label class="choice"><input type="radio" name="decision" value="continuer">
  <span><b>Laisser l'algorithme continuer</b><span>La campagne travaille bien.</span></span></label>
 <label class="choice"><input type="radio" name="decision" value="arreter">
  <span><b>Arrêter la campagne</b><span>Il n'y a plus grand-chose à espérer, autant
  garder les essais restants.</span></span></label>
</div>

<div id="proposal">
 <label>Les conditions que vous proposez</label>
 <div class="grid">%(fields)s</div>
 <label>Pourquoi ces conditions ?</label>
 <textarea name="why" placeholder="Le raisonnement nous intéresse autant que le point."></textarea>
</div>

<label>3. Aviez-vous reconnu ce système chimique ?
<span class="hint">Question de méthode, pas un examen : répondre non n'est pas un aveu.</span></label>
<div class="choices">
 <label class="choice"><input type="radio" name="known" value="oui"><span><b>Oui</b>
  <span>Je connais cette réaction et son résultat publié.</span></span></label>
 <label class="choice"><input type="radio" name="known" value="peut-etre"><span>
  <b>Ça me dit quelque chose</b><span>Sans être sûr.</span></span></label>
 <label class="choice"><input type="radio" name="known" value="non"><span><b>Non</b>
  <span>Je raisonne uniquement sur ce que je vois ici.</span></span></label>
</div>

<label>4. À quel point êtes-vous sûr de vous ?</label>
<select name="confidence"><option value="">—</option><option>1 — pas du tout</option>
<option>2</option><option>3 — moyennement</option><option>4</option>
<option>5 — tout à fait</option></select>

<label>Votre nom ou vos initiales
<span class="hint">pour relier vos réponses entre les cas</span></label>
<input name="who" placeholder="ex. MC">

<div class="actions">
 <button type="button" onclick="show()">Voir ma réponse</button>
 <button type="button" class="ghost" onclick="copyIt()">Copier ma réponse</button>
 <button type="button" class="ghost" onclick="save()">Enregistrer un fichier</button>
</div>
<p class="hint">Copiez votre réponse dans un mail, ou enregistrez le fichier et
renvoyez-le. Rien n'est envoyé automatiquement.</p>
<div id="out"></div>
</form>

<script>
 var CAMPAIGN = "%(campaign_id)s";
 document.querySelectorAll('input[name=decision]').forEach(function (r) {
   r.addEventListener('change', function () {
     document.getElementById('proposal').style.display =
       (r.value === 'proposer' && r.checked) ? 'block' : 'none';
   });
 });
 function answer() {
   var d = {campagne: CAMPAIGN, date: new Date().toISOString()};
   new FormData(document.getElementById('f')).forEach(function (v, k) { d[k] = v; });
   return JSON.stringify(d, null, 2);
 }
 function show() {
   var o = document.getElementById('out');
   o.textContent = answer(); o.style.display = 'block';
 }
 function copyIt() {
   navigator.clipboard.writeText(answer()).then(
     function () { alert('Réponse copiée. Collez-la dans votre mail.'); },
     function () { show(); alert('Copie impossible : sélectionnez le texte affiché.'); });
 }
 function save() {
   var b = new Blob([answer()], {type: 'application/json'});
   var a = document.createElement('a');
   a.href = URL.createObjectURL(b);
   a.download = 'reponse_' + CAMPAIGN + '.json';
   a.click();
 }
</script>
</div></body></html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", help="log stem, e.g. ii__no_hitl__seed03")
    parser.add_argument("--stop-at", type=int, default=16)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list or not args.log:
        for path in sorted(glob.glob(os.path.join(RESULTS, "*.json"))):
            log = json.load(open(path, encoding="utf-8"))
            name = log["config"].get("benchmark") or log["config"].get("case")
            print("%-34s %s" % (os.path.basename(path)[:-5], name))
        return
    print("ecrit :", build(args.log, args.stop_at))


if __name__ == "__main__":
    main()

r"""Build the page a chemist is shown at a checkpoint, as a standalone HTML file.

The chemist does not code and may not know what Bayesian optimisation is. So the
page shows the campaign the way a chemist reads one - a table of experiments with
named catalysts and real units - and never mentions hypervolume, acquisition
functions or Pareto fronts. It asks three things: what they make of the campaign,
what they want to do about it, and whether they recognised the system.

That last question is not optional. The Reizman work is published and its
conclusion, PCy3 at 110 C, is in the abstract. A participant who recognises the
system recites rather than reasons, and without asking you cannot tell the two
apart afterwards.

    cd C:\Users\mathi\REACTO\dash-chem
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe hitl_bench/scripts/make_chemist_form.py ^
        --case ii --seed 3 --stop-at 16
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")
DATA = os.path.join(HERE, "data")
FORMS = os.path.join(HERE, "forms")

REACTION = {
    "title": "Couplage de Suzuki-Miyaura en flux continu",
    "intro": "Un robot de chimie en flux teste des conditions une par une. "
             "Après chaque essai, un algorithme choisit la condition suivante. "
             "La campagne ci-dessous est en cours, et on vous demande votre avis.",
    "variables": [
        ("Catalyseur", "7 possibilités, voir la liste"),
        ("Temps de séjour", "de 60 à 600 s"),
        ("Température", "de 30 à 110 °C"),
        ("Charge en palladium", "de 0,5 à 2,5 mol%"),
    ],
    "measured": [("Rendement", "%"), ("TON", "nombre de rotations du catalyseur")],
}


def catalyst_label(code, names):
    entry = names["mapping"].get(code, {})
    ligand, pair = entry.get("ligand"), entry.get("pair", code)
    return "%s (%s)" % (ligand, pair) if ligand else pair


def build(case, seed, stop_at):
    names = json.load(open(os.path.join(DATA, "catalyst_names.json"), encoding="utf-8"))
    log = json.load(open(os.path.join(RESULTS, "%s__no_hitl__seed%02d.json" % (case, seed)),
                         encoding="utf-8"))
    records = log["experiments"][:stop_at]
    labels = [catalyst_label(c, names) for c in
              sorted({r["ligand"] for r in log["experiments"]})]
    all_codes = sorted(names["mapping"])
    options = "".join('<option value="%s">%s</option>' % (c, catalyst_label(c, names))
                      for c in all_codes if c != "L7")

    best = max(r["yield"] for r in records) or 1.0
    rows = []
    for r in records:
        width = 100.0 * r["yield"] / max(best, 1e-9)
        rows.append(
            "<tr><td class=n>%d</td><td>%s</td><td class=n>%.0f</td><td class=n>%.0f</td>"
            "<td class=n>%.2f</td><td class=n>%.1f</td><td class=n>%.1f</td>"
            "<td class=bar><span style=\"width:%.1f%%\"></span></td></tr>"
            % (r["experiment"], catalyst_label(r["ligand"], names), r["res_time"],
               r["temperature"], r["catalyst_loading"], r["yield"], r["turnover"], width))

    by_catalyst = {}
    for r in records:
        key = catalyst_label(r["ligand"], names)
        by_catalyst.setdefault(key, []).append(r["yield"])
    summary = "".join(
        "<tr><td>%s</td><td class=n>%d</td><td class=n>%.1f</td><td class=n>%.1f</td></tr>"
        % (k, len(v), max(v), sum(v) / len(v))
        for k, v in sorted(by_catalyst.items(), key=lambda kv: -max(kv[1])))

    html = PAGE % {
        "title": REACTION["title"],
        "intro": REACTION["intro"],
        "n": len(records),
        "budget": log["config"]["n_init"] + log["config"]["n_iterations"],
        "rows": "\n".join(rows),
        "summary": summary,
        "options": options,
        "variables": "".join("<li><b>%s</b> — %s</li>" % v for v in REACTION["variables"]),
        "campaign_id": "%s-seed%02d-exp%02d" % (case, seed, stop_at),
        "catalysts": ", ".join(labels),
    }
    os.makedirs(FORMS, exist_ok=True)
    path = os.path.join(FORMS, "campagne_%s_seed%02d.html" % (case, seed))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(html)
    return path


PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s — votre avis</title>
<style>
 :root{--ink:#16181d;--soft:#5b6472;--faint:#8b93a1;--rule:#dfe3e9;--paper:#f7f8fa;
       --card:#fff;--accent:#1f5f8b;--accent-soft:#e6eef5;--warm:#a8552f}
 *{box-sizing:border-box}
 body{margin:0;background:var(--paper);color:var(--ink);
      font:16px/1.6 "Segoe UI",system-ui,sans-serif}
 .wrap{max-width:60rem;margin:0 auto;padding:2rem 1.5rem 5rem}
 h1{font-size:1.7rem;margin:0 0 .3rem;line-height:1.2}
 h2{font-size:1.15rem;margin:2.2rem 0 .8rem;padding-bottom:.4rem;
    border-bottom:1px solid var(--rule)}
 p{margin:.6rem 0;max-width:62ch}
 .lede{color:var(--soft);font-size:1.05rem;max-width:60ch}
 .card{background:var(--card);border:1px solid var(--rule);border-radius:6px;
       padding:1.1rem 1.3rem;margin:1rem 0}
 ul{margin:.4rem 0;padding-left:1.2rem}
 table{border-collapse:collapse;width:100%%;font-size:.92rem}
 th,td{padding:.4rem .6rem;border-bottom:1px solid var(--rule);text-align:left}
 th{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);
    font-weight:600}
 td.n{text-align:right;font-variant-numeric:tabular-nums}
 td.bar{width:26%%;padding-right:0}
 td.bar span{display:block;height:.62rem;border-radius:2px;background:var(--accent);
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
 .choice b{display:block}
 .choice span{color:var(--soft);font-size:.9rem}
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
<p>Le robot peut régler quatre choses :</p>
<ul>%(variables)s</ul>
<p>Deux résultats sont mesurés à chaque essai : le <b>rendement</b> en %% et le
<b>TON</b>, le nombre de rotations du catalyseur, qui dit combien de produit on
obtient par unité de palladium. On cherche à avoir les deux élevés.</p>
<p class="hint">Catalyseurs disponibles : %(catalysts)s. Deux d'entre eux ne sont
pas nommés dans l'article d'origine et gardent leur code.</p>

<h2>Où en est la campagne</h2>
<p><b>%(n)d essais faits sur %(budget)d prévus.</b> Voici tout ce qui a été
testé, dans l'ordre.</p>
<div class="card scroll">
<table><thead><tr><th>#</th><th>Catalyseur</th><th>Temps (s)</th><th>T (°C)</th>
<th>Pd (mol%%)</th><th>Rendement (%%)</th><th>TON</th><th>Rendement</th></tr></thead>
<tbody>%(rows)s</tbody></table>
</div>

<div class="card scroll">
<p style="margin-top:0"><b>Résumé par catalyseur</b></p>
<table><thead><tr><th>Catalyseur</th><th>Essais</th><th>Meilleur rendement</th>
<th>Rendement moyen</th></tr></thead><tbody>%(summary)s</tbody></table>
</div>

<h2>Vos réponses</h2>
<form id="f">
<label>1. Que pensez-vous de cette campagne ?
<span class="hint">Va-t-elle dans la bonne direction ? Quelque chose vous gêne ?</span></label>
<textarea name="reading" placeholder="Quelques phrases suffisent."></textarea>

<label>2. Que faut-il faire maintenant ?</label>
<div class="choices">
 <label class="choice"><input type="radio" name="decision" value="proposer">
  <span><b>Je propose un essai</b><span>Vous choisissez vous-même les conditions du
  prochain essai, puis le robot reprend la main.</span></span></label>
 <label class="choice"><input type="radio" name="decision" value="continuer">
  <span><b>Laisser l'algorithme continuer</b><span>La campagne travaille bien, pas
  besoin d'intervenir.</span></span></label>
 <label class="choice"><input type="radio" name="decision" value="arreter">
  <span><b>Arrêter la campagne</b><span>Il n'y a plus grand-chose à espérer, autant
  garder les essais restants.</span></span></label>
</div>

<div id="proposal">
 <label>Les conditions que vous proposez</label>
 <div class="grid">
  <div><label class="hint">Catalyseur</label><select name="catalyst">%(options)s</select></div>
  <div><label class="hint">Temps de séjour (s)</label>
       <input name="res_time" type="number" min="60" max="600" step="1" value="600"></div>
  <div><label class="hint">Température (°C)</label>
       <input name="temperature" type="number" min="30" max="110" step="1" value="100"></div>
  <div><label class="hint">Pd (mol%%)</label>
       <input name="loading" type="number" min="0.5" max="2.5" step="0.05" value="2.0"></div>
 </div>
 <label>Pourquoi ces conditions ?</label>
 <textarea name="why" placeholder="Le raisonnement nous intéresse autant que le point."></textarea>
</div>

<label>3. Aviez-vous reconnu ce système chimique ?
<span class="hint">Réponse sans conséquence : c'est une question de méthode, pas un examen.</span></label>
<div class="choices">
 <label class="choice"><input type="radio" name="known" value="oui"><span>
  <b>Oui</b><span>Je connais cette réaction et son résultat publié.</span></span></label>
 <label class="choice"><input type="radio" name="known" value="peut-etre"><span>
  <b>Ça me dit quelque chose</b><span>Sans être sûr.</span></span></label>
 <label class="choice"><input type="radio" name="known" value="non"><span>
  <b>Non</b><span>Je raisonne uniquement sur ce que je vois ici.</span></span></label>
</div>

<label>4. À quel point êtes-vous sûr de vous ?</label>
<select name="confidence">
 <option value="">—</option><option>1 — pas du tout</option><option>2</option>
 <option>3 — moyennement</option><option>4</option><option>5 — tout à fait</option>
</select>

<label>Votre nom ou vos initiales <span class="hint">pour relier vos réponses entre les cas</span></label>
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
   navigator.clipboard.writeText(answer()).then(function () {
     alert('Réponse copiée. Collez-la dans votre mail.');
   }, function () { show(); alert('Copie impossible : sélectionnez le texte affiché.'); });
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
    parser.add_argument("--case", default="ii")
    parser.add_argument("--seed", type=int, default=3)
    parser.add_argument("--stop-at", type=int, default=16,
                        help="last experiment the chemist is shown")
    args = parser.parse_args()
    print("ecrit :", build(args.case, args.seed, args.stop_at))


if __name__ == "__main__":
    main()

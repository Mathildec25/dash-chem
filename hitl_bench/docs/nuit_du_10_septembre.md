# Nuit du 10 au 11 septembre — rapport

Rédigé au fil de la nuit. Les chiffres viennent de `results/arms_report_edbo_ch_arylation.md`,
qui est régénéré par `analyse_arms.py` et donc toujours à jour ; ce document-ci
raconte ce qui a été fait et ce qu'il faut en penser.

## 1. La reproductibilité, qui bloquait tout

**Le problème.** Deux exécutions identiques d'une même campagne, même graine,
même processus, divergeaient à partir de l'expérience 26 — AUC 16,42 contre
17,46. Ton design apparié repose entièrement sur l'idée qu'un fork sans
intervention reproduit sa campagne parente ; sans ça, l'écart entre bras mélange
l'effet de l'intervention et du bruit d'exécution.

**La cause.** REACTO construisait la stratégie BoFire **sans lui passer de
graine**. BoFire en tire alors une lui-même :

```python
seed = np.random.SeedSequence().generate_state(1, dtype=np.uint32).item()
```

`np.random.SeedSequence()` sans argument puise dans **l'entropie du système
d'exploitation**. Vérifié : après `np.random.seed(0)`, `torch.manual_seed(0)` et
`random.seed(0)`, trois appels donnent 1025538384, 2553151549, 4229010206. Aucune
graine globale ne l'atteint. Une graine fraîche était donc tirée **à chacun des
trente pas d'acquisition de chaque campagne**, les échantillons quasi-Monte-Carlo
différaient, et là où deux candidats se valaient de peu l'argmax basculait.

**La correction.** `bayesian_optimization` accepte désormais `seed=`. Avec
`None`, le comportement de l'application est inchangé au bit près. Le banc
d'essai passe une graine dérivée de la campagne et de l'itération —
arithmétique et non hachée, pour qu'on puisse la retrouver à la main depuis un
log, et différente à chaque itération pour ne pas rejouer trente fois les mêmes
points quasi-Monte-Carlo.

**Vérifications.** Deux exécutions identiques coïncident sur les 40 expériences
et à la douzième décimale sur l'AUC. Un fork sans intervention reproduit sa
parente **exactement**, aux points de branchement 15, 22 et 30.

**Conséquence à assumer.** Les 51 campagnes antérieures ne se rejouent pas. Elles
restent valides comme échantillons indépendants — taux d'échec, structure du
piège, instants de déclenchement — mais ne peuvent pas servir de bras témoin.
Tout ce qui suit a été recalculé.

`runtime.py` affirmait le contraire ; le paragraphe est corrigé et daté.

## 2. Les deux bras calculables

**Trois décisions de conception**, chacune pouvant se discuter, toutes inscrites
dans le code :

Le point injecté **remplace** la proposition de la BO au lieu de s'y ajouter.
Les deux bras dépensent donc exactement 40 expériences, et un gain ne peut pas
venir d'une mesure supplémentaire.

Les alertes sont **recalculées après chaque intervention**. Une injection
déplace la campagne, donc les alertes de la parente ne sont plus celles de la
branche ; le trigger est réévalué sur la nouvelle histoire.

Chaque parente est branchée **plusieurs fois** avec des tirages différents. Un
seul point au hasard ne dit rien de ce que « le hasard » obtient à cet instant.

**Le protocole** est celui que tu as figé : P\*, W = 5, seuil 0,30, cooldown 5,
première alerte possible à l'expérience 15.

## 3. Ce que ça donne sur l'arylation C–H

Chiffres à 19 branches sur 40 ; ils bougeront encore un peu.

| | campagnes | fraction du front | atteignent 90 % |
|---|---|---|---|
| BO seule | 20 | 0,888 | **10 / 20 (50 %)** |
| + point au hasard aux alertes | 19 | 0,915 | **14 / 19 (74 %)** |

**Gain apparié moyen : +2,7 points** de fraction du front. Il était de +4,0 à
onze branches : l'estimation redescend quand l'échantillon grandit, ce qui est
attendu, et c'est une raison de ne pas s'emballer sur le chiffre moyen.

**L'effet le plus net n'est pas le gain moyen mais le taux de succès** : la
moitié des campagnes atteignent 90 % du front sans intervention, les trois quarts
avec.

### D'où vient le gain

C'est le résultat que je trouve le plus utile pour l'article, parce qu'il est
mécanistique et pas seulement descriptif.

```
points injectés sur un ligand du front : 16 / 63
gain final moyen : +4,2 pt quand oui, +2,7 pt quand non
```

Tomber sur un ligand qui porte le front rapporte nettement plus, et le hasard n'y
tombe qu'**une fois sur quatre**. C'est exactement la quantité que ton bras humain
doit battre : un chimiste qui sait quel ligand choisir devrait faire mieux, et on
sait désormais de combien.

## 4. Ce qui est prêt pour les chimistes

**Une page dans REACTO**, `/chemist-input`. Elle lit des checkpoints déposés en
JSON, donc ajouter une campagne ne demande aucune modification de code.

Vingt checkpoints sont générés, un par campagne, **à sa première alerte**.

Trois choix de conception, chacun destiné à ne pas fabriquer de données :

- **Rien n'est pré-sélectionné.** Un menu posé sur sa première valeur
  alphabétique ressemble à une réponse et serait enregistré comme telle.
- **Toute proposition est un point de la grille**, donc toujours évaluable.
- **La réponse attendue n'est jamais servie avec la question.** Elle vit dans
  `forms/checkpoint_keys/`, que la page ne lit pas — vérifié explicitement.

**L'évaluation du troisième bras est écrite** (`evaluate_human.py`) : elle relit
une réponse, rejoue la campagne avec le point proposé, et rend le gain apparié
ainsi que son percentile parmi les tirages au hasard du même checkpoint.

## 5. Ce que je n'ai pas pu faire, et ce qui cloche

**Le percentile individuel n'est pas atteignable avec ce lot.** Comme on
intervient à chaque alerte, seule la première est commune entre deux répétitions
d'une même graine : avec deux tirages par graine, on n'a que deux points de
comparaison par checkpoint. Ça suffit pour l'effet moyen du hasard, pas pour
situer la réponse d'un chimiste. Il faudrait une nuit dédiée à un tir groupé sur
la première alerte seulement — environ vingt tirages sur cinq campagnes.

**J'avais prévu cinq tirages par graine, j'ai dû descendre à deux.** Une branche
coûte 7,5 minutes et non 4 : cent branches auraient demandé 12,5 heures.

**Le substrat de l'arylation nous est inconnu.** Les données viennent d'un
criblage réel publié (Torres et al., *JACS* 2022), mais ni le jeu redistribué ni
le dépôt ne donnent la structure, et l'article est derrière un péage. Tes
chimistes pourront raisonner sur les ligands, bases et solvants — l'essentiel du
criblage — mais pas sur le substrat. À leur dire, et à écrire dans l'article.

**J'ai tué deux fois des calculs qui fonctionnaient**, en croyant les processus
bloqués : la colonne CPU de `Get-Process` ne se met pas à jour pour ces
processus, et le vrai processus s'appelle `python3.11` et non `python`. J'ai
perdu une vingtaine de minutes. La seule mesure fiable est le nombre de fichiers
écrits.

## 6. Où en est le calcul

Bras 1 arylation complet, bras 2 en cours, Suzuki cas ii en cours. Les deux
boucles reprennent d'elles-mêmes après une coupure mémoire et sautent ce qui
existe déjà.

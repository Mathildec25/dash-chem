# Ce que font les chimistes, et ce qu'on leur dit

Document de travail. Ce que les chimistes reçoivent, c'est un lien vers la page
**HITL live** de REACTO et une page Word d'introduction ; ceci explique ce que
la page leur fait faire et pourquoi.

## Ce qu'ils font

Trois campagnes, une par réaction (Suzuki cas I, Suzuki cas II, arylation C–H),
dans l'ordre qu'ils veulent, dix à quinze minutes chacune. Pour chaque
campagne :

1. Ils lisent la chimie : le schéma réactionnel, les catalyseurs dessinés, les
   conditions, ce qu'on contrôle et ce qu'on mesure, les prix au gramme quand le
   coût est un objectif.
2. Ils regardent les dix essais de départ (tirés au hasard, identiques pour
   tout le monde) et lancent l'optimiseur.
3. Les essais défilent un par seconde. Ce sont exactement ceux de la campagne
   témoin assignée : tant que le chimiste n'impose rien, tout le monde voit la
   même campagne.
4. Quand l'alarme se déclenche (P\*, W = 5, seuil 0,30, cooldown 5, au plus
   tôt à l'essai 15), la page s'arrête et demande une des trois réponses,
   **avec une justification obligatoire** :
   - laisser l'algorithme continuer (sa prochaine proposition est affichée) ;
   - proposer soi-même le prochain essai (menus déroulants sur les niveaux de
     la grille) — dès lors l'optimiseur tourne pour de vrai à partir de là ;
   - arrêter la campagne.
5. Tout est sauvegardé à chaque essai. Un chimiste qui ferme la page reprend
   plus tard en choisissant son nom dans la liste « Resume ».

## Ce qu'ils ne voient jamais

Les mots hypervolume, fonction d'acquisition, front de Pareto ; la valeur de
P\* ; les résultats des autres participants ; les optima publiés par les
articles (la colonne « conditions optimales » a été retirée du schéma Suzuki
exprès). Un participant qui saurait quel catalyseur porte le front ne
mesurerait rien.

## Les campagnes assignées, et pourquoi

`forms/live/assignment.json`. Une campagne piégée par réaction, choisie parmi
les vingt témoins (`scripts/seed_choice.py`) : la BO seule finit sous 90 % du
front, l'alarme sonne assez tôt pour qu'il reste du budget, et le ligand
gagnant a été vu dans le plan initial — un chimiste qui lit la table peut
remarquer qu'il a été écarté.

| Réaction | Graine | BO seule | 1re alerte | Le piège |
|---|---|---|---|---|
| Suzuki I | 8 | 69 % | 20 | Xantphos vu une fois à 40 °C → 0 %, retrouvé trop tard |
| Suzuki II | 12 | 44 % | 16 | PCy3 vu une fois à 0 %, la campagne finit sur XPhos |
| Arylation | 2 | 72 % | 16 | 77 % sur CgMe-PPh dès le départ, puis plus rien pendant 28 essais |

## Ce qu'on en tire

`scripts/collect_live.py` produit une ligne par campagne (résultat final contre
le témoin au même essai et au budget complet, réponses données à chaque alerte)
et une ligne par décision (choix, P\*, justification, point imposé, ce que
l'optimiseur aurait fait). La comparaison est **appariée** : chaque branche de
chimiste contre sa campagne témoin, et contre le bras aléatoire mesuré sur la
même campagne (`results/arms/`). Point ouvert : comment comparer une campagne
arrêtée à un témoin qui a dépensé 40 essais (voir `CLAUDE.md`).

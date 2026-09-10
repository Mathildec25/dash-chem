# Quelles réactions montrer aux chimistes

Compte rendu de la recherche de nouveaux bancs d'essai, nuit du 8 au 9 septembre.
Onze grilles ont été récupérées et dix ont été effectivement testées avec notre
BO. Ce document dit laquelle retenir et pourquoi.

> **Mise à jour du 10 septembre.** La provenance des neuf grilles ajoutées
> cette nuit-là n'avait pas été consignée. Elle a depuis été rétablie et
> vérifiée pour **les neuf** (`data/other/README.md`,
> `scripts/verify_other_grids.py`), y compris l'arylation C–H, qui s'avère être
> les mesures expérimentales originales d'EDBO+. Deux surprises au passage : la
> SNAr n'est pas un jeu de données mais un modèle cinétique sans bruit, et
> l'arylation n'est pas l'expansion virtuelle de Minerva.

## Ce qu'on cherchait

Le protocole a besoin d'une réaction qui remplit trois conditions à la fois, et
la troisième est celle qui élimine presque tout.

**1. Une grille factorielle complète.** Toutes les combinaisons de conditions
sont déjà mesurées, donc le front de Pareto exact est connu et évaluer un point
est une simple lecture de table. C'est ce qui rend une campagne reproductible à
la virgule près et ce qui permet de dire « cette campagne a atteint 58 % du
front global », une phrase impossible avec un émulateur entraîné.

**2. Des réactifs qui ont un nom.** C'est ta contrainte, et elle est
éliminatoire : un chimiste ne peut pas répondre à « que penses-tu de L4 ? » ni à
« que penses-tu du ligand dont le descripteur stérique vaut 2,7 ? ». Il faut
qu'il puisse dire « essaie plutôt la XPhos ». Beaucoup de jeux de données
publics sont anonymisés ou fournis uniquement sous forme de descripteurs
calculés ; ceux-là ont été écartés d'office.

**3. De la place pour que le chimiste change quelque chose.** C'est le critère
le plus important et le moins évident. Si la BO seule trouve le front à tous les
coups, l'intervention du chimiste ne peut rien améliorer et l'expérience ne
mesure rien. Si elle échoue toujours, pareil. Il faut une réaction où le
résultat **dépend de la chance du tirage initial**.

On mesure ça très simplement : on lance la même BO sur plusieurs graines
aléatoires et on regarde l'écart entre la meilleure et la pire campagne. Un
écart large veut dire que la campagne aurait pu tourner autrement, donc qu'il y
a quelque chose à corriger.

## Le tableau de sélection

Fraction du front de Pareto global atteinte en 40 expériences (10 tirages
initiaux + 30 propositions de la BO), sur 3 à 5 graines.

| Réaction | Points | Objectifs | Moyenne | Écart pire → meilleure | Réactifs nommés |
|---|---|---|---|---|---|
| **Suzuki cas ii** | 5 670 | rendement, TON | 67 % | **63 points** | oui |
| **Suzuki cas i** | 5 670 | rendement, TON | 87 % | **45 points** | oui |
| **Arylation C–H (EDBO+)** | 1 728 | rendement, coût | 85 % | **22 points** | oui |
| Suzuki cas iii | 5 670 | rendement, TON | 95 % | 20 points | oui |
| Buchwald-Hartwig (a) | 792 | rendement seul | 84 % | 9 points | non (SMILES) |
| Nanoparticules lipidiques | 768 | 3 objectifs | 97,5 % | 3 points | oui |
| Buchwald-Hartwig (d) | 792 | rendement seul | 92 % | 3 points | non (SMILES) |
| Suzuki cas iv | 5 670 | rendement, TON | 96 % | 2 points | oui |
| SNAr en flux | 900 | productivité, facteur E | 100 % | **0 point** | pas de catalyseur |
| Colorants laser | 3 458 | 3 objectifs | **27 %** | 29 points | SMILES seuls |

La colonne qui décide est l'avant-dernière, pas la moyenne.

## Ce que je propose de montrer aux chimistes

### Réaction principale : le Suzuki cas ii, qu'on garde

C'est déjà notre cas d'étude et rien de ce que j'ai trouvé cette nuit ne fait
mieux. L'écart entre graines est de 63 points de front, et surtout l'échec a une
cause chimique lisible : les campagnes qui ratent se fixent sur la **XPhos** et
n'en bougent plus, alors que tout le front global est sur la **PCy3**. Ce n'est
pas un artefact numérique, c'est ce que dit le papier de Reizman — PCy3 à 110 °C
est le bon catalyseur, XPhos donne des rendements moyens à plus basse
température. Un chimiste à qui on montre une campagne bloquée sur XPhos a une
vraie raison de proposer autre chose.

Réserve à garder en tête : la conclusion du papier est publiée et figure dans le
résumé. Un participant qui reconnaît le système récite au lieu de raisonner.
C'est pour ça que le formulaire pose la question « avez-vous reconnu cette
réaction ? » — sans elle on ne peut pas séparer les deux après coup.

### Deuxième réaction : l'arylation C–H d'EDBO+

> **Provenance établie le 10 septembre**, après une alerte : la grille avait été
> ajoutée sans que rien ne soit consigné, et elle a été brièvement retirée. Elle
> est identique, au dernier chiffre sur le rendement **et** sur le coût, au
> fichier `experiments_yield_and_cost.csv` du dépôt officiel EDBO+
> (Torres et al., JACS 2022, DOI 10.1021/jacs.2c08592).
>
> Point important découvert au passage : ce sont les **mesures réelles**, pas
> l'expansion virtuelle par modèle que distribue Minerva (7680 lignes, mêmes
> niveaux mais valeurs de modèle). Voir `data/other/README.md`.

C'était la trouvaille de la nuit, et elle est complémentaire du Suzuki sur un
point précis.

Sur le Suzuki, nos deux objectifs sont le rendement et le TON, qui sont
largement redondants — pousser l'un pousse l'autre. Ici les deux objectifs sont
le **rendement** et le **coût des réactifs**, et leur corrélation sur la grille
est de **−0,002**, c'est-à-dire rien du tout. C'est un vrai problème
multi-objectif : il faut arbitrer, pas seulement optimiser.

Tout est nommé et lisible : 12 ligands (BrettPhos, CgMe-PPh, GorlosPhos·HBF4,
JackiePhos, P(fur)₃, PCy₃·HBF₄, PPh₂Me, PPh₃, PPhMe₂, PPh(tBu)₂, XPhos,
tBPh-CPhos), 4 bases (CsOAc, CsOPiv, KOAc, KOPiv), 4 solvants (BuCN, BuOAc,
DMAc, p-xylène), 3 concentrations, 3 températures. 1 728 combinaisons.

Le front global tient en 9 points, et il a une structure qu'un chimiste peut
reconnaître : **9 fois sur 9 le solvant est le DMAc**, et 7 fois sur 9 la base
est le KOPiv. Les ligands du front sont CgMe-PPh (rendements de 98 à 100 %) et
PPh₃ (rendements moyens mais très bon marché) — les deux extrémités de
l'arbitrage. Une campagne qui n'a jamais essayé le DMAc à haute concentration ne
peut pas atteindre le front, et ça se voit à l'œil nu dans le tableau
d'expériences.

Une campagne dure 4 minutes, contre 12 pour le Suzuki. C'est confortable quand
il faudra en lancer plusieurs centaines pour la comparaison appariée.

### Contrôle : la SNAr en flux

À garder, mais pas pour la même chose. Les trois graines atteignent **100 % du
front**, à chaque fois. Il n'y a rien à réparer, donc rien à demander à un
chimiste.

Vérification faite, ce n'est pas la grille SNAr d'Olympus — celle-ci fait 66
lignes, la nôtre 900. C'est le **modèle cinétique** `SnarBenchmark` de Summit
évalué sur une grille 6×6×5×5, confirmé en le rejouant. Autrement dit ce sont
des valeurs calculées par un modèle mécanistique, **sans aucun bruit de mesure**,
et quatre variables continues et lisses. Les 100 % ne sont donc pas un exploit de
la BO, c'est ce qu'on attend d'un paysage analytique sans bruit. À dire tel quel
si on s'en sert comme contrôle.

J'y étais allé en pensant que ce serait le cas où le déclencheur doit rester
silencieux. Mesuré, il ne l'est pas : il se déclenche 4 à 5 fois par campagne.
Mais en regardant *quand*, ce n'est pas une fausse alerte — voir la section
suivante, qui est le résultat le plus utile de la nuit.

## Ce que le déclencheur fait sur ces nouvelles réactions

J'ai passé notre déclencheur (P\*, le rythme récent rapporté au rythme moyen) sur
toutes les campagnes, sans rien réajuster. Il ne lit que la courbe d'avancement,
donc il tourne tel quel sur des réactions qu'il n'a jamais vues — ce qui est
précisément ce qu'on lui demandait.

La question intéressante n'est pas « se déclenche-t-il ? » mais **« au premier
déclenchement, combien restait-il encore à gagner ? »**. C'est ce chiffre qui
décide si la bonne réponse du chimiste est « arrête » ou « essaie plutôt ça ».

Deux colonnes sont nécessaires, et c'est là tout l'intérêt. « Gain restant » est
mesuré par rapport à ce que **cette campagne-là** finira par atteindre ; « niveau
final » par rapport au **front global**, que la campagne ne connaît pas.

| Campagne | 1er déclenchement | Gain restant à ce moment | Niveau final atteint | Bon geste |
|---|---|---|---|---|
| SNAr, 3 graines | exp. 13-17 | 0-2 % | **100 %** | arrêter, gratuit |
| Buchwald, 6 graines | exp. 13 | 0-8 % | 80-94 % | arrêter |
| Arylation C–H, graine 2 | exp. 16 | **0 %** | **72 %** | **intervenir** |
| Arylation C–H, graines 1 et 3 | exp. 13, 19 | 23 %, 36 % | 94 %, 89 % | continuer |
| Suzuki ii, graines 1, 3, 5 | exp. 14-18 | 20 %, 29 %, 62 % | 58 %, 37 %, 47 % | **intervenir** |
| Suzuki ii, graine 4 | exp. 15 | **86 %** | **100 %** | continuer |

Comparez la ligne SNAr et la ligne « arylation, graine 2 ». Les deux ont le même
signal : le déclencheur sonne, et il ne reste plus rien à gagner. Vues de
l'intérieur de la campagne, elles sont **indiscernables**. Vue de l'extérieur,
l'une est à 100 % du front et l'autre à 72 %, coincée pour de bon.

C'est la même conclusion qu'on avait tirée du Suzuki — aucun signal calculé sur
l'historique de la campagne ne distingue une campagne coincée d'une campagne
finie — mais elle est ici démontrée sur cinq réactions supplémentaires, dont des
chimies sans rapport entre elles. Ce n'est plus une observation sur un jeu de
données, c'est une propriété du problème.

Et ça donne, je pense, l'argument le plus solide qu'on ait pour ta décision de
laisser le chimiste choisir entre proposer et arrêter plutôt que l'algorithme.
Ce qui sépare ces deux lignes, c'est de savoir si la chimie a encore quelque
chose à offrir : la SNAr est un espace lisse à quatre variables continues qu'on
a fini d'explorer, l'arylation graine 2 n'a jamais essayé le bon ligand. Un
chimiste voit la différence en regardant le tableau ; le déclencheur, non.

La graine 4 du Suzuki ii est le contre-exemple à ne pas oublier : le déclencheur
sonne à l'expérience 15 alors que **86 % du gain restait à venir**, sur la seule
campagne qui atteint 100 % du front. Si l'algorithme avait décidé d'arrêter, il
aurait tué la meilleure campagne du lot.

Le cas ii reste donc le meilleur banc d'essai pour la question, précisément
parce qu'il est celui où le déclencheur est le plus ambigu.

## Une chose à savoir sur l'arylation avant de la retenir

En regardant les campagnes d'arylation ligne par ligne, j'ai vu quelque chose
d'anormal : à partir de l'expérience 25 environ, les trois graines proposent la
même chose, dans l'ordre alphabétique des ligands, en balayant les quatre
solvants dans l'ordre alphabétique aussi. CgMe-PPh, puis GorlosPhos, puis
JackiePhos, puis P(fur)₃ — quelle que soit l'histoire de la campagne. Ce n'est
pas de l'optimisation, c'est une lecture de table.

J'ai mesuré ce qui se passe. À l'expérience 30, sur les 1 698 conditions encore
possibles, **175 sont exactement à égalité** au maximum de la fonction
d'acquisition — égalité au dernier chiffre de la représentation flottante, pas
« presque ». Le modèle est rigoureusement indifférent entre elles, et c'est donc
l'ordre de la table qui tranche.

La cause est simple et instructive. La grille a 12 ligands × 4 bases × 4
solvants = **192 combinaisons catégorielles**, et une campagne de 40 expériences
n'en visite que **17**. Pour toutes les autres, le modèle n'a strictement rien
qui les distingue : même a priori, même postérieur, même valeur d'acquisition.
Vérifié : les 175 ex æquo sont **toutes** dans une combinaison jamais visitée, et
aucune dans une combinaison visitée.

**J'ai vérifié que le Suzuki n'a pas ce problème** — c'est le point important,
parce que c'est lui qui porte l'étude. Sur les quatre cas, à l'expérience 20, 30
et 40, le maximum de l'acquisition est **unique à chaque fois**, sans aucun ex
æquo. Un seul catégoriel à 7 niveaux, ça se couvre en 40 expériences ; trois
catégoriels qui font 192 cellules, non.

### Le même défaut, en pire, sur les colorants laser

Les colorants laser en donnent la forme extrême, et c'est ce qui les élimine
vraiment. Leur grille est faite de trois fragments moléculaires et de rien
d'autre : 14 × 13 × 19 = **3 458 combinaisons, toutes catégorielles, sans aucune
variable continue**. Une campagne de 40 expériences en visite 30.

À l'expérience 30, la mesure donne : maximum de l'acquisition −4,59192, médiane
−4,59192, minimum −4,59192. **Les 3 428 candidats restants sont tous à égalité,
à 100 %.** Le modèle n'a aucune opinion sur quoi que ce soit, et la campagne
n'est plus qu'une lecture de la table dans l'ordre. C'est pour ça qu'elle
n'atteint que 27 % du front : elle n'optimise pas du tout.

Les trois cas se rangent proprement, et le classement suit la part de l'espace
catégoriel que le budget permet de visiter :

| Réaction | Cellules catégorielles | Visitées en 40 exp. | Candidats à égalité |
|---|---|---|---|
| Suzuki (1 catégoriel, 7 niveaux) | 7 | toutes | **0** |
| Arylation C–H | 192 | 17 (9 %) | 175 sur 1 698 (10 %) |
| Colorants laser | 3 458 | 30 (0,9 %) | 3 428 sur 3 428 (**100 %**) |

Ça donne au passage une mesure simple qu'on pourrait mettre dans l'article : **la
proportion de candidats à égalité dit si la BO fonctionne encore**. À 0 % elle
optimise, à 100 % elle épelle la table. C'est calculable en cours de campagne,
sans rien connaître du front.

### Ce que ça change pour l'arylation

Est-ce que ça disqualifie l'arylation ? Je ne pense pas, mais ça change ce
qu'elle raconte. Le Suzuki et l'arylation illustrent **deux façons différentes
dont une BO à petit budget échoue** :

- **Suzuki cas ii — la sur-exploitation.** Le modèle a une opinion, elle est
  fausse, et il s'y enferme : il rejoue XPhos et ses environs. Le chimiste sert à
  contredire une conviction.
- **Arylation — la sous-détermination.** Le modèle n'a aucune opinion sur 90 %
  de l'espace et le dit en donnant la même note à 175 conditions. Le chimiste
  sert à fournir l'information qui manque.

C'est arguablement plus intéressant que d'avoir deux fois le même échec, et ça
donne un argument chiffré très direct pour la boucle humaine : à l'expérience 30,
l'algorithme choisit alphabétiquement entre 175 conditions équivalentes ; un
chimiste qui nomme un ligand apporte strictement plus que ça.

À condition de le dire dans l'article. Une comparaison « intervention du chimiste
contre BO seule » où la BO seule balaye la table par ordre alphabétique doit être
présentée comme telle.

## Ce que j'écarte, et pourquoi

**Les nanoparticules lipidiques.** Trois objectifs, ce qui aurait été un joli
élargissement, et des lipides nommés (Compritol 888, monostéarate de glycéryle,
acide stéarique). Mais la BO atteint 97,5 % du front en moyenne (98,6, 95,4, 98,4) avec un écart de 3
points entre graines : il n'y a rien à réparer. Et une campagne coûte 16 minutes
au lieu de 4, parce que le calcul d'hypervolume en trois dimensions est cher.
Mauvais rapport coût / information.

**Les cinq grilles Buchwald-Hartwig.** Elles n'ont qu'un seul objectif, le
rendement, ce qui les met hors de notre cadre multi-objectif. Et leurs ligands,
bases et additifs sont stockés en SMILES bruts, pas en noms — les traduire
demanderait le même travail de vérification qu'on a fait pour les catalyseurs du
Suzuki, et je ne veux pas deviner. Je les garde de côté au cas où tu voudrais
plus tard une extension mono-objectif.

**Les colorants laser.** Correction de ce que j'avais écrit plus haut dans la
nuit : leurs fragments ne sont pas des codes anonymes, ce sont des SMILES —
acides boroniques, cœurs BODIPY, dibromoarènes. Un chimiste peut les lire, mais
avec un effort, et ce n'est pas l'ergonomie « donne-moi un nom de ligand » qu'on
cherche.

Ce n'est de toute façon pas le motif décisif. C'est la réaction où la BO échoue
le plus fort — 15 %, 23 % et 44 % du front — et j'ai failli la retenir pour ça.
Mais la mesure ci-dessus montre qu'elle n'échoue pas *en optimisant mal* : elle
n'optimise pas. Comparer « chimiste » contre une BO qui lit la table dans
l'ordre ne mesurerait rien. Ajoutons que la photophysique n'est pas le métier de
tes chimistes et qu'une campagne coûte 25 minutes, la plus chère du lot.

## Les documents pour les chimistes

### Le notebook Colab, `forms/campagnes_chimistes.ipynb`

C'est la voie retenue. Un seul lien, rien à installer, rien à télécharger, ça s'ouvre sur téléphone, et aucun serveur de messagerie ne bloque un lien Colab — là où une pièce jointe `.html` se fait souvent jeter par Outlook. Le notebook vit dans le dépôt, donc celui qui reprendra rouvrira exactement la page que les participants ont vue.

Le chimiste ne voit **jamais de code** : chaque cellule porte `cellView: "form"`, le mécanisme de Colab qui masque la source et n'affiche que les champs. Trois gestes, sans jamais parler de cellule :

1. **Exécution → Tout exécuter** : les tableaux s'affichent.
2. Remplir les champs.
3. **Exécution → Tout exécuter** à nouveau, puis cliquer sur le bouton d'envoi. Le lien ouvre leur logiciel de mail avec tout déjà rédigé.

Le deuxième « Tout exécuter » n'est pas une coquetterie : modifier un champ `#@param` réécrit la source de la cellule mais ne la relance pas, et une relance complète est le seul geste qui capture toutes les réponses sans avoir à expliquer ce qu'est une cellule.

**Les menus déroulants sont construits à partir de la grille, pas de l'historique de la campagne.** Une campagne de 40 essais ne touche qu'une poignée de niveaux ; n'offrir que ceux-là interdirait silencieusement de demander 1,0 mol%, une condition parfaitement valide que cette campagne n'a pas essayée. C'est précisément ce qu'on veut leur laisser demander. Corollaire utile : toute proposition est forcément un point de la grille, donc évaluable par simple lecture de table.

Les quatre campagnes retenues sont équilibrées exprès : deux où il faut intervenir, une qui a l'air mal partie et se rétablit seule, une où il n'y a plus rien à trouver.

### Les deux autres jeux de pages

Il en existe deux sortes, et l'ordre compte.

### 1. L'invitation, `forms/00_invitation_chimistes.html`

C'est le fichier que tu leur envoies en premier, avant qu'ils voient la moindre
campagne. Il explique en quelques phrases ce qu'on cherche, ce qu'on leur
demande et combien de temps ça prend, puis présente les trois réactions dans
leurs termes : ce qu'on peut régler, ce qu'on mesure, avec les vrais niveaux lus
directement dans les grilles — la page ne peut donc pas se désynchroniser de ce
que les campagnes font vraiment. Il finit par quatre questions.

Deux d'entre elles ne sont pas de la politesse.

**« Connaissez-vous déjà ce système ? »**, posée *avant* de montrer quoi que ce
soit. La conclusion de Reizman est publiée et figure dans le résumé de
l'article : PCy3 à 110 °C. Un participant qui la connaît récitera au lieu de
raisonner, et il faut pouvoir faire le tri après coup. Posée après avoir vu une
campagne, la question invite à se sous-déclarer ; posée avant, sans enjeu, non.

**« Qu'est-ce qui vous met la puce à l'oreille quand une série n'avance
plus ? »** C'est littéralement l'énoncé de ton déclencheur, posé à des humains
avant qu'on leur montre le nôtre. Si plusieurs chimistes citent spontanément un
signal auquel on n'avait pas pensé, c'est un résultat en soi ; s'ils citent ceux
qu'on a déjà testés et rejetés, c'est un argument pour la section « signaux
écartés ».

Les deux autres questions sont utilitaires : sur quelles réactions ils acceptent
de se prononcer, et leur patience habituelle avant d'arrêter une campagne.

Les sept ligands du Suzuki y sont nommés, sauf deux : la page dit « plus 2 paires
dont le nom n'est pas publié (P1-L6, P1-L7) » plutôt que de lâcher un code
inexpliqué au milieu d'une liste de phosphines. Deviner ces deux noms
corromprait l'étude, c'est écrit dans `data/catalyst_names.json`.

### 2. Les pages de checkpoint

Les pages sont dans `hitl_bench/forms/`. Ce sont des fichiers HTML autonomes :
un double-clic les ouvre dans n'importe quel navigateur, il n'y a rien à
installer, et ils fonctionnent hors ligne.

Ce que la page montre : le tableau des expériences déjà faites, avec les noms
des réactifs et les vraies unités, plus une barre visuelle par ligne pour voir
d'un coup d'œil où ça monte. Ce qu'elle ne montre jamais : le mot hypervolume,
la fonction d'acquisition, le front de Pareto. Rien qui suppose de connaître la
BO.

Ce qu'elle demande, dans cet ordre :
1. Ce que le chimiste comprend de la campagne telle qu'elle est.
2. Ce qu'il veut en faire : proposer une expérience précise, ou arrêter la
   campagne. C'est bien lui qui choisit entre les deux, pas nous.
3. S'il a reconnu le système.

### Les neuf pages, et ce que chacune teste

Chaque page s'arrête exactement à l'expérience où **le déclencheur sonne pour la
première fois** sur cette campagne — pas à un moment choisi à la main. La
dernière colonne est la réponse attendue, à ne pas leur montrer.

| Fichier | Ce que le chimiste voit à ce point | Fin sans intervention |
|---|---|---|
| `ii…seed01_exp18` | 8 essais d'affilée sur **XPhos**, rendement plafonné à 27 % | 58 % |
| `ii…seed03_exp16` | enfermée sur **RuPhos**, rendement à 24 % | **37 %**, la pire |
| `ii…seed05_exp14` | hésite entre XPhos et SPhos, 18 % au mieux | 47 % |
| `ii…seed04_exp15` | 16 % au mieux, ça a l'air mal parti | **100 %** — le piège |
| `i…seed02_exp29` | 87 % déjà atteint, campagne d'apparence réussie | **55 %** |
| `edbo…seed01_exp13` | départ correct | 94 % |
| `edbo…seed03_exp19` | milieu de campagne | 89 % |
| `edbo…seed02_exp16` | rendement bloqué sous 77 % | **72 %**, coincée |
| `snar…seed01_exp14` | tout est déjà trouvé | 100 % |

Deux pages sont là pour vérifier que les chimistes ne disent pas oui à tout.
`ii…seed04` a l'air mal partie et finira pourtant à 100 % : un chimiste qui
propose d'arrêter là se trompe. `snar…seed01` n'a plus rien à donner : un
chimiste qui propose une expérience de plus dépense pour rien. Sans ces deux
cas, on ne pourra pas dire si leurs interventions valent mieux que « intervenir
tout le temps ».

# Ce qu'on demande aux chimistes, et comment

Document de travail, pas le document qu'ils reçoivent. Celui-là est la page
**Chemist input** de REACTO ; ceci explique ce qu'elle contient et pourquoi.

## Ce qu'ils voient

Une campagne d'optimisation arrêtée en cours de route. Le tableau de tous les
essais déjà faits, avec les réactifs nommés et les vraies unités, les dix
premiers grisés parce qu'ils sont le tirage de départ et non des choix de
l'algorithme. Puis quatre questions.

Ils ne voient jamais les mots hypervolume, fonction d'acquisition ou front de
Pareto. Un participant qui doit apprendre ce que ça veut dire avant de répondre
est évalué sur l'optimisation bayésienne, pas sur sa chimie.

## Les quatre questions, et pourquoi chacune

**1. Que pensez-vous de cette campagne ?** En texte libre, avant toute
proposition. C'est le diagnostic brut : ce qu'un chimiste remarque sans qu'on
l'oriente. Si plusieurs citent spontanément le même signal — « elle n'a jamais
essayé le DMAc », « elle tourne sur le même ligand » — c'est un résultat en soi,
et c'est comparable à ce que notre déclencheur détecte.

**2. Que faut-il faire ?** Proposer un essai, laisser continuer, ou arrêter.
C'est le chimiste qui choisit entre les trois, pas nous : on a mesuré qu'aucun
signal calculé sur l'historique ne distingue une campagne coincée d'une campagne
finie, donc la décision d'arrêter ne peut pas être automatisée.

Rien n'est pré-coché. Un menu posé sur sa première valeur alphabétique
ressemble à une réponse et serait enregistré comme telle.

**3. Aviez-vous reconnu la réaction ?** Question de méthode. Certaines de ces
chimies sont publiées, et la conclusion du Suzuki figure dans le résumé de
l'article de Reizman. Un participant qui la reconnaît récite au lieu de
raisonner, et sans cette question on ne peut pas faire le tri après coup. Elle
est posée après l'examen mais avant qu'on ne révèle quoi que ce soit.

**4. À quel point êtes-vous sûr ?** Permet de pondérer, et surtout de voir si la
confiance prédit la qualité de la suggestion. Rien ne garantit qu'elle le fasse.

## Contraintes de conception

**Toute proposition est un point de la grille.** Les menus sont construits à
partir du banc d'essai, donc un chimiste ne peut pas demander une condition que
nous serions incapables d'évaluer. C'est une contrainte réelle qu'il faut leur
dire : ils choisissent parmi des niveaux existants, pas dans un continuum.

**Une réponse par fichier.** Chaque enregistrement produit un JSON nommé d'après
le checkpoint et le participant, donc deux chimistes répondant au même
checkpoint ne s'écrasent pas et rassembler les données revient à copier un
dossier.

**La réponse attendue n'est jamais servie avec la question.** Elle vit dans
`forms/checkpoint_keys/`, que la page ne lit pas. Un seul fichier contenant les
deux fuirait par les outils de développement du navigateur, ou par un transfert
de pièce jointe un peu rapide.

## Combien de checkpoints par personne

Le déclencheur figé — P\*, W=5, seuil 0,30, cooldown 5 — sonne **2,5 fois par
campagne** en moyenne sur le cas Suzuki ii, et 3,3 sur l'arylation. Comme on
intervient à chaque alerte, une campagne complète demande donc trois réponses en
moyenne à la même personne, dans l'ordre, puisque chaque intervention change la
suite.

C'est le point à arbitrer avec le temps disponible : couvrir peu de campagnes en
entier, ou beaucoup de campagnes sur leur première alerte seulement. Le premier
choix est plus fidèle à un usage réel, le second donne plus de points de
comparaison indépendants.

## Une limite à annoncer

**Le substrat de l'arylation C–H n'est pas connu de nous.** Les données viennent
d'un criblage réel publié (Torres et al., *J. Am. Chem. Soc.* 2022, 144,
19999-20007), mais ni le jeu de données redistribué ni le dépôt ne donnent la
structure. Un chimiste peut donc raisonner sur les ligands, les bases et les
solvants — ce qui est déjà l'essentiel du criblage — mais pas sur le substrat.

Il faut le leur dire plutôt que de les laisser chercher une information absente,
et il faut le dire dans l'article. Sur le Suzuki, à l'inverse, la chimie est
entièrement identifiée.

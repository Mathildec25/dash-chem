"""
Optimisation Bayésienne avec descripteurs de solvants
ET CONTRAINTES TEMPÉRATURE/POINT D'ÉBULLITION
Version COMPLÈTEMENT DISCRÈTE (contraintes natives BoFire)
"""

import pandas as pd
import numpy as np
from bofire.data_models.features.api import (
    CategoricalDescriptorInput, 
    DiscreteInput,
    ContinuousOutput
)
from bofire.data_models.domain.api import Domain, Inputs, Outputs, Constraints
from bofire.data_models.strategies.api import SoboStrategy
from bofire.data_models.objectives.api import MinimizeObjective
from bofire.strategies.api import SoboStrategy as SoboStrategyRunner

# ✅ IMPORTS POUR LES CONTRAINTES
from bofire.data_models.constraints.api import (
    CategoricalExcludeConstraint,
    SelectionCondition,
    ThresholdCondition
)

import sys

print(f"🐍 Python: {sys.executable}")
print(f"📦 Pandas: {pd.__version__}")
print(f"📦 Numpy: {np.__version__}")

# ===== 1. DÉFINITION DU PROBLÈME =====
print("=" * 70)
print("OPTIMISATION BAYÉSIENNE AVEC ESPACE COMPLÈTEMENT DISCRET")
print("ET CONTRAINTES NATIVES BOFIRE")
print("=" * 70)

solvents = ["Water", "Ethanol", "DMSO", "Acetone"]
descriptors = ["Polarity", "Viscosity"]
descriptor_values = [
    [10.2, 1.0],   # Water
    [5.2, 1.2],    # Ethanol  
    [7.2, 2.0],    # DMSO
    [5.1, 0.3]     # Acetone
]

boiling_points = {
    "Water": 100,      # °C
    "Ethanol": 78.4,   # °C
    "DMSO": 189,       # °C
    "Acetone": 56      # °C
}

SAFETY_MARGIN = 10  # °C
TEMP_STEP = 5       # Pas de la grille de température (°C)
CONC_STEP = 0.1     # Pas de la grille de concentration (M)

print(f"\n📊 Solvants: {solvents}")
print(f"🌡️  Points d'ébullition avec marge de sécurité:")
for solvent, bp in boiling_points.items():
    print(f"   {solvent}: {bp}°C → T_max = {bp - SAFETY_MARGIN}°C")

# ===== 2. CRÉER LES FEATURES =====
print("\n" + "=" * 70)
print("CRÉATION DES FEATURES")
print("=" * 70)

try:
    solvent_feature = CategoricalDescriptorInput(
        key="Solvent",
        categories=solvents,
        allowed=[True, True, True, True],
        descriptors=descriptors,
        values=descriptor_values
    )
    print("✅ CategoricalDescriptorInput créé")
    print("\nDescripteurs:")
    print(solvent_feature.to_df())
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ✅ TEMPÉRATURE DISCRÉTISÉE
temp_values = list(range(20, 201, TEMP_STEP))  # [20, 25, 30, ..., 200]
temperature_feature = DiscreteInput(
    key="Temperature",
    values=temp_values
)
print(f"\n✅ Température discrétisée:")
print(f"   Grille: {len(temp_values)} valeurs de {temp_values[0]}°C à {temp_values[-1]}°C")
print(f"   Pas: {TEMP_STEP}°C")

# ✅ CONCENTRATION DISCRÉTISÉE
conc_values = [round(x, 2) for x in np.arange(0.1, 2.05, CONC_STEP)]
concentration_feature = DiscreteInput(
    key="Concentration",
    values=conc_values
)
print(f"\n✅ Concentration discrétisée:")
print(f"   Grille: {len(conc_values)} valeurs de {conc_values[0]}M à {conc_values[-1]}M")
print(f"   Pas: {CONC_STEP}M")

yield_output = ContinuousOutput(
    key="Yield",
    objective=MinimizeObjective(w=1.0)
)

# ===== 3. CRÉER LES CONTRAINTES =====
print("\n" + "=" * 70)
print("CRÉATION DES CONTRAINTES TEMPÉRATURE/POINT D'ÉBULLITION")
print("=" * 70)

constraint_list = []

for solvent_name, bp in boiling_points.items():
    try:
        temp_limit = bp - SAFETY_MARGIN
        
        # Trouver la température discrète la plus proche (arrondie vers le bas)
        temp_limit_discrete = temp_limit - (temp_limit % TEMP_STEP)
        
        # CategoricalExcludeConstraint exclut les combinaisons où:
        # Solvent == solvent_name AND Temperature >= temp_limit_discrete
        constraint = CategoricalExcludeConstraint(
            features=["Solvent", "Temperature"],
            conditions=[
                SelectionCondition(selection=[solvent_name]),
                ThresholdCondition(threshold=temp_limit_discrete, operator=">="),
            ],
        )
        constraint_list.append(constraint)
        print(f"   ✅ Contrainte: {solvent_name} → T < {temp_limit_discrete}°C "
              f"(limite réelle: {temp_limit}°C)")
        
    except Exception as e:
        print(f"   ❌ Erreur pour {solvent_name}: {e}")

# Créer l'objet Constraints
try:
    constraints = Constraints(constraints=constraint_list)
    print(f"\n✅ {len(constraint_list)} contrainte(s) créée(s)")
except Exception as e:
    print(f"\n❌ Erreur lors de la création des contraintes: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ===== 4. CRÉER LE DOMAINE AVEC CONTRAINTES =====
print("\n" + "=" * 70)
print("CRÉATION DU DOMAINE AVEC CONTRAINTES")
print("=" * 70)

try:
    domain = Domain(
        inputs=Inputs(features=[solvent_feature, temperature_feature, concentration_feature]),
        outputs=Outputs(features=[yield_output]),
        constraints=constraints  # ✅ Contraintes natives
    )
    
    print(f"\n✅ Domaine créé avec:")
    print(f"   - {len(domain.inputs)} inputs (tous discrets/catégoriels)")
    print(f"   - {len(domain.outputs)} outputs")
    print(f"   - {len(domain.constraints.constraints)} contraintes natives")
    print(f"   - Espace de recherche: {len(solvents)} × {len(temp_values)} × {len(conc_values)} "
          f"= {len(solvents) * len(temp_values) * len(conc_values):,} combinaisons possibles")
    
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ===== 5. GÉNÉRATION DE DONNÉES INITIALES VALIDES =====
print("\n" + "=" * 70)
print("GÉNÉRATION DE DONNÉES INITIALES")
print("=" * 70)

np.random.seed(42)

# Fonction pour vérifier les contraintes
def is_valid_experiment(row):
    """Vérifie si une expérience respecte les contraintes BP"""
    solvent = row["Solvent"]
    temp = row["Temperature"]
    bp = boiling_points[solvent]
    limit = bp - SAFETY_MARGIN
    return temp < limit

# Générer des échantillons valides
initial_experiments = pd.DataFrame()
max_attempts = 1000
attempts = 0

while len(initial_experiments) < 8 and attempts < max_attempts:
    # Générer un batch de samples
    samples = domain.inputs.sample(n=20, seed=42+attempts)
    
    # Filtrer pour ne garder que les valides
    valid_mask = samples.apply(is_valid_experiment, axis=1)
    valid_samples = samples[valid_mask]
    
    # Ajouter aux expériences initiales
    if len(valid_samples) > 0:
        initial_experiments = pd.concat([initial_experiments, valid_samples], ignore_index=True)
    
    attempts += 1

# Garder seulement le nombre demandé
initial_experiments = initial_experiments.head(8)

print(f"✅ {len(initial_experiments)} expériences initiales valides générées:")
print(initial_experiments[["Solvent", "Temperature", "Concentration"]])

# ===== 6. FONCTION DUMMY POUR SIMULER LES RÉSULTATS =====
def dummy_experiment(row):
    """Fonction simulée pour générer des résultats"""
    solvent_effect = {"Water": 0.5, "Ethanol": 1.0, "DMSO": 1.5, "Acetone": 2.0}
    base = solvent_effect.get(row["Solvent"], 1.0)
    temp_effect = (row["Temperature"] - 60) ** 2 / 1000
    conc_effect = (row["Concentration"] - 1.0) ** 2
    noise = np.random.randn() * 0.5
    return base + temp_effect + conc_effect + noise

initial_experiments["Yield"] = initial_experiments.apply(dummy_experiment, axis=1)
all_experiments = initial_experiments.copy()

# ===== 7. INITIALISER LA STRATÉGIE BO =====
print("\n" + "=" * 70)
print("INITIALISATION DE L'OPTIMISATION BAYÉSIENNE")
print("=" * 70)

try:
    strategy_model = SoboStrategy(domain=domain)
    strategy = SoboStrategyRunner(data_model=strategy_model)
    print("✅ Stratégie SOBO créée avec contraintes natives")
    
    strategy.tell(experiments=all_experiments)
    print("✅ Données initiales fournies")
    
except Exception as e:
    print(f"❌ Erreur lors de l'initialisation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ===== 8. TEST D'UNE SUGGESTION =====
print("\n" + "=" * 70)
print("TEST: GÉNÉRATION D'UNE SUGGESTION")
print("=" * 70)

try:
    test_suggestion = strategy.ask(candidate_count=1)
    
    print("✅ Suggestion générée:")
    print(test_suggestion[["Solvent", "Temperature", "Concentration"]])
    
    # Vérifier la contrainte
    test_solvent = test_suggestion["Solvent"].values[0]
    test_temp = test_suggestion["Temperature"].values[0]
    test_bp = boiling_points[test_solvent]
    test_limit = test_bp - SAFETY_MARGIN
    
    if test_temp < test_limit:
        print(f"\n✅✅✅ CONTRAINTE RESPECTÉE!")
        print(f"   {test_solvent}: {test_temp:.1f}°C < {test_limit}°C")
    else:
        print(f"\n❌❌❌ CONTRAINTE VIOLÉE!")
        print(f"   {test_solvent}: {test_temp:.1f}°C >= {test_limit}°C")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ===== 9. BOUCLE D'OPTIMISATION =====
print("\n" + "=" * 70)
print("BOUCLE D'OPTIMISATION BAYÉSIENNE")
print("=" * 70)

n_iterations = 10

for i in range(n_iterations):
    print(f"\n📍 Itération {i+1}/{n_iterations}")
    
    try:
        # Demander suggestion
        suggestion = strategy.ask(candidate_count=1)
        
        solv = suggestion['Solvent'].values[0]
        temp = suggestion['Temperature'].values[0]
        conc = suggestion['Concentration'].values[0]
        
        print(f"   Suggestion: {solv}, T={temp:.1f}°C, C={conc:.2f}M")
        
        # Vérifier contrainte
        bp = boiling_points[solv]
        limit = bp - SAFETY_MARGIN
        is_valid = temp < limit
        status = "✅" if is_valid else "❌"
        print(f"   {status} Contrainte: {temp:.1f}°C < {limit}°C")
        
        # Évaluer
        suggestion["Yield"] = suggestion.apply(dummy_experiment, axis=1)
        
        # Mettre à jour
        strategy.tell(experiments=suggestion)
        all_experiments = pd.concat([all_experiments, suggestion], ignore_index=True)
        
        # Meilleur résultat actuel
        best_idx = all_experiments["Yield"].idxmin()
        best_exp = all_experiments.loc[best_idx]
        print(f"   🏆 Meilleur: Yield={best_exp['Yield']:.3f}, "
              f"{best_exp['Solvent']}, T={best_exp['Temperature']:.1f}°C")
        
    except Exception as e:
        print(f"❌ Erreur à l'itération {i+1}: {e}")
        import traceback
        traceback.print_exc()
        break

# ===== 10. RÉSULTATS FINAUX =====
print("\n" + "=" * 70)
print("RÉSULTATS FINAUX")
print("=" * 70)

best_idx = all_experiments["Yield"].idxmin()
best_experiment = all_experiments.loc[best_idx]

print(f"\n🎯 MEILLEURE EXPÉRIENCE:")
print(f"   Solvent: {best_experiment['Solvent']}")
print(f"   Temperature: {best_experiment['Temperature']:.1f}°C")
print(f"   Concentration: {best_experiment['Concentration']:.2f} M")
print(f"   Yield: {best_experiment['Yield']:.3f}")

# Vérification finale
print(f"\n🔍 Vérification finale: toutes expériences respectent contraintes?")
violations = 0
for _, exp in all_experiments.iterrows():
    solv = exp["Solvent"]
    temp = exp["Temperature"]
    bp = boiling_points[solv]
    limit = bp - SAFETY_MARGIN
    if temp >= limit:
        violations += 1
        print(f"   ❌ Violation: {solv} à {temp:.1f}°C >= {limit}°C")

if violations == 0:
    print(f"   ✅✅✅ TOUTES les {len(all_experiments)} expériences respectent les contraintes!")
else:
    print(f"   ⚠️ {violations}/{len(all_experiments)} violations détectées")

print(f"\n📊 Top 10 meilleures expériences:")
top10 = all_experiments.sort_values("Yield")[["Solvent", "Temperature", "Concentration", "Yield"]].head(10)
print(top10)

# ===== 11. STATISTIQUES =====
print("\n" + "=" * 70)
print("STATISTIQUES")
print("=" * 70)

print("\nDistribution des solvants testés:")
solvent_counts = all_experiments["Solvent"].value_counts()
for solvent in solvents:
    count = solvent_counts.get(solvent, 0)
    pct = 100 * count / len(all_experiments)
    print(f"   {solvent}: {count} expériences ({pct:.1f}%)")

print("\nDistribution des températures par solvant:")
for solvent in solvents:
    solvent_temps = all_experiments[all_experiments["Solvent"] == solvent]["Temperature"]
    if len(solvent_temps) > 0:
        print(f"\n{solvent}:")
        print(f"   N = {len(solvent_temps)} expériences")
        print(f"   T_min = {solvent_temps.min():.1f}°C")
        print(f"   T_max = {solvent_temps.max():.1f}°C")
        print(f"   T_mean = {solvent_temps.mean():.1f}°C ± {solvent_temps.std():.1f}°C")
        print(f"   Limite BP: < {boiling_points[solvent] - SAFETY_MARGIN}°C")

print("\n✅ Script terminé avec succès!")
print("\n" + "=" * 70)
print("RÉSUMÉ:")
print(f"   ✅ Contraintes natives BoFire utilisées")
print(f"   ✅ Espace complètement discret")
print(f"   ✅ {len(all_experiments)} expériences réalisées")
print(f"   ✅ Meilleur yield: {best_experiment['Yield']:.3f}")
print("=" * 70)
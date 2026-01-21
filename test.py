"""
Conversion du notebook bo_categorical_descriptors.ipynb en script Python
Test pour vérifier que CategoricalDescriptorInput fonctionne
"""

import pandas as pd
import numpy as np
from bofire.data_models.features.api import CategoricalDescriptorInput, ContinuousInput, ContinuousOutput
from bofire.data_models.domain.api import Domain, Inputs, Outputs
from bofire.data_models.strategies.api import SoboStrategy
from bofire.data_models.objectives.api import MinimizeObjective
from bofire.strategies.api import SoboStrategy as SoboStrategyRunner
import sys

print(f"🐍 Python utilisé: {sys.executable}")
print(f"📦 Pandas: {pd.__version__}")
print(f"📦 Numpy: {np.__version__}")

# ===== 1. DÉFINIR LE PROBLÈME =====
print("=" * 60)
print("OPTIMISATION BAYÉSIENNE AVEC DESCRIPTEURS DE SOLVANTS")
print("=" * 60)

# Définir les solvants avec leurs descripteurs
solvents = ["Water", "Ethanol", "DMSO", "Acetone"]
descriptors = ["Polarity", "Viscosity"]
descriptor_values = [
    [10.2, 1.0],   # Water
    [5.2, 1.2],    # Ethanol  
    [7.2, 2.0],    # DMSO
    [5.1, 0.3]     # Acetone
]

print(f"\n📊 Solvants disponibles: {solvents}")
print(f"📊 Descripteurs: {descriptors}")

# ===== 2. CRÉER LE FEATURE AVEC DESCRIPTEURS =====
print("\n" + "=" * 60)
print("CRÉATION DU CATEGORICAL DESCRIPTOR INPUT")
print("=" * 60)

try:
    solvent_feature = CategoricalDescriptorInput(
        key="Solvent",
        categories=solvents,
        allowed=[True, True, True, True],
        descriptors=descriptors,
        values=descriptor_values
    )
    print("\n✅ CategoricalDescriptorInput créé avec succès!")
    print("\nTableau des descripteurs:")
    print(solvent_feature.to_df())
except Exception as e:
    print(f"\n❌ Erreur lors de la création du feature: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Ajouter d'autres paramètres continus
temperature_feature = ContinuousInput(
    key="Temperature",
    bounds=(20, 100)
)

concentration_feature = ContinuousInput(
    key="Concentration",
    bounds=(0.1, 2.0)
)

# Définir l'objectif (sortie à minimiser)
yield_output = ContinuousOutput(
    key="Yield",
    objective=MinimizeObjective(w=1.0)
)

# ===== 3. VALIDATION =====
print("\n" + "=" * 60)
print("VALIDATION DES DONNÉES")
print("=" * 60)

assert len(solvent_feature.categories) == len(solvent_feature.values)
assert all(len(v) == len(solvent_feature.descriptors) for v in solvent_feature.values)
print("✅ Validation passée!")

# ===== 4. CRÉER LE DOMAINE =====
print("\n" + "=" * 60)
print("CRÉATION DU DOMAINE")
print("=" * 60)

try:
    domain = Domain(
        inputs=Inputs(features=[solvent_feature, temperature_feature, concentration_feature]),
        outputs=Outputs(features=[yield_output])
    )
    
    print(f"\n✅ Domaine créé avec {len(domain.inputs)} inputs et {len(domain.outputs)} outputs")
    print(f"   Inputs: {[f.key for f in domain.inputs.features]}")
    print(f"   Outputs: {[f.key for f in domain.outputs.features]}")
except Exception as e:
    print(f"\n❌ Erreur lors de la création du domaine: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ===== 5. GÉNÉRATION DE DONNÉES INITIALES =====
print("\n" + "=" * 60)
print("GÉNÉRATION DE DONNÉES INITIALES")
print("=" * 60)

np.random.seed(42)
initial_experiments = domain.inputs.sample(8)
print(f"\n✅ {len(initial_experiments)} expériences initiales générées:")
print(initial_experiments)

# Fonction dummy pour simuler les résultats
def dummy_experiment(row):
    """Fonction simulée pour générer des résultats"""
    # Simuler un rendement basé sur les paramètres
    solvent_effect = {"Water": 0.5, "Ethanol": 1.0, "DMSO": 1.5, "Acetone": 2.0}
    base = solvent_effect.get(row["Solvent"], 1.0)
    temp_effect = (row["Temperature"] - 60) ** 2 / 1000
    conc_effect = (row["Concentration"] - 1.0) ** 2
    return base + temp_effect + conc_effect + np.random.randn() * 0.5

# Évaluer les expériences initiales
initial_experiments["Yield"] = initial_experiments.apply(dummy_experiment, axis=1)
all_experiments = initial_experiments.copy()

print(f"\n✅ Expériences évaluées:")
print(all_experiments)

# ===== 6. STRATÉGIE D'OPTIMISATION BAYÉSIENNE =====
print("\n" + "=" * 60)
print("INITIALISATION DE LA STRATÉGIE BO")
print("=" * 60)

try:
    strategy_model = SoboStrategy(domain=domain)
    strategy = SoboStrategyRunner(data_model=strategy_model)
    
    print("✅ Stratégie SOBO créée")
    
    # Fournir les données initiales
    strategy.tell(experiments=all_experiments)
    print("✅ Données initiales fournies à la stratégie")
    
except Exception as e:
    print(f"\n❌ Erreur lors de l'initialisation de la stratégie: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ===== 7. BOUCLE D'OPTIMISATION =====
print("\n" + "=" * 60)
print("BOUCLE D'OPTIMISATION BAYÉSIENNE")
print("=" * 60)

n_iterations = 10

for i in range(n_iterations):
    print(f"\n📍 Itération {i+1}/{n_iterations}")
    
    try:
        # Demander la prochaine suggestion
        suggestion = strategy.ask(candidate_count=1)
        print(f"   Suggestion: Solvent={suggestion['Solvent'].values[0]}, "
              f"Temp={suggestion['Temperature'].values[0]:.1f}, "
              f"Conc={suggestion['Concentration'].values[0]:.2f}")
        
        # Évaluer l'expérience
        suggestion["Yield"] = suggestion.apply(dummy_experiment, axis=1)
        
        # Mettre à jour le modèle
        strategy.tell(experiments=suggestion)
        all_experiments = pd.concat([all_experiments, suggestion], ignore_index=True)
        
        # Afficher le meilleur résultat actuel
        best_idx = all_experiments["Yield"].idxmin()
        best_exp = all_experiments.loc[best_idx]
        print(f"🏆 Meilleur résultat: Yield = {best_exp['Yield']:.3f}")
        print(f"   Solvent: {best_exp['Solvent']}, Temp: {best_exp['Temperature']:.1f}, Conc: {best_exp['Concentration']:.2f}")
        
    except Exception as e:
        print(f"\n❌ Erreur à l'itération {i+1}: {e}")
        import traceback
        traceback.print_exc()
        break

# ===== 8. RÉSULTATS FINAUX =====
print("\n" + "=" * 60)
print("RÉSULTATS FINAUX")
print("=" * 60)

best_idx = all_experiments["Yield"].idxmin()
best_experiment = all_experiments.loc[best_idx]

print(f"\n🎯 MEILLEURE EXPÉRIENCE TROUVÉE:")
print(f"   Solvent: {best_experiment['Solvent']}")
print(f"   Temperature: {best_experiment['Temperature']:.2f}°C")
print(f"   Concentration: {best_experiment['Concentration']:.2f} M")
print(f"   Yield: {best_experiment['Yield']:.3f}")

print(f"\n📊 Nombre total d'expériences: {len(all_experiments)}")
print(all_experiments.sort_values("Yield")[["Solvent", "Temperature", "Concentration", "Yield"]].head(10))

print("\n✅ Script terminé avec succès!")
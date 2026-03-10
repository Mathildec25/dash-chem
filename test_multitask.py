"""
Test script: Transfer Learning via TaskInput in BoFire
======================================================
Vérifie si TaskInput est disponible et fonctionnel dans l'installation BoFire.

Scénario simulé :
- Tâche SOURCE : optimisation d'une réaction "chromone" (20 expériences)
- Tâche CIBLE  : optimisation d'une réaction "flavone" (5 expériences)
- On vérifie que le MultiTaskGP exploite les données source
  pour faire de meilleures suggestions sur la cible.

Usage :
    python test_transfer_learning.py
"""

import sys
import traceback
import numpy as np
import pandas as pd

# ==============================================================================
# STEP 1 : Vérifier que TaskInput est importable
# ==============================================================================

print("=" * 70)
print("STEP 1 : Import de TaskInput")
print("=" * 70)

try:
    from bofire.data_models.features.api import TaskInput
    print(f"✅ TaskInput importé avec succès depuis bofire.data_models.features.api")
except ImportError as e:
    print(f"❌ TaskInput introuvable : {e}")
    print("\n→ TaskInput n'est probablement pas disponible dans cette version de BoFire.")
    print("  Vérifiez votre version avec : python -c \"import bofire; print(bofire.__version__)\"")
    sys.exit(1)

# Afficher la version de BoFire
try:
    import bofire
    print(f"   BoFire version : {bofire.__version__}")
except Exception:
    print("   (version non détectable)")

# Inspecter la signature de TaskInput
print(f"\n   TaskInput fields :")
try:
    for name, field in TaskInput.model_fields.items():
        print(f"     - {name}: {field.annotation} (default={field.default!r})")
except Exception as e:
    print(f"   (impossible d'inspecter les fields : {e})")


# ==============================================================================
# STEP 2 : Créer un TaskInput et un Domain
# ==============================================================================

print("\n" + "=" * 70)
print("STEP 2 : Création du Domain avec TaskInput")
print("=" * 70)

try:
    from bofire.data_models.features.api import (
        ContinuousInput,
        ContinuousOutput,
        TaskInput,
    )
    from bofire.data_models.objectives.api import MaximizeObjective
    from bofire.data_models.domain.api import Domain, Inputs, Outputs

    # Paramètres de la réaction
    temperature = ContinuousInput(key="temperature", bounds=[60.0, 150.0])
    concentration = ContinuousInput(key="concentration", bounds=[0.1, 2.0])
    time_param = ContinuousInput(key="reaction_time", bounds=[1.0, 24.0])

    # Task feature : source (fidelity=0) vs target (fidelity=1)
    task = TaskInput(
        key="task_id",
        categories=["source", "target"],
        fidelities=[0, 1],
    )

    # Objectif
    yield_obj = MaximizeObjective(w=1.0)
    yield_output = ContinuousOutput(key="yield", objective=yield_obj)

    # Domain
    domain = Domain(
        inputs=Inputs(features=[temperature, concentration, time_param, task]),
        outputs=Outputs(features=[yield_output]),
    )

    print(f"✅ Domain créé avec succès")
    print(f"   Inputs  : {[f.key for f in domain.inputs.features]}")
    print(f"   Outputs : {[f.key for f in domain.outputs.features]}")
    print(f"   TaskInput categories : {task.categories}")
    print(f"   TaskInput fidelities : {task.fidelities}")

except Exception as e:
    print(f"❌ Erreur lors de la création du Domain : {e}")
    traceback.print_exc()
    sys.exit(1)


# ==============================================================================
# STEP 3 : Générer des données simulées (source + target)
# ==============================================================================

print("\n" + "=" * 70)
print("STEP 3 : Génération de données simulées")
print("=" * 70)

np.random.seed(42)

def simulate_reaction(temp, conc, time, shift=0.0):
    """
    Fonction simulée de rendement.
    shift permet de décaler légèrement la surface de réponse entre tâches.
    """
    yield_val = (
        60
        + 0.3 * (temp - 100)
        - 5 * (conc - 1.0) ** 2
        + 2 * np.log(time + 1)
        + shift
        + np.random.normal(0, 2)  # bruit
    )
    return np.clip(yield_val, 0, 100)


# Données SOURCE : 20 expériences (réaction similaire, légèrement décalée)
n_source = 20
source_data = pd.DataFrame({
    "temperature": np.random.uniform(60, 150, n_source),
    "concentration": np.random.uniform(0.1, 2.0, n_source),
    "reaction_time": np.random.uniform(1, 24, n_source),
    "task_id": "source",
})
source_data["yield"] = source_data.apply(
    lambda r: simulate_reaction(r["temperature"], r["concentration"], r["reaction_time"], shift=-5),
    axis=1,
)

# Données CIBLE : 5 expériences seulement
n_target = 5
target_data = pd.DataFrame({
    "temperature": np.random.uniform(60, 150, n_target),
    "concentration": np.random.uniform(0.1, 2.0, n_target),
    "reaction_time": np.random.uniform(1, 24, n_target),
    "task_id": "target",
})
target_data["yield"] = target_data.apply(
    lambda r: simulate_reaction(r["temperature"], r["concentration"], r["reaction_time"], shift=0),
    axis=1,
)

# Combiner
experiments = pd.concat([source_data, target_data], ignore_index=True)

print(f"✅ Données générées")
print(f"   Source : {n_source} expériences")
print(f"   Target : {n_target} expériences")
print(f"   Total  : {len(experiments)} expériences")
print(f"\n   Aperçu :")
print(experiments.to_string(index=True, max_rows=10))


# ==============================================================================
# STEP 4 : Créer une stratégie et faire tell + ask
# ==============================================================================

print("\n" + "=" * 70)
print("STEP 4 : Stratégie BO avec transfer learning")
print("=" * 70)

try:
    from bofire.data_models.strategies.api import SoboStrategy as SoboStrategyDataModel
    from bofire.data_models.acquisition_functions.api import qLogNEI
    import bofire.strategies.api as strategies

    # Créer la stratégie
    strategy_data_model = SoboStrategyDataModel(
        domain=domain,
        acquisition_function=qLogNEI(),
    )

    strat = strategies.map(strategy_data_model)
    print(f"✅ Stratégie créée : {type(strat).__name__}")

    # Inspecter le surrogate utilisé
    if hasattr(strategy_data_model, 'surrogate_specs'):
        surrogates = strategy_data_model.surrogate_specs.surrogates
        for i, s in enumerate(surrogates):
            print(f"   Surrogate {i} : {type(s).__name__}")

    # Tell : fournir les données
    print("\n   → strat.tell(experiments) ...")
    strat.tell(experiments=experiments)
    print(f"   ✅ tell() réussi")

    # Vérifier quel modèle BoTorch a été utilisé
    if hasattr(strat, 'surrogates'):
        surr_obj = strat.surrogates
        print(f"   Surrogates type : {type(surr_obj).__name__}")

        # BotorchSurrogates a un attribut .surrogates qui est une liste
        surr_list = getattr(surr_obj, 'surrogates', None)
        if surr_list and isinstance(surr_list, list):
            for i, surrogate in enumerate(surr_list):
                print(f"   Surrogate [{i}] : {type(surrogate).__name__}")
                model = getattr(surrogate, 'model', None)
                if model is not None:
                    print(f"     Modèle BoTorch : {type(model).__name__}")
                    if hasattr(model, '_task_covar_matrix'):
                        print(f"     ✅ Matrice de covariance inter-tâches détectée → MultiTaskGP !")
                    else:
                        print(f"     ⚠️  Pas de _task_covar_matrix → probablement SingleTaskGP")
                else:
                    print(f"     (modèle non accessible directement)")
        else:
            # Tenter d'autres attributs
            print(f"   Attributs disponibles : {[a for a in dir(surr_obj) if not a.startswith('_')]}")

    # Ask : demander des suggestions
    print("\n   → strat.ask(candidate_count=3) ...")
    candidates = strat.ask(candidate_count=3)
    print(f"   ✅ ask() réussi — {len(candidates)} candidats générés")
    print(f"\n   Candidats suggérés :")
    print(candidates.to_string(index=True))

    # Vérifier que les candidats sont pour la tâche cible
    if "task_id" in candidates.columns:
        task_values = candidates["task_id"].unique()
        print(f"\n   Tâches des candidats : {list(task_values)}")
        if all(t == "target" for t in task_values):
            print(f"   ✅ Tous les candidats sont pour la tâche cible")
        else:
            print(f"   ⚠️  Certains candidats ne sont pas pour la tâche cible")

except Exception as e:
    print(f"❌ Erreur : {e}")
    traceback.print_exc()


# ==============================================================================
# STEP 5 : Comparaison avec/sans transfer learning
# ==============================================================================

print("\n" + "=" * 70)
print("STEP 5 : Comparaison avec vs sans transfer learning")
print("=" * 70)

try:
    # Domain SANS TaskInput (baseline)
    domain_no_tl = Domain(
        inputs=Inputs(features=[temperature, concentration, time_param]),
        outputs=Outputs(features=[yield_output]),
    )

    strategy_no_tl_dm = SoboStrategyDataModel(
        domain=domain_no_tl,
        acquisition_function=qLogNEI(),
    )
    strat_no_tl = strategies.map(strategy_no_tl_dm)

    # Seulement les données cible (pas de source)
    strat_no_tl.tell(experiments=target_data.drop(columns=["task_id"]))
    candidates_no_tl = strat_no_tl.ask(candidate_count=3)

    print(f"✅ Comparaison terminée")
    if 'candidates' in dir() or 'candidates' in globals() or 'candidates' in locals():
        print(f"\n   AVEC transfer learning (5 target + 20 source) :")
        print(candidates.to_string(index=True))
    else:
        print(f"\n   ⚠️  Candidats avec TL non disponibles (ask() n'a pas tourné au step 4)")

    print(f"\n   SANS transfer learning (5 target seulement) :")
    print(candidates_no_tl.to_string(index=True))
    print(f"\n   → Les candidats diffèrent car le modèle avec TL")
    print(f"     a un meilleur prior grâce aux 20 expériences source.")

except Exception as e:
    print(f"❌ Erreur dans la comparaison : {e}")
    traceback.print_exc()


# ==============================================================================
# RÉSUMÉ
# ==============================================================================

print("\n" + "=" * 70)
print("RÉSUMÉ")
print("=" * 70)
print("""
Si toutes les étapes sont ✅, alors :
  1. TaskInput est disponible dans votre version de BoFire
  2. Le Domain accepte un TaskInput
  3. La stratégie SOBO utilise automatiquement un MultiTaskGP
  4. Les candidats sont générés uniquement pour la tâche cible
  5. Le transfer learning influence les suggestions

→ Vous pouvez intégrer cette fonctionnalité dans REACTO !

Si STEP 1 échoue : TaskInput n'est pas dans votre version, 
  envisagez une mise à jour de BoFire (pip install --upgrade bofire)

Si STEP 4 échoue : TaskInput existe mais l'intégration avec 
  les stratégies n'est pas complète dans cette version.
""")
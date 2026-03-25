"""
Constrained MOBO pour synthese chimique - structure 100% inspiree du tutorial BoTorch
Ref : constrained_multi_objective_bo.ipynb

Adaptation du tutorial C2-DTLZ2 a une reaction chimique :
    - Objectifs  : Yield (max), TON (max)
    - Contrainte : Yield >= 0.60  =>  c(x) = 0.60 - Yield  <= 0  (convention BoTorch)
    - Inputs     : t_res (cont), Temperature (cont), catalyst_loading (cont), Catalyst (OHE)

Structure identique au tutorial :
    load_initial_data()      ->  train_x, train_obj, train_con
    initialize_model()       ->  mll, model  (ModelListGP : GP_Yield, GP_TON, GP_constraint)
    optimize_qnehvi()        ->  new_x, new_obj, new_con
    main()                   ->  fit / optimize / suggestion
"""

import warnings
import torch
import numpy as np

from botorch import fit_gpytorch_mll
from botorch.exceptions import BadInitialCandidatesWarning
from botorch.models.gp_regression import SingleTaskGP
from botorch.models.model_list_gp_regression import ModelListGP
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.utils.transforms import normalize, unnormalize
from botorch.acquisition.multi_objective.logei import qLogNoisyExpectedHypervolumeImprovement
from botorch.acquisition.multi_objective.objective import IdentityMCMultiOutputObjective
from botorch.optim.optimize import optimize_acqf_mixed
from botorch.utils.multi_objective.hypervolume import Hypervolume
from botorch.utils.multi_objective.pareto import is_non_dominated
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood

warnings.filterwarnings("ignore", category=BadInitialCandidatesWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

import botorch
print(f"BoTorch version : {botorch.__version__}")

# ── tkwargs (identique au tutorial) ──────────────────────────────────────────
tkwargs = {
    "dtype": torch.double,
    "device": torch.device("cuda" if torch.cuda.is_available() else "cpu"),
}

# ── Parametres du probleme ────────────────────────────────────────────────────
YIELD_THRESHOLD = 0.60   # Yield >= 60%  =>  c(x) = 0.60 - Yield <= 0
CATALYSTS       = ["P1-L1", "P2-L1", "P1-L2", "P1-L3", "P1-L4", "P1-L5", "P1-L6", "P1-L7"]

# Bornes des inputs continus : t_res (s), Temperature (C), catalyst_loading (mol%)
CONT_BOUNDS = torch.tensor([[ 60.0, 30.0, 0.5],
                             [600.0, 110.0, 2.5]], **tkwargs)

# Bornes de TOUS les inputs apres OHE du catalyseur (11 dimensions)
# dims 0-2 : cont normalises -> [0, 1] apres normalize()
# dims 3-10 : OHE catalyseur -> deja dans [0, 1]
D_CONT  = 3
D_OHE   = len(CATALYSTS)
D_TOTAL = D_CONT + D_OHE

# standard_bounds (identique au tutorial) : tout dans [0, 1]^d
standard_bounds = torch.zeros(2, D_TOTAL, **tkwargs)
standard_bounds[1] = 1

# Ref point pour le calcul d'hypervolume (a definir selon les donnees)
# On utilisera un ref point dynamique dans la boucle.
REF_POINT = torch.tensor([0.0, 0.0], **tkwargs)   # sera mis a jour

# ── Parametres BO (identique au tutorial) ─────────────────────────────────────
BATCH_SIZE   = 1
NUM_RESTARTS = 10
RAW_SAMPLES  = 128
MC_SAMPLES   = 128


# ============================================================================
# Donnees initiales  -  A REMPLIR PAR L'UTILISATEUR
#
# Chaque ligne : catalyst, t_res (s), temperature (C), catalyst_loading (mol%),
#                yld (fraction 0-1), ton (0-200)
# ============================================================================
INITIAL_DATA = [
    {"catalyst": "P1-L7", "t_res": 333.88, "temperature": 46.67, "catalyst_loading": 1.08, "yld": 0.03393, "ton": 1.152551},
    {"catalyst": "P1-L2", "t_res": 261.59, "temperature": 53.61, "catalyst_loading": 2.11, "yld": 0.06553, "ton": 5.381159},
    {"catalyst": "P1-L4", "t_res": 129.89, "temperature": 30.09, "catalyst_loading": 1.27, "yld": 0.03926, "ton": 1.297489},
    {"catalyst": "P2-L1", "t_res": 495.14, "temperature": 76.44, "catalyst_loading": 2.48, "yld": 0.18012, "ton": 1.473942},
    {"catalyst": "P1-L3", "t_res": 296.83, "temperature": 103.26, "catalyst_loading": 0.54, "yld": 0.15096, "ton": 27.927135},
    {"catalyst": "P1-L5", "t_res": 101.02, "temperature": 88.41, "catalyst_loading": 1.71, "yld": 0.22296, "ton": 13.134931},
    {"catalyst": "P1-L6", "t_res": 589.76, "temperature": 61.75, "catalyst_loading": 0.89, "yld": 0.01535, "ton": 4.959741},
    {"catalyst": "P1-L1", "t_res": 415.06, "temperature": 91.93, "catalyst_loading": 1.91, "yld": 0.48624, "ton": 26.791769},
    {"catalyst": "P1-L1", "t_res": 429.17, "temperature": 43.68, "catalyst_loading": 0.5, "yld": 0.0693, "ton": 9.2},
    {"catalyst": "P1-L1", "t_res": 362.55, "temperature": 106.55, "catalyst_loading": 2.202, "yld": 0.6605, "ton": 31.11153},    
]

# ============================================================================
# Encodage / decodage  (OHE + normalisation continue)
# ============================================================================

def encode(t_res, temperature, catalyst_loading, catalyst):
    """(t_res, temperature, catalyst_loading, catalyst) -> tenseur normalise [0,1]^11."""
    cont = normalize(
        torch.tensor([[t_res, temperature, catalyst_loading]], **tkwargs),
        CONT_BOUNDS
    ).squeeze(0)                              # (3,)
    ohe = torch.zeros(D_OHE, **tkwargs)
    ohe[CATALYSTS.index(catalyst)] = 1.0
    return torch.cat([cont, ohe])             # (11,)


def decode(x: torch.Tensor):
    """Tenseur [0,1]^11 -> (t_res, temperature, catalyst_loading, catalyst)."""
    cont_raw = unnormalize(x[:D_CONT].unsqueeze(0), CONT_BOUNDS).squeeze(0)
    t_res, temperature, catalyst_loading = cont_raw[0].item(), cont_raw[1].item(), cont_raw[2].item()
    catalyst = CATALYSTS[x[D_CONT:].argmax().item()]
    return t_res, temperature, catalyst_loading, catalyst


# ============================================================================
# load_initial_data  (remplace generate_initial_data du tutorial)
# ============================================================================

def load_initial_data():
    """
    Charge les donnees saisies manuellement dans INITIAL_DATA.

    Retourne (train_x, train_obj, train_con) exactement comme le tutorial :
        train_x   : (n, 11)  inputs normalises + OHE
        train_obj : (n, 2)   [Yield, TON]
        train_con : (n, 1)   c(x) = YIELD_THRESHOLD - Yield
                             negative values imply feasibility  (comme le tutorial)
    """
    rows_x, rows_obj, rows_con = [], [], []
    for row in INITIAL_DATA:
        rows_x.append(encode(row["t_res"], row["temperature"], row["catalyst_loading"], row["catalyst"]))
        rows_obj.append(torch.tensor([row["yld"], row["ton"]], **tkwargs))
        # negative values imply feasibility in botorch  (comme dans le tutorial)
        rows_con.append(torch.tensor([YIELD_THRESHOLD - row["yld"]], **tkwargs))
    train_x   = torch.stack(rows_x)    # (n, 11)
    train_obj = torch.stack(rows_obj)  # (n, 2)
    train_con = torch.stack(rows_con)  # (n, 1)
    return train_x, train_obj, train_con


# ============================================================================
# initialize_model  (copie exacte du tutorial)
# ============================================================================

def initialize_model(train_x, train_obj, train_con):
    """
    Copie exacte de la fonction du tutorial.

    train_y = cat([train_obj, train_con], dim=-1)   # (n, 3)
    Un SingleTaskGP par colonne : GP_Yield, GP_TON, GP_constraint
    """
    train_y = torch.cat([train_obj, train_con], dim=-1)   # (n, 3)
    models  = []
    for i in range(train_y.shape[-1]):
        models.append(SingleTaskGP(train_x, train_y[..., i : i + 1]))
    model = ModelListGP(*models)
    mll   = SumMarginalLogLikelihood(model.likelihood, model)
    return mll, model


# ============================================================================
# optimize_qnehvi_and_get_observation  (structure identique au tutorial)
# ============================================================================

def optimize_qnehvi_and_get_observation(model, train_x, train_obj, train_con, sampler):
    """
    Structure identique au tutorial.

    Differences vs tutorial :
     - optimize_acqf_mixed au lieu de optimize_acqf  (catalyseur categoriel)
     - fixed_features_list pour les 8 catalyseurs possibles
     - decode() pour reconstruire les conditions reelles

    Conservation stricte :
     - objective = IdentityMCMultiOutputObjective(outcomes=[0, 1])
     - constraints = [lambda Z: Z[..., -1]]
    """
    acq_func = qLogNoisyExpectedHypervolumeImprovement(
        model          = model,
        ref_point      = REF_POINT.tolist(),
        X_baseline     = train_x,
        sampler        = sampler,
        prune_baseline = True,
        # define an objective that specifies which outcomes are the objectives
        objective      = IdentityMCMultiOutputObjective(outcomes=[0, 1]),
        # specify that the constraint is on the last outcome
        constraints    = [lambda Z: Z[..., -1]],
    )

    # fixed_features_list : enumere les 8 catalyseurs possibles (OHE dims 3-10)
    fixed_features_list = [
        {D_CONT + k: (1.0 if k == cat_idx else 0.0) for k in range(D_OHE)}
        for cat_idx in range(D_OHE)
    ]

    candidates, _ = optimize_acqf_mixed(
        acq_function        = acq_func,
        bounds              = standard_bounds,
        q                   = BATCH_SIZE,
        num_restarts        = NUM_RESTARTS,
        raw_samples         = RAW_SAMPLES,
        fixed_features_list = fixed_features_list,
        options             = {"batch_limit": 5, "maxiter": 200},
    )

    new_x = candidates.detach()
    t_res, temperature, catalyst_loading, catalyst = decode(new_x.squeeze(0))

    return new_x, (t_res, temperature, catalyst_loading, catalyst)


# ============================================================================
# Points de controle GP
# ============================================================================

def check_constraint_gp(model, new_x):
    """
    Interroge les 3 GPs sur le candidat propose.
    Affiche les predictions et verifie la contrainte.

    GP[0] -> Yield          (objectif 1)
    GP[1] -> TON            (objectif 2)
    GP[2] -> c(x)=T-Yield   (contrainte : <= 0 si faisable)
    """
    from scipy.stats import norm

    model.eval()
    with torch.no_grad():
        posterior = model.posterior(new_x)
        mean = posterior.mean.reshape(-1, 3)          # (q, 3) robuste
        std  = posterior.variance.sqrt().reshape(-1, 3)

    print(f"\n  --- Points de controle GP ---")
    print(f"  train_y = [Yield, TON, c(x)=Threshold-Yield]")
    print(f"  Contrainte BoTorch : Z[..., -1] <= 0  <=>  c(x) <= 0  <=>  Yield >= {YIELD_THRESHOLD}")
    print(f"  {'':3} {'Output':<22} {'GP mean':>10} {'GP std':>10}")
    print(f"  {'-'*50}")
    names = ["GP[0] Yield", "GP[1] TON", "GP[2] c(x)=T-Yield"]
    for i, name in enumerate(names):
        mu = mean[0, i].item()
        sg = std[0, i].item()
        print(f"  {'':3} {name:<22} {mu:>10.4f} {sg:>10.4f}")

    # Verification contrainte via GP[2]
    c_mu  = mean[0, 2].item()
    c_sig = std[0, 2].item()
    prob  = norm.cdf(0.0, loc=c_mu, scale=c_sig)   # P(c(x) <= 0)
    status = "OK  faisable" if c_mu <= 0 else "WARN infaisable selon GP"
    print(f"\n  GP[2] c(x) = {c_mu:+.4f}  [{status}]")
    print(f"  P(c(x) <= 0) = P(Yield >= {YIELD_THRESHOLD}) = {prob:.2%}")


# ============================================================================
# Point d'entree principal
# ============================================================================

def main():
    print("=" * 65)
    print("  Constrained MOBO - structure tutorial BoTorch")
    print(f"  Objectifs : Yield (max), TON (max)")
    print(f"  Contrainte : Yield >= {YIELD_THRESHOLD}  =>  c(x) = {YIELD_THRESHOLD} - Yield <= 0")
    print("=" * 65)

    # Charge les donnees initiales
    train_x, train_obj, train_con = load_initial_data()
    n_init = len(INITIAL_DATA)

    # Affiche les donnees initiales
    print(f"\nDonnees initiales ({n_init} exp.) :")
    print(f"  {'Catalyst':<8} {'t_res':>7} {'Temp':>6} {'CatLoad':>8} {'Yield':>7} {'TON':>7} {'c(x)':>7} {'Faisable'}")
    print(f"  {'-'*68}")
    for i in range(len(train_x)):
        t_res, temp, cat_load, cat = decode(train_x[i])
        y   = train_obj[i, 0].item()
        ton = train_obj[i, 1].item()
        cx  = train_con[i, 0].item()
        ok  = "oui" if cx <= 0 else "non"
        print(f"  {cat:<8} {t_res:>7.1f} {temp:>6.1f} {cat_load:>8.3f} {y:>7.4f} {ton:>7.1f} {cx:>+7.4f} {ok}")

    # Calcule hypervolume initial (sur points faisables)
    is_feas  = (train_con <= 0).all(dim=-1)
    feas_obj = train_obj[is_feas]
    hv_indicator = Hypervolume(ref_point=REF_POINT)
    if feas_obj.shape[0] > 0:
        pareto_mask = is_non_dominated(feas_obj)
        volume = hv_indicator.compute(feas_obj[pareto_mask])
    else:
        volume = 0.0
    print(f"\n  Hypervolume initial : {volume:.4f}")
    print(f"  Points faisables    : {is_feas.sum().item()}/{n_init}")

    # Initialise le modele (identique au tutorial)
    mll, model = initialize_model(train_x, train_obj, train_con)

    # fit the models  (identique au tutorial)
    fit_gpytorch_mll(mll)

    # define the qNEHVI acquisition using a QMC sampler  (identique au tutorial)
    qnehvi_sampler = SobolQMCNormalSampler(sample_shape=torch.Size([MC_SAMPLES]))

    # optimize acquisition function and get suggestion
    print(f"\n  Optimisation de qLogNEHVI en cours...")
    new_x, (t_res, temperature, catalyst_loading, catalyst) = optimize_qnehvi_and_get_observation(
        model, train_x, train_obj, train_con, qnehvi_sampler
    )

    # Points de controle GP
    check_constraint_gp(model, new_x)

# Affiche le candidat propose
    print(f"\n{'='*65}")
    print(f"  EXPERIENCE SUIVANTE SUGGEREE")
    print(f"{'='*65}")
    print(f"\n  -> Copier-coller dans conditions :")
    print(f'\n  conditions = [["{catalyst}", {t_res:.2f}, {temperature:.2f}, {catalyst_loading:.3f}]]')
    print(f"\n  -> Puis ajouter Yield (fraction 0-1) et TON dans INITIAL_DATA et relancer.\n")

if __name__ == "__main__":
    main()
"""
Constrained MOBO pour synthese chimique - structure 100% inspiree du tutorial BoTorch
Ref : constrained_multi_objective_bo.ipynb

Reaction : MD_DMIPP_Phosphorylation
    - Objectifs   : YIELD (max), STY (max)
    - Contrainte  : YIELD >= 0.50  =>  c(x) = 0.50 - YIELD <= 0  (convention BoTorch)
    - Contrainte  : DMIPP <= BUOH  (lineaire, passee via inequality_constraints)
    - Inputs      : DMIPP (cont), BUOH (cont), T (cont), RES (discret 5 niveaux)

Structure identique au tutorial :
    load_initial_data()      ->  train_x, train_obj, train_con
    initialize_model()       ->  mll, model  (ModelListGP : GP_YIELD, GP_STY, GP_constraint)
    optimize_qnehvi()        ->  new_x
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
YIELD_THRESHOLD = 0.60   # YIELD >= 60%  =>  c(x) = 0.60 - YIELD <= 0
STY_MAX         = 73.2   # upper bound reel pour normalisation

RES_LEVELS = [0.5, 1.0, 1.5, 2.0, 2.5]   # valeurs discretes de RES

# Bornes des inputs continus : DMIPP, BUOH, T, RES
# RES traite comme continu pour la normalisation, enumere dans fixed_features
CONT_BOUNDS = torch.tensor(
    [[1.0,  1.0,  25.0, 0.5],
     [6.7, 10.9,  80.0, 2.5]],
    **tkwargs
)

D_TOTAL = 4   # DMIPP, BUOH, T, RES

# standard_bounds (identique au tutorial) : tout dans [0, 1]^d
standard_bounds = torch.zeros(2, D_TOTAL, **tkwargs)
standard_bounds[1] = 1

# Ref point pour le calcul d'hypervolume
REF_POINT = torch.tensor([0.0, 0.0], **tkwargs)

# ── Parametres BO (identique au tutorial) ─────────────────────────────────────
BATCH_SIZE   = 1
NUM_RESTARTS = 10
RAW_SAMPLES  = 128
MC_SAMPLES   = 128

# ── Contrainte lineaire DMIPP <= BUOH ────────────────────────────────────────
# En espace normalise : dmipp_n * (6.7-1.0) + 1.0 <= buoh_n * (10.9-1.0) + 1.0
# => -5.7 * dmipp_n + 9.9 * buoh_n >= 0
# Format BoTorch : (indices, coefficients, rhs)  avec sum(coeff * x[idx]) >= rhs
INEQUALITY_CONSTRAINTS = [
    (torch.tensor([0, 1]), torch.tensor([-5.7, 9.9], **tkwargs), 0.0)
]


# ============================================================================
# Donnees initiales  -  A REMPLIR PAR L'UTILISATEUR
#
# Chaque ligne : dmipp, buoh, temperature (T), res,
#                yld (fraction 0-1), sty (g/L/h, valeurs reelles)
# ============================================================================
INITIAL_DATA = [
    {"dmipp": 5.0, "buoh": 8.2, "temperature": 40.0, "res": 2.5, "yld": 0.27, "sty": 2.9},
    {"dmipp": 2.2, "buoh": 9.0, "temperature": 65.0, "res": 1.0, "yld": 0.26, "sty": 3.1},
    {"dmipp": 2.2, "buoh": 6.2, "temperature": 70.0, "res": 2.5, "yld": 0.54, "sty": 2.6},
    {"dmipp": 5.0, "buoh": 8.5, "temperature": 35.0, "res": 1.0, "yld": 0.06, "sty": 0.1},
    {"dmipp": 5.0, "buoh": 8.2, "temperature": 65.0, "res": 0.5, "yld": 0.24, "sty": 13.0},
    {"dmipp": 2.4, "buoh": 6.3, "temperature": 35.0, "res": 0.5, "yld": 0.04, "sty": 1.1},
    {"dmipp": 2.2, "buoh": 4.4, "temperature": 40.0, "res": 2.0, "yld": 0.35, "sty": 2.1},
    {"dmipp": 5.0, "buoh": 8.2, "temperature": 70.0, "res": 2.0, "yld": 0.43, "sty": 5.9},
    {"dmipp": 2.2, "buoh": 8.8, "temperature": 40.0, "res": 2.0, "yld": 0.09, "sty": 0.5},
    {"dmipp": 2.2, "buoh": 4.2, "temperature": 65.0, "res": 1.0, "yld": 0.59, "sty": 7.2},
    {"dmipp": 3.2, "buoh": 3.2, "temperature": 70.0, "res": 1.0, "yld": 0.44, "sty": 7.8},
]


# ============================================================================
# Encodage / decodage  (normalisation continue, RES discret)
# ============================================================================

def encode(dmipp, buoh, temperature, res):
    """(dmipp, buoh, temperature, res) -> tenseur normalise [0,1]^4."""
    return normalize(
        torch.tensor([[dmipp, buoh, temperature, res]], **tkwargs),
        CONT_BOUNDS
    ).squeeze(0)   # (4,)


def decode(x: torch.Tensor):
    """Tenseur [0,1]^4 -> (dmipp, buoh, temperature, res)."""
    raw = unnormalize(x.unsqueeze(0), CONT_BOUNDS).squeeze(0)
    dmipp       = raw[0].item()
    buoh        = raw[1].item()
    temperature = raw[2].item()
    # snap RES a la valeur discrete la plus proche
    res = min(RES_LEVELS, key=lambda v: abs(v - raw[3].item()))
    return dmipp, buoh, temperature, res


# ============================================================================
# load_initial_data  (remplace generate_initial_data du tutorial)
# ============================================================================

def load_initial_data():
    """
    Charge les donnees saisies manuellement dans INITIAL_DATA.

    Retourne (train_x, train_obj, train_con) exactement comme le tutorial :
        train_x   : (n, 4)   inputs normalises
        train_obj : (n, 2)   [YIELD, STY/STY_MAX]
        train_con : (n, 1)   c(x) = YIELD_THRESHOLD - YIELD
                             negative values imply feasibility  (comme le tutorial)
    """
    rows_x, rows_obj, rows_con = [], [], []
    for row in INITIAL_DATA:
        rows_x.append(encode(row["dmipp"], row["buoh"], row["temperature"], row["res"]))
        rows_obj.append(torch.tensor([row["yld"], row["sty"] / STY_MAX], **tkwargs))
        # negative values imply feasibility in botorch  (comme dans le tutorial)
        rows_con.append(torch.tensor([YIELD_THRESHOLD - row["yld"]], **tkwargs))
    train_x   = torch.stack(rows_x)    # (n, 4)
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
    Un SingleTaskGP par colonne : GP_YIELD, GP_STY, GP_constraint
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
     - optimize_acqf_mixed au lieu de optimize_acqf  (RES discret)
     - fixed_features_list pour les 5 valeurs de RES
     - inequality_constraints pour DMIPP <= BUOH
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

    # fixed_features_list : enumere les 5 valeurs discretes de RES (dim 3)
    res_normalized = [
        normalize(torch.tensor([[0.0, 0.0, 0.0, v]], **tkwargs), CONT_BOUNDS)[0, 3].item()
        for v in RES_LEVELS
    ]
    fixed_features_list = [{3: v} for v in res_normalized]

    candidates, _ = optimize_acqf_mixed(
        acq_function         = acq_func,
        bounds               = standard_bounds,
        q                    = BATCH_SIZE,
        num_restarts         = NUM_RESTARTS,
        raw_samples          = RAW_SAMPLES,
        fixed_features_list  = fixed_features_list,
        inequality_constraints = INEQUALITY_CONSTRAINTS,
        options              = {"batch_limit": 5, "maxiter": 200},
    )

    new_x = candidates.detach()
    dmipp, buoh, temperature, res = decode(new_x.squeeze(0))

    return new_x, (dmipp, buoh, temperature, res)


# ============================================================================
# Points de controle GP
# ============================================================================

def check_constraint_gp(model, new_x):
    """
    Interroge les 3 GPs sur le candidat propose.
    Affiche les predictions et verifie la contrainte.

    GP[0] -> YIELD           (objectif 1)
    GP[1] -> STY/STY_MAX     (objectif 2)
    GP[2] -> c(x)=T-YIELD    (contrainte : <= 0 si faisable)
    """
    from scipy.stats import norm

    model.eval()
    with torch.no_grad():
        posterior = model.posterior(new_x)
        mean = posterior.mean.reshape(-1, 3)          # (q, 3) robuste
        std  = posterior.variance.sqrt().reshape(-1, 3)

    print(f"\n  --- Points de controle GP ---")
    print(f"  train_y = [YIELD, STY/STY_MAX, c(x)=Threshold-YIELD]")
    print(f"  Contrainte BoTorch : Z[..., -1] <= 0  <=>  c(x) <= 0  <=>  YIELD >= {YIELD_THRESHOLD}")
    print(f"  {'':3} {'Output':<26} {'GP mean':>10} {'GP std':>10}")
    print(f"  {'-'*54}")
    names = ["GP[0] YIELD", f"GP[1] STY/{STY_MAX}", "GP[2] c(x)=T-YIELD"]
    for i, name in enumerate(names):
        mu = mean[0, i].item()
        sg = std[0, i].item()
        print(f"  {'':3} {name:<26} {mu:>10.4f} {sg:>10.4f}")

    # Verification contrainte via GP[2]
    c_mu  = mean[0, 2].item()
    c_sig = std[0, 2].item()
    prob  = norm.cdf(0.0, loc=c_mu, scale=c_sig)   # P(c(x) <= 0)
    status = "OK  faisable" if c_mu <= 0 else "WARN infaisable selon GP"
    print(f"\n  GP[2] c(x) = {c_mu:+.4f}  [{status}]")
    print(f"  P(c(x) <= 0) = P(YIELD >= {YIELD_THRESHOLD}) = {prob:.2%}")


# ============================================================================
# Point d'entree principal
# ============================================================================

def main():
    print("=" * 65)
    print("  Constrained MOBO - structure tutorial BoTorch")
    print(f"  Objectifs  : YIELD (max), STY (max)")
    print(f"  Contrainte : YIELD >= {YIELD_THRESHOLD}  =>  c(x) = {YIELD_THRESHOLD} - YIELD <= 0")
    print(f"  Contrainte : DMIPP <= BUOH  (lineaire)")
    print("=" * 65)

    # Charge les donnees initiales
    train_x, train_obj, train_con = load_initial_data()
    n_init = len(INITIAL_DATA)

    # Affiche les donnees initiales
    print(f"\nDonnees initiales ({n_init} exp.) :")
    print(f"  {'DMIPP':>6} {'BUOH':>6} {'T':>5} {'RES':>5} {'YIELD':>7} {'STY':>7} {'c(x)':>7} {'Faisable'}")
    print(f"  {'-'*60}")
    for i in range(len(train_x)):
        dmipp, buoh, temp, res = decode(train_x[i])
        y   = train_obj[i, 0].item()
        sty = train_obj[i, 1].item() * STY_MAX
        cx  = train_con[i, 0].item()
        ok  = "oui" if cx <= 0 else "non"
        print(f"  {dmipp:>6.2f} {buoh:>6.2f} {temp:>5.1f} {res:>5.1f} {y:>7.4f} {sty:>7.2f} {cx:>+7.4f} {ok}")

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
    new_x, (dmipp, buoh, temperature, res) = optimize_qnehvi_and_get_observation(
        model, train_x, train_obj, train_con, qnehvi_sampler
    )

    # Points de controle GP
    check_constraint_gp(model, new_x)

    # Affiche le candidat propose
    print(f"\n{'='*65}")
    print(f"  EXPERIENCE SUIVANTE SUGGEREE")
    print(f"{'='*65}")
    print(f"\n  -> Copier-coller dans conditions :")
    print(f'\n  conditions = [[{dmipp:.2f}, {buoh:.2f}, {temperature:.1f}, {res}]]')
    print(f"  # [DMIPP, BUOH, T, RES]")
    print(f"\n  -> Puis ajouter YIELD (fraction 0-1) et STY dans INITIAL_DATA et relancer.\n")


if __name__ == "__main__":
    main()
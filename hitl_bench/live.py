# -*- coding: utf-8 -*-
"""A live campaign a chemist drives, one experiment at a time.

This is the human arm of the study, as a state machine with no user interface
attached. The REACTO page is a thin skin over it, and so could a notebook be:
everything that decides what happens next lives here, where it can be tested.

**Identical for everyone, until they act.** A live campaign starts from one of
the study's replayable control campaigns. As long as the chemist has not imposed
a point of their own, every experiment is *copied* from that control - the same
initial design, the same optimiser proposals, in the same order, for every
participant. That is what makes their decisions comparable, and it costs no
computation. The moment they impose a point, the campaign diverges and the
optimiser runs for real from then on, seeded exactly as the control was, so
that even the diverged part is replayable.

**The alert is the study's trigger, unchanged.** P* with the frozen settings,
evaluated on the live history exactly as run_arms.py evaluates it on the random
arm. Same burn-in, same cooldown, same rule that only alerts after the last
handled one count.

**Nothing is decided for the chemist.** At an alert the campaign waits. Three
answers are possible - stop, take the optimiser's proposal, impose a point - and
each is recorded with its moment, its justification and the value of P* at that
moment. Taking the optimiser's proposal is recorded as a decision too: declining
to intervene is information.

**Saved after every experiment**, twice: as a REACTO project so that the
campaign opens in the Results page like any other, and as a JSON that carries
what an Excel sheet cannot - the decisions, the alerts, the timings, the mode.
"""

import datetime
import json
import os
import re
import time

from hitl_bench import triggers

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = os.path.join(HERE, "results", "arms")
LIVE = os.path.join(HERE, "forms", "live")

PHASE_CHEMIST = "chemist"


# --- what a chemist is shown about each reaction ----------------------------
REACTIONS = {
    "edbo_ch_arylation": {
        "titre": "Arylation C–H",
        "intro": "Un criblage à haut débit. À chaque essai on choisit une base, un "
                 "ligand, un solvant, une concentration et une température ; on "
                 "mesure le rendement et le coût des réactifs. Les deux objectifs "
                 "sont indépendants : améliorer l'un n'améliore pas l'autre.",
        "reserve": "Données réelles publiées (Torres et al., JACS 2022). Le substrat "
                   "n'est pas redistribué avec le jeu de données : raisonnez sur les "
                   "réactifs et les conditions.",
        "params": {"base": ("Base", ""), "ligand": ("Ligand", ""),
                   "solvent": ("Solvant", ""), "concentration": ("Concentration", "M"),
                   "temperature": ("Température", "°C")},
        "objectives": {"yield": ("Rendement", "%", "max"),
                       "cost": ("Coût des réactifs", "", "min")},
    },
    "suzuki": {
        "titre": "Couplage de Suzuki-Miyaura en flux continu",
        "intro": "Un montage en flux teste une condition à la fois. À chaque essai "
                 "on choisit une paire précatalyseur-ligand au palladium, un temps "
                 "de séjour, une température et une charge en palladium ; on mesure "
                 "le rendement et le nombre de rotations du catalyseur.",
        "reserve": "Données des campagnes en flux de Reizman et al. (React. Chem. "
                   "Eng. 2016), interpolées sur une grille complète. Deux paires "
                   "n'ont pas de nom publié et gardent leur code.",
        "params": {"ligand": ("Catalyseur", ""), "res_time": ("Temps de séjour", "s"),
                   "temperature": ("Température", "°C"),
                   "catalyst_loading": ("Charge en Pd", "mol%")},
        "objectives": {"yield": ("Rendement", "%", "max"),
                       "turnover": ("TON", "", "max")},
    },
}


def presentation(benchmark_name):
    """What to tell a chemist about this benchmark. The four Suzuki cases share
    one description but must not share one title: a participant given two of
    them needs to tell them apart by something other than a seed number."""
    case = benchmark_name.replace("summit_", "")
    if case in ("i", "ii", "iii", "iv"):
        pres = dict(REACTIONS["suzuki"])
        pres["titre"] = "%s — cas %s" % (REACTIONS["suzuki"]["titre"], case.upper())
        return pres
    return REACTIONS[benchmark_name]


def load_benchmark(name):
    from hitl_bench.scripts.run_arms import load_benchmark
    return load_benchmark(name)


# --- labels: what the chemist reads, and the way back --------------------------
def french(value, digits=6):
    return (("%." + str(digits) + "g") % float(value)).replace(".", ",")


def label(benchmark, key, value):
    if isinstance(value, str):
        if key == "ligand" and value.startswith("L") and value[1:].isdigit():
            from hitl_bench.scripts.make_chemist_form import catalyst_names, label_value
            return label_value("ligand", value, catalyst_names())
        return value
    return french(value, 4)


def levels(benchmark, key):
    """Every level of one variable, as the chemist reads it, from the grid."""
    import pandas as pd
    if key not in benchmark.grid.columns:              # Suzuki: ligand is one-hot
        from hitl_bench.benchmark import LIGANDS
        return [label(benchmark, "ligand", code) for code in LIGANDS]
    column = benchmark.grid[key]
    values = sorted(column.unique(), key=lambda v: (isinstance(v, str), v))
    if pd.api.types.is_numeric_dtype(column):
        return [french(v) for v in values]
    return [str(v) for v in values]


def unlabel(benchmark, key, shown):
    """Map a shown label back to what the grid stores; raise rather than guess."""
    if key == "ligand" and key not in benchmark.grid.columns:
        from hitl_bench.scripts.make_chemist_form import catalyst_names, label_value
        names = catalyst_names()
        for code in names["mapping"]:
            if label_value("ligand", code, names) == shown:
                return code
        raise KeyError("catalyseur non reconnu : %r" % shown)
    try:
        return float(str(shown).replace(" ", "").replace(",", "."))
    except ValueError:
        return shown


def slug(text):
    return re.sub(r"[^A-Za-z0-9_-]", "", str(text).strip().replace(" ", "_"))[:24] or "anonyme"


# --- the state machine ------------------------------------------------------
class LiveCampaign:
    """One chemist, one control campaign, driven experiment by experiment."""

    def __init__(self, chemist, benchmark_name, seed, domaine=""):
        self.chemist = slug(chemist)
        self.domaine = domaine
        self.name = benchmark_name
        self.seed = int(seed)
        self.benchmark = load_benchmark(benchmark_name)
        self.pres = presentation(benchmark_name)

        parent_path = os.path.join(ARMS, "%s__no_hitl__seed%02d.json" % (benchmark_name, seed))
        with open(parent_path, encoding="utf-8") as handle:
            self.parent = json.load(handle)
        self.n_init = self.parent["config"]["n_init"]
        self.budget = self.n_init + self.parent["config"]["n_iterations"]

        os.makedirs(LIVE, exist_ok=True)
        self.path = os.path.join(LIVE, "%s__%s__seed%02d.json"
                                 % (self.chemist, benchmark_name, seed))
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as handle:
                self.state = json.load(handle)
        else:
            self.state = {
                "chemist": self.chemist, "domaine": domaine,
                "benchmark": benchmark_name, "seed": self.seed,
                "n_init": self.n_init, "budget": self.budget,
                "started": datetime.datetime.now().isoformat(timespec="seconds"),
                "mode": "replay",            # replay the control until a point is imposed
                "experiments": [dict(r) for r in self.parent["experiments"][: self.n_init]],
                "decisions": [],
                "pending_alert": None,       # set when waiting for the chemist
                "last_handled_alert": self.n_init,
                "done": False,
                "stopped_at": None,
            }
            self.save()

    # --- reading the state --------------------------------------------------
    @property
    def experiments(self):
        return self.state["experiments"]

    @property
    def n_done(self):
        return len(self.experiments)

    @property
    def waiting(self):
        return self.state["pending_alert"] is not None

    @property
    def finished(self):
        return self.state["done"] or self.n_done >= self.budget

    def fraction(self):
        """Fraction of the reference front held so far. Kept out of the page:
        the chemist sees their own campaign, not how far it is from an optimum
        they are not supposed to know."""
        return [r["hypervolume"] / self.parent["reference"]["max_hypervolume"]
                for r in self.experiments]

    # --- advancing ------------------------------------------------------------
    def _alerts_now(self):
        fires = triggers.firing_times(triggers.pace_ratio, self.experiments,
                                      self.n_init, self.budget)
        return [e for e in fires if e > self.state["last_handled_alert"]]

    def _record(self, evaluated, phase, iteration, seconds):
        import pandas as pd
        from hitl_bench.campaign import _columns
        frame = pd.DataFrame(
            [{**{k: r[k] for k in self.benchmark.parameter_keys},
              **{k: r[k] for k in self.benchmark.objectives},
              **{k: 1 for k in self.benchmark.valid_keys}} for r in self.experiments]
            + [evaluated], columns=_columns(self.benchmark))
        record = {
            "experiment": self.n_done + 1, "phase": phase, "iteration": iteration,
            "seconds": seconds,
            **{k: (evaluated[k].item() if hasattr(evaluated[k], "item") else evaluated[k])
               for k in self.benchmark.parameter_keys},
            **{k: float(evaluated[k]) for k in self.benchmark.objectives},
            "hypervolume": self.benchmark.hypervolume(frame),
            "igd_plus": self.benchmark.igd_plus(frame),
        }
        self.experiments.append(record)
        return record

    def _frame(self):
        import pandas as pd
        from hitl_bench.campaign import _columns
        return pd.DataFrame(
            [{**{k: r[k] for k in self.benchmark.parameter_keys},
              **{k: r[k] for k in self.benchmark.objectives},
              **{k: 1 for k in self.benchmark.valid_keys}} for r in self.experiments],
            columns=_columns(self.benchmark))

    def optimiser_proposal(self):
        """What the optimiser would run next. Copied from the control while the
        campaign is still a replay; computed live once it has diverged."""
        if self.state["mode"] == "replay" and self.n_done < len(self.parent["experiments"]):
            nxt = self.parent["experiments"][self.n_done]
            return {k: nxt[k] for k in self.benchmark.parameter_keys}
        from hitl_bench.campaign import _acquisition_seed
        from hitl_bench.runtime import limit_acquisition_memory
        from utils.bofire_optimization import bayesian_optimization
        limit_acquisition_memory()
        iteration = self.n_done - self.n_init + 1
        candidate = bayesian_optimization(
            self.benchmark.domain, self._frame(), n_candidates=1, verbose=False,
            seed=_acquisition_seed(self.seed, iteration)).iloc[0]
        return {k: (candidate[k].item() if hasattr(candidate[k], "item") else candidate[k])
                for k in self.benchmark.parameter_keys}

    def step(self):
        """One optimiser experiment. Returns the record, or None if waiting/finished."""
        if self.finished or self.waiting:
            return None
        started = time.time()
        proposal = self.state.pop("cached_proposal", None) or self.optimiser_proposal()
        evaluated = self.benchmark.evaluate(proposal)
        record = self._record(evaluated, "bo", self.n_done - self.n_init + 1,
                              round(time.time() - started, 2))
        alerts = self._alerts_now()
        if alerts and not self.finished:
            self.state["pending_alert"] = {
                "experiment": alerts[0],
                "p_star": triggers.pace_ratio_value(self.experiments, self.budget),
                "proposal": self.optimiser_proposal(),   # shown to the chemist
            }
        self.save()
        return record

    # --- the chemist's three answers -------------------------------------------
    def _decide(self, choice, **extra):
        alert = self.state["pending_alert"]
        self.state["decisions"].append({
            "at_experiment": alert["experiment"], "p_star": alert["p_star"],
            "optimiser_proposal": alert["proposal"], "choice": choice,
            "when": datetime.datetime.now().isoformat(timespec="seconds"), **extra})
        self.state["last_handled_alert"] = alert["experiment"]
        self.state["pending_alert"] = None

    def stop(self, why=""):
        self._decide("stop", why=why)
        self.state["done"] = True
        self.state["stopped_at"] = self.n_done
        self.save()

    def take_proposal(self, why=""):
        """Decline to intervene. The optimiser's own point runs next; in replay
        mode that is exactly the control's next experiment, so nothing diverges."""
        proposal = self.state["pending_alert"]["proposal"]
        self._decide("optimiser", why=why)
        self.state["cached_proposal"] = proposal
        self.save()

    def impose(self, shown_point, why=""):
        """The chemist's own conditions. From here on the optimiser runs live."""
        point = {k: unlabel(self.benchmark, k, shown_point[k])
                 for k in self.benchmark.parameter_keys}
        evaluated = self.benchmark.evaluate(point)     # KeyError if off the grid
        self._decide("chemist", why=why, point=point)
        self._record(evaluated, PHASE_CHEMIST, self.n_done - self.n_init + 1, 0.0)
        self.state["mode"] = "live"
        self.save()

    # --- persistence ----------------------------------------------------------
    def save(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self.state, handle, ensure_ascii=False, indent=1)
        self._save_reacto_project()

    def _save_reacto_project(self):
        """The campaign as a REACTO project, so it opens in Results like any other."""
        import pandas as pd
        try:
            from config_path import EXCEL_FOLDER
            from domain_storage import DomainStorage
        except ImportError:
            return
        excel_name = "hitl_%s_%s_seed%02d.xlsx" % (self.chemist, self.name, self.seed)
        rows = []
        for r in self.experiments:
            row = {"Point type": {"lhs": "Init", "bo": "BO", PHASE_CHEMIST: "Chemist"}[r["phase"]]}
            for k in self.benchmark.parameter_keys:
                row[self.pres["params"].get(k, (k, ""))[0]] = label(self.benchmark, k, r[k])
            for o in self.benchmark.objectives:
                row[self.pres["objectives"].get(o, (o, "", "max"))[0]] = r[o]
            rows.append(row)
        os.makedirs(EXCEL_FOLDER, exist_ok=True)
        pd.DataFrame(rows).to_excel(os.path.join(EXCEL_FOLDER, excel_name),
                                    sheet_name="Experiments", index=False)
        parameters = [{"name": self.pres["params"].get(k, (k, ""))[0],
                       "type": "categorical" if isinstance(self.experiments[0][k], str)
                       else "float"} for k in self.benchmark.parameter_keys]
        objectives = [{"name": self.pres["objectives"].get(o, (o, "", "max"))[0],
                       "direction": self.pres["objectives"].get(o, (o, "", "max"))[2]}
                      for o in self.benchmark.objectives]
        DomainStorage.save_domain(excel_name, self.benchmark.domain, parameters, objectives,
                                  metadata={"hitl_study": True, "chemist": self.chemist,
                                            "benchmark": self.name, "seed": self.seed})


# --- the assignment: which campaigns each chemist is given ----------------------
ASSIGNMENT_PATH = os.path.join(LIVE, "assignment.json")
DEFAULT_ASSIGNMENT = {
    # One campaign per reaction, the same for everyone, so that the chemists'
    # decisions on a given campaign can be compared with each other and with
    # the random draws made on that very campaign.
    "i": [1], "ii": [1], "edbo_ch_arylation": [1],
}


def assignment():
    if os.path.exists(ASSIGNMENT_PATH):
        with open(ASSIGNMENT_PATH, encoding="utf-8") as handle:
            return json.load(handle)
    return DEFAULT_ASSIGNMENT


def campaigns_for(chemist):
    """(benchmark, seed, done?) for one chemist, in the order they should be run."""
    out = []
    for name, seeds in assignment().items():
        if name.startswith("_"):            # a comment key, not a reaction
            continue
        for seed in seeds:
            parent = os.path.join(ARMS, "%s__no_hitl__seed%02d.json" % (name, seed))
            if not os.path.exists(parent):
                continue
            path = os.path.join(LIVE, "%s__%s__seed%02d.json" % (slug(chemist), name, seed))
            done = False
            if os.path.exists(path):
                with open(path, encoding="utf-8") as handle:
                    state = json.load(handle)
                done = state["done"] or len(state["experiments"]) >= state["budget"]
            out.append((name, seed, done))
    return out

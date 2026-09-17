# Article outline — a chemist in the loop of a Bayesian optimisation campaign

Working document, 17 September 2026. Written to be handed to a writing
assistant: every claim carries the number that supports it, where that number
lives, and its status.

    [MEASURED]   the number exists and is final
    [TO MEASURE] the experiment is designed, the data do not exist yet
    [DECIDE]     someone has to choose before this can be written

Never write a sentence in this paper that is not one of the first kind, or
explicitly flagged as the second. Numbers quoted here are the reference; if the
repository and this file disagree, the repository wins.

---

## 0. The claim

One sentence, everything else serves it:

> On the initial designs that trap Bayesian optimisation — a minority, but a
> large one — a chemist called by a pace alarm recovers what neither the
> optimiser nor a random intervention recovers, and the same mechanism, applied
> to a real synthesis, ends a campaign that had converged ten points below what
> the literature achieves.

Two things that sentence deliberately does **not** claim, and that the paper
must never drift into: that human-in-the-loop helps *on average* (five
participants cannot support it), and that the alarm *diagnoses* a trapped
campaign (it does not; it books an appointment).

**[DECIDE] Title.** Candidates, in decreasing order of how much they promise:

- *Knowing when to call a chemist: a stall alarm for Bayesian reaction optimisation*
- *A chemist in the loop: what a human adds when Bayesian optimisation stalls*
- *Bayesian optimisation gets trapped by its own starting design; chemists do not*

**[DECIDE] Target journal**, because it sets length, figure count and how much
goes to the SI. The study is a tool + a human-factors result + a lab
validation, which sits awkwardly across venues. To settle with JCM.

---

## 1. Figures — the spine of the paper

Decide these before writing prose: one figure is one result is one subsection.

| # | Figure | Status |
|---|---|---|
| 1 | The mechanism: a campaign, the alarm firing, the three answers, the REACTO page | to draw |
| 2 | The trap: 20 campaigns per reaction, the ones ending below 90 % in orange, alarm firings as dashes | **[MEASURED]** exists, weekly report |
| 3 | The calibration: where the alarm fires against how the campaign ends; (W, threshold) chosen as a pair | **[MEASURED]** `scripts/plot_firings.py`, `scripts/seed_choice.py` |
| 4 | The null model: random branches against their parent campaigns, and the drift of the estimate with sample size | **[MEASURED]** arylation only — **[TO MEASURE]** the two Suzuki |
| 5 | The chemists: each participant's branch against its control and the random arm, on the three assigned campaigns, plus the decision table | **[TO MEASURE]** |
| 6 | The laboratory: flavone, BO alone against BO + HITL; best yield against experiment; the three domain bounds the campaign collapsed onto; the literature ceiling as a line | half **[MEASURED]** (BO alone), half **[TO MEASURE]** |

Figure 4 is the one that forces a decision now: it exists only for the
arylation. Two nights of computation buy the two Suzuki campaigns. **[DECIDE]
whether the paper carries three reactions or one.**

---

## 2. Section skeleton

### Introduction

1. Bayesian optimisation is now standard for reaction conditions, and works.
2. It fails in a way that is invisible from the inside: a good catalyst tried
   once under bad conditions is written off, and the campaign spends its budget
   elsewhere. **[MEASURED]** how often, section 3.1.
3. Existing human-in-the-loop work in chemistry is mostly about *what* the
   human supplies (priors, constraints, preferences). The question here is
   different and simpler: **when should the algorithm ask, and what should it
   ask for?**
4. What this paper does: measures the failure, shows no internal signal can
   diagnose it, calibrates an alarm that calls rather than decides, measures
   what chance achieves at the call, what chemists achieve, and what happens in
   a real laboratory campaign.
5. **[DECIDE]** how much REACTO itself is a contribution here versus the
   vehicle. My preference: the vehicle, with the tool described in Methods and
   its own short paper later.

### 3.1 Bayesian optimisation is trapped by a minority of starting designs

**Claim.** The failure is frequent, and it is a chemistry failure rather than a
numerical one.

**[MEASURED]** 20 campaigns per reaction from 20 random starts, 10 initial
experiments + 30 optimiser proposals. Ending below 90 % of the best achievable
result: **13 of 20** on Suzuki case II, **5 of 20** on case I, **10 of 20** on
the C–H arylation. Mechanism, every time: the front-carrying catalyst is tried
once under bad conditions, gives 0 %, and is never tried again — on case II the
whole global front sits on L4 (PCy3) while the optimiser settles on L0 (XPhos).

*Source:* `CLAUDE.md` § What the data already settled; weekly report 7–13 Sept.
*Flag:* `CLAUDE.md` § The frozen settings says "13 of 18", the weekly report
says 13 of 20. **Regenerate the number from `analyse_arms.py` before
submission** and use one count everywhere.

*Figure 2.*

### 3.2 The trap is set by the initial design, not by the optimiser's randomness

**Claim.** A trapped campaign owes its outcome to its ten starting points; the
optimiser's own stochasticity contributes nothing.

**[MEASURED]** Initial design held fixed, acquisition seed varied over four
values: 72.5 % of the front every time on the arylation (seed 2), 37.3 % every
time on Suzuki case ii seed 3. Run on a benchmark with tied acquisition maxima
and on one without, so the result is not an artefact of ties.

**Why it matters, and it is the hinge of the whole paper:** it licenses the
case-study frame. Each assigned campaign is a *deterministic* object given its
start, so a single chemist's branch is comparable with a single control.

*Source:* `CLAUDE.md` § The trap is in the initial design.

### 3.3 No signal computable from the campaign itself can diagnose the trap

**Claim.** From the inside, a trapped campaign and a healthy one that is
converging look identical.

**[MEASURED]** Progress, ligand coverage (all seven tried by experiment 15 in
every campaign), model over-confidence, the value of the next proposal: none
discriminates. Trapped versus successful at experiment 15: 48 % against 46 %
concentration; at experiment 20, 75 % against 74 %. Only the *identity* of the
ligand differs, and that is what the campaign cannot know. The frozen P trigger
fires 41 times over nine campaigns at a cadence set by its cooldown, with mean
first firing 19.0 for campaigns ending below 60 % and 19.0 for those above 90 %.

**The consequence, which is the paper's idea:** the alarm should not try to
diagnose. It calls the chemist whenever progress stalls, and the chemist
diagnoses. The asymmetry pays for it — **[MEASURED]** interrupting a healthy
campaign costs one experiment in thirty; missing a trapped one costs about half
the result.

*Source:* `CLAUDE.md` § Signals tested and rejected; § What the checkpoint is for.

### 3.4 Calibrating the call

**Claim.** One dimensionless signal, three settings, all fixed by measurement.

**[MEASURED]**

    P* = progress over the last W experiments / average progress per experiment
         since the initial design
    W = 5 (0.125 of the budget) | threshold 0.30 | cooldown 5
    burn-in = n_init + max(5 BO experiments, W)  ->  experiment 15 on a 40-budget

P* equals 1 for a campaign progressing steadily, at any budget — the earlier
version divided by the accumulated gain, which decays as 1/t and silently
encoded a firing time. On case II: alerts **all 13** failed campaigns, **2.5
solicitations** per campaign, first firing at experiment **22.6** with **26 %**
of the final gain still ahead. The single campaign never interrupted is the one
reaching 100 % of the front.

State the declined alternative, it is a strength: W = 3 with threshold 0.10
fires three experiments earlier and leaves 35 % of the gain, at 3.1
solicitations. Better for detection; rejected for the load on five chemists.

State the false alarms: the trigger also fires on healthy campaigns, and that
is accepted by design.

*Source:* `CLAUDE.md` § The trigger, as decided; § The frozen settings.
*Figure 3.*

### 3.5 Three answers, and why the third one has to be human

**Claim.** At each call the chemist may let the optimiser continue, propose the
experiment themselves, or stop the campaign. Stopping cannot be delegated to a
rule.

**[MEASURED]** Stopping at the trigger's first firing over the ten selection
campaigns saves 20 experiments on average but loses a third of the
hypervolume; a campaign that would have reached 100 % keeps 14 % of its result
if stopped at its first firing. Only firings landing at experiments 29–30 could
be stopped nearly for free. A stop rule would have to be later and stricter
than an intervention rule and would still not tell a converged campaign from a
trapped one.

The distribution of the three answers is a result in itself, not a protocol
detail.

*Source:* `CLAUDE.md` § What the checkpoint is for (owner's decision, 9 Sept).

### 3.6 What chance achieves at the call — the null model

**Claim.** An intervention that carries no knowledge achieves almost nothing,
so anything the chemists gain above it is knowledge rather than disturbance.

**[MEASURED]** Arylation: 20 campaigns, 40 random branches, 130 interventions.
A random grid point at every alarm changes the final result by **+1.3 points**
on average; 18 branches improve, 11 are unchanged, 11 get worse; range −27 to
+23. One random point in five happens to use a front-carrying catalyst and
those branches gain about three times more.

**Write this sentence in the paper, it protects the whole analysis:** the same
estimate read +4.0 at 11 branches, +2.7 at 19 and +1.3 at 40. Small samples
flatter, and the human arm is a small sample.

**[TO MEASURE]** the same arm on Suzuki case I seed 8 and case II seed 12
(~12 h of computation), and 20 draws at the first alert of each assigned
campaign so that a single human answer can be placed by a percentile rather
than against a mean.

*Source:* `docs/nuit_du_10_septembre.md`; `results/arms_report_*.md`.
*Figure 4.*

### 3.7 What chemists do when they are called

**Claim.** **[TO MEASURE]** — the analysis is pre-specified below and must not
be chosen after seeing the data.

Design, **[MEASURED]** and frozen: three trapped campaigns, the same for every
participant, replayed experiment by experiment.

| Reaction | Seed | BO alone ends at | First alert | The trap |
|---|---|---|---|---|
| Suzuki I | 8 | 69 % of the front | 20 | Xantphos tried once at 40 °C, 0 %, rediscovered too late |
| Suzuki II | 12 | 44 % | 16 | PCy3 tried once at 0 %; campaign ends on XPhos |
| C–H arylation | 2 | 72 % | 16 | 77 % on CgMe-PPh at the start, then flat for 28 experiments |

Each participant: initials, three campaigns in any order, 10–15 minutes each,
alone, no discussion until everyone has finished. At each alert: one of three
answers and a written reason, both required by the page.

**Pre-specified analysis** (write it here, before the data):

1. Paired against the control at the same experiment count, and at the full
   budget. Both readings reported; `collect_live.py` computes both.
2. Paired against the random arm on the same campaign, reported as a
   percentile of the random distribution at the same alert, never as a
   difference of means.
3. Answers reported as a distribution over the three choices, with P\* at the
   moment of each.
4. The written reasons are data: read against what the campaign had actually
   shown the participant at that moment.
5. **[DECIDE]** how a stopped campaign is compared with a control that spent
   the full budget. Three readings are possible — report progress and
   experiments spent separately, report progress per experiment, or hold a
   stopped campaign flat to the full budget. The third needs no new metric.
   Choose before the first participant's data are read.
6. **[DECIDE]** the minimum number of participants below which this becomes an
   illustration rather than a result.

*Figure 5.*

### 3.8 In the laboratory: the flavone synthesis

**Claim.** The same alarm, in a real campaign, calls at the two moments a
chemist would want to be called; the optimiser alone converged onto the
boundary of its own domain and stopped ten points below the literature.

**[MEASURED]** on the BO-alone campaign (46 experiments: 14 k-means initial
points + 32 proposals; objectives yield and space-time yield, both maximised;
qLogNEHVI; outcome constraint yield ≥ 60 %; constraint T < bp(solvent) − 5 °C):

- The alarm fires at **experiment 20** (P\* = 0.156) and **experiment 44**
  (P\* = 0.000). Replayed prospectively, experiment by experiment, and
  retrospectively over the whole sheet: same firings, which also shows the
  running renormalisation of the objectives does not move the trigger.
- At the first alert, the best point is still **experiment 4, from the initial
  design** (86.8 % yield): six optimiser proposals had improved the yield by
  nothing, and **96.8 %** of the campaign's eventual progress was still ahead.
- The campaign then collapsed onto the corner of its own domain: of the last 21
  experiments, **18 at exactly 182 °C** (the ceiling imposed by the
  boiling-point constraint on DMSO, 189 − 5), **14 at exactly 5 min** (the
  lower bound of the time range), and **I₂ at 1.50 equiv** (the upper bound) in
  the last nine. Experiments 38 to 46 are the same point re-measured, yields
  oscillating between 65.7 % and 87.4 % with no progress.
- Exploration narrowed early: after the initial design, **DMSO in 32 of 32**
  proposals; bases TBD 24, triethylamine 7, DBU 1 — three of the six never
  revisited.
- Best results: **94.3 %** yield (triethylamine, DMSO, 135 °C, 295 min) and
  **1517.7 g L⁻¹ h⁻¹** at 87.2 % (TBD, DMSO, 182 °C, 5 min).
- A single experiment at 182 °C and **10 min** (experiment 32, 84.5 %), never
  revisited: the optimiser abandoned it because space-time yield rewards the
  shorter time.

**[TO MEASURE]** the literature ceiling. ~98 % yield, conditions inside the
domain, time possibly ~10 min — **to confirm from the paper**, with its
reference, its substrate, and whether it is batch or flow. If it is a batch
number at a different scale it remains legitimate chemical knowledge for the
chemist in the loop, but it cannot be the formal target of the comparison.

**[TO MEASURE]** the BO + HITL campaign, run during the leave. Conditions for
it to be a paired arm rather than a second campaign:

- the same 14 initial experiments, copied;
- the same domain, the same constraint, the same acquisition settings, the
  same announced budget;
- the chemist in the loop **blind to the BO-alone campaign's table**. Knowing
  that the synthesis reaches ~98 % is legitimate chemical knowledge and is
  precisely what the study measures; knowing which conditions the first
  campaign found is contamination;
- the reason for every answer written before the optimiser's own proposal is
  revealed;
- **[DECIDE]** the primary metric, pre-specified: number of experiments to
  reach an absolute target — e.g. yield ≥ 95 % — with the space-time yield
  reported alongside. BO alone: never, in 46 experiments.

**Two points worth making in the discussion rather than the results.** First,
this is a *different* trap from the in-silico one: not a catalyst written off,
but a convergence onto the domain's own boundary under the pressure of a
second objective. Same alarm, both cases. Second, the boiling-point constraint
is itself a chemist's decision — 184 °C in DMSO is prudent at atmospheric
pressure and arguable in a pressurised flow reactor. The optimiser inherits it
and cannot question it; the chemist can.

*Figure 6.*

### 4. Discussion

- What the chemists actually noticed, read against what they were shown. This
  is the heart of the discussion and cannot be drafted before the data.
- The alarm books an appointment; it does not diagnose. State it as a design
  position, with the asymmetry that justifies it.
- Cost of the intervention: one experiment in thirty for a false alarm.
- Two kinds of trap, one alarm (see 3.8).
- **Limitations, in the paper, not left to a referee:** five participants;
  a case study on trapped designs weighted by a base rate rather than an
  unbiased estimate; the arylation's substrate is not disclosed by its source,
  so participants reason on ligands, bases and solvents only; replayed
  campaigns are not laboratory work, which is what the flavone campaign is for;
  one laboratory reaction, one operator.
- **[DECIDE]** whether the blind validation on Reizman cases III and IV is
  reported here. It was reserved from the start, never used for any choice, and
  is applied once at the end whatever it says. My reading: it belongs in this
  paper, as one paragraph and one SI table.

### 5. Conclusion

Three sentences, no new claim. What was measured, what it licenses, what it
does not.

---

## 3. Methods — inventory

- Benchmarks and provenance: four Reizman Suzuki grids (5,670 conditions each)
  and the C–H arylation of Shields et al. (1,728 conditions, yield against
  reagent cost). Twelve grids were screened, three kept; the criterion was not
  where the optimiser does best but where the outcome depends on the random
  start, with a complete grid and named reagents. `data/README.md`.
- Campaign protocol: 10-point Latin hypercube, 30 sequential proposals,
  qLogNEHVI, one candidate at a time, REACTO's own optimiser.
- Reproducibility: the strategy is seeded; `sampling(..., seed)` and
  `_acquisition_seed(seed, iteration) = 100000 + 1000·seed + iteration`. Two
  runs agree to the twelfth decimal; a fork reproduces its parent exactly.
  Say plainly that 51 earlier campaigns predate the fix and are used only as
  independent samples, never as controls.
- Metrics: hypervolume on objectives normalised to [0, 1] by the grid's own
  range, reference point (0, 0); IGD+ reported alongside because case II's
  global front has three points and the hypervolume advances in steps.
- The alarm as implemented in REACTO, for a campaign with no fixed budget:
  the frozen fractions evaluated at 40.
- The live page: replay at one experiment per second, identical for every
  participant; after an imposed point the optimiser runs for real.
- The laboratory campaign: reactor, analysis, how yield and space-time yield
  are measured. **[TO WRITE]** — Deepak's material.
- Ethics / participants: what was told to the chemists, what was recorded.
  **[DECIDE]** whether ULiège requires anything formal for five colleagues
  answering an anonymised questionnaire-like task.

## 4. Supporting information — inventory

1. Provenance of every grid, checked against its published source
   (`verify_other_grids.py`); the nine grids whose provenance was missing.
2. Signals tested and rejected, with the measurement that rejected each.
3. The (W, threshold) pair: detection and firing time across the grid of
   settings; the declined W = 3 / 0.10 setting.
4. Reproducibility: the seeding, and the acquisition-tie analysis on the
   arylation.
5. Seed selection: why these three campaigns (`seed_choice.py`).
6. The full decision table: every participant, every alert, P\*, choice,
   reason, imposed point, and what the optimiser would have done.
7. The flavone campaign in full, and the HITL campaign beside it.
8. REACTO: what it is, where it lives, how to reproduce every campaign here.

---

## 5. Open decisions, collected

| # | Decision | Blocks |
|---|---|---|
| 1 | Target journal | length, figure count, SI |
| 2 | Three reactions or one — i.e. whether to compute the two Suzuki random arms | figure 4, section 3.6 |
| 3 | Participants and deadline | section 3.7 |
| 4 | Minimum number of participants for 3.7 to be a result | section 3.7 |
| 5 | How a stopped campaign is compared | sections 3.5, 3.7 |
| 6 | Flavone: the primary metric, pre-specified | section 3.8 |
| 7 | Flavone: who is the chemist in the loop, and blind to what | section 3.8 |
| 8 | Whether cases III and IV are reported here | discussion |
| 9 | REACTO: contribution or vehicle | introduction, methods |

## 6. What to hand to the writing assistant

This file, plus:

- `hitl_bench/CLAUDE.md` — every decision with its date and its measurement;
- the weekly report of 7–13 September — the same story in prose;
- `docs/nuit_du_10_septembre.md` — the computed arms;
- `docs/protocole_chimistes.md` — what the participants were asked;
- `data/README.md` — provenance;
- the CSVs from `collect_live.py` once the participants have answered.

Ask it to draft section by section, never to supply a number that is not in
these files, and to leave `[TO MEASURE]` holes visible rather than fill them.

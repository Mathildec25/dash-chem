# hitl-bench: decisions that are frozen

Read this before changing anything scientific. These are the study owner's
calls, recorded so that they are not quietly undone. Ask before departing from
any of them.

## Experimental design

**Benchmarks.** The four Reizman-Suzuki cases, as published grids (see
`data/README.md`). No MIT kinetics: the four cases serve as independent
replicates instead.

**Selection and blind validation.** Decided before looking at the data, and
binding:

| Cases | Role |
|---|---|
| I and II | selection. Build the gain table here, compare candidate triggers here, choose here. |
| III and IV | blind validation. Not used for any choice. The chosen trigger is applied once, at the end, and that number is reported whatever it says. |

Running no-intervention campaigns on III and IV is fine, they are the baseline.
What is forbidden is letting their outcomes influence any decision.

**Intervention.** A single point drawn at random among the untested grid points,
evaluated, appended, and the optimisation resumes. There is no simulated
chemist: the random draw is the null model against which real chemists are
measured in the human study. Arms: `no_hitl`, `trigger`, `fixed:t`.

**Paired design.** Both branches share their history up to the intervention, so
a forked branch is resumed from a saved campaign rather than replayed. The
Monte Carlo replication is over the random draw of the intervention point,
since the optimisation step itself is near-deterministic given the data.

## What the data already settled

**The frozen P trigger does not work, and was dropped.** Measured on nine
campaigns: it fires 41 times, at a cadence set by the cooldown rather than the
signal, because its condition holds in 46% of eligible experiments; on a grid
the hypervolume is a step function that does not move in 61% of them. Mean
first firing is experiment 19.0 for campaigns ending below 60% of the global
front and 19.0 for those ending above 90%. It does not discriminate.

**No signal built from the campaign's own history distinguishes a campaign
converging on the right answer from one converging on the wrong one.** Neither
progress, nor ligand coverage (all seven are tried by experiment 15 in every
campaign), nor concentration (48% for trapped campaigns against 46% for
successful ones at experiment 15, 75% against 74% at experiment 20). The two
behaviours are identical; only the identity of the ligand differs, and that is
precisely what the campaign cannot know.

**The useful intervention window closes early.** Campaigns that succeed commit
to the front-carrying ligand at experiment 11 or 21; those that fail reach it at
35, 36 or never. Meanwhile stall signals with any predictive value only fire
around experiment 31. The window where intervention would help is the window
where no signal is informative.

**Whether to intervene does not require knowing why progress stopped.**
Intervening on a converged campaign costs one experiment in thirty; missing a
trapped one costs about fifty points of hypervolume. The asymmetry settles it.

## The trigger, as decided

`pace_ratio`, the owner's own signal with its denominator corrected:

    P* = (recent gain / window) / (gain since the initial design / experiments since)

Frozen parameters, all hers except the threshold: window 3, threshold 0.10,
nothing before experiment 13, cooldown 5, **no deadline**. A forced call at a
fixed experiment was considered and rejected: the trigger only fires when it has
a reason to.

Why the denominator changed. The original divided by the gain accumulated since
the initial design, so under steady progress the ratio falls like W/(t - n_init)
whatever the campaign does, and the threshold silently encoded a firing time: at
a lookback of 3, a threshold of 0.05 is reached by that decay alone at
experiment 70 and one of 0.30 at experiment 20. Dividing by the same decay
removes it. P* equals 1 while a campaign progresses at its usual pace, at any
point, so 0.10 means what it says.

The cooldown was right all along. The earlier criticism that "the cooldown, not
the signal, sets the cadence" held only because a threshold of 0.05 on the old
formula was true in 46% of experiments. With a signal that discriminates the two
do different jobs: the threshold decides whether this is a real standstill, the
cooldown decides how often a chemist is disturbed. Measured on nine campaigns:
9.7 firings per campaign with no cooldown, 3.7 with a cooldown of 3, 2.1 with 8.

Known blind spot, stated because it has no fix in the history: a campaign that
crawls slowly but steadily never fires, its recent pace being its average pace.
Four of the nine campaigns are only called from experiment 24 on for that
reason. Saying "this one is too slow" needs a reference for how fast it should
go, and the campaign's own past cannot supply one. The initial design was tried
as that reference and does not work: the ratio of BO gain to LHS gain is 0.27 on
a campaign that ends trapped at 57.6% and 0.30 on the one that ends at 100%.
The only reference left is the model's own expectation, which is what
`over_optimism` reads and why the enriched logs matter.

## What the checkpoint is for

The trigger does not diagnose, it books an appointment. At each firing the
chemist is shown the campaign and chooses one of three answers:

1. **propose an experiment** - the intervention arm;
2. **let it run** - the trigger was a false alarm, which costs nothing;
3. **stop the campaign** - no more is expected from it.

The third is the study owner's decision of 9 September and it settles the
stopping question: no algorithmic stop criterion is needed or wanted.

Why it has to be the human. Stopping at the trigger's first firing was measured
on the ten selection campaigns: 20 experiments saved on average, but a third of
the hypervolume lost. A campaign ending at 100% of the global front would have
kept 14% of its result had it stopped at its first firing. Only firings that
land late (experiments 29-30) could be stopped nearly for free, at 87% to 100%
of the final result. A stop rule would therefore need to be later and stricter
than an intervention rule, and it would still be unable to tell a converged
campaign from a trapped one. The chemist can, because they know whether 44%
yield on this coupling is a good result or a failure.

**Open question, to settle before the human study.** A stopped campaign has not
spent 40 experiments, so its hypervolume cannot be compared to a no_hitl
campaign that has. Three options: report hypervolume and experiments spent
separately; report hypervolume per experiment; or hold a stopped campaign's
hypervolume flat to experiment 40, which penalises stopping too early and
rewards stopping when there was genuinely nothing left. The third needs no new
metric.

**Consequence for the layers.** A random suggestion cannot decide to stop, so
the null model has no equivalent and the in-silico layer can neither calibrate
nor benchmark that decision. Stopping exists only in the human layers, and the
protocol must record which of the three answers was given at each checkpoint:
their distribution is a result in itself, as is whether chemists stop the right
campaigns.

## Signals tested and rejected, so they are not tried again

All measured on the selection cases. None discriminates a trapped campaign from
a successful one; several are anti-correlated, firing more readily on campaigns
that end well.

| Signal | What it reads | Outcome |
|---|---|---|
| `plateau` | length of a run without improvement | fires late, no separation |
| `over_optimism` | standardised residual of the surrogate | saturated: fires at its earliest possible experiment in 9 campaigns out of 10, the GP being over-optimistic everywhere |
| `confidence_without_evidence` | collapse of the model's uncertainty | silent on a campaign at 37% and on one at 100% |
| D1, expected gain over total hypervolume | acquisition value | fires on 8 of 9 checkpoints of a successful campaign against 5 of 9 of a trapped one: the denominator grows with success |
| D_avant, expected gain over average pace | acquisition value | promising on 2 campaigns, refuted on 10: fires on 71% of a successful campaign's checkpoints against 50% of a trapped one's |
| dry-run p-value | run length against the campaign's own rate | never fires: as a campaign slows its estimated rate falls with it, so a long silence stays expected |
| exploration collapse | ligand entropy and spread | contradicted: concentration is 48% on trapped campaigns against 46% on successful ones at experiment 15 |
| LOO calibration | coverage of the GP's own intervals | untestable here: the grid is noiseless, the GP fits a noise of 0.3% of the signal variance, and coverage collapses to 0.25-0.34 in every campaign |

The last row matters beyond that signal: **the benchmark has no experimental
noise**, since an evaluation is a table lookup. Minerva's own protocol injects
Gaussian noise on the objectives; ours does not. Any detector built on the
model's calibration is therefore untestable on this benchmark, and the realism
of the whole in-silico layer deserves a decision on this point.

## Other candidates, kept for comparison

Deliberately few: each extra candidate is another chance to overfit the
selection set. All must be computable during a live campaign and expressed in
dimensionless quantities, so that they transfer to a reaction with a different
yield range.

1. `plateau` - no hypervolume improvement for K experiments. The honest
   representative of the hypervolume-curve family, and the floor to beat.
2. `over_optimism` - the model keeps promising more than it delivers.
3. `exhausted_promises` - the model proposes points it predicts to be dominated.
4. `confidence_without_evidence` - the model's uncertainty has collapsed.

A fifth candidate, based on the model's predictions for the ligands it has
stopped visiting, was considered and rejected: it would have required exposing
the fitted model out of REACTO's `bayesian_optimization`.

References every candidate is scored against: the best fixed fraction of the
budget, a random time, and not intervening. **A trigger that does not beat the
best fixed schedule does not deserve to exist**, and "intervene at 45% of the
budget, do not try to detect" is an acceptable and useful conclusion.

## Metrics

`hv_curve_auc` stays primary, with a rule of reading: it measures earliness,
not quality. Two campaigns of case I ended at the same 98.6% of the global
front with areas of 0.549 and 0.876. So the area is only compared **paired, at
equal intervention time**, where the shared prefix cancels exactly; across
different intervention times it is reported relative to its ceiling at that
time. Unpaired tables report the final hypervolume fraction and IGD+.

## Reactions beyond Suzuki, and why only one was added

Nine complete grids were run with the same optimiser on 3 to 5 seeds each. The
selection criterion is **not** how well plain BO does on average, it is the
spread between seeds: a reaction where every campaign reaches the front leaves
the chemist nothing to change, and measures nothing. See
`docs/reactions_candidates.md` for the full table.

Kept: **Suzuki case ii** (spread 63 points of front, failure has a chemical
reading) and **edbo_ch_arylation** (spread 22 points, 12 named ligands, and
objectives whose correlation is -0.002 where the Suzuki pair is redundant).
**snar** is kept as a control: 100% of the front on all three seeds.

Rejected: lnp3 and the five Buchwald grids reach the front too reliably, the
Buchwald grids are single-objective and store their reagents as raw SMILES, and
dye_lasers names its fragments by code.

### The trigger fires on healthy campaigns too, and that is not a fault

`pace_ratio` was run unchanged on every benchmark. At its first firing, the
fraction of the campaign's own final gain still to come is 0-2% on snar (which
ends at 100% of the front) and also 0% on edbo seed 2 (which ends at 72%,
stuck). **From inside the campaign these two are indistinguishable**, which is
the finding already established on Suzuki, now reproduced across unrelated
chemistries. Suzuki ii seed 4 is the counter-example to keep: the trigger fires
at experiment 15 with 86% of the gain still to come, on the one campaign that
reaches 100%. This is the quantitative argument for leaving the stop-or-suggest
decision to the chemist.

### edbo_ch_arylation has tied acquisition values; Suzuki does not

Measured, not suspected. At experiment 30 on edbo, **175 of the 1698 remaining
candidates are exactly tied** at the acquisition maximum, to the last float
digit, and `optimize_acqf_discrete` therefore returns the first in table order.
The tail of an edbo campaign is an alphabetical sweep of ligands and solvents,
identical across seeds. Cause: 12 ligands x 4 bases x 4 solvents = 192
categorical cells, of which a 40-experiment campaign visits 17; every tied
candidate sits in an unvisited cell and no tied candidate sits in a visited one.

The four Suzuki cases were checked at experiments 20, 30 and 40: the maximum is
**unique every time**, no ties. One categorical of 7 levels is coverable at this
budget; 192 cells are not.

So the two kept reactions illustrate two different failure modes of small-budget
BO - Suzuki ii over-exploits a wrong belief, edbo has no belief at all over most
of the space - and any comparison on edbo must state that the unaided baseline
is partly decided by table order.

### The tie fraction measures whether BO is working at all

Extending the tie measurement to dye_lasers gives a clean ordering, and it
follows how much of the categorical space a 40-experiment budget can visit:

    Suzuki (one categorical, 7 levels)   7 cells,    all visited,  0 tied
    edbo_ch_arylation                  192 cells,  17 visited,   175 / 1698 tied
    dye_lasers                        3458 cells,  30 visited,  3428 / 3428 tied

On dye_lasers the maximum, median and minimum of the acquisition are all
-4.59192: every remaining candidate is tied, the campaign is a table scan, and
that is why it reaches only 27% of the front. It is rejected for that, not for
its reagents - correcting an earlier note, its fragments are SMILES (boronic
acids, BODIPY cores, dibromoarenes), not anonymous codes.

The tie fraction is worth reporting in its own right: it is computable during a
live campaign, needs no knowledge of the front, and says whether the optimiser
is still choosing or merely enumerating.

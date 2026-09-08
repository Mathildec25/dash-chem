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
nothing before experiment 13, cooldown 3, **no deadline**. A forced call at a
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

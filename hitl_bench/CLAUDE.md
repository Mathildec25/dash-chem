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

## Candidate triggers to be tested

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

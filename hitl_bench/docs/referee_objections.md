# The referee's report we would rather write ourselves

Written 17 September 2026, against the paper as planned in
`article_outline.md`. Each objection: what a hostile but competent referee
says, how dangerous it is, where the answer already lives, and what is still
missing. A paper that answers these in its own text is not reviewed the same
way as one that waits to be asked.

Danger is scored for **this** paper, not in general:

    HIGH    can cost the paper, or force a major revision
    MEDIUM  will be raised; a paragraph settles it if the paragraph exists
    LOW     will be raised by someone; one sentence settles it

---

## A. The human layer

### A1. "Five participants is not a study." — HIGH

The single most likely rejection reason.

*Answer in hand.* The paper never claims an average benefit. It is a case
study on trapped initial designs, weighted back by a measured base rate, with
each participant's branch compared against its own control and against a
measured null. Say this **in the abstract**, not only in the limitations: a
referee who reaches the limitations section still believing an average was
claimed is already lost.

*Still missing.* A decision, before the data: the minimum number of
participants below which this becomes an illustration (open decision 4).
Never report a mean over participants. Report every participant individually,
in the figure and in the table.

### A2. "Your participants are your colleagues, and they know what you want to find." — HIGH

Demand characteristics. Chemists who guess that the study hopes they intervene
will intervene.

*Answer in hand.* The invitation says it in as many words: *"There is no score
and no trick. A campaign that ends badly says something about the algorithm,
not about you. Letting it continue is a perfectly good answer when you think it
is on the right track."* Quote that sentence in the Methods — it is evidence,
not decoration.

*Still missing.* The distribution of the three answers is the test. If nobody
ever answers "let it continue", the objection stands whatever the instructions
said. Report the distribution first, before any outcome.

### A3. "A decision with no cost is not a decision." — HIGH

On the replayed page a proposed experiment costs nothing: no reagent, no
week, no failure in front of a supervisor.

*Answer in hand.* This is exactly why the laboratory layer exists, and the
cleanest justification for section 2.3. Make the argument explicitly rather
than leaving the reader to notice.

*Irreducible for the replayed layer.* State it.

### A4. "Order effects." — MEDIUM

Participants run three campaigns in any order. By the third they know the
format, and may have worked out that a stall means a trap.

*Answer available but not yet computed.* The JSON records `started` per
campaign, so the order is recoverable for every participant. Report it, and
report the answers by position (first, second, third campaign). If the rate of
intervention rises with position, say so — it is a finding, not a flaw.

### A5. "Anonymity and consent." — LOW, but only if handled before the data

The written reasons are published verbatim in the SI.

*Still missing.* Confirm the participants were told this. One sentence added to
the invitation settles it, and it has to be added **before** they answer.

---

## B. The trigger

### B1. "You tuned the trigger on the same cases you evaluate it on." — HIGH if unanswered, neutralised if reported

*Answer in hand, and it is a strength.* Cases I and II are the selection set,
cases III and IV were reserved before any data were seen and used for no
choice. The trigger is applied to them once, at the end, and the number is
reported whatever it says.

*Still missing.* Actually run it, and report it even if it is disappointing
(section 2.4). A pre-registered hold-out that only appears when it flatters is
worse than none.

### B2. "What is your false-alarm rate?" — HIGH, and this is a real gap

The paper says the trigger fires on healthy campaigns and that this is
accepted. A referee will ask for the number: **of the campaigns that end well,
what fraction are interrupted, and how often?**

*Computable today from the existing arms, no new campaigns.* Report it as a
two-by-two: campaigns ending below / above 90 %, alerted / not. Then the cost
sentence — one experiment in thirty — lands on measured ground instead of
rhetoric.

### B3. "Why pace, why 0.30, why a window of five?" — MEDIUM

*Answer in hand and unusually strong.* Alternatives tested and rejected with
the measurement that rejected each; W and the threshold chosen as a pair;
the better-detecting setting (W = 3, threshold 0.10) **declined and reported**,
with the reason. Publish the rejected alternative: a paper that shows what it
gave up is read as careful.

### B4. "Your detection is 13 out of 13, which with 13 events means very little." — MEDIUM

*Honest answer.* With 13 events the 95 % interval runs from 77 % to 100 %. So
write "alerts at least 77 % of failed campaigns (13 of 13, Wilson 95 %)", never
"alerts every failed campaign". Doubling case II to 40 campaigns would move
that floor to about 87 % for roughly 3.5 hours of computation.

---

## C. The benchmark

### C1. "Pre-computed grids have no experimental noise; real optimisation does." — HIGH

A chemistry referee will raise this. A campaign that reads its yields from a
table never has to distinguish a bad condition from a bad measurement.

*Partial answer in hand.* The grids are real published measurements, not an
emulator, and the laboratory campaign carries real noise.

*Cheap strengthening, worth considering.* Re-run a subset of campaigns with
noise added to the observed objectives, at a level taken from the replicates
the source reports, and show whether the trap and the firing times survive. It
is the kind of control that removes the objection entirely, and it is one
night of computation.

### C2. "One optimiser, one acquisition function. Is this a property of BO or of BoFire's qLogNEHVI?" — HIGH

*Partial answer already in the repository, and it is under-used:* two different
surrogates agree on which catalyst carries the front, in all four cases
(`CLAUDE.md`). Bring that measurement into the paper — it is the beginning of
an answer and it currently sits unread in a decisions file.

*Honest limit.* `CLAUDE.md` already records that the determinism result "does
not say that another optimiser would be trapped by the same design". Say the
same in the paper, in the same words.

### C3. "Three reactions out of twelve screened — how were they chosen?" — MEDIUM

*Answer in hand.* The criterion was stated before looking at outcomes: not
where the optimiser does best, but where the outcome depends on the random
start, with a complete grid and named reagents. Show the screening figure, not
just the three survivors.

### C4. "A budget of forty experiments is arbitrary." — LOW

It matches the published campaigns, and every window in the trigger is a
fraction of the budget rather than a count, so the alarm transfers to a
campaign of any length. One sentence.

---

## D. The laboratory campaign

### D1. "One campaign per arm, no replicate." — HIGH, and irreducible

*Own it.* This is a demonstration that the mechanism transfers, not a
statistical comparison. Word it that way everywhere, including the abstract.

### D2. "The two campaigns were run at different times, perhaps with different batches." — HIGH

*Still missing, and it must be handled before the HITL campaign runs.* Record
the reagent batches, the analytical method and the operator for both campaigns.
If anything differs, repeating two or three conditions of the first campaign at
the start of the second costs almost nothing and settles the question.

### D3. "The chemist in the loop already knew the answer." — HIGH

*Draw the line explicitly in the Methods.* Knowing that the synthesis reaches
~98 % is chemical knowledge, and measuring what that knowledge is worth is the
entire point. Having seen the first campaign's table is contamination. State
exactly what the chemist was shown and what they were not.

### D4. "The plateau is your constraint's fault, not the optimiser's." — HIGH, and it is the sharpest one

The campaign pressed against a temperature ceiling the user imposed, at the
shortest permitted time and the highest permitted iodine loading. A referee
will say: the optimiser behaved correctly inside a badly specified box; this is
user error, not a failure of Bayesian optimisation.

*The answer is not a defence, it is the point.* A constraint is a chemist's
judgement frozen at project creation — prudent at atmospheric pressure,
arguable in a pressurised reactor — and the optimiser inherits it without being
able to question it. The checkpoint is where it becomes questionable again.
Section 3.4 must make this argument head-on and early, or the referee will make
it first and it will read as an excuse.

### D5. "With two objectives, space-time yield dragged the campaign to the corner. Another weighting would have found the literature optimum." — MEDIUM

Fair, and partly the same point as D4. Say plainly that the campaign optimised
what it was asked to optimise, and that recognising when the trade-off has gone
somewhere unhelpful is a judgement the optimiser has no access to.

### D6. "Comparing against a literature yield obtained under different conditions." — MEDIUM

*Handle by construction.* Pre-specify an internal target reached by both arms
in the same reactor, and use the literature number as context and as the
chemist's knowledge, not as the axis of the comparison — unless the conditions
turn out to be transposable, which is still being checked.

---

## E. Framing

### E1. "Human-in-the-loop optimisation is not new." — HIGH

*The angle has to be one sentence and it has to be early:* existing work asks
what the human supplies — priors, constraints, preferences. This paper asks
**when the algorithm should ask**, and shows that no signal computable from the
campaign can answer it, so the call has to be cheap and frequent rather than
accurate. Write the related-work paragraph so that a reader can place the paper
in one reading.

### E2. "Is this a tool paper or a study?" — MEDIUM

Open decision 9. My reading: a study, with the tool described honestly in
Methods and available, which is what this journal's readership wants anyway.

### E3. "Where is the code and the data?" — LOW here, and a strength

Everything is in one repository with the decisions, the seeds and the
provenance. Archive it at a DOI before submission and say that any campaign can
be regenerated from its seed.

---

## What to compute before submission, in order

1. **Wilson intervals everywhere.** Free, already in `analyse_arms.py`. Answers
   B4 and most of A1.
2. **The false-alarm rate** (B2). Existing data, no new campaigns. The largest
   missing number in the paper.
3. **Sensitivity of "failure" to the 90 % threshold.** Existing data. If 13/20
   becomes 9/20 at 85 %, better to know it than to be told.
4. **The blind validation on cases III and IV** (B1). It is the whole point of
   having reserved them.
5. **The random arm on the two Suzuki campaigns.** A missing figure, not an
   imprecise number — worth more than any extra precision elsewhere.
6. **Noise sensitivity** (C1), if a night is free after the rest.

## What to record before the flavone HITL campaign runs

- reagent batches, analytical method, operator, for both arms (D2);
- exactly what the chemist in the loop was shown and told (D3);
- the pre-specified target and budget, written down before the first
  experiment (D6);
- two or three conditions of the first campaign repeated at the start of the
  second, if anything in the set-up has changed (D2).

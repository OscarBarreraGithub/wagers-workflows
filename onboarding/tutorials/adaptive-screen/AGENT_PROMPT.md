# Agent exercise: fictional propose–measure–import–update

You are learning software bookkeeping and a small fixed statistical model.
Everything in this exercise is fictional. `FABLE-*` IDs are invented; they are
not genes, biological targets or recommendations. Do not connect this tutorial
to robots, culture manipulations, experiment controllers or publications.
Do not call a synthetic high score a biological hit. GP uncertainty is model
uncertainty under fixed assumptions, not validated biological uncertainty.

Read README.md and use the isolated pinned runtime. Run the single suite command
once on a clean code checkpoint, using a fresh ignored output directory. Report
PASS/FAIL honestly, exact tested commit/source hashes, environment hashes, command
logs and observed trajectories. Do not tune seeds/settings or demand adaptive
superiority. Linux, independent review and integration remain separate gates.

1. Generate the default 200 fictional candidates and six round-zero observations.
   Initialize a snapshot using only candidate features/status and the observed
   CSV. Keep `truth.csv` with the separate simulator/evaluator; selection must
   never read it, including indirectly through feature engineering or seed choice.
2. Propose four candidates with `mean + 1.5*std` from the fixed sklearn GP. Explain
   what mean, std and score mean under this toy model. Inspect all saved scores
   and identities. Do not issue another batch while one is pending.
3. Ask the separate simulator for a fictional outcome CSV. Deliberately make a
   *copy* with a wrong sample identity or missing value. Import that copy and
   verify refusal, no output snapshot and byte-identical prior state. Correct
   the copy and retry at the same destination. Never modify accepted snapshots.
4. Import only the complete, identity-matched batch. Explain how the new observed
   values, rather than pending requests, change the next fit. Repeat for three
   batches at most. Stop after the finite budget.
5. Compare against seeded random selection from exactly the same initial state,
   seed and observation budget. Hidden truth is for retrospective evaluation
   only. Report observed best per round and hidden evaluator regret, whether
   either strategy wins or loses. Do not generalize this one toy run.

This deliberately omits study design. For any real study, feature design,
functional assay choice, batch sizes, control/replicate design, measurement
quality, confounding, outcome definitions and wet-lab review remain
study-specific human decisions. This CSV contract has one fictional sample and
one outcome per target; it is not an assay/replicate schema. Do not invent those
decisions, infer biological confidence from GP std, recommend real genes or
execute wet-lab actions. Stop at the fictional software exercise and report its
limits plainly.

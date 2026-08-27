# K1 Split C -- banked evaluation (FINAL, single-shot) -- 2026-08-28

Chain: d08eaf7 -> b01d01d -> ea06927 -> 00735af -> 2d61ab9 ->
afc386a -> a6c934a -> 2997876 (evaluation code sync) -> 6e08456
(provenance repair; corpus + frozen predictions tracked). Run on the
Windows/committed-gauge platform, seneca-ml environment; per rev D.2
no development intervened after Split A closed, so this single
evaluation is the final.

## Setup

Train: 98 systems -- ALL non-mixed H4 + H6, per the FROZEN protocol
Sec. 4. Recorded deviation resolution: splits.json's split_C field
("all non-mixed") would have included the test system itself; the
frozen text governs and the runner implements it verbatim, printing
the resolution into its own output. Test: h8_chain (6333 letters,
support 2468), never seen, four sites larger than any training
system; no copy baseline exists. Model: v1 = C1C2K, five seeds.
Predictions FROZEN to k1_corpus/predictions_splitC_h8.pkl (committed
at 6e08456) before scoring.

## Result

  MODEL  F1 0.093 +- 0.000 (seed spread) | theta R2 -7.237 +- 0.009
  B2     F1 0.055                        | theta R2 -12.315

  P1 gates: content F1 >= 0.60           FAIL
            content >= B2 + 0.10 (0.155) FAIL
            theta R2 >= 0.5              FAIL
  T4 warm-start: PENDING -- to be scored from the frozen predictions
  once the compile-side harness exists (staged scoring, one touch of
  the test system, declared in advance).

Single-system caveat, stated in advance and repeated here: no
fold-level CI exists on Split C; seed spread is the only reported
uncertainty.

## Honest reading

The model beats B2 on both metrics (content +0.038; theta "+5.08"
only because B2 collapsed to -12.3). At R2 = -7.2 the model's theta
predictions are worthless in absolute terms on H8: beating a
collapsed baseline is drowning slower, not swimming. The mechanism
of the content failure is visible in the predictions themselves:
~380 predicted letters against 6333 true -- the MULTIPLICITY SCALE
learned from H4/H6 does not transfer to H8-sized repetition counts.
Which-letters knowledge transfers; how-many and theta do not, at
this model and data scale.

## rev E.1 size-slope (registered secondary endpoint)

  n=4 : dR2 -0.067   dF1 +0.016   (Split-A final, fold-weighted)
  n=6 : dR2 -0.147   dF1 +0.039   (Split-A final, fold-weighted)
  n=8 : dR2 +5.078   dF1 +0.038   (vs B2, the only defined baseline)

The CONTENT edge over the strongest available baseline is
size-stable (+0.016 / +0.039 / +0.038) -- the one transfer signal
that survives, seed-stable, and consistent with the rev D.3
hypothesis in its honest form: the model's content advantage holds
where baselines weaken. The n=8 theta point is baseline-collapse
artifact and is NOT evidence of theta transfer.

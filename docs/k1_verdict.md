# K1 Learnability Test -- VERDICT: INCONCLUSIVE -- 2026-08-28

Recorded per the frozen decision rule (rev A sections 7-8, amended
B through E; full chain d08eaf7 -> b01d01d -> ea06927 -> 00735af ->
2d61ab9 -> afc386a -> a6c934a -> 2997876 -> 6e08456). Every banked
evaluation, every amendment, and every null result named below is in
that history, older than the claims it supports.

## Why INCONCLUSIVE, mechanically

- PASS and WEAK PASS: blocked. P2 failed at the final Split-A
  evaluation (theta CI-separated below the strongest baseline,
  -0.098 +- 0.078, despite content CI-separated ABOVE copy,
  +0.028 +- 0.021). P1 failed at Split C (all three gates).
- FAIL: cannot fire. The frozen clause requires that NEITHER model
  family beats B2 on ANY transfer split; only M1 was built (M2
  never attempted), and M1 beats B2 on Split C content (+0.038,
  seed-stable). The clause is unsatisfiable on the evidence.
- Therefore, by rev A L1: INCONCLUSIVE, with its pre-committed
  consequences in force.

## Pre-committed consequences (now in force)

1. K1 stays OPEN. No "chains are learnable" claim is made in any
   pitch or paper; no "chains are unlearnable" claim either.
2. Commercial claims RESTRICT to D2 (exact amplitude corpora with
   machine-precision certificates) and D4 (benchmark suites with
   frozen splits and the verification harness) -- both of which now
   exist as shipped, committed artifacts.
3. NAMED FOLLOW-UP (registered here; threshold and date):
   K1b-T4 -- warm-start scoring of the FROZEN Split-C predictions
   (k1_corpus/predictions_splitC_h8.pkl, committed 6e08456) against
   a cold compile of h8_chain, once the compile-side warm-start
   harness exists. Threshold, inherited from the frozen P1:
   >= 30 percent optimizer-cost savings vs cold start AND >= 1.3x
   the savings of a B2-seeded warm start. Date: harness built and
   the measurement banked by 2026-09-30. This is also the first
   measurement of the plan-B architecture (NN proposes, exact/
   variational machinery refines), so its result feeds K1b design
   regardless of sign.

## What the test established (positives, all banked)

- Content-layer learnability with a SIZE-STABLE edge over the
  physics baseline: dF1 +0.016 / +0.039 / +0.038 at n = 4 / 6 / 8
  (rev E.1 secondary endpoint) -- which-letters knowledge transfers
  across system size.
- Content above copy in aggregate at Split A (CI-separated), with
  the dev-loop gains confirmed inner -> outer (rev D.1 protocol
  faithful; no overfitting-to-dev).
- The model's theta wins concentrate exactly where baselines break
  (c2_singlet +0.273 +- 0.091 CI-separated) -- the rev D.3 pattern,
  standing.
- Four measured gauge layers, one discovered by the apparatus
  auditing itself (the theta-redundancy manifold, rev C), plus the
  count-vs-set pinning separation -- physics results with standing
  value independent of any ML verdict.
- The corpus, splits, harness, baselines, and verifier: a shipped
  benchmark product (D4) and pilot data product (D2), platform-pair
  certified.

## What the test established (negatives, equally banked)

- Theta does NOT transfer across size at this model and data scale
  (R2 -7.2 on H8; worthless in absolute terms).
- Multiplicity SCALE does not transfer (~380 predicted letters vs
  6333 true).
- Ring-family theta resisted every tested feature family (rev E.3
  ledger: C1, C3, SG nulls by name).
- All three P1 gates failed at Split C; P2 failed at Split A.

## Process ledger (deviations and repairs, by name)

- splits.json split_C field contradicted frozen Sec. 4; resolved in
  favor of the frozen text, printed into the evaluation output.
- The Phase-0 freeze silently omitted the corpus data (*.npz/*.pkl
  ignore rules; git add drops ignored files without warning);
  repaired at 6e08456 with content certified equal to the freeze-era
  zip and the platform-pair verification. Rules and splits were
  frozen on time; data was tracked late.
- A stale interactive rebase from the co-author cleanup sat dormant
  in .git for a week; cleared via rebase --quit at the repair. It
  also retroactively explains the orphan commit e350dda.

## What feeds the pitch (DOE Sep 10; Activate Sep 15)

The honest sentence: "A pre-registered learnability test with
frozen thresholds returned INCONCLUSIVE: chain content transfers
across system size and beats physics baselines; angles and
multiplicities do not, at small-model scale. The certified corpus,
benchmark, and amplitude products shipped regardless, and the
registered follow-up measures whether NN proposals cut certified
compile cost -- the metric that matters at scale." Every number in
that sentence has a commit hash.

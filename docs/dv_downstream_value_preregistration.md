# DV Downstream-Value Test -- Pre-Registration Protocol (draft for sign-off)
# tucc-chain-compile | Seneca Labs | drafted 2026-09-07
# freeze by commit AFTER the K1b-T4 verdict and BEFORE any training

## 0. What this test can and cannot establish (read first)

A PASS establishes, with pre-registered criteria and controls: "a small
model trained on Seneca's certified data outperforms the same model
trained on approximate data for the same systems, evaluated on held-out
systems in the strong-correlation regime, at measured sample
efficiency; and training with the certified derivations as an auxiliary
target improves generalization beyond what any auxiliary target
provides." That licenses the two withheld pitch sentences (Strategy
Addendum B §4).

It cannot establish that the effect persists at foundation-model scale
(the corpus is 116 systems, mostly small), nor market demand. It yields
sign and slope at the tested scale, with error bars. That is the honest
bar and it is the one an ML reviewer will hold.

Naming note: K1-K4 are kill criteria in the strategy memo; K2-VAR
already strains that convention. This experiment is labeled DV to avoid
a second collision. Settle naming at freeze.

## 1. Objects under test

DV-LC  G_exact  : (system description) -> (certified property), learned
                  from certified labels;
       G_approx : the same map learned from approximate labels of the
                  SAME systems (paired design);
       both evaluated against certified labels on held-out systems.
DV-PS  G_exact with an auxiliary chain-content head, versus without,
       versus with a shuffled-chain auxiliary head.

System description: the pinned-gauge integral dump, as K1 §1.
Primary property: correlation energy at the certified geometry.
Secondary (reported, not in the rule): total energy; support size and
max|theta| as correlation-hardness proxies.

## 2. Corpus

Tier A + Tier B as K1 §3 (116 certified systems). No new compilation.

Approximate labels, generated once and archived with the dumps:
  - MP2 in the model space, from the dump (available for every system;
    already a K1 feature).
  - DFT (draft: PBE and B3LYP) in the same basis, for systems whose
    certified label is full-space FCI (Tier A; confirm which Tier B
    systems qualify). Not defined for CAS-restricted systems, where the
    comparison would be across model spaces; MP2 is the universal
    approximate label, DFT the stronger one where it applies.
  DECIDE AT FREEZE: functional list; which Tier B systems enter the
  DFT comparison.

Chain labels for DV-PS: grown-portion letter multisets. Gauge-averaged
labels (milestone §8.4) where available; otherwise the single certified
chain, with the measured ceiling (N2 F1 0.492; H8 four-way value when
banked) reported alongside.

## 3. Splits (frozen as JSON, committed before training)

  A INTERPOLATION leave-one-geometry-out within each scan. Exact labels
                  are expected to win by construction; measures margin.
  S STRETCH       train weak-to-moderate correlation -> test strong.
                  Draft boundary: R <= 2.0 bohr train, R >= 2.6 bohr
                  test, per scan; C2 and N2 series by the same rule.
                  THE DECISIVE SPLIT for DV-LC: the regime where
                  approximate labels are systematically wrong and the
                  product's premise lives.
  C CROSS-SIZE    train H4 + H6 (both topologies) -> test H8 chain;
                  C2 as stretch. The scale test. Reported for both
                  tests; a failure here is pre-registered as a
                  corpus-size finding and does NOT enter the rule.

## 4. Baselines (each under the same compute cap)

  B-DIRECT   the approximate label itself as the prediction (no model).
             "Does a model trained on exact data beat simply using
             DFT / MP2?" is the buyer's question; this is its comparator.
  B-COPY     nearest training geometry's certified label.
  B-NOAUX    (DV-PS) the model with no auxiliary head.
  B-SHUFFLE  (DV-PS) auxiliary head trained on shuffled chain labels
             (shuffled across systems). Separates content from
             regularization: if any auxiliary target helps equally,
             the effect is not the derivations.

## 5. Models

DV-LC: M1 family (physics-featurized gradient-boosted trees, as
  k1_model_m1.py), single family at freeze so architecture cannot be
  the excuse in either direction.
DV-PS: a small MLP with a shared trunk and two heads (property;
  chain-content multiset over the compiler's combinatorial pool), since
  auxiliary supervision requires a shared representation and trees do
  not share one. Parameter count fixed at freeze (draft: <= 1e5).
Compute cap fixed and equal across arms and baselines. 5 seeds each;
report mean and 95% CI. Frozen test sets touched exactly once.

## 6. Learning curves (DV-LC)

Training-set sizes n in {8, 16, 32, 64, all}, stratified across scans,
identical system draws for the exact and approximate arms at each n.
Metric: MAE in mHa against certified labels on the split's test set.
Sample-efficiency ratio: n_approx / n_exact at matched MAE; report
"not reached" if the approximate arm never reaches the exact arm's MAE.

## 7. Decision rule (numbers are DRAFTS; freeze at sign-off)

DV-LC PASS requires ALL of:
  L1 Split S: model_exact beats model_approx on MAE, CI-separated, at
     every n >= 16.
  L2 Split S: model_exact beats B-DIRECT (best available approximate
     method) at n = all, CI-separated.
  L3 Sample-efficiency ratio >= 2 at the largest matched MAE.
DV-LC WEAK PASS: L1 and L2 hold on Split A but not S (label quality
  helps in-distribution only; claim scoped to interpolation).
DV-LC FAIL: L2 fails on both A and S under the cap (the model cannot
  beat just using the approximate method; the corpus does not teach
  what DFT/MP2 do not already know at this scale).

DV-PS PASS requires ALL of:
  P1 Split S: model_aux beats B-NOAUX on property MAE, CI-separated.
  P2 Split S: model_aux beats B-SHUFFLE, CI-separated.
DV-PS FAIL: P1 fails; or P1 passes and P2 fails (any auxiliary target
  would have helped; the derivations add nothing beyond
  regularization).

Split C outcomes are reported for both tests and do not enter either
rule.

## 8. Procedure and hygiene

  Day 0     Freeze this document (Logan sign-off on §2 choices and §7
            thresholds); commit hash = pre-registration.
  Day 1     Generate approximate labels; archive with dumps; commit.
  Day 2     Freeze splits, metrics harness, baselines; commit.
  Day 3-5   DV-LC: Splits A, S, C, one evaluation each; bank.
  Day 6-8   DV-PS: Splits S, C, one evaluation each; bank.
  Day 9     Write-up; feed outcomes into Strategy Addendum B §4 table.
  Deviations recorded in a ledger by name. No arm re-run after its
  test set is touched.

## 9. What becomes sellable, by outcome

  DV-LC PASS:  "Training on certified labels improves a downstream
               model by Y at Z samples, in the regime where DFT is
               wrong." Full sentence, with numbers.
  DV-LC WEAK:  Same sentence scoped to interpolation within a scan.
  DV-LC FAIL:  D2 remains sellable as verification/evaluation data; the
               training-improvement sentence is retired at this scale.
  DV-PS PASS:  "Training on the derivations improves generalization
               beyond any auxiliary target." D3 lives.
  DV-PS FAIL:  D3 retired as a training product; chains remain
               provenance/verification data (K1 §9 amended reading).

## 10. Known threats to validity, addressed

  - Exact labels win by construction in-distribution: the experiment
    measures margin and sample efficiency, not existence. The headline
    is Split S, where winning is not guaranteed.
  - Approximate labels are biased, not noisy: this is not the classical
    label-noise setting; learning curves reflect systematic error, and
    the write-up says so.
  - Corpus scale: 116 systems; Split C may fail for scale reasons;
    pre-registered as a scale finding.
  - Auxiliary-task confound: B-SHUFFLE.
  - Chain-label gauge: roughly half the content label is convention
    (N2 F1 0.492); auxiliary targets use gauge-averaged or
    invariant-core content where available; the ceiling is reported.
  - Architecture as excuse: one family per test at freeze; a second
    family only if the first passes.
  - Leakage: features and both label sets derive from the same dumps;
    splits are by system, never by geometry-within-system for S and C;
    test sets touched once; the protocol hash predates training;
    clean-checkout replication on the second platform before any
    public claim.

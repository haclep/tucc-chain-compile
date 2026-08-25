# K1 Learnability Test -- Pre-Registration Protocol (draft for sign-off)
# tucc-chain-compile | drafted 2026-08-25 | freeze by commit before any training

## 0. What this test can and cannot establish (read first)

A PASS establishes, with pre-registered criteria and controls: "certified
UCC factor chains are a learnable representation -- a small model trained
on chains from smaller/nearby systems predicts the content, amplitudes,
and useful ordering of chains for held-out systems, beating physics
baselines, including across system size." That retires kill-criterion K1
and licenses building the learned-compiler product and selling chain
corpora as training data ON TECHNICAL GROUNDS.

It cannot establish market demand, pricing, or buyer behavior (K2-K4
remain live), and no experiment yields "100%." What it yields is the
strongest currency that exists for the claim: falsifiable, baseline-
controlled, pre-registered evidence that a technical reviewer at a
model-training lab would accept. That is the correct bar.

One correction to the audit memo, for pitch hygiene: the falsified
per-support cost law was shown to be STATE-FAMILY-dependent (triplet
flat ~2.28, singlet decaying 2.89 -> 2.30), not shown to be a routing
gauge artifact. Demote it from "geometry-only law"; do not call it
gauge -- that is a different, unproven claim.

## 1. The object under test

The map F: (system description) -> (certified chain), where the system
description is the pinned-gauge integral dump (orbital energies,
one/two-electron MO integrals, geometry) and the chain is the ordered
list of letters (holes, parts) with angles theta produced by the
deterministic sd_routed compiler. F is well-defined: with the dump's MO
gauge pinned, the compiler is platform-deterministic to the digit
(measured, 12/12 and 5/5 reproductions). Measured layer anatomy of F
(this campaign) fixes the task hierarchy:

  L0 support membership   -- pinned within families; gauge-invariant
  L1 letter content       -- which letters, with multiplicity (smooth
                             within topology, J 0.70-0.93)
  L2 amplitudes theta     -- smooth within molecule (r 0.51-0.96)
  L3 ordering             -- churns (LCS 0.33-0.51); partially
                             transferable across topology (tau 0.59)

## 2. Tasks (all four evaluated; the decision rule weighs them below)

T1 CONTENT: predict the letter multiset of the chain from the dump.
T2 AMPLITUDE: predict theta for each true letter (regression).
T3 ORDER: next-letter prediction given a chain prefix (the audit memo's
   literal task), plus Kendall tau of predicted vs actual first-
   occurrence order.
T4 WARM-START (the commercially decisive endpoint): initialize the
   certified compiler from the model's predicted (letters, theta);
   measure optimizer iterations + growth rounds saved to reach the same
   residual as a cold start. The compiler stays in the loop, so every
   output remains exactly certified: "model proposes, compiler
   certifies" is the product shape this test underwrites.

## 3. Corpus (Tier A minted this week in-container; no flagship-class
##    compilation, honoring the audit's no-new-big-compute constraint)

Tier A (dense, minutes per system, mint + compile in-container):
  - H4 chain + H4 ring, spacings 1.2-3.6 bohr step 0.1  (2 x 25)
  - H6 chain + H6 ring, same grid                        (2 x 25)
  Compiled sd_routed at dim 36 / 400; every dump archived (gauge law).
  ~100 systems, ~2-3 x 10^4 letters total.
Tier B (already banked): LiH scan (5), H2O series (3), N2 series (3),
  H8 chain (1), C2 family (6 incl. both states at 2.6/2.8/3.0 + eq).
Labels per system: dump, chain (letters + theta), support set, exact
  T amplitudes (cluster analysis), certificates, compile trajectory
  (residual-vs-iteration curve from the console log where retained).
NOTE: this corpus IS the pilot data product; the test doubles as the
  first sellable artifact (benchmark + starter corpus + verification
  harness).

## 4. Splits (frozen as JSON, committed before training)

  A INTERPOLATION  leave-one-geometry-out within each scan.
  B TRANSITION     train C2 singlet {2.348, 2.6, 2.8} -> test 3.0.
                   Pre-registered EXPECTED-HARD control: measured
                   support migration says content should degrade;
                   a model that "passes" B trivially signals leakage.
  C CROSS-SIZE     train ALL H4 + H6 (both topologies, all spacings)
                   -> test H8 chain, never seen. THE DECISIVE SPLIT:
                   no copy baseline exists across size, and size
                   transfer is the property the product needs.
  D CROSS-TOPOLOGY train chains -> test rings at matched spacing.
                   Measured-hard (content setJ ~0.24); modest bar;
                   pass is upside, not requirement.
  E CROSS-MOLECULE (stretch) train H-family + LiH + H2O + N2 ->
                   test C2 equilibrium singlet. Informative either way.

## 5. Baselines (the airtightness core; each gets the same compute cap)

  B0 chance / letter-frequency.
  B1 COPY: nearest-training-geometry chain copied verbatim (strong
     within scans because of set pinning; undefined for split C --
     which is why C is decisive).
  B2 PHYSICS: letters ranked by |MP2 amplitude| (and |H_ij| coupling);
     theta from arctan of the perturbative amplitude and from the
     secant dressing law; ordering by routing heuristic. The model
     must beat B2, not merely B0/B1, for "learnable beyond known
     physics" to be claimable.
  B3 NEGATIVE CONTROL: identical model trained on shuffled labels
     must land at B0. Detects leakage through features or splits.
  B4 ABLATION: model minus all physics features (integrals) must
     degrade materially; otherwise it is fitting indices, not physics.

## 6. Models (two families, so architecture cannot be the excuse)

  M1 permutation-equivariant set model over candidate letters, features
     from the dump (orbital energies, couplings, MP2 t, letter rank) ->
     content probability + theta regression heads.
  M2 small transformer over letter tokens (<= ~1M params) for T3.
  Compute cap: fixed and equal across models and baselines (CPU-days
  scale; specify exact cap at freeze). 5 seeds each; report mean and
  95% CI; frozen test sets touched exactly once per phase.

## 7. Decision rule (numbers frozen at sign-off; drafts below)

PASS (K1 retired) requires ALL of:
  P1 Split C: content F1 >= 0.60 AND >= B2 + 0.10; theta R^2 >= 0.5
     on true letters; warm-start saving >= 30% vs cold AND >= 1.3x B2.
  P2 Split A: beats B1 copy on multiset Jaccard (CI-separated).
  P3 Controls behave: B3 at chance; B4 degrades; Split B degrades on
     content as pre-registered.
WEAK PASS: P2+P3 and Split C content+theta pass but ordering (T3) at
  baseline -> product shape narrows to "unordered proposal + exact
  router"; still commercially viable; claim scoped accordingly.
FAIL (K1 fires): under the compute cap, neither model family beats B2
  beyond CI on ANY transfer split (C, D, E) on ANY of T1/T2/T4.
  Consequence per the strategy memo: the learned-compiler product is
  dead as specified; the pitch pivots to the certification/
  verification moat; corpora remain sellable as evaluation +
  verification data (Sec. 9).

## 8. Procedure and hygiene

  Day 1-2   Freeze this document (Logan sign-off on thresholds),
            commit hash = pre-registration; mint Tier A; freeze splits
            + metrics harness + baselines; commit.
  Day 3-7   Splits A + B; one evaluation each; bank.
  Day 8-12  Split C (then D); one evaluation each; bank.
  Day 13-14 Write-up; feed the verdict -- pass, weak pass, or fail,
            stated plainly -- into the DOE pitch (due Sep 10) and
            Activate (opens Sep 15).
  All training configs, seeds, splits, and results committed; any
  deviation from this protocol is recorded in the ledger by name.

## 9. What becomes sellable, by outcome

On PASS or WEAK PASS:
  D1 Certified chain corpora: ordered factor programs + theta +
     machine-precision certificates (supervised targets for
     science-foundation-model training).
  D2 Exact amplitude sets (T1..T8) with certificates -- the data class
     the MoLe line of work already consumes; external demand
     evidenced.
  D3 Process-supervision data: compile trajectories, cold-vs-warm
     traces, residual curves (reasoning-style / process-reward
     training data no other source produces).
  D4 Benchmark suites: frozen splits + verification harness (the
     evaluation product; typically the first thing a lab buys).
On FAIL: D2 and D4 survive unchanged; D1 survives as verification/
  provenance data rather than as a prediction target; D3 dies.

## 10. Known threats to validity, addressed

  - Small data: Tier A grid multiplies the corpus ~x4 this week at
    trivial cost; claims are scoped to the tested distribution shifts.
  - Gauge confounds: all inputs are pinned-gauge dumps (archived);
    degenerate-pair systems enter only via a fixed partner convention
    or are excluded from training (decide at freeze; default:
    exclude pair-mixtures from Tier B training, keep as challenge).
  - Ordering gauge: T3 is reported but the decision rule lets content
    + amplitudes + warm-start carry a WEAK PASS, because the campaign
    measured ordering churn that may be optimizer gauge.
  - Overfitting-to-benchmark: test sets are evaluated once; the
    protocol hash predates training; a clean-checkout replication on
    the second platform is required before any public claim.

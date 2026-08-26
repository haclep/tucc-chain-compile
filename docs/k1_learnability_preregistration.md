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

## 7. Decision rule (rev A: amendments L1-L4, Logan, 2026-08-25;
##    numbers frozen at sign-off; drafts below)

PASS (K1 retired) requires ALL of:
  P1 Split C: content F1 >= 0.60 AND >= B2 + 0.10; theta R^2 >= 0.5
     on true letters; warm-start saving >= 30% vs cold AND >= 1.3x B2.
  P2 (re-targeted, L2) Split A: the model BEATS B1 copy on THETA
     (CI-separated) AND MATCHES B1 on content multiset Jaccard within
     CI. Rationale: set pinning makes copy near-ceiling on content
     within a scan; the within-scan signal lives in the amplitudes.
     An undershoot beyond CI on content is a failed match.
  P3 Controls behave: B3 shuffled-label lands at chance; B4 feature
     ablation degrades materially.
  P4 REPLICATION LADDER (L4): a Split-C pass triggers exactly ONE
     confirmatory cross-size compile -- fixed here as the H8 RING
     (support 2306; overnight-scale) -- before any public or pitch
     claim. The first new large compilation is thereby EARNED by the
     result, not scheduled ahead of it. H10 chain is ruled out as
     confirmer on measured cost (dim 63,504; months on current code).
     Attribution rule, pre-stated: a ring FAIL after a chain pass is
     charged to the topology axis (consistent with Split D priors)
     and does not revoke the size-transfer claim; a ring PASS
     upgrades the claim to size + topology transfer.

TRIPWIRE, not a gate (L3): if Split B FAILS TO DEGRADE on content as
  pre-registered, leakage forensics run BEFORE any verdict is
  recorded: (i) rerun B3 on Split B, (ii) audit features for
  geometry-identifying leakage, (iii) verify split boundaries against
  the archived dumps. If forensics come back clean, the result stands
  and is reported as genuine extrapolation. Surprising results are
  audited, never penalized.

VERDICT BANDS (exactly one is recorded):
  PASS -- P1 through P4 met.
  WEAK PASS -- P2 + P3 met and Split C passes on content + theta +
    warm-start, but ordering (T3) sits at baseline: the product shape
    narrows to "unordered proposal + exact router"; commercially
    viable; every claim scoped accordingly. P4 still applies before
    any public claim.
  FAIL (K1 fires) -- under the compute cap, neither model family
    beats B2 beyond CI on ANY transfer split (C, D, E) on ANY of
    T1/T2/T4. Consequence per the strategy memo: the learned-compiler
    product is dead as specified; the pitch pivots to the
    certification/verification moat; corpora remain sellable as
    evaluation + verification data (Sec. 9).
  INCONCLUSIVE (L1) -- any outcome not matching the three bands
    above. Pre-committed consequence: reported as partial evidence;
    K1 stays OPEN; commercial claims restrict to D2 and D4; and a
    NAMED follow-up experiment -- specific test, specific threshold,
    specific date -- is registered at verdict time. INCONCLUSIVE is
    a real verdict with an expiry, not a parking lot.

## 8. Procedure and hygiene

  Day 1-2   Freeze this document (Logan sign-off on thresholds),
            commit hash = pre-registration; mint Tier A; freeze splits
            + metrics harness + baselines; commit.
  Day 3-7   Splits A + B; one evaluation each; bank.
  Day 8-12  Split C (then D); one evaluation each; bank.
  Day 13-14 Write-up; record exactly one verdict band -- PASS, WEAK
            PASS, FAIL, or INCONCLUSIVE -- and feed it, stated
            plainly, into the DOE pitch (due Sep 10) and Activate
            (opens Sep 15). If P4's confirmatory H8-ring compile is
            triggered, it is scheduled AFTER the Sep 10 pitch ships
            unless the Split-C pass lands early enough to run it
            first; the pitch may cite the chain-level pass with the
            confirmation explicitly marked pending.
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

## Amendment log

Rev B -- 2026-08-26. Confirmed by Logan ("confirm rev B"),
PRE-TRAINING: no model has contacted any data; splits v2 generated
the same date. Rev-A text above is left intact; these amendments
govern where they conflict.

B.1 P2 theta comparator. "beats B1 copy on THETA" is replaced by:
    the model must beat the STRONGEST of {B0 frequency, B1 copy,
    B2 physics} on theta, per fold, CI-separated. The content clause
    is unchanged (match B1 within CI; an undershoot beyond CI is a
    failed match). Reason, measured: on the h6_chain_19 smoke fold
    B0 reaches theta R^2 +0.71 while B1 sits at -0.03; the
    sign-calibrated B2 reaches +0.73/+0.74/+0.58 on its window. A
    gate must face the measured-strongest simple predictor, and the
    strongest one varies by fold.

B.2 B2 sign convention. B2's theta carries exactly ONE global sign,
    fitted on training folds only and recorded per split -- the
    convention is measured, never assumed (same discipline as the C4
    cross-check's conversion map). Measured motivation: uncalibrated
    B2 sign accuracy was 0.03 (anti-correlated); calibrated, 0.83.

B.3 Section-10 gauge note, sharpened. Degenerate-shell MO gauge is
    pinned by platform AND by the SCF iteration path INCLUDING the
    damping schedule (measured: same platform, different damping ->
    different chain at identical energies). Consequently the
    k1_corpus dump files are the sole canonical model inputs; per-
    system damping values are recorded in the mint log.

B.4 Splits v2 (recorded inside splits.json, "splits_revision"):
    Split-A families extended with lih (5), c2_singlet (4),
    h2o_fc_series (3), n2_series (3), for 8 families total. Census
    note logged with it: support COUNT-pinning and SET-pinning come
    apart (H2O-fc and N2 are count-only) -- set-pinning is
    molecule-selective, so the per-fold strongest-comparator rule of
    B.1 is load-bearing.

Rev C -- 2026-08-26. Pre-training: the platform pair passed the same
date; no model has contacted any data. Trigger: verifier v1 falsified
its own 1e-9 pointwise-theta tolerance -- an unmeasured assumption,
corrected by measurement.

C.1 THE THETA-REDUNDANCY MANIFOLD (measured). Compiled chains are
    overparameterized: length exceeds support-1 in every corpus
    system, so a manifold of angle vectors of dimension at least
    len-(support-1) reproduces the target state at the residual
    floor, and each platform's optimizer parks at a different point
    on it. Measured, Windows vs Linux, six probe systems: pointwise
    max|dtheta| spans 2.0e-10 to 7.4e-04, ordered with the
    redundancy dimension (4 -> 139), while every cross-replay
    deficit is <= 6.7e-16 -- the same state in different
    coordinates. This is gauge layer FOUR, alongside MO gauge
    (degenerate shells), degenerate-partner selection, and chain
    ordering.

C.2 Verifier criterion, v2 (recorded): a platform-pair pass is
    exact discrete identity -- letters, order, support, pivot,
    monomial count -- AND cross-replay deficit <= 1e-11 between the
    fresh and committed angle vectors applied through the identical
    letter sequence. Pointwise dtheta is a reported diagnostic,
    never a pass/fail quantity.

C.3 Theta REPORTING floors. The measured pointwise widths become
    per-family label-uncertainty floors: h4 families ~1e-9, lih
    ~4e-8, h6 chains ~2e-5, h6 rings up to ~7e-4. No theta metric
    (MAE or otherwise) may be quoted below its family's floor, and
    every theta table in the write-up carries the floor alongside.

C.4 Gates unchanged, with the reason stated: manifold widths
    (<= 1e-3) are negligible against the theta scale of the physics
    (0.1-1.5) and the pre-registered targets (R^2 >= 0.5,
    CI-separated comparisons). P1 and P2 therefore stand exactly as
    written in Rev B. This amendment changes what may be CLAIMED
    about precision, not what must be ACHIEVED to pass.

Rev D -- 2026-08-26. Confirmed by Logan ("confirm rev D"). Trigger:
first contact with Split A (M1-v0, evaluation #1) exposed a protocol
gap -- under leave-one-out folds every system is a held-out system,
so iterating the model against Split A would constitute test-set
reuse, and the frozen text defined no development loop.

D.1 DEV PROTOCOL. All model development -- features, architectures,
    hyperparameters -- is conducted on INNER cross-validation carved
    from training folds only. No development decision may condition
    on any held-out system's score. The dev construction is recorded
    in the dev runner's docstring and committed with it.

D.2 EVALUATION BUDGET. Split-A banked evaluations are capped at
    exactly TWO: v0 (2026-08-26, table in results/k1_splitA_v0.md,
    SPENT) and one FINAL M1. Both are published side by side in
    every report regardless of outcome. The same two-evaluation cap
    applies prospectively to Splits B, C, D, and E: an optional
    first look plus a mandatory final; if only one evaluation is
    ever taken, it is the final.

D.3 THE v0 RECORD: P2 NOT MET at v0. One CI-separated theta win
    (c2_singlet, dR2 +0.280 +- 0.077 -- the family where every
    baseline collapses), one CI-separated theta loss (h6_ring,
    -0.286 +- 0.068), one CI-separated content-match failure
    (h6_chain, dF1 -0.070 +- 0.015); all other families at
    statistical parity. The observed pattern -- the model loses at
    baseline ceilings and wins where baselines break -- is recorded
    as the standing hypothesis for Split C, where no copy baseline
    exists.

D.4 Small families (n = 3) remain in every table with their
    confidence intervals. Nothing is excluded post hoc; low
    statistical power self-reports through non-separation.

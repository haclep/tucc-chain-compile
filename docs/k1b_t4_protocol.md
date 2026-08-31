# K1b-T4 Warm-Start Measurement -- Protocol (FROZEN)
# tucc-chain-compile | frozen 2026-08-27 by Logan ("freeze k1b") | this
# commit is the pre-registration; no H8 arm has run before it

## 0. What is registered (docs/k1_verdict.md, consequence 3, verbatim intent)

K1b-T4: warm-start scoring of the FROZEN Split-C predictions
(k1_corpus/predictions_splitC_h8.pkl, committed 6e08456) against a cold
compile of h8_chain. Threshold, inherited from the frozen P1: >= 30 percent
optimizer-cost savings vs cold start AND >= 1.3x the savings of a B2-seeded
warm start. Date: harness built and the measurement banked by 2026-09-30.
This is also the first measurement of the plan-B architecture (NN proposes,
exact/variational machinery refines); its result feeds K1b design regardless
of sign.

This document fixes everything the registration left open: the target, the
arms, how a proposal enters the compiler, the cost currency, the stopping
rule, the plateau rule, the verdict arithmetic, and the launch gate. Rule
of the campaign: what is written here before the H8 arms run governs; any
deviation is recorded in Section 11 by name.

## 1. The object under test

The cost to CERTIFY the H8-chain ground state (dim 4900, support 2468) when
the sd_routed compiler is given a proposal for the letters it would
otherwise discover by growth. The compiler stays in the loop; every arm
ends at the same certification gate; only the cost differs. "Model
proposes, compiler certifies" is measured here as a cost ratio.

## 2. The target

The certified H8 vector stored in the finished campaign checkpoint
data/h8_chain_bigsd.pkl (ct, pivot 255, support_tol 1e-10, E0 =
-4.30604886305086, residual 8.0e-13, chain 6333 = 2467 routed + 3866
grown, 8 rounds). Every arm compiles this identical vector; no eigensolve
is run. A run whose routed+greedy prefix differs from the certified chain's
first 2467 letters is a target mismatch and is stopped (the oracle arms
assert this; on the Linux container the assertion held for n2_3111).

## 3. Arms

Registered (mandatory for the verdict):
  cold          no proposal -- the comparator.
  pred          predictions_splitC_h8.pkl, seed 0, letters AND theta as
                predicted. Facts fixed before any arm runs: 383 letters,
                300 distinct, 254 pivot-referenced; multiset precision
                0.78 against the certified GROWN letters, recall 0.077;
                the five seeds agree at multiset Jaccard >= 0.979, so one
                arm on seed 0 stands for the model; |theta_pred| median
                1.6e-3, max 0.16 (predicted angles are numerically near
                zero -- no separate theta=0 arm is needed).
  b2            the physics baseline exactly as scored in Split C:
                k1_harness.b2_physics (all pivot-referenced S/D letters
                in the MP2 window, 360 for H8, precision 0.51 against the
                grown letters), theta = b2_sign * arctan(t_MP2) with
                b2_sign = -1.0 read from the frozen predictions file.
  oracle_full   the certified chain itself: its 3866 grown letters with
                their certified angles, and the routed angles replaced by
                the certified ones. The known-answer ceiling (expected
                cost: one Jacobian).
Recommended (ceiling, no verdict weight):
  oracle_content  the certified chain's grown MULTISET at theta = 0 in a
                fixed-seed shuffled order (seed 1): what a perfect
                content-with-multiplicity proposal is worth with no
                angle and no order information.

## 4. How a proposal enters the compiler

1. Routing and greedy ordering run exactly as in the cold driver
   (deterministic, identical in every arm; solve_resumable stops after
   greedy via the stop_after_greedy knob).
2. The proposal is APPENDED after the greedy-ordered routed chain, before
   the first Gauss-Newton solve -- i.e. outermost in preparation, first
   applied to the eigenvector in compile direction, the position growth
   itself uses. Its angles start at the proposed values.
3. Ordering within a proposal ("rank"): round-robin over copies -- one copy
   of every distinct letter per pass, passes repeated until the multiset
   is exhausted, so identical letters are never adjacent; within a pass,
   descending weight (pred: predicted multiplicity, then |theta_pred|;
   b2: |t_MP2|), canonical (holes, parts) tie-break. oracle_full keeps the
   certified order; oracle_content is shuffled (seed 1).
4. From that point the cold rules run unchanged: joint Gauss-Newton
   (budget 300), growth rounds (saturated-letter duplicates + torque-
   scored letters, batch max(4, len//8)), Gauss-Newton per round (budget
   400), restarts, gate 1e-12 on 1 - fid^2, angles bounded to
   |theta| < pi/2 - 0.02 -- plus the plateau rule of Section 6, which
   applies identically to every arm.

## 5. Cost currency

GOVERNING: rotations -- the number of elementary 2x2 block rotations
executed by the optimizer, one per (letter block pair x vector column),
counted from the first Gauss-Newton solve to the certification gate. It is
deterministic and platform-independent, and it is the dominant cost term
(the Jacobian build: letter k propagates k columns). Routing + greedy work
is identical in every arm; it is recorded (rot_prep) and not charged.

Reported alongside, no verdict weight: Gauss-Newton iterations, growth
rounds, and the wall-clock of the optimizer phases (wall_opt, accumulated
across invocations). Iterations are NOT the currency because a proposal
lengthens the chain and makes every iteration dearer: on n2_3111 the b2
arm needed 42% fewer iterations but only 19% fewer rotations. Wall-clock
is quoted only for arms run one at a time on an otherwise idle machine.

## 6. Plateau rule (applies to every arm)

A Gauss-Newton phase (joint or grow_gn) ends when a completed slice lowers
|r| by less than 1 percent of its value at the slice start (plateau =
0.01; slices are the driver's own 10-iteration slices, probe slice 2).
The remaining iteration budget is forfeited and growth proceeds.

Why it is ON: the campaign record says each H8 round burned most of its
400 iterations at < 1 percent improvement. Measured before this freeze on
training-distribution systems (Linux container, commit 195dba5 + harness):
  - k1_h6_chain_19: cold 291 -> 129 GN iterations, same chain (250
    letters, 2 rounds), same certificate (2.2e-16).
  - n2_3111 (certified checkpoint target): cold finished in 262 GN
    iterations, 5 rounds, 1170 letters, residual 0.0, E(chain) - E0 =
    4.3e-14, versus the campaign's 6 rounds, 1323 letters and ~2,100+
    iterations at full budgets. Same state, one round shorter, roughly
    8x fewer iterations.
The rule makes the COLD arm cheaper, so it tightens the baseline the
proposals must beat; it does not relax the certificate. The campaign's H8
cold cost without the rule, reconstructed exactly from the checkpoint
(chain prefixes x budgeted iterations), is 1.21e13 rotations; it is
reported as context only and is not the comparator.

## 7. Stopping and certification

Every arm runs to the gate (1 - fid^2 < 1e-12) under the same rules; an
arm that finishes above the gate is an error, not a result. At the gate
the harness re-checks the deficit from the saved angles, prints
E(chain) - E0 from the dump's Hamiltonian, saves the chain
(k1b/<stem>_<arm>_chain.npz), and writes results/k1b_t4_<stem>_<arm>.md.
The constructive translation is not part of the cost and is not run for
the race (available as --translate).

## 8. Verdict

savings(arm) = 1 - rotations(arm) / rotations(cold).
PASS iff savings(pred) >= 0.30 AND savings(pred) >= 1.3 x savings(b2);
otherwise FAIL. Computed by `python k1b_warmstart.py h8_chain --score`,
written to results/k1b_t4_h8_chain.md, banked by 2026-09-30. Each arm is
run exactly once to completion; a re-run is permitted only for a defect
recorded in Section 11. The per-slice traces (k1b/*_trace.jsonl:
residual, rotations, iterations, wall per slice) are banked with the
result -- they are the cold-vs-warm compile traces of product class D3.

## 9. Forecasts, stated before any H8 arm runs (prediction audit)

  - pred: near +10 percent (band -10 to +25). 383 letters cannot complete
    the rank that 3866 grown letters complete; the arm buys at most one
    or two early rounds and pays a longer chain in every iteration.
  - b2: near +10 percent (band -10 to +25), same mechanism; on n2_3111 it
    measured +19 percent.
  - oracle_full: >= 99 percent (one Jacobian at length 6333, ~9.3e9
    rotations, against a cold of order 2-4e12).
  - oracle_content (shuffled, theta 0): >= 80 percent (n2_3111 measured
    +90 percent).
  - cold under the plateau rule: 8-10 rounds, 400-800 GN iterations,
    2-4e12 rotations, of order one day of wall on the campaign machine.
  - Therefore the registered threshold is expected to FAIL for the frozen
    predictions, while the oracle arms are expected to show that a
    content-with-multiplicity proposal is worth most of the compile. If
    that is what the measurement returns, the honest sentence is: plan-B
    is worth building; the current model captures little of it; the gap
    is multiplicity scale, already named in the K1 verdict.

## 10. Shakedown and launch gate

Before any H8 arm: run the four arms on n2_3111 on the campaign (Windows)
platform. Expected: the oracle_full assertion holds (routed prefix equals
the certified chain), every arm certifies, and the round/iteration counts
reproduce the Linux record below up to optimizer-fence jitter. Both
platforms' scoreboards are kept.

Linux container record (commit 195dba5 + harness), n2_3111, plateau 0.01:
  | arm            | proposal | len  | rounds | GN it | rotations  | savings |
  | cold           |    0     | 1170 |   5    |  262  | 2.7437e+10 |    0.0% |
  | b2             |  315     | 1221 |   2    |  152  | 2.2252e+10 |  +18.9% |
  | oracle_content |  672     | 1323 |   0    |   12  | 2.6620e+09 |  +90.3% |
  | oracle_full    |  672     | 1323 |   0    |    2  | 4.4095e+08 |  +98.4% |
k1_h6_chain_19 (dense target), plateau 0.01: cold 129 it / 1.2726e+08;
b2 +78.8%; oracle_content +73.4%; oracle_full +100%.

H8 launch order, arms one at a time: oracle_full first (it is the target
check and costs minutes past greedy), then cold, pred, b2, oracle_content.
Invocation: `python -u k1b_warmstart.py h8_chain --arm <arm> --deadline
14400`, repeated until DONE, under the unattended loop.

## 11. Process ledger (deviations and repairs, by name)

(empty at freeze)

2026-08-27 -- SHAKEDOWN PASSED on the campaign platform (Windows,
commit 6957f89); no rule changed. Discrete identity with the Linux
record of Section 10: cold 1170 letters / 5 rounds / 262 GN iterations,
b2 1221 / 2 / 152, oracle_content 1323 / 0 / 12, oracle_full 1323 / 0 /
2; the routed prefix equals the certified chain (oracle_full assertion
held on both platforms); joint-phase |r| trajectories identical to four
digits; every arm certified (cold and b2 residual 0.0, E(chain) - E0 <=
5.7e-14). Rotation counts, Windows vs Linux: cold 2.74343e10 vs
2.74367e10 (+0.009%), b2 2.22383e10 vs 2.22523e10 (+0.063%),
oracle_content 2.66169e9 vs 2.66201e9 (+0.012%), oracle_full 4.40636e8
vs 4.40950e8 (+0.071%) -- Linux higher by whole line-search trial passes
(the O(N) term; optimizer-fence jitter), the O(N^2) Jacobian work
identical. The governing currency is platform-reproducible three orders
of magnitude below the 30 percent threshold. Windows scoreboard banked as
results/k1b_t4_n2_3111.md with the four arm reports and the k1b/ traces
and summaries. H8 launch gate met; the H8 arms run in the Section 10
order.

2026-08-28 -- H8 TARGET CHECK PASSED; LOOP DEFECT, NO DATA AFFECTED.
oracle_full on h8_chain (commit 663a146): routed prefix equals the
certified chain, |r| routed 2.165e-02 -> seeded 8.970e-07 (the campaign
rn to the digit), 2 GN iterations, 1.8571e10 rotations (= 2 x the
reconstructed per-iteration work at length 6333, 9.281e9, plus the O(N)
passes), wall 486 s (243 s per iteration), residual 7.6e-13, E(chain) -
E0 = 4.2e-12. Banked. Defect: the unattended PowerShell loop failed to
recognise DONE -- Windows PowerShell 5.1's Tee-Object appends UTF-16
while the loop's separator lines were UTF-8, and the mixed-encoding log
defeated the '^DONE' regex -- so the finished arm was re-invoked 105
times before the 100-invocation cap. Each re-invocation resumed at
phase 'noc', ran no optimizer phase, re-saved the same state and
re-wrote the same report: rotation and iteration counts unchanged
(18,571,263,060 / 2 on every line), wall_opt unchanged to the second,
trace untouched. The arm report's provenance line therefore reads "106
invocations"; the arm finished in its first. The loop was replaced by
one that detects completion from the harness's own summary file
(k1b/<tag>_summary.json), which exists only when an arm has certified,
and skips finished arms on rerun. The harness itself is unchanged.

## 12. Files frozen with this protocol

  k1b_warmstart.py           the harness (arms, seeding, counter, reports,
                             scoreboard); harness version k1b-warmstart-1
  examples/run_big_sd.py     two default-off knobs on solve_resumable:
                             stop_after_greedy, plateau; the recursive
                             growth call now forwards save and plateau;
                             with defaults the mirror is unchanged
                             (tests/test_fastpath.py 4/4)
  tests/test_k1b_harness.py  miniature checks: defaults still mirror,
                             stop-after-greedy halts at joint, a known-
                             answer seed reaches the gate with no growth,
                             round-robin never adjacent

**2026-08-30 — Ordering-gauge provenance (recording only; no rule change).**
Chen, Cheng & Freericks, arXiv:2109.13461v1 (2021), states in print that the
factorized form is ordering-dependent because factors do not commute, and that
a chosen ordering imposes constraints on the amplitudes. The protocol's
treatment of ordering (§1, L3) as partially gauge-dependent is therefore
corroborated by the primary literature, not inferred from campaign data alone.
No threshold, baseline, or arm definition is affected.

**2026-08-30 — B2 provenance (recording only; no rule change).**
B2's perturbative selection-and-ordering scheme is the published strategy of
Chen, Cheng & Freericks, arXiv:2008.06637v2 (2020), adopted there on the stated
assumption that later factors are less relevant, with improved screening left
explicitly to future work. B2 is a literature baseline, not an internally
devised one. To be stated as such in the write-up. No rule change.
# K1c-T4 Self-Warm-Start Race on h8_chain -- Pre-Registration Protocol
# (DRAFT for sign-off; freeze by commit AFTER the K1b-T4 scoreboard closes,
#  BEFORE any H8 arm is launched)
# tucc-chain-compile | Seneca Labs | drafted 2026-09-11

## 0. What this race tests (read first)

Whether the compiler's own first-order gradient, read once after a short
joint solve, replaces growth on the certified H8 target at the cost
reduction it delivered on twelve H6 systems (K1c H6 sweep, 8-10 Sep:
56-98 percent in K1b's currency against the cheapest cold run per
system). It tests a compiler feature with no learned parameters. It does
not test learning, prediction, or transfer; every arm holds the exact
target, and the only thing that varies is how the search for the
factorization is started.

It cannot establish anything about unsolved molecules (goal B), and it
does not alter the K1b-T4 verdict, which stands as recorded.

## 1. Object under test

Cost, in rotations, of certifying h8_chain (checkpoint target
data/h8_chain_bigsd.pkl, sector (4,4), dim 4900, gate R < 1e-12) from a
POST-JOINT insertion of a proposal computed from the compiler's own state,
versus cold. Same frozen harness code (k1b_warmstart.py at 89e3c9c, tag
k1b-t4-harness) wrapped by k1c_warmstart.py, which changes only the
insertion point and the proposal source.

## 2. Arms (all post-joint, --target checkpoint, plateau 0.01)

  A0  cold_pj          no proposal. Prefix under the plateau rule. The
                       SECOND COLD SAMPLE: cold's exit-rule variance was
                       measured at 20-40 percent on H6 and the K1b race
                       has one sample; A0 bounds it at H8. Runs on its own
                       core; its result is not required for W1/W2.
  A1  topk_quarter     top-K distinct letters by tangent score at the
                       insertion state, one copy each, angle zero,
                       K = round(0.25 x pool)
  A2  topk_half        K = round(0.50 x pool)
  A3  topk_full        K = pool
  A4  tangent_law      tangent-proportional allocation at the H6 scale-law
                       size (value fixed at freeze, Sec. 7)
  A5  poolall_live     every pool letter once
  A6  topk_quarter_p10 as A1 with the prefix capped at 10 iterations
  A7  oracle_content_pj  the certified grown multiset of the campaign
                       chain at zero angle, post-joint (cheat; ceiling for
                       this insertion point). K1b's oracle_content (greedy
                       insertion) is the other ceiling.
Reference (banked): K1b cold 1.2256e13 (greedy insertion; K1b currency),
K1b oracle_full 1.857e10, K1b pred 9.9446e12, K1b b2 1.2951e13.

No seeds: every arm is deterministic given the environment (Sec. 8).

## 3. Insertion and prefix

Post-joint: routing, greedy ordering, then the joint Gauss-Newton phase on
the routed chain (300-iteration budget, plateau 0.01, tol 1e-13, angle
bound pi/2 - 0.02), exactly K1b's joint phase (on this target it exited at
92 iterations, |r| 3.529e-03, 1.227e11 rotations). The proposal is
appended at that state; the seeded chain receives a fresh 300-iteration
joint budget; growth follows the frozen rules if the gate is not reached.
A6 caps the prefix at 10 iterations (H6: sufficient for the pool, 10 Sep).

Pool: edges from the TOP = 24 largest-residual determinants at the
insertion state (fixed from N2 on 8 Sep before H8 was examined; H8
containment of the grown multiset at this width, 96.1 percent by mass,
recorded 8 Sep as a design input, not used to tune anything since).

## 4. Currency

Rotations (2x2, per column), K1b's definition: from the first
Gauss-Newton solve to the gate, i.e. charged cost PLUS the pre-insertion
joint solve (rot_prep_uncharged in the summary, less the negligible
routing/greedy count). Both columns reported. Iterations, rounds, final
length, and wall are context only.

Denominators: primary, K1b cold 1.2256e13; secondary, A0 when banked.
Savings are quoted against the primary, with A0's value alongside.

## 5. Decision rule (drafts; Logan sets the numbers at freeze)

  W1  The best of A1-A6 saves >= 90 percent against K1b cold in K1b's
      currency.
  W2  That arm reaches the gate with zero growth rounds.
PASS: W1 and W2. PARTIAL: W1 without W2 (the warm start works but does not
fully replace growth at this scale). FAIL: W1 fails. A3 or A5 being the
best arm is reported but does not change the rule.

## 6. Forecasts (on record before the run)

  F1  Best arm: 92-99 percent, central 97, in K1b's currency.
  F2  A2 (half pool, ~1000 letters) at or near the optimum; A3 (full pool,
      chain ~4500 letters) more expensive than A2; A1 within a few points
      of A2.
  F3  A6 within 10 percent of A1 in charged cost.
  F4  A0 within +-30 percent of 1.2256e13.
  F5  A7 (exact content, post-joint) beaten by the best top-K arm, as on
      11 of 12 H6 systems.
  F6  Zero growth rounds for A1, A2, A4, A6; the 4 percent of grown mass
      outside the pool is the risk to F6.

## 7. Fixed before the run

  - TOP = 24 (N2).
  - K for A1-A3 from the pool size measured at the insertion state at run
    time; never from the H8 label.
  - A4's size from the H6 scale law: value computed at freeze from the
    H8 pool cache's post-joint residual and pool size
    (python k1c_model.py --split C --write-proposals, no --score) and
    recorded here: ________ letters.
  - Prefix rule (Sec. 3). Plateau 0.01. Gate 1e-12.
  - Environment: .venv, Python 3.11.10, numpy 2.4.6, numba 0.67.0
    (requirements-campaign.txt). Harness tag k1b-t4-harness.
  - H8's exact state is used only to certify (the gate recheck) and by the
    compiler's own residual, as in every K1b arm. No arm is re-run after
    its summary exists. No parameter is changed after the freeze commit.

## 8. Procedure

  Freeze   Fill Sec. 7 blanks; commit this file; tag k1c-t4-protocol.
  Launch   One process per arm, each on its own core, from the single
           checkout, all at once except A0 which starts with them and
           finishes last:
             python k1c_warmstart.py h8_chain --arm pred --pred-source topk --scale-mult 0.25 --pred-tag topk_quarter --insert post-joint --target checkpoint --deadline 14400
             python k1c_warmstart.py h8_chain --arm pred --pred-source topk --scale-mult 0.5  --pred-tag topk_half    --insert post-joint --target checkpoint --deadline 14400
             python k1c_warmstart.py h8_chain --arm pred --pred-source topk --scale-mult 1.0  --pred-tag topk_full    --insert post-joint --target checkpoint --deadline 14400
             python k1c_warmstart.py h8_chain --arm pred --pred-source tangent --scale <A4> --pred-tag tangent_law   --insert post-joint --target checkpoint --deadline 14400
             python k1c_warmstart.py h8_chain --arm pred --pred-source poolall --pred-tag poolall_live               --insert post-joint --target checkpoint --deadline 14400
             python k1c_warmstart.py h8_chain --arm pred --pred-source topk --scale-mult 0.25 --pred-tag topk_quarter --prejoint-iters 10 --insert post-joint --target checkpoint --deadline 14400
             python k1c_warmstart.py h8_chain --arm oracle_content --insert post-joint --target checkpoint --deadline 14400
             python k1c_warmstart.py h8_chain --arm cold           --insert post-joint --target checkpoint --deadline 14400
           Each command is re-run to resume after its deadline exactly as
           the K1b loop does (state saved at every checkpoint). Log-only
           output; QuickEdit off; Windows updates paused.
  Cost     Warm arms: the prefix (~1.2e11) plus a joint solve at 3000-4500
           letters, expected 1e11-1e12 each, hours. A0: days.
  Bank     Per arm: summary, trace, report, chain; three-file commit as
           for K1b arms; ledger entry with forecasts audited by name.
  Score    python k1c_race.py --table-only (K1b currency column) once
           A1-A7 are in; verdict recorded; A0 appended when banked.

## 9. Threats to validity, addressed

  - Pool containment 96 percent: a growth round may be needed (F6, W2).
  - Scale flatness at 12x the training support: A1-A3 span a factor of
    four in K; the H6 optimum was broad.
  - Cold variance: A0 is the second sample; K1b cold remains the primary
    denominator for comparability with the K1b record.
  - Environment: invocations run under the rebuilt .venv; recorded.
  - Symmetry ties: h8_chain has inversion symmetry; ties affect growth,
    which the warm arms are forecast not to enter.
  - Proposal construction is not counted as rotations (pool enumeration
    and scoring, O(pool x dim)); its size is recorded in provenance.

## 10. What the outcome changes

PASS: the self-warm-start becomes the compiler's default for corpus
generation; the gauge factory is scheduled at the measured cost; the
learned-compiler by-product's target is a set of about K letters.
PARTIAL: default with growth retained as fallback.
FAIL: the pool-and-gradient approach does not scale past H6; growth stays;
the factory runs at cold cost on large systems; recorded by name.


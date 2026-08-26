# K1 Split A -- banked evaluation #1 (M1-v0) -- 2026-08-26

Pre-registration b01d01d; apparatus freeze + platform pair through
00735af (phase-0 freeze is its parent commit). Model: M1-v0, shared
per-letter gradient-boosted scorer (k1_model_m1.py at this commit),
two heads (multiplicity, theta), 5 seeds, features = system context
(spacing, sqrt dim, support size, MP2 score stats) + per-letter
physics (rank, spin pattern, MP2 score, MP2 theta seed, index
geometry). Candidate universe per fold = train letters union B2
window. B2 sign train-fitted per fold (rev B.2). Scoring: k1_harness
conventions; theta floors per rev C.3 apply to all reporting.

Delta-theta-R2 is model minus STRONGEST of {B0, B1, B2} per fold;
Delta-F1 is model minus B1 copy. CI = 1.96 * sd / sqrt(n_folds) over
fold means (5 seeds averaged within fold).

  family        folds  model_thR2 best_base  dR2            F1/B1F1        dF1
  h4_chain        25    +0.959     +0.989   -0.030+-0.005   0.989/0.990   -0.001+-0.006
  h4_ring         25    +0.430     +0.450   -0.020+-0.177   0.716/0.710   +0.005+-0.113
  h6_chain        25    +0.664     +0.683   -0.019+-0.038   0.773/0.844   -0.070+-0.015
  h6_ring         25    +0.167     +0.452   -0.286+-0.068   0.580/0.615   -0.034+-0.021
  lih              5    +0.711     +0.680   +0.031+-0.096   0.643/0.710   -0.067+-0.066
  h2o_fc_series    3    -0.649     +0.487   -1.14 +-1.80    0.498/0.422   +0.076+-0.063
  n2_series        3    -1.030     -1.382   +0.35 +-1.54    0.487/0.430   +0.057+-0.210
  c2_singlet       4    +0.124     -0.157   +0.280+-0.077   0.531/0.528   +0.003+-0.229

VERDICT AT v0: P2 not met. CI-separated theta win on c2_singlet
only; CI-separated theta loss on h6_ring; CI-separated content-match
failure on h6_chain; parity elsewhere. Standing hypothesis for Split
C (recorded, rev D.3): the model wins where baselines break.

This evaluation is SPENT (rev D.2). One final Split-A evaluation
remains; all further development runs on the inner-CV dev protocol
(rev D.1) and never touches held-out systems.

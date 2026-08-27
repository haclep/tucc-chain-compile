# K1 Split A -- banked evaluation #2 (M1-v1, FINAL) -- 2026-08-27

Pre-registration chain: d08eaf7 -> b01d01d -> ea06927 -> 00735af ->
2d61ab9 -> afc386a. Model: v1 = C1C2K (frozen on inner folds, rev
E.3): split-head gradient-boosted per-letter scorer -- content head
sees physics + neighborhood statistics (pool frequency, pool-mean
theta, two nearest-spacing neighbors), theta head sees physics only.
Five seeds, outer LOGO folds, every held-out system evaluated once.
Adjudication per rev E.2 (aggregate over all folds, fixed before this
evaluation existed). Theta reporting floors per rev C.3 apply.

## Per-family table (v1 final; v0 in parentheses where it moved)

  family        n   thR2 model/best   dR2              F1 model/B1     dF1
  h4_chain      25   +0.956/+0.989   -0.034+-0.016     0.987/0.990    -0.002+-0.011
  h4_ring       25   +0.350/+0.450   -0.100+-0.220     0.743/0.710    +0.033+-0.084
  h6_chain      25   +0.665/+0.683   -0.017+-0.036     0.863/0.844    +0.019+-0.013 (v0 -0.070)
  h6_ring       25   +0.175/+0.452   -0.277+-0.065     0.673/0.615    +0.058+-0.019 (v0 -0.034)
  lih            5   +0.751/+0.680   +0.071+-0.097     0.693/0.710    -0.017+-0.044
  h2o_fc_series  3   -0.531/+0.487   -1.02 +-1.47      0.515/0.422    +0.093+-0.024
  n2_series      3   -1.034/-1.382   +0.35 +-1.60      0.438/0.430    +0.008+-0.193
  c2_singlet     4   +0.116/-0.157   +0.273+-0.091     0.598/0.528    +0.070+-0.251

## E.2 aggregate (115 folds)

  Delta-theta-R2 = -0.098 +- 0.078   CI-SEPARATED BELOW the strongest
                                     baseline -> P2 theta clause FAILS
  Delta-F1       = +0.028 +- 0.021   CI-SEPARATED ABOVE B1 copy
                                     -> P2 content clause PASSES,
                                        exceeding

## Verdict contribution

P2 NOT MET at the final Split-A evaluation: content exceeds copy in
aggregate; theta sits below the strongest baseline in aggregate,
with the deficit concentrated in the ring family (-0.277+-0.065,
the known open item of rev E.3) and at the h4_chain ceiling
(baselines at 0.989 leave no winnable headroom). The model's theta
wins are exactly where baselines break: c2_singlet +0.273+-0.091
(CI-separated), n2 positive at low power, lih positive.

Consequences under the frozen bands: PASS and WEAK PASS are blocked
from Split A alone (both require P2). FAIL cannot fire (it requires
the model to beat B2 nowhere on ANY transfer split; Splits C, D, E
are untouched). The K1 verdict therefore rests on the transfer
splits, with the rev E.1 size-slope endpoint and the rev D.3
standing hypothesis -- the model wins where baselines break --
awaiting their H8 point.

## Dev-protocol faithfulness (rev D.1 audit)

Inner-fold predictions matched outer outcomes: the content gains
promised by inner folds (h6_chain 0.772 -> 0.862 inner) appeared on
outer folds (0.773 -> 0.863); the ring-theta resistance promised
inner appeared outer. Two banked evaluations, both published, per
rev D.2; this evaluation is SPENT and Split A is closed.

## Next (declared)

Split C is evaluated ONCE, as its final: v1, five seeds, train = all
115 clean systems, test = h8_chain. No development intervenes
between this record and that evaluation, so the optional first look
is waived and the single evaluation is the final, per rev D.2's "if
only one evaluation is ever taken, it is the final."

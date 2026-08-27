# K1b-T4 warm-start arm -- n2_3111 / cold

Source: target checkpoint n2_3111_bigsd.pkl; dump n2_3111.npz; sector (5,5) dim 3136; harness k1b-warmstart-1 at commit 6957f89.
Provenance: invocation k1b_warmstart.py n2_3111 --arm cold --order rank --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 0 letters appended after the 651 routed (greedy-ordered) letters; |r| routed 1.003e-01 -> seeded 1.003e-01. Seed provenance: {"arm": "cold", "order": "rank"}.

Cost (from the first Gauss-Newton solve to the gate): 27434268359 rotations (2x2, per column), 262 GN iterations, 5 growth rounds, 0 restarts, wall 670 s.

Certificate: final chain 1170 letters (grown 519), ranks {'2': 1100, '1': 70}, max|theta| 0.629430, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = 5.68e-14.

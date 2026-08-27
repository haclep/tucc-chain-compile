# K1b-T4 warm-start arm -- n2_3111 / oracle_content

Source: target checkpoint n2_3111_bigsd.pkl; dump n2_3111.npz; sector (5,5) dim 3136; harness k1b-warmstart-1 at commit 6957f89.
Provenance: invocation k1b_warmstart.py n2_3111 --arm oracle_content --order shuffle --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 672 letters appended after the 651 routed (greedy-ordered) letters; |r| routed 1.003e-01 -> seeded 1.003e-01. Seed provenance: {"arm": "oracle_content", "order": "shuffle", "source": "certified chain grown multiset, theta 0", "n": 672}.

Cost (from the first Gauss-Newton solve to the gate): 2661692136 rotations (2x2, per column), 12 GN iterations, 0 growth rounds, 0 restarts, wall 76 s.

Certificate: final chain 1323 letters (grown 0), ranks {'2': 1270, '1': 53}, max|theta| 0.370896, residual (1-fid^2) 1.8e-15 (recheck 1.8e-15), E(chain) - E0 = 1.42e-13.

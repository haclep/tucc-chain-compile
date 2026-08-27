# K1b-T4 warm-start arm -- n2_3111 / oracle_full

Source: target checkpoint n2_3111_bigsd.pkl; dump n2_3111.npz; sector (5,5) dim 3136; harness k1b-warmstart-1 at commit 6957f89.
Provenance: invocation k1b_warmstart.py n2_3111 --arm oracle_full --order rank --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 672 letters appended after the 651 routed (greedy-ordered) letters; |r| routed 1.003e-01 -> seeded 8.968e-07. Seed provenance: {"arm": "oracle_full", "order": "rank", "source": "certified chain (label)", "n": 672, "routed_theta": "certified"}.

Cost (from the first Gauss-Newton solve to the gate): 440635520 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 12 s.

Certificate: final chain 1323 letters (grown 0), ranks {'2': 1270, '1': 53}, max|theta| 1.549255, residual (1-fid^2) 8.0e-13 (recheck 8.0e-13), E(chain) - E0 = 1.98e-12.

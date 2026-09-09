# K1b-T4 warm-start arm -- k1_h6_ring_22 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_22 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 531 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 8.321e-03 -> seeded 8.321e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_ring_22_poolall.pkl", "pred_seed": 0, "config": "K1c-poolall", "insert": "post-joint", "n": 531, "n_distinct": 531}.

Cost (from the first Gauss-Newton solve to the gate): 49604192 rotations (2x2, per column), 5 GN iterations, 0 growth rounds, 0 restarts, wall 39 s.

Certificate: final chain 690 letters (grown 0), ranks {'2': 652, '1': 38}, max|theta| 0.576719, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -3.55e-15.

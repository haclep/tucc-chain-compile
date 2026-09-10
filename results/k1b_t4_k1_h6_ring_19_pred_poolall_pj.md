# K1b-T4 warm-start arm -- k1_h6_ring_19 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_19.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_19 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 515 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 2.383e-03 -> seeded 2.383e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_ring_19_poolall.pkl", "pred_seed": 0, "config": "K1c-poolall", "insert": "post-joint", "n": 515, "n_distinct": 515}.

Cost (from the first Gauss-Newton solve to the gate): 47494336 rotations (2x2, per column), 5 GN iterations, 0 growth rounds, 0 restarts, wall 9 s.

Certificate: final chain 674 letters (grown 0), ranks {'2': 636, '1': 38}, max|theta| 0.388176, residual (1-fid^2) 8.9e-16 (recheck 8.9e-16), E(chain) - E0 = 1.78e-15.

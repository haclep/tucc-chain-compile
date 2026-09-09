# K1b-T4 warm-start arm -- k1_h6_ring_14 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_14 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 188 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 3.029e-03 -> seeded 3.029e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_ring_14_model_s0.pkl", "pred_seed": 0, "config": "K1c-model_s0", "insert": "post-joint", "n": 188, "n_distinct": 15}.

Cost (from the first Gauss-Newton solve to the gate): 225382304 rotations (2x2, per column), 98 GN iterations, 0 growth rounds, 0 restarts, wall 429 s.

Certificate: final chain 347 letters (grown 0), ranks {'2': 339, '1': 8}, max|theta| 0.304424, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -1.78e-14.

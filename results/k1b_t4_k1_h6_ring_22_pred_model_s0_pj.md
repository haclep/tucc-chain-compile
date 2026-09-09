# K1b-T4 warm-start arm -- k1_h6_ring_22 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_22 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 195 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 8.321e-03 -> seeded 8.321e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_ring_22_model_s0.pkl", "pred_seed": 0, "config": "K1c-model_s0", "insert": "post-joint", "n": 195, "n_distinct": 10}.

Cost (from the first Gauss-Newton solve to the gate): 146713184 rotations (2x2, per column), 62 GN iterations, 0 growth rounds, 0 restarts, wall 212 s.

Certificate: final chain 354 letters (grown 0), ranks {'2': 346, '1': 8}, max|theta| 0.569614, residual (1-fid^2) 4.4e-16 (recheck 4.4e-16), E(chain) - E0 = 8.88e-15.

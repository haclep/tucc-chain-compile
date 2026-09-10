# K1b-T4 warm-start arm -- k1_h6_ring_30 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_30.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_30 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 175 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 1.810e-02 -> seeded 1.810e-02. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_ring_30_model_s0.pkl", "pred_seed": 0, "config": "K1c-model_s0", "insert": "post-joint", "n": 175, "n_distinct": 10}.

Cost (from the first Gauss-Newton solve to the gate): 46823800 rotations (2x2, per column), 22 GN iterations, 0 growth rounds, 0 restarts, wall 30 s.

Certificate: final chain 334 letters (grown 0), ranks {'2': 326, '1': 8}, max|theta| 0.968560, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = 9.77e-15.

# K1b-T4 warm-start arm -- k1_h6_ring_26 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_26.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_26 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 154 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 1.034e-02 -> seeded 1.034e-02. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_ring_26_model_s0.pkl", "pred_seed": 0, "config": "K1c-model_s0", "insert": "post-joint", "n": 154, "n_distinct": 8}.

Cost (from the first Gauss-Newton solve to the gate): 168989204 rotations (2x2, per column), 90 GN iterations, 0 growth rounds, 0 restarts, wall 208 s.

Certificate: final chain 313 letters (grown 0), ranks {'2': 305, '1': 8}, max|theta| 0.705832, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = 2.66e-15.

# K1b-T4 warm-start arm -- k1_h6_ring_30 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_30.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_30 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 142 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 1.811e-02 -> seeded 1.811e-02. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 142, "n_distinct": 142, "theta": "zero", "pool": 569, "top": 24, "scale_target": 142, "prejoint_iters": 20, "rn_at_insertion": 0.018112569334575702}.

Cost (from the first Gauss-Newton solve to the gate): 9259404 rotations (2x2, per column), 5 GN iterations, 0 growth rounds, 0 restarts, wall 2 s.

Certificate: final chain 301 letters (grown 0), ranks {'2': 289, '1': 12}, max|theta| 1.046886, residual (1-fid^2) 6.7e-16 (recheck 4.4e-16), E(chain) - E0 = 1.33e-14.

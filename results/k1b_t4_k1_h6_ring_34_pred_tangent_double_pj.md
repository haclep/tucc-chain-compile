# K1b-T4 warm-start arm -- k1_h6_ring_34 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_34.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_34 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 1138 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 2.859e-02 -> seeded 2.859e-02. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 1138, "n_distinct": 261, "theta": "zero", "pool": 569, "top": 24, "scale_target": 1138, "rn_at_insertion": 0.02859194685909598}.

Cost (from the first Gauss-Newton solve to the gate): 132311856 rotations (2x2, per column), 4 GN iterations, 0 growth rounds, 0 restarts, wall 8 s.

Certificate: final chain 1297 letters (grown 0), ranks {'2': 1251, '1': 46}, max|theta| 0.803576, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -1.33e-14.

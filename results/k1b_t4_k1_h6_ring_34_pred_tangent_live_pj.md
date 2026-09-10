# K1b-T4 warm-start arm -- k1_h6_ring_34 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_34.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_34 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 569 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 2.859e-02 -> seeded 2.859e-02. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 569, "n_distinct": 232, "theta": "zero", "pool": 569, "top": 24, "scale_target": 569, "rn_at_insertion": 0.02859194685909598}.

Cost (from the first Gauss-Newton solve to the gate): 42025372 rotations (2x2, per column), 4 GN iterations, 0 growth rounds, 0 restarts, wall 4 s.

Certificate: final chain 728 letters (grown 0), ranks {'2': 701, '1': 27}, max|theta| 0.803484, residual (1-fid^2) 1.3e-15 (recheck 1.3e-15), E(chain) - E0 = 3.55e-15.

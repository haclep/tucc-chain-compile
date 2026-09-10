# K1b-T4 warm-start arm -- k1_h6_ring_30 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_30.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_30 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 142 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 1.810e-02 -> seeded 1.810e-02. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 142, "n_distinct": 119, "theta": "zero", "pool": 569, "top": 24, "scale_target": 142, "rn_at_insertion": 0.018095198704593665}.

Cost (from the first Gauss-Newton solve to the gate): 9147496 rotations (2x2, per column), 5 GN iterations, 0 growth rounds, 0 restarts, wall 2 s.

Certificate: final chain 301 letters (grown 0), ranks {'2': 290, '1': 11}, max|theta| 1.049486, residual (1-fid^2) 4.4e-16 (recheck 4.4e-16), E(chain) - E0 = 1.51e-14.

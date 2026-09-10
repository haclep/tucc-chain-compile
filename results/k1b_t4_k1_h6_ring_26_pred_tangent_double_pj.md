# K1b-T4 warm-start arm -- k1_h6_ring_26 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_26.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_26 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 1136 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 1.034e-02 -> seeded 1.034e-02. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 1136, "n_distinct": 251, "theta": "zero", "pool": 568, "top": 24, "scale_target": 1136, "rn_at_insertion": 0.010336677994129776}.

Cost (from the first Gauss-Newton solve to the gate): 161796956 rotations (2x2, per column), 5 GN iterations, 0 growth rounds, 0 restarts, wall 11 s.

Certificate: final chain 1295 letters (grown 0), ranks {'2': 1254, '1': 41}, max|theta| 0.389547, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -1.07e-14.

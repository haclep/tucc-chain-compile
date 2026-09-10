# K1b-T4 warm-start arm -- k1_h6_ring_22 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_22 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 282 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 8.321e-03 -> seeded 8.321e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 282, "n_distinct": 157, "theta": "zero", "pool": 564, "top": 24, "scale_target": 282, "rn_at_insertion": 0.008321006007398157}.

Cost (from the first Gauss-Newton solve to the gate): 19540440 rotations (2x2, per column), 5 GN iterations, 0 growth rounds, 0 restarts, wall 5 s.

Certificate: final chain 441 letters (grown 0), ranks {'2': 422, '1': 19}, max|theta| 0.573698, residual (1-fid^2) 3.1e-15 (recheck 3.1e-15), E(chain) - E0 = 3.20e-14.

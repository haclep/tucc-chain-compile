# K1b-T4 warm-start arm -- k1_h6_ring_22 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_22 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 1128 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 8.321e-03 -> seeded 8.321e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 1128, "n_distinct": 252, "theta": "zero", "pool": 564, "top": 24, "scale_target": 1128, "rn_at_insertion": 0.008321006007398157}.

Cost (from the first Gauss-Newton solve to the gate): 162070792 rotations (2x2, per column), 5 GN iterations, 0 growth rounds, 0 restarts, wall 10 s.

Certificate: final chain 1287 letters (grown 0), ranks {'2': 1238, '1': 49}, max|theta| 0.587178, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -1.60e-14.

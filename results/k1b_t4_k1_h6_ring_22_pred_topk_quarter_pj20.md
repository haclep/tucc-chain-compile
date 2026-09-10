# K1b-T4 warm-start arm -- k1_h6_ring_22 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit dfcb1b1.
Provenance: invocation k1b_warmstart.py k1_h6_ring_22 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 141 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 8.418e-03 -> seeded 8.418e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 141, "n_distinct": 141, "theta": "zero", "pool": 564, "top": 24, "scale_target": 141, "prejoint_iters": 20, "rn_at_insertion": 0.008417975582031214}.

Cost (from the first Gauss-Newton solve to the gate): 19324232 rotations (2x2, per column), 10 GN iterations, 0 growth rounds, 0 restarts, wall 5 s.

Certificate: final chain 300 letters (grown 0), ranks {'2': 283, '1': 17}, max|theta| 0.511179, residual (1-fid^2) 1.8e-15 (recheck 1.8e-15), E(chain) - E0 = 2.31e-14.

# K1b-T4 warm-start arm -- k1_h6_ring_26 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_26.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit dfcb1b1.
Provenance: invocation k1b_warmstart.py k1_h6_ring_26 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 142 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 1.102e-02 -> seeded 1.102e-02. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 142, "n_distinct": 142, "theta": "zero", "pool": 570, "top": 24, "scale_target": 142, "prejoint_iters": 20, "rn_at_insertion": 0.011016489204031536}.

Cost (from the first Gauss-Newton solve to the gate): 9590620 rotations (2x2, per column), 5 GN iterations, 0 growth rounds, 0 restarts, wall 1 s.

Certificate: final chain 301 letters (grown 0), ranks {'2': 285, '1': 16}, max|theta| 0.499755, residual (1-fid^2) 8.9e-16 (recheck 8.9e-16), E(chain) - E0 = 1.60e-14.

# K1b-T4 warm-start arm -- k1_h6_ring_30 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_30.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_30 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 284 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 1.810e-02 -> seeded 1.810e-02. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 284, "n_distinct": 284, "theta": "zero", "pool": 569, "top": 24, "scale_target": 284, "prejoint_iters": 300, "rn_at_insertion": 0.018095198704593665}.

Cost (from the first Gauss-Newton solve to the gate): 16076184 rotations (2x2, per column), 4 GN iterations, 0 growth rounds, 0 restarts, wall 2 s.

Certificate: final chain 443 letters (grown 0), ranks {'2': 423, '1': 20}, max|theta| 1.054731, residual (1-fid^2) 1.8e-15 (recheck 1.8e-15), E(chain) - E0 = 2.22e-14.

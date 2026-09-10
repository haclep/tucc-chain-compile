# K1b-T4 warm-start arm -- k1_h6_ring_14 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_14 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 142 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 5.103e-03 -> seeded 5.103e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 142, "n_distinct": 142, "theta": "zero", "pool": 568, "top": 24, "scale_target": 142, "prejoint_iters": 10, "rn_at_insertion": 0.005102826544364792}.

Cost (from the first Gauss-Newton solve to the gate): 13315760 rotations (2x2, per column), 7 GN iterations, 0 growth rounds, 0 restarts, wall 2 s.

Certificate: final chain 301 letters (grown 0), ranks {'2': 285, '1': 16}, max|theta| 0.162998, residual (1-fid^2) 2.2e-16 (recheck 8.9e-16), E(chain) - E0 = 3.55e-15.

# K1b-T4 warm-start arm -- k1_h6_ring_14 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_14 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 284 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 3.029e-03 -> seeded 3.029e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 284, "n_distinct": 284, "theta": "zero", "pool": 568, "top": 24, "scale_target": 284, "prejoint_iters": 300, "rn_at_insertion": 0.0030288395647985185}.

Cost (from the first Gauss-Newton solve to the gate): 23793216 rotations (2x2, per column), 6 GN iterations, 0 growth rounds, 0 restarts, wall 6 s.

Certificate: final chain 443 letters (grown 0), ranks {'2': 425, '1': 18}, max|theta| 0.355251, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -1.95e-14.

# K1b-T4 warm-start arm -- k1_h6_chain_26 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_26.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit dfcb1b1.
Provenance: invocation k1b_warmstart.py k1_h6_chain_26 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 142 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 4.780e-04 -> seeded 4.780e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 142, "n_distinct": 142, "theta": "zero", "pool": 570, "top": 24, "scale_target": 142, "prejoint_iters": 40, "rn_at_insertion": 0.00047800551763347226}.

Cost (from the first Gauss-Newton solve to the gate): 5135112 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 1 s.

Certificate: final chain 341 letters (grown 0), ranks {'2': 316, '1': 25}, max|theta| 0.528635, residual (1-fid^2) 2.0e-15 (recheck 2.0e-15), E(chain) - E0 = 1.78e-14.

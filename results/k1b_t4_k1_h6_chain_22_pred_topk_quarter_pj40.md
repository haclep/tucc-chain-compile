# K1b-T4 warm-start arm -- k1_h6_chain_22 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit dfcb1b1.
Provenance: invocation k1b_warmstart.py k1_h6_chain_22 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 142 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 6.971e-04 -> seeded 6.971e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 142, "n_distinct": 142, "theta": "zero", "pool": 568, "top": 24, "scale_target": 142, "prejoint_iters": 40, "rn_at_insertion": 0.0006971102191145888}.

Cost (from the first Gauss-Newton solve to the gate): 5188080 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 1 s.

Certificate: final chain 341 letters (grown 0), ranks {'2': 314, '1': 27}, max|theta| 0.420444, residual (1-fid^2) 1.4e-14 (recheck 1.4e-14), E(chain) - E0 = 2.84e-14.

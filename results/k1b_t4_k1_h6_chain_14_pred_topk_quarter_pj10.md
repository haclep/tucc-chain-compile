# K1b-T4 warm-start arm -- k1_h6_chain_14 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit dfcb1b1.
Provenance: invocation k1b_warmstart.py k1_h6_chain_14 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 142 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 1.026e-03 -> seeded 1.026e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 142, "n_distinct": 142, "theta": "zero", "pool": 570, "top": 24, "scale_target": 142, "prejoint_iters": 10, "rn_at_insertion": 0.0010259392630804233}.

Cost (from the first Gauss-Newton solve to the gate): 14649000 rotations (2x2, per column), 6 GN iterations, 0 growth rounds, 0 restarts, wall 2 s.

Certificate: final chain 341 letters (grown 0), ranks {'2': 319, '1': 22}, max|theta| 0.160392, residual (1-fid^2) 4.4e-16 (recheck 4.4e-16), E(chain) - E0 = 1.24e-14.

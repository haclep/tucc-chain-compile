# K1b-T4 warm-start arm -- k1_h6_chain_22 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit dfcb1b1.
Provenance: invocation k1b_warmstart.py k1_h6_chain_22 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 142 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 2.016e-03 -> seeded 2.016e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 142, "n_distinct": 142, "theta": "zero", "pool": 567, "top": 24, "scale_target": 142, "prejoint_iters": 20, "rn_at_insertion": 0.0020158909982328312}.

Cost (from the first Gauss-Newton solve to the gate): 9735440 rotations (2x2, per column), 4 GN iterations, 0 growth rounds, 0 restarts, wall 2 s.

Certificate: final chain 341 letters (grown 0), ranks {'2': 320, '1': 21}, max|theta| 0.344813, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = 7.99e-15.

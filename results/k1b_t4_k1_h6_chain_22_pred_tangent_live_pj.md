# K1b-T4 warm-start arm -- k1_h6_chain_22 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_22 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 570 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 3.446e-04 -> seeded 3.446e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 570, "n_distinct": 239, "theta": "zero", "pool": 570, "top": 24, "scale_target": 570, "rn_at_insertion": 0.000344607460390847}.

Cost (from the first Gauss-Newton solve to the gate): 22797704 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 3 s.

Certificate: final chain 769 letters (grown 0), ranks {'2': 744, '1': 25}, max|theta| 0.428254, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -7.99e-15.

# K1b-T4 warm-start arm -- k1_h6_chain_19 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_19.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_19 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 142 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 1.062e-03 -> seeded 1.062e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 142, "n_distinct": 119, "theta": "zero", "pool": 567, "top": 24, "scale_target": 142, "prejoint_iters": 40, "rn_at_insertion": 0.0010620111523001287}.

Cost (from the first Gauss-Newton solve to the gate): 10379464 rotations (2x2, per column), 4 GN iterations, 0 growth rounds, 0 restarts, wall 2 s.

Certificate: final chain 341 letters (grown 0), ranks {'2': 312, '1': 29}, max|theta| 0.325049, residual (1-fid^2) 4.4e-16 (recheck 4.4e-16), E(chain) - E0 = 5.33e-15.

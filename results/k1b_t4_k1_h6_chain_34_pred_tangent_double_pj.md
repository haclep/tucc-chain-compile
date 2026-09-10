# K1b-T4 warm-start arm -- k1_h6_chain_34 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_34.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_34 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 1134 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 1.110e-04 -> seeded 1.110e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 1134, "n_distinct": 268, "theta": "zero", "pool": 567, "top": 24, "scale_target": 1134, "rn_at_insertion": 0.00011104870258608999}.

Cost (from the first Gauss-Newton solve to the gate): 69425416 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 5 s.

Certificate: final chain 1333 letters (grown 0), ranks {'2': 1287, '1': 46}, max|theta| 0.782234, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = 9.77e-15.

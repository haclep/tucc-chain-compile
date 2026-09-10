# K1b-T4 warm-start arm -- k1_h6_chain_14 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_14 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 567 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 4.820e-04 -> seeded 4.820e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 567, "n_distinct": 220, "theta": "zero", "pool": 567, "top": 24, "scale_target": 567, "rn_at_insertion": 0.0004820280546317125}.

Cost (from the first Gauss-Newton solve to the gate): 45462572 rotations (2x2, per column), 4 GN iterations, 0 growth rounds, 0 restarts, wall 6 s.

Certificate: final chain 766 letters (grown 0), ranks {'2': 739, '1': 27}, max|theta| 0.202326, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -5.33e-15.

# K1b-T4 warm-start arm -- k1_h6_chain_30 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_30.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_30 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 1136 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 1.572e-03 -> seeded 1.572e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 1136, "n_distinct": 269, "theta": "zero", "pool": 568, "top": 24, "scale_target": 1136, "rn_at_insertion": 0.0015715495455387958}.

Cost (from the first Gauss-Newton solve to the gate): 69760720 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 5 s.

Certificate: final chain 1335 letters (grown 0), ranks {'2': 1287, '1': 48}, max|theta| 0.958177, residual (1-fid^2) 3.6e-15 (recheck 3.6e-15), E(chain) - E0 = 2.13e-14.

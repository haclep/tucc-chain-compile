# K1b-T4 warm-start arm -- k1_h6_chain_30 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_30.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_30 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 568 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 1.572e-03 -> seeded 1.572e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "poolall", "insert": "post-joint", "n": 568, "n_distinct": 568, "theta": "zero", "pool": 568, "top": 24, "scale_target": 568, "rn_at_insertion": 0.0015715495455387958}.

Cost (from the first Gauss-Newton solve to the gate): 24502800 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 2 s.

Certificate: final chain 767 letters (grown 0), ranks {'2': 721, '1': 46}, max|theta| 0.958208, residual (1-fid^2) 1.3e-15 (recheck 1.3e-15), E(chain) - E0 = 4.44e-15.

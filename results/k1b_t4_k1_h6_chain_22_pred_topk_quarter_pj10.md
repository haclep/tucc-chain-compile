# K1b-T4 warm-start arm -- k1_h6_chain_22 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_22 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 142 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 5.295e-03 -> seeded 5.295e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 142, "n_distinct": 142, "theta": "zero", "pool": 566, "top": 24, "scale_target": 142, "prejoint_iters": 10, "rn_at_insertion": 0.0052948210799177884}.

Cost (from the first Gauss-Newton solve to the gate): 12743772 rotations (2x2, per column), 5 GN iterations, 0 growth rounds, 0 restarts, wall 2 s.

Certificate: final chain 341 letters (grown 0), ranks {'2': 316, '1': 25}, max|theta| 0.259987, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -1.15e-14.

# K1b-T4 warm-start arm -- k1_h6_chain_30 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_30.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_30 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 141 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 4.371e-03 -> seeded 4.371e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 141, "n_distinct": 141, "theta": "zero", "pool": 563, "top": 24, "scale_target": 141, "prejoint_iters": 20, "rn_at_insertion": 0.004370726395763762}.

Cost (from the first Gauss-Newton solve to the gate): 9840548 rotations (2x2, per column), 4 GN iterations, 0 growth rounds, 0 restarts, wall 3 s.

Certificate: final chain 340 letters (grown 0), ranks {'2': 319, '1': 21}, max|theta| 0.467407, residual (1-fid^2) 1.3e-15 (recheck 8.9e-16), E(chain) - E0 = 5.33e-15.

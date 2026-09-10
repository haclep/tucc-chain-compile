# K1b-T4 warm-start arm -- k1_h6_chain_34 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_34.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit dfcb1b1.
Provenance: invocation k1b_warmstart.py k1_h6_chain_34 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 142 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 6.643e-04 -> seeded 6.643e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 142, "n_distinct": 142, "theta": "zero", "pool": 566, "top": 24, "scale_target": 142, "prejoint_iters": 20, "rn_at_insertion": 0.0006643403923334704}.

Cost (from the first Gauss-Newton solve to the gate): 4937304 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 1 s.

Certificate: final chain 341 letters (grown 0), ranks {'2': 319, '1': 22}, max|theta| 0.733366, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = 4.44e-15.

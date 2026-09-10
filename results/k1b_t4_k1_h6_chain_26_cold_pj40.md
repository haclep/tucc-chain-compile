# K1b-T4 warm-start arm -- k1_h6_chain_26 / cold

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_26.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit dfcb1b1.
Provenance: invocation k1b_warmstart.py k1_h6_chain_26 --arm cold --order rank --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 0 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 4.780e-04 -> seeded 4.780e-04. Seed provenance: {"arm": "cold", "order": "rank", "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 25163292 rotations (2x2, per column), 26 GN iterations, 1 growth rounds, 0 restarts, wall 4 s.

Certificate: final chain 223 letters (grown 24), ranks {'2': 207, '1': 16}, max|theta| 0.515894, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -8.88e-16.

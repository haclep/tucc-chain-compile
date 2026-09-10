# K1b-T4 warm-start arm -- k1_h6_chain_22 / cold

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_22 --arm cold --order rank --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 0 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 6.971e-04 -> seeded 6.971e-04. Seed provenance: {"arm": "cold", "order": "rank", "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 79862976 rotations (2x2, per column), 80 GN iterations, 1 growth rounds, 0 restarts, wall 24 s.

Certificate: final chain 223 letters (grown 24), ranks {'2': 207, '1': 16}, max|theta| 0.416307, residual (1-fid^2) 8.9e-16 (recheck 1.1e-15), E(chain) - E0 = 1.33e-14.

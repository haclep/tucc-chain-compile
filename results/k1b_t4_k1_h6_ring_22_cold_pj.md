# K1b-T4 warm-start arm -- k1_h6_ring_22 / cold

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_22 --arm cold --order rank --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 0 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 8.321e-03 -> seeded 8.321e-03. Seed provenance: {"arm": "cold", "order": "rank", "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 280318708 rotations (2x2, per column), 182 GN iterations, 6 growth rounds, 0 restarts, wall 199 s.

Certificate: final chain 319 letters (grown 160), ranks {'2': 290, '1': 29}, max|theta| 0.872410, residual (1-fid^2) 1.3e-15 (recheck 1.3e-15), E(chain) - E0 = 1.95e-14.

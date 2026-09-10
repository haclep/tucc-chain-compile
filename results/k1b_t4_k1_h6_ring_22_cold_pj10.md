# K1b-T4 warm-start arm -- k1_h6_ring_22 / cold

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_22 --arm cold --order rank --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 0 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 8.984e-03 -> seeded 8.984e-03. Seed provenance: {"arm": "cold", "order": "rank", "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 312896016 rotations (2x2, per column), 201 GN iterations, 7 growth rounds, 0 restarts, wall 79 s.

Certificate: final chain 358 letters (grown 199), ranks {'2': 314, '1': 44}, max|theta| 1.092815, residual (1-fid^2) 1.3e-15 (recheck 1.6e-15), E(chain) - E0 = 1.95e-14.

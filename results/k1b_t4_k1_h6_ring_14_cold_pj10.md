# K1b-T4 warm-start arm -- k1_h6_ring_14 / cold

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_14 --arm cold --order rank --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 0 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 5.103e-03 -> seeded 5.103e-03. Seed provenance: {"arm": "cold", "order": "rank", "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 1052904992 rotations (2x2, per column), 440 GN iterations, 8 growth rounds, 0 restarts, wall 210 s.

Certificate: final chain 402 letters (grown 243), ranks {'2': 334, '1': 68}, max|theta| 0.375083, residual (1-fid^2) 4.4e-16 (recheck 1.1e-15), E(chain) - E0 = 3.55e-15.

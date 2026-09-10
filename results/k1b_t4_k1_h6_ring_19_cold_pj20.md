# K1b-T4 warm-start arm -- k1_h6_ring_19 / cold

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_19.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_19 --arm cold --order rank --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 0 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 2.451e-03 -> seeded 2.451e-03. Seed provenance: {"arm": "cold", "order": "rank", "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 202162940 rotations (2x2, per column), 186 GN iterations, 6 growth rounds, 0 restarts, wall 57 s.

Certificate: final chain 319 letters (grown 160), ranks {'2': 290, '1': 29}, max|theta| 0.754538, residual (1-fid^2) 2.2e-16 (recheck 2.2e-16), E(chain) - E0 = -1.78e-15.

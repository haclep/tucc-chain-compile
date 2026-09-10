# K1b-T4 warm-start arm -- k1_h6_ring_14 / cold

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_14 --arm cold --order rank --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 0 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 3.118e-03 -> seeded 3.118e-03. Seed provenance: {"arm": "cold", "order": "rank", "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 1221150336 rotations (2x2, per column), 562 GN iterations, 7 growth rounds, 0 restarts, wall 323 s.

Certificate: final chain 358 letters (grown 199), ranks {'2': 316, '1': 42}, max|theta| 0.751392, residual (1-fid^2) 7.6e-13 (recheck 7.6e-13), E(chain) - E0 = 5.82e-12.

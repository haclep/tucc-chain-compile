# K1b-T4 warm-start arm -- k1_h6_ring_30 / cold

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_30.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_30 --arm cold --order rank --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 0 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 3.254e-02 -> seeded 3.254e-02. Seed provenance: {"arm": "cold", "order": "rank", "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 178580584 rotations (2x2, per column), 138 GN iterations, 6 growth rounds, 0 restarts, wall 41 s.

Certificate: final chain 319 letters (grown 160), ranks {'2': 279, '1': 40}, max|theta| 1.250541, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -3.55e-15.

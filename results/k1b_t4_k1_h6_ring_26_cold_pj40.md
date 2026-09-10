# K1b-T4 warm-start arm -- k1_h6_ring_26 / cold

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_26.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit dfcb1b1.
Provenance: invocation k1b_warmstart.py k1_h6_ring_26 --arm cold --order rank --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 0 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 1.034e-02 -> seeded 1.034e-02. Seed provenance: {"arm": "cold", "order": "rank", "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 140610856 rotations (2x2, per column), 122 GN iterations, 5 growth rounds, 0 restarts, wall 22 s.

Certificate: final chain 284 letters (grown 125), ranks {'2': 270, '1': 14}, max|theta| 0.625836, residual (1-fid^2) 1.8e-15 (recheck 1.8e-15), E(chain) - E0 = 1.60e-14.

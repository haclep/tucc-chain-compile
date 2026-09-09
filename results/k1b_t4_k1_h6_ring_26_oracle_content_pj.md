# K1b-T4 warm-start arm -- k1_h6_ring_26 / oracle_content

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_26.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_26 --arm oracle_content --order shuffle --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 160 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 1.034e-02 -> seeded 1.034e-02. Seed provenance: {"arm": "oracle_content", "order": "shuffle", "source": "certified chain grown multiset, theta 0", "n": 160, "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 19039788 rotations (2x2, per column), 9 GN iterations, 0 growth rounds, 0 restarts, wall 11 s.

Certificate: final chain 319 letters (grown 0), ranks {'2': 303, '1': 16}, max|theta| 0.396211, residual (1-fid^2) 4.4e-16 (recheck 4.4e-16), E(chain) - E0 = 1.15e-14.

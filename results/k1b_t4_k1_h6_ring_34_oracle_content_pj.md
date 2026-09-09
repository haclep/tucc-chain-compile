# K1b-T4 warm-start arm -- k1_h6_ring_34 / oracle_content

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_34.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_34 --arm oracle_content --order shuffle --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 127 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 2.859e-02 -> seeded 2.859e-02. Seed provenance: {"arm": "oracle_content", "order": "shuffle", "source": "certified chain grown multiset, theta 0", "n": 127, "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 12429060 rotations (2x2, per column), 7 GN iterations, 0 growth rounds, 0 restarts, wall 8 s.

Certificate: final chain 286 letters (grown 0), ranks {'2': 269, '1': 17}, max|theta| 0.757257, residual (1-fid^2) 1.3e-15 (recheck 1.3e-15), E(chain) - E0 = 4.44e-15.

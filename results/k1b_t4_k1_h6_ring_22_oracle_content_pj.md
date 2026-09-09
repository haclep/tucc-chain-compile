# K1b-T4 warm-start arm -- k1_h6_ring_22 / oracle_content

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_22 --arm oracle_content --order shuffle --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 199 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 8.321e-03 -> seeded 8.321e-03. Seed provenance: {"arm": "oracle_content", "order": "shuffle", "source": "certified chain grown multiset, theta 0", "n": 199, "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 29899688 rotations (2x2, per column), 10 GN iterations, 0 growth rounds, 0 restarts, wall 16 s.

Certificate: final chain 358 letters (grown 0), ranks {'2': 325, '1': 33}, max|theta| 0.549287, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -3.55e-15.

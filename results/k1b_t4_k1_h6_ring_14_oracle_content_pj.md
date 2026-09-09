# K1b-T4 warm-start arm -- k1_h6_ring_14 / oracle_content

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_14 --arm oracle_content --order shuffle --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 199 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 3.029e-03 -> seeded 3.029e-03. Seed provenance: {"arm": "oracle_content", "order": "shuffle", "source": "certified chain grown multiset, theta 0", "n": 199, "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 33669456 rotations (2x2, per column), 12 GN iterations, 0 growth rounds, 0 restarts, wall 79 s.

Certificate: final chain 358 letters (grown 0), ranks {'2': 335, '1': 23}, max|theta| 0.315337, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -1.07e-14.

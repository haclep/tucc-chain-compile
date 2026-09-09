# K1b-T4 warm-start arm -- k1_h6_chain_22 / oracle_content

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_chain_22 --arm oracle_content --order shuffle --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 24 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 3.446e-04 -> seeded 3.446e-04. Seed provenance: {"arm": "oracle_content", "order": "shuffle", "source": "certified chain grown multiset, theta 0", "n": 24, "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 24123216 rotations (2x2, per column), 22 GN iterations, 0 growth rounds, 0 restarts, wall 10 s.

Certificate: final chain 223 letters (grown 0), ranks {'2': 207, '1': 16}, max|theta| 0.389952, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = 5.33e-15.

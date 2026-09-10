# K1b-T4 warm-start arm -- k1_h6_chain_14 / cold

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_chain_14 --arm cold --order rank --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 0 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 4.820e-04 -> seeded 4.820e-04. Seed provenance: {"arm": "cold", "order": "rank", "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 338213036 rotations (2x2, per column), 230 GN iterations, 4 growth rounds, 0 restarts, wall 176 s.

Certificate: final chain 316 letters (grown 117), ranks {'2': 300, '1': 16}, max|theta| 0.400743, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -5.33e-15.

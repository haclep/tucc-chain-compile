# K1b-T4 warm-start arm -- k1_h6_chain_19 / cold

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_19.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit dfcb1b1.
Provenance: invocation k1b_warmstart.py k1_h6_chain_19 --arm cold --order rank --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 0 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 2.047e-03 -> seeded 2.047e-03. Seed provenance: {"arm": "cold", "order": "rank", "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 185889820 rotations (2x2, per column), 172 GN iterations, 2 growth rounds, 0 restarts, wall 37 s.

Certificate: final chain 250 letters (grown 51), ranks {'2': 234, '1': 16}, max|theta| 0.420049, residual (1-fid^2) 4.3e-13 (recheck 4.3e-13), E(chain) - E0 = 1.49e-12.

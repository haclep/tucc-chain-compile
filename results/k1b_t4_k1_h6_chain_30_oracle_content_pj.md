# K1b-T4 warm-start arm -- k1_h6_chain_30 / oracle_content

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_30.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_chain_30 --arm oracle_content --order shuffle --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 26 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 1.572e-03 -> seeded 1.572e-03. Seed provenance: {"arm": "oracle_content", "order": "shuffle", "source": "certified chain grown multiset, theta 0", "n": 26, "insert": "post-joint"}.

Cost (from the first Gauss-Newton solve to the gate): 13784736 rotations (2x2, per column), 12 GN iterations, 0 growth rounds, 0 restarts, wall 8 s.

Certificate: final chain 225 letters (grown 0), ranks {'2': 208, '1': 17}, max|theta| 0.974479, residual (1-fid^2) 4.4e-16 (recheck 4.4e-16), E(chain) - E0 = 4.44e-15.

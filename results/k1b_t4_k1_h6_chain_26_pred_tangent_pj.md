# K1b-T4 warm-start arm -- k1_h6_chain_26 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_26.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_chain_26 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 127 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 4.412e-04 -> seeded 4.412e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_chain_26_tangent.pkl", "pred_seed": 0, "config": "K1c-tangent", "insert": "post-joint", "n": 127, "n_distinct": 112}.

Cost (from the first Gauss-Newton solve to the gate): 4527216 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 2 s.

Certificate: final chain 326 letters (grown 0), ranks {'2': 306, '1': 20}, max|theta| 0.519054, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -7.11e-15.

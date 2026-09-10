# K1b-T4 warm-start arm -- k1_h6_chain_22 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_22.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_chain_22 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 532 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 3.446e-04 -> seeded 3.446e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_chain_22_poolall.pkl", "pred_seed": 0, "config": "K1c-poolall", "insert": "post-joint", "n": 532, "n_distinct": 532}.

Cost (from the first Gauss-Newton solve to the gate): 22395088 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 4 s.

Certificate: final chain 731 letters (grown 0), ranks {'2': 685, '1': 46}, max|theta| 0.427658, residual (1-fid^2) 8.9e-16 (recheck 8.9e-16), E(chain) - E0 = 1.24e-14.

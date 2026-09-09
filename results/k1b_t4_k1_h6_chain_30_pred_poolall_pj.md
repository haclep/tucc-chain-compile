# K1b-T4 warm-start arm -- k1_h6_chain_30 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_30.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_chain_30 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 507 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 1.572e-03 -> seeded 1.572e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_chain_30_poolall.pkl", "pred_seed": 0, "config": "K1c-poolall", "insert": "post-joint", "n": 507, "n_distinct": 507}.

Cost (from the first Gauss-Newton solve to the gate): 21057264 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 3 s.

Certificate: final chain 706 letters (grown 0), ranks {'2': 660, '1': 46}, max|theta| 0.958182, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -1.78e-15.

# K1b-T4 warm-start arm -- k1_h6_chain_26 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_26.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_chain_26 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 546 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 4.412e-04 -> seeded 4.412e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_chain_26_poolall.pkl", "pred_seed": 0, "config": "K1c-poolall", "insert": "post-joint", "n": 546, "n_distinct": 546}.

Cost (from the first Gauss-Newton solve to the gate): 23239304 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 4 s.

Certificate: final chain 745 letters (grown 0), ranks {'2': 699, '1': 46}, max|theta| 0.518955, residual (1-fid^2) 1.8e-15 (recheck 1.8e-15), E(chain) - E0 = 1.42e-14.

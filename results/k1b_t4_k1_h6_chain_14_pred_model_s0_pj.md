# K1b-T4 warm-start arm -- k1_h6_chain_14 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_chain_14 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 107 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 4.820e-04 -> seeded 4.820e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_chain_14_model_s0.pkl", "pred_seed": 0, "config": "K1c-model_s0", "insert": "post-joint", "n": 107, "n_distinct": 19}.

Cost (from the first Gauss-Newton solve to the gate): 98030928 rotations (2x2, per column), 52 GN iterations, 0 growth rounds, 0 restarts, wall 42 s.

Certificate: final chain 306 letters (grown 0), ranks {'2': 290, '1': 16}, max|theta| 0.250017, residual (1-fid^2) 6.7e-16 (recheck 6.7e-16), E(chain) - E0 = 1.24e-14.

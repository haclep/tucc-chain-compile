# K1b-T4 warm-start arm -- k1_h6_chain_19 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_19.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_chain_19 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 536 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 6.549e-04 -> seeded 6.549e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_chain_19_poolall.pkl", "pred_seed": 0, "config": "K1c-poolall", "insert": "post-joint", "n": 536, "n_distinct": 536}.

Cost (from the first Gauss-Newton solve to the gate): 22560328 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 4 s.

Certificate: final chain 735 letters (grown 0), ranks {'2': 689, '1': 46}, max|theta| 0.364735, residual (1-fid^2) 2.7e-13 (recheck 2.7e-13), E(chain) - E0 = 5.52e-13.

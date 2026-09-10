# K1b-T4 warm-start arm -- k1_h6_ring_34 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_34.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_ring_34 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 538 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 2.859e-02 -> seeded 2.859e-02. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_ring_34_poolall.pkl", "pred_seed": 0, "config": "K1c-poolall", "insert": "post-joint", "n": 538, "n_distinct": 538}.

Cost (from the first Gauss-Newton solve to the gate): 40516036 rotations (2x2, per column), 4 GN iterations, 0 growth rounds, 0 restarts, wall 30 s.

Certificate: final chain 697 letters (grown 0), ranks {'2': 659, '1': 38}, max|theta| 0.805639, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -7.99e-15.

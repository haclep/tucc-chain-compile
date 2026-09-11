# K1b-T4 warm-start arm -- h8_chain / b2

Source: target checkpoint h8_chain_bigsd.pkl; dump h8_chain.npz; sector (4,4) dim 4900; harness k1b-warmstart-1 at commit c918b61.
Provenance: invocation k1b_warmstart.py h8_chain --arm b2 --order rank --plateau 0.01 (repeated to completion, 34 invocations).

Proposal: 360 letters appended after the 2467 routed (greedy-ordered) letters; |r| routed 2.165e-02 -> seeded 2.242e-01. Seed provenance: {"arm": "b2", "order": "rank", "source": "k1_harness.b2_physics (MP2 window)", "b2_sign": -1.0, "n": 360}.

Cost (from the first Gauss-Newton solve to the gate): 12951278337840 rotations (2x2, per column), 1532 GN iterations, 8 growth rounds, 0 restarts, wall 391601 s.

Certificate: final chain 7249 letters (grown 4422), ranks {'2': 6214, '1': 1035}, max|theta| 0.551069, residual (1-fid^2) 8.7e-13 (recheck 8.7e-13), E(chain) - E0 = 5.01e-12.

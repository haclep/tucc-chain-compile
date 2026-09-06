# K1b-T4 warm-start arm -- h8_chain / pred

Source: target checkpoint h8_chain_bigsd.pkl; dump h8_chain.npz; sector (4,4) dim 4900; harness k1b-warmstart-1 at commit 89e3c9c.
Provenance: invocation k1b_warmstart.py h8_chain --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 25 invocations).

Proposal: 383 letters appended after the 2467 routed (greedy-ordered) letters; |r| routed 2.165e-02 -> seeded 3.585e-01. Seed provenance: {"arm": "pred", "order": "rank", "source": "predictions_splitC_h8.pkl", "pred_seed": 0, "config": "C1C2K", "n": 383, "n_distinct": 300}.

Cost (from the first Gauss-Newton solve to the gate): 9944641373280 rotations (2x2, per column), 1432 GN iterations, 7 growth rounds, 0 restarts, wall 297641 s.

Certificate: final chain 6495 letters (grown 3645), ranks {'2': 5560, '1': 935}, max|theta| 0.668539, residual (1-fid^2) 9.3e-13 (recheck 9.3e-13), E(chain) - E0 = 5.30e-12.

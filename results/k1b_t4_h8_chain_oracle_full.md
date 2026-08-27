# K1b-T4 warm-start arm -- h8_chain / oracle_full

Source: target checkpoint h8_chain_bigsd.pkl; dump h8_chain.npz; sector (4,4) dim 4900; harness k1b-warmstart-1 at commit 663a146.
Provenance: invocation k1b_warmstart.py h8_chain --arm oracle_full --order rank --plateau 0.01 (repeated to completion, 173 invocations).

Proposal: 3866 letters appended after the 2467 routed (greedy-ordered) letters; |r| routed 2.165e-02 -> seeded 8.970e-07. Seed provenance: {"arm": "oracle_full", "order": "rank", "source": "certified chain (label)", "n": 3866, "routed_theta": "certified"}.

Cost (from the first Gauss-Newton solve to the gate): 18571263060 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 486 s.

Certificate: final chain 6333 letters (grown 0), ranks {'2': 6040, '1': 293}, max|theta| 1.534693, residual (1-fid^2) 7.6e-13 (recheck 7.6e-13), E(chain) - E0 = 4.23e-12.

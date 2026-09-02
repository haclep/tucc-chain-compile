# K1b-T4 warm-start arm -- h8_chain / cold

Source: target checkpoint h8_chain_bigsd.pkl; dump h8_chain.npz; sector (4,4) dim 4900; harness k1b-warmstart-1 at commit 89e3c9c.
Provenance: invocation k1b_warmstart.py h8_chain --arm cold --order rank --plateau 0.01 (repeated to completion, 31 invocations).

Proposal: 0 letters appended after the 2467 routed (greedy-ordered) letters; |r| routed 2.165e-02 -> seeded 2.165e-02. Seed provenance: {"arm": "cold", "order": "rank"}.

Cost (from the first Gauss-Newton solve to the gate): 12255796099500 rotations (2x2, per column), 1612 GN iterations, 9 growth rounds, 0 restarts, wall 369560 s.

Certificate: final chain 7113 letters (grown 4646), ranks {'2': 6251, '1': 862}, max|theta| 1.063362, residual (1-fid^2) 8.9e-13 (recheck 8.9e-13), E(chain) - E0 = 5.00e-12.

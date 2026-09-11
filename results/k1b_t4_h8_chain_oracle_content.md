# K1b-T4 warm-start arm -- h8_chain / oracle_content

Source: target checkpoint h8_chain_bigsd.pkl; dump h8_chain.npz; sector (4,4) dim 4900; harness k1b-warmstart-1 at commit 4950194.
Provenance: invocation k1b_warmstart.py h8_chain --arm oracle_content --order shuffle --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 3866 letters appended after the 2467 routed (greedy-ordered) letters; |r| routed 2.165e-02 -> seeded 2.165e-02. Seed provenance: {"arm": "oracle_content", "order": "shuffle", "source": "certified chain grown multiset, theta 0", "n": 3866}.

Cost (from the first Gauss-Newton solve to the gate): 200898961580 rotations (2x2, per column), 22 GN iterations, 0 growth rounds, 0 restarts, wall 5788 s.

Certificate: final chain 6333 letters (grown 0), ranks {'2': 6040, '1': 293}, max|theta| 0.233683, residual (1-fid^2) 4.4e-16 (recheck 4.4e-16), E(chain) - E0 = -6.75e-14.

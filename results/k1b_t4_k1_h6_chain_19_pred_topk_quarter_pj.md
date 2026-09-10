# K1b-T4 warm-start arm -- k1_h6_chain_19 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_19.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_19 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 141 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 6.549e-04 -> seeded 6.549e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 141, "n_distinct": 141, "theta": "zero", "pool": 563, "top": 24, "scale_target": 141, "prejoint_iters": 300, "rn_at_insertion": 0.0006549228926334925}.

Cost (from the first Gauss-Newton solve to the gate): 9573652 rotations (2x2, per column), 4 GN iterations, 0 growth rounds, 0 restarts, wall 2 s.

Certificate: final chain 340 letters (grown 0), ranks {'2': 319, '1': 21}, max|theta| 0.364536, residual (1-fid^2) 4.4e-16 (recheck 4.4e-16), E(chain) - E0 = 7.11e-15.

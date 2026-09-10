# K1b-T4 warm-start arm -- k1_h6_chain_34 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_34.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_34 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 284 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 1.110e-04 -> seeded 1.110e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 284, "n_distinct": 284, "theta": "zero", "pool": 567, "top": 24, "scale_target": 284, "prejoint_iters": 300, "rn_at_insertion": 0.00011104870258608999}.

Cost (from the first Gauss-Newton solve to the gate): 9600064 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 1 s.

Certificate: final chain 483 letters (grown 0), ranks {'2': 456, '1': 27}, max|theta| 0.782235, residual (1-fid^2) 4.4e-16 (recheck 4.4e-16), E(chain) - E0 = 1.51e-14.

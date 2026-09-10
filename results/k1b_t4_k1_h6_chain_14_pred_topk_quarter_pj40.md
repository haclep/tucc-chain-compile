# K1b-T4 warm-start arm -- k1_h6_chain_14 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_14 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 142 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 4.822e-04 -> seeded 4.822e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "topk", "insert": "post-joint", "n": 142, "n_distinct": 142, "theta": "zero", "pool": 567, "top": 24, "scale_target": 142, "prejoint_iters": 40, "rn_at_insertion": 0.0004821509276934736}.

Cost (from the first Gauss-Newton solve to the gate): 11831372 rotations (2x2, per column), 5 GN iterations, 0 growth rounds, 0 restarts, wall 3 s.

Certificate: final chain 341 letters (grown 0), ranks {'2': 322, '1': 19}, max|theta| 0.205315, residual (1-fid^2) 2.2e-16 (recheck 0.0e+00), E(chain) - E0 = 1.24e-14.

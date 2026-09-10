# K1b-T4 warm-start arm -- k1_h6_chain_26 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_26.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_26 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 1130 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 4.412e-04 -> seeded 4.412e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 1130, "n_distinct": 255, "theta": "zero", "pool": 565, "top": 24, "scale_target": 1130, "rn_at_insertion": 0.00044121315524196753}.

Cost (from the first Gauss-Newton solve to the gate): 70541304 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 6 s.

Certificate: final chain 1329 letters (grown 0), ranks {'2': 1270, '1': 59}, max|theta| 0.518913, residual (1-fid^2) 3.8e-15 (recheck 3.8e-15), E(chain) - E0 = 2.75e-14.

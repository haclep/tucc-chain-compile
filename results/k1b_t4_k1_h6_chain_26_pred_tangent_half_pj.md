# K1b-T4 warm-start arm -- k1_h6_chain_26 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_26.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_26 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 282 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 4.412e-04 -> seeded 4.412e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 282, "n_distinct": 183, "theta": "zero", "pool": 565, "top": 24, "scale_target": 282, "rn_at_insertion": 0.00044121315524196753}.

Cost (from the first Gauss-Newton solve to the gate): 9516192 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 1 s.

Certificate: final chain 481 letters (grown 0), ranks {'2': 455, '1': 26}, max|theta| 0.518899, residual (1-fid^2) 1.1e-15 (recheck 1.1e-15), E(chain) - E0 = 1.15e-14.

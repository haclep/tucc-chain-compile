# K1b-T4 warm-start arm -- k1_h6_ring_19 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_19.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_19 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 2 invocations).

Proposal: 1132 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 2.383e-03 -> seeded 2.383e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 1132, "n_distinct": 249, "theta": "zero", "pool": 566, "top": 24, "scale_target": 1132, "rn_at_insertion": 0.002383091760826739}.

Cost (from the first Gauss-Newton solve to the gate): 158164040 rotations (2x2, per column), 5 GN iterations, 0 growth rounds, 0 restarts, wall 12 s.

Certificate: final chain 1291 letters (grown 0), ranks {'2': 1257, '1': 34}, max|theta| 0.387409, residual (1-fid^2) 2.2e-16 (recheck 2.2e-16), E(chain) - E0 = -5.33e-15.

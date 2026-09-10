# K1b-T4 warm-start arm -- k1_h6_ring_14 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_ring_14.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_ring_14 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 284 letters appended after the 159 routed (greedy-ordered) letters; |r| routed 3.029e-03 -> seeded 3.029e-03. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 284, "n_distinct": 138, "theta": "zero", "pool": 568, "top": 24, "scale_target": 284, "rn_at_insertion": 0.0030288395647985185}.

Cost (from the first Gauss-Newton solve to the gate): 22832880 rotations (2x2, per column), 6 GN iterations, 0 growth rounds, 0 restarts, wall 4 s.

Certificate: final chain 443 letters (grown 0), ranks {'2': 430, '1': 13}, max|theta| 0.359625, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -3.20e-14.

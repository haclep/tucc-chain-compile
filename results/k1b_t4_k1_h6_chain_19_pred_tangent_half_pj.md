# K1b-T4 warm-start arm -- k1_h6_chain_19 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_19.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 7bf387f.
Provenance: invocation k1b_warmstart.py k1_h6_chain_19 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 282 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 6.549e-04 -> seeded 6.549e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "tangent", "insert": "post-joint", "n": 282, "n_distinct": 180, "theta": "zero", "pool": 563, "top": 24, "scale_target": 282, "rn_at_insertion": 0.0006549228926334925}.

Cost (from the first Gauss-Newton solve to the gate): 9396360 rotations (2x2, per column), 2 GN iterations, 0 growth rounds, 0 restarts, wall 1 s.

Certificate: final chain 481 letters (grown 0), ranks {'2': 455, '1': 26}, max|theta| 0.364299, residual (1-fid^2) 4.7e-13 (recheck 4.7e-13), E(chain) - E0 = 1.08e-12.

# K1b-T4 warm-start arm -- k1_h6_chain_19 / pred

Source: target dense eigh of the dump (root 0); dump k1_h6_chain_19.npz; sector (3,3) dim 400; harness k1b-warmstart-1 at commit 75754a3.
Provenance: invocation k1b_warmstart.py k1_h6_chain_19 --arm pred --order rank --seed 0 --plateau 0.01 (repeated to completion, 1 invocations).

Proposal: 118 letters appended after the 199 routed (greedy-ordered) letters; |r| routed 6.549e-04 -> seeded 6.549e-04. Seed provenance: {"arm": "pred", "order": "rank", "source": "k1_h6_chain_19_tangent.pkl", "pred_seed": 0, "config": "K1c-tangent", "insert": "post-joint", "n": 118, "n_distinct": 107}.

Cost (from the first Gauss-Newton solve to the gate): 8359020 rotations (2x2, per column), 4 GN iterations, 0 growth rounds, 0 restarts, wall 3 s.

Certificate: final chain 317 letters (grown 0), ranks {'2': 297, '1': 20}, max|theta| 0.363622, residual (1-fid^2) 0.0e+00 (recheck 0.0e+00), E(chain) - E0 = -1.60e-14.

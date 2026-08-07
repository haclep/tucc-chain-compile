# Stage-1 certification -- operator-kernel and dressing law

C1: an independent tuple-determinant kernel (ported from the upgradation symbolic engine; composite operator ordering pinned to chaincompile.dets) must reproduce the vector-machinery chain state. C2: the committed chain JSON must round-trip to the eigenstate. C3: the first-order operator-valued dressing law -- each letter's amplitude tan(theta_k) dressed by sec(theta_j) over sharing letters (Freericks Symmetry 2022 eqs. 38/46/51; measured exactly on two-factor probes in tests) -- scored against exact cluster amplitudes. Deviations and un-covered ranks quantify the folded structure a first-order operator-valued form does not carry.

## L6_U2_gs_sd

C1 kernel-vs-vector max deviation: 1.39e-16. C2 eigenstate infidelity: -8.88e-16. Cluster-analysis rebuild error: 1.8e-16.

Letters: 84 (45 distinct, 25 pivot-anchored, 25 scored). Median relative error of the dressing law on anchored amplitudes: later-secants 2.151, all-secants 2.247, bare tan(theta) 0.155.

Chain coverage of ||T_r||^2 by letter substitutions: T2: 1.0000, T3: 0.0000, T4: 0.0000, T6: 0.0000. Largest folded (composite) amplitudes: rank 3 (0,1,3)->(4,5,7) t=-0.0047; rank 3 (1,10,11)->(6,7,9) t=+0.0047; rank 3 (0,10,11)->(6,7,8) t=+0.0047; rank 3 (0,1,2)->(4,5,6) t=-0.0047; rank 3 (1,2,3)->(5,6,7) t=+0.0047.

| sub | rank | n_letters | anchored | t_exact | t_pred | t_pred_all | t_bare |
|---|---|---|---|---|---|---|---|
| (2,3)->(8,9) | 2 | 2 | True | 0.109650 | 0.623447 | 0.226468 | 0.087476 |
| (10,11)->(4,5) | 2 | 1 | True | 0.109650 | 0.188361 | 0.188361 | 0.103665 |
| (2,11)->(4,9) | 2 | 1 | True | 0.086799 | 0.183586 | 0.196524 | 0.081002 |
| (3,10)->(5,8) | 2 | 1 | True | 0.086799 | 0.269505 | 0.288497 | 0.095582 |
| (2,11)->(5,8) | 2 | 1 | True | -0.063949 | -0.142890 | -0.161844 | -0.068730 |
| (3,10)->(4,9) | 2 | 1 | True | -0.063949 | -0.268386 | -0.303987 | -0.132623 |
| (0,11)->(4,7) | 2 | 2 | True | 0.063763 | 0.252591 | 0.189361 | 0.053906 |
| (1,10)->(5,6) | 2 | 2 | True | 0.063763 | 0.163973 | 0.243329 | 0.072657 |
| (1,2)->(6,9) | 2 | 2 | True | -0.063763 | -0.302249 | -0.226575 | -0.062556 |
| (0,3)->(7,8) | 2 | 2 | True | -0.063763 | -0.422729 | -0.117362 | -0.032963 |


## L6_U6_gs_sd

C1 kernel-vs-vector max deviation: 7.63e-17. C2 eigenstate infidelity: 0.00e+00. Cluster-analysis rebuild error: 5.4e-16.

Letters: 76 (41 distinct, 25 pivot-anchored, 25 scored). Median relative error of the dressing law on anchored amplitudes: later-secants 5462.944, all-secants 30949.980, bare tan(theta) 1.608.

Chain coverage of ||T_r||^2 by letter substitutions: T2: 1.0000, T3: 0.0000, T4: 0.0000, T6: 0.0000. Largest folded (composite) amplitudes: rank 4 (2,3,10,11)->(4,5,8,9) t=-0.1358; rank 3 (0,10,11)->(4,8,9) t=+0.0419; rank 3 (0,2,3)->(4,5,8) t=+0.0419; rank 3 (2,3,10)->(4,5,6) t=-0.0419; rank 3 (2,10,11)->(6,8,9) t=-0.0419.

| sub | rank | n_letters | anchored | t_exact | t_pred | t_pred_all | t_bare |
|---|---|---|---|---|---|---|---|
| (10,11)->(4,5) | 2 | 1 | True | 0.420164 | 2502.836473 | 2502.836473 | 0.354864 |
| (2,3)->(8,9) | 2 | 2 | True | 0.420164 | 920.747306 | 1909.115812 | 0.662856 |
| (2,11)->(4,9) | 2 | 1 | True | 0.272091 | 909.828948 | 965.439124 | 0.145148 |
| (3,10)->(5,8) | 2 | 1 | True | 0.272091 | -857.165815 | -909.557137 | -0.107050 |
| (1,10)->(5,6) | 2 | 2 | True | 0.214886 | 16812.879643 | 2189.099015 | 0.560332 |
| (0,11)->(4,7) | 2 | 2 | True | 0.214886 | 1384.015154 | 833.599825 | 0.267103 |
| (1,2)->(6,9) | 2 | 2 | True | -0.214886 | -7907.453960 | -2082.209491 | -0.276256 |
| (0,3)->(7,8) | 2 | 2 | True | -0.214886 | -1142.299258 | -634.604655 | -0.169415 |
| (0,1)->(6,7) | 2 | 6 | True | 0.168310 | 1578.014882 | 5209.370724 | 0.283079 |
| (0,11)->(5,6) | 2 | 2 | True | -0.153972 | -5.124054 | -26.929145 | -0.884876 |


## L4_U8_gs_sd (in-process)

C1 kernel-vs-vector max deviation: 2.78e-17. C2 eigenstate infidelity: 0.00e+00. Cluster-analysis rebuild error: 1.5e-15.

Letters: 13 (10 distinct, 8 pivot-anchored, 8 scored). Median relative error of the dressing law on anchored amplitudes: later-secants 0.399, all-secants 0.764, bare tan(theta) 0.447.

Chain coverage of ||T_r||^2 by letter substitutions: T2: 1.0000, T4: 0.0000. Largest folded (composite) amplitudes: rank 4 (0,1,2,3)->(4,5,6,7) t=-0.2649.

| sub | rank | n_letters | anchored | t_exact | t_pred | t_pred_all | t_bare |
|---|---|---|---|---|---|---|---|
| (2,3)->(6,7) | 2 | 1 | True | 1.000000 | 1.283601 | 1.283601 | 1.003649 |
| (1,2)->(4,7) | 2 | 1 | True | -0.420236 | -0.282071 | -0.406483 | -0.232458 |
| (0,3)->(5,6) | 2 | 1 | True | -0.420236 | -0.282071 | -0.406483 | -0.232458 |
| (0,1)->(4,5) | 2 | 2 | True | 0.399410 | 0.248255 | 0.250941 | 0.196028 |
| (0,3)->(4,7) | 2 | 1 | True | 0.210118 | 0.320286 | 0.520067 | 0.309130 |
| (1,2)->(5,6) | 2 | 1 | True | 0.210118 | 0.320286 | 0.520067 | 0.309130 |
| (0,2)->(4,6) | 2 | 1 | True | -0.210118 | -0.298184 | -0.452922 | -0.262694 |
| (1,3)->(5,7) | 2 | 1 | True | -0.210118 | -0.298184 | -0.452922 | -0.262694 |
| (3,4)->(1,6) | 2 | 2 | False | 0 | -0.268457 | -0.479702 | -0.267269 |
| (2,5)->(0,7) | 2 | 2 | False | 0 | -0.268457 | -0.479702 | -0.267269 |


# chaincompile worked validation -- summary

generated 2026-08-04, chaincompile 0.1.0; momentum-space Hubbard ring, t=1; all compiles exact (residual < 1e-12) by construction.

| system | pivot | len_sd | len_direct | max_theta_sd | max_theta_direct | direct_ranks | sd_cap_fidelity | sd_cap_dE_mt | fid |
|---|---|---|---|---|---|---|---|---|---|
| L6_U2 GS | |0u 0d 1u 1d 5u 5d> | 84 | 220 | 0.610679 | 0.109072 | {2: 25, 4: 97, 6: 82, 3: 16} |  |  | 1.000000 |
| L6_U6 GS | |0u 0d 1u 1d 5u 5d> | 76 | 220 | 1.549385 | 0.362724 | {2: 25, 4: 97, 6: 82, 3: 16} | 0.986730 | 197.493807 | 1.000000 |
| L6_U6 root 2 (S2=-0.00) | |0u 0d 1u 1d 2d 5u> | 84 | - | 1.526155 | - | - |  |  | 1.000000 |
| L4_U8 GS | |0u 0d 1u 1d> | 13 | 13 | 0.787219 | 0.748429 | {2: 8, 4: 5} |  |  | 1.000000 |

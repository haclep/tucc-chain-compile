# H4 molecular validation -- off-lattice, self-contained

STO-3G s-Gaussian integrals in closed form (Boys F0), plain RHF, MO transform, and the sector Hamiltonian built with the stack's own elementary-operator kernel. External anchor: H2 at 1.4 bohr reproduces the textbook E_RHF = -1.116714 / E_FCI = -1.137276 Ha; internal certification: <HF|H|HF> + Enuc = E_RHF to ~1e-12 at every geometry. Molecules have no momentum label, so routing runs with k_pure = None -- exercised here for the first time -- and roots carry (E, S^2, dominant det) per ADR-003 without the K column.

## H4 rectangle 2.0 x 2.5 (bohr)

RHF converged: True; E_RHF = -1.947428 Ha; E_FCI = -2.045601 Ha; Ecorr = -0.098173; |c_HF| = 0.9406; <HF|H|HF> identity deviation 2.3e-12; GS <S^2> = 1.78e-19.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -2.045601 | 1.780e-19 | |0u 0d 1u 1d> | 0.884771 |
| 1 | -1.924985 | 2.000000 | |0u 0d 1d 2u> | 0.461214 |
| 2 | -1.731003 | 2.000000 | |0d 1u 1d 2u> | 0.269958 |
| 3 | -1.709650 | -7.939e-18 | |0u 0d 2u 2d> | 0.766697 |


| mode | length | ranks | max_theta | residual | noc_dev | noc_terms |
|---|---|---|---|---|---|---|
| sd_routed | 15 | {2: 15} | 0.232904 | 0 | 3.469e-17 | 12 |
| direct | 16 | {2: 10, 4: 6} | 0.236375 | 0 | 1.041e-16 | 12 |
| sd_paired | 18 | {2: 18} | 0.232905 | 0 | 1.388e-17 | 12 |


Cluster analysis: rebuild error 2.2e-15; ||T2||^2 = 0.1280, ||T4||^2 = 0.0000.

## H4 near-square 2.0 x 2.05 (multireference stress) (bohr)

RHF converged: True; E_RHF = -1.799983 Ha; E_FCI = -1.945688 Ha; Ecorr = -0.145705; |c_HF| = 0.7627; <HF|H|HF> identity deviation 4.9e-12; GS <S^2> = -2.63e-18.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -1.945688 | -2.628e-18 | |0u 0d 1u 1d> | 0.581717 |
| 1 | -1.924397 | 2.000000 | |0u 0d 1d 2u> | 0.476550 |
| 2 | -1.789508 | 1.038e-18 | |0u 0d 2u 2d> | 0.553569 |
| 3 | -1.721422 | 7.662e-29 | |0u 0d 1u 2d> | 0.498715 |


| mode | length | ranks | max_theta | residual | noc_dev | noc_terms |
|---|---|---|---|---|---|---|
| sd_routed | 15 | {2: 15} | 0.667379 | 0 | 1.388e-17 | 12 |
| direct | 16 | {2: 10, 4: 6} | 0.666056 | 2.220e-16 | 3.469e-17 | 12 |
| sd_paired | 18 | {2: 18} | 0.667382 | 0 | 1.388e-17 | 12 |


Cluster analysis: rebuild error 3.9e-15; ||T1||^2 = 0.0000, ||T2||^2 = 0.7145, ||T4||^2 = 0.0010.

Readings: direct mode exposes H4's genuine quadruple content (6 rank-4 factors) which sd_routed and sd_paired replace with all-doubles chains; every constructive translation lands at ~1e-16 with a support-saturated term curve; T1 is Brillouin-small at both geometries and ||T2||^2 grows from 0.13 to 0.71 approaching the square -- the multireference character the geometry scan was designed to exhibit.
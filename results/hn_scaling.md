# Hydrogen-systems scaling -- richer basis, bigger molecules

All integrals from the s-only closed forms (`molecular.py`); certification identity <HF|H|HF> + Enuc = E_RHF checked at every system. Roots tables use canonical (min-mask) dominant-determinant labels among amplitude ties, so triplet spin-partner labels are platform-stable.

## H2 anchors

| system | E_RHF | E_FCI | dim | identity_dev |
|---|---|---|---|---|
| H2/sto-3g (textbook -1.116714/-1.137276) | -1.116714 | -1.137276 | 4 | 4.441e-16 |
| H2/6-31g (literature -1.1267/-1.1517) | -1.126743 | -1.151679 | 16 | 1.514e-13 |


## H4 / 6-31G rectangle 2.0 x 2.5 bohr

RHF converged True; E_RHF = -2.043357; E_FCI = -2.125153; Ecorr = -0.081796; |c_HF| = 0.9485; sector dim 784; support 208; identity deviation 8.5e-13. Direct compile: length 668 (fill-in factor 3.2x support), ranks {1: 4, 2: 56, 3: 192, 4: 416}, residual 1.6e-15, fidelity 1.000000000000. Cluster analysis: rebuild 5.9e-15; ||T1||^2 = 0.0012, ||T2||^2 = 0.1085, ||T3||^2 = 0.0001, ||T4||^2 = 0.0000.
Note the 6-31G mean field (-2.0434) nearly ties the STO-3G FCI (-2.0456) -- basis quality vs correlation, quantified.

## H6 / STO-3G ring (side 1.9 bohr)

RHF converged True; E_RHF = -3.156052; E_FCI = -3.237170; Ecorr = -0.081118; sector dim 400; support 160; identity deviation 3.0e-12. Direct compile: length 735 (fill-in 4.6x), ranks {2: 47, 4: 262, 6: 218, 5: 144, 3: 64}, residual 0.0e+00.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -3.237170 | -1.450e-18 | |0u 0d 1u 1d 2u 2d> | 0.939748 |
| 1 | -2.863222 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.228800 |
| 2 | -2.790908 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.206842 |
| 3 | -2.790908 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.206842 |


## Measured laws and the frontier

Composer rank-cost law: a rank-r factor's exact normal-ordered polynomial has 4^r + 2 monomials (measured [(1, 6), (2, 18), (3, 66), (4, 258)]) -- so SD chains are the translation-scalable class, and direct-mode chains (ranks up to 6 here) are not the constructive-translation path. Fill-in law: off-lattice direct chains lengthen to 3-5x support (K-purity suppressed fill-in on the lattice) while staying exact and fast. Performance history: molecular sd_routed at support >= 60 initially exceeded a 5-minute budget; profiling attributed 100% of wall time to the Gauss-Newton Jacobian build, now column-batched (bitwise-equivalent) with a raised growth-round cap -- both flagship molecular systems now solve exactly in ~30-50 s and translate constructively (see run_hn_sd.py / results/hn_sd.md). The p-function basis boundary (cc-pVDZ and beyond, any non-hydrogen atom) is exactly the Psi4 integration hand-off.

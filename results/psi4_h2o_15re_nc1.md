# Psi4-dump ingestion -- h2o_15re

Source: psi4 1.11; basis sto-3g; active nmo 6; sector (4,4) dim 225; 1 core orbitals frozen, E_core = -59.92444653.

Provenance: dump file h2o_15re.npz; invocation run_psi4_dump.py h2o_15re.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 1.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 7.11e-14. E_SCF = -74.74715250; E_FCI = -74.89664523; Ecorr = -0.14949272.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -74.896645 | 5.499e-18 | |0u 0d 1u 1d 2u 2d 3u 3d> | 0.840818 |
| 1 | -74.787351 | 2.000000 | |0u 0d 1u 1d 2d 3u 3d 4u> | 0.397886 |
| 2 | -74.765210 | -2.977e-19 | |0u 0d 1u 1d 2d 3u 3d 4u> | 0.374311 |
| 3 | -74.745340 | 2.000000 | |0u 0d 1u 1d 2d 3u 3d 5u> | 0.375044 |


Symmetry blocks: HF-connected 65, ground-state-connected 65 of 225; ground support 65.


sd_routed: length 81, ranks {2: 69, 1: 12}, max|theta| 0.702330, residual 0.0e+00. Prefix <S2> peak 0.4345. Constructive translation: 65 creator monomials, acceptance 1.2e-16.

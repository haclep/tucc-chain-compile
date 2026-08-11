# Psi4-dump ingestion -- h2o_sto3g

Source: psi4 1.11; basis sto-3g; active nmo 6; sector (4,4) dim 225; 1 core orbitals frozen, E_core = -60.66178181.

Provenance: dump file h2o_sto3g.npz; invocation run_psi4_dump.py h2o_sto3g.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 1.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 5.68e-14. E_SCF = -74.96294684; E_FCI = -75.01235941; Ecorr = -0.04941257.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -75.012359 | -8.666e-20 | |0u 0d 1u 1d 2u 2d 3u 3d> | 0.973600 |
| 1 | -74.613980 | 2.000000 | |0u 0d 1u 1d 2u 2d 3d 4u> | 0.477915 |
| 2 | -74.554240 | 9.922e-19 | |0u 0d 1u 1d 2u 2d 3d 4u> | 0.470105 |
| 3 | -74.510363 | 2.000000 | |0u 0d 1u 1d 2d 3u 3d 4u> | 0.463905 |


Symmetry blocks: HF-connected 65, ground-state-connected 65 of 225; ground support 65.


sd_routed: length 81, ranks {2: 67, 1: 14}, max|theta| 0.916844, residual 0.0e+00. Prefix <S2> peak 0.1073. Constructive translation: 65 creator monomials, acceptance 9.9e-17.

# Psi4-dump ingestion -- c2_30

Source: psi4 1.11; basis sto-3g; active nmo 8; sector (4,4) dim 4900; 2 core orbitals frozen, E_core = -70.63996117.

Provenance: dump file c2_30.npz; invocation run_psi4_dump.py c2_30.npz --mode direct --nroots 4 --max-dim 5000 --n-core 2.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 9.95e-14. E_SCF = -74.39846910; E_FCI = -74.61600327; Ecorr = -0.21753417.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -74.616003 | 2.000000 | |0u 0d 1u 1d 2d 3u 3d 4u> | 0.389943 |
| 1 | -74.616003 | 2.000000 | |0u 0d 1u 1d 2d 3u 4u 4d> | 0.389943 |
| 2 | -74.599068 | 1.078e-19 | |0u 0d 1u 1d 3u 3d 4u 4d> | 0.597413 |
| 3 | -74.585315 | 2.000000 | |0u 0d 1u 1d 2u 2d 3d 4u> | 0.437600 |


Symmetry blocks: HF-connected 660, ground-state-connected 608 of 4900; ground support 608 -- ground state NOT in the HF block (state reordering); degenerate pair projected onto the dominant block.


direct: length 11967, ranks {1: 3, 2: 49, 3: 209, 4: 822, 5: 1684, 6: 3074, 8: 4918, 7: 1208}, max|theta| 0.728663, residual 0.0e+00.

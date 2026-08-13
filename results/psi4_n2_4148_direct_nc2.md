# Psi4-dump ingestion -- n2_4148

Source: psi4 1.11; basis sto-3g; active nmo 8; sector (5,5) dim 3136; 2 core orbitals frozen, E_core = -94.24334876.

Provenance: dump file n2_4148.npz; invocation run_psi4_dump.py n2_4148.npz --mode direct --nroots 4 --max-dim 4000 --n-core 2.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 1.14e-13. E_SCF = -106.75449609; E_FCI = -107.44498064; Ecorr = -0.69048454.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -107.444981 | 3.645e-18 | |0u 0d 1u 1d 2u 2d 3u 3d 4u 4d> | 0.155772 |
| 1 | -107.440876 | 2.000000 | |0u 0d 1u 1d 2u 2d 3u 3d 4d 5u> | 0.049994 |
| 2 | -107.431875 | 6.000000 | |0u 0d 1u 1d 2u 2d 3d 4d 5u 6u> | 0.066861 |
| 3 | -107.414116 | 12.000000 | |0u 0d 1u 1d 2d 3d 4d 5u 6u 7u> | 0.049848 |


Symmetry blocks: HF-connected 784, ground-state-connected 784 of 3136; ground support 652.


direct: length 7515, ranks {1: 2, 2: 84, 4: 1281, 3: 260, 5: 2484, 6: 3404}, max|theta| 0.571915, residual 2.2e-16.

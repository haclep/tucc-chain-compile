# Psi4-dump ingestion -- n2_2074

Source: psi4 1.11; basis sto-3g; active nmo 8; sector (5,5) dim 3136; 2 core orbitals frozen, E_core = -100.03293875.

Provenance: dump file n2_2074.npz; invocation run_psi4_dump.py n2_2074.npz --mode direct --nroots 4 --max-dim 4000 --n-core 2.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 9.95e-14. E_SCF = -107.49584213; E_FCI = -107.65242571; Ecorr = -0.15658358.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -107.652426 | 2.388e-19 | |0u 0d 1u 1d 2u 2d 3u 3d 4u 4d> | 0.917374 |
| 1 | -107.354070 | 2.000000 | |0u 0d 1u 1d 2u 2d 3u 3d 4d 6u> | 0.458428 |
| 2 | -107.354070 | 2.000000 | |0u 0d 1u 1d 2u 2d 3u 3d 4d 5u> | 0.458428 |
| 3 | -107.339601 | 2.000000 | |0u 0d 1u 1d 2u 2d 3d 4u 4d 5u> | 0.220712 |


Symmetry blocks: HF-connected 784, ground-state-connected 784 of 3136; ground support 652.


direct: length 7535, ranks {1: 2, 2: 84, 3: 260, 4: 1281, 5: 2484, 6: 3424}, max|theta| 0.127309, residual 0.0e+00.

# Psi4-dump ingestion -- n2_3111

Source: psi4 1.11; basis sto-3g; active nmo 8; sector (5,5) dim 3136; 2 core orbitals frozen, E_core = -96.17279017.

Provenance: dump file n2_3111.npz; invocation run_psi4_dump.py n2_3111.npz --mode direct --nroots 4 --max-dim 4000 --n-core 2.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 2.84e-14. E_SCF = -107.14473931; E_FCI = -107.52560412; Ecorr = -0.38086481.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -107.525604 | -2.684e-18 | |0u 0d 1u 1d 2u 2d 3u 3d 4u 4d> | 0.600730 |
| 1 | -107.485320 | 2.000000 | |0u 0d 1u 1d 2u 2d 3d 4u 4d 5u> | 0.183679 |
| 2 | -107.431910 | 6.000000 | |0u 0d 1u 1d 2u 2d 3d 4d 5u 6u> | 0.151311 |
| 3 | -107.403475 | 2.000000 | |0u 0d 1u 1d 2u 2d 3d 4u 4d 5u> | 0.131141 |


Symmetry blocks: HF-connected 784, ground-state-connected 784 of 3136; ground support 652.


direct: length 7139, ranks {1: 2, 2: 84, 3: 260, 4: 1277, 5: 2448, 6: 3068}, max|theta| 0.357954, residual 1.9e-14.

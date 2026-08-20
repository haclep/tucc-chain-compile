# Psi4-dump ingestion -- c2_2348

Source: psi4 1.11; basis sto-3g; active nmo 8; sector (4,4) dim 4900; 2 core orbitals frozen, E_core = -72.49241251.

Provenance: dump file c2_2348.npz; invocation run_psi4_dump.py c2_2348.npz --mode direct --nroots 4 --max-dim 5000 --n-core 2.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 1.42e-14. E_SCF = -74.42203718; E_FCI = -74.68975162; Ecorr = -0.26771445.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -74.689752 | 1.600e-18 | |0u 0d 1u 1d 2u 2d 3u 3d> | 0.666700 |
| 1 | -74.639982 | 2.000000 | |0u 0d 1u 1d 2u 2d 3d 4u> | 0.359081 |
| 2 | -74.639982 | 2.000000 | |0u 0d 1u 1d 2d 3u 3d 4u> | 0.359081 |
| 3 | -74.638974 | 2.000000 | |0u 0d 1d 2u 2d 3u 3d 4u> | 0.389554 |


Symmetry blocks: HF-connected 1252, ground-state-connected 1252 of 4900; ground support 1108.


direct: length 61977, ranks {1: 4, 2: 90, 3: 456, 4: 2382, 6: 17960, 5: 7064, 8: 25549, 7: 8472}, max|theta| 0.417084, residual 3.4e-13.

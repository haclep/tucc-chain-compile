# Psi4-dump ingestion -- h2o_20re

Source: psi4 1.11; basis sto-3g; active nmo 6; sector (4,4) dim 225; 1 core orbitals frozen, E_core = -59.55575827.

Provenance: dump file h2o_20re.npz; invocation run_psi4_dump.py h2o_20re.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 1.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 2.84e-14. E_SCF = -74.44566136; E_FCI = -74.77187811; Ecorr = -0.32621676.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -74.771878 | -5.709e-18 | |0u 0d 1u 1d 2u 2d 3u 3d> | 0.524563 |
| 1 | -74.750394 | 2.000000 | |0u 0d 1d 2u 2d 3u 3d 4u> | 0.235441 |
| 2 | -74.746808 | 4.168e-18 | |0u 0d 1d 2u 2d 3u 3d 4u> | 0.224428 |
| 3 | -74.743813 | 2.000000 | |0u 0d 1u 1d 2u 2d 3d 4u> | 0.218222 |


Symmetry blocks: HF-connected 65, ground-state-connected 65 of 225; ground support 65.


sd_routed: length 73, ranks {2: 61, 1: 12}, max|theta| 1.458359, residual 0.0e+00. Prefix <S2> peak 0.2222. Constructive translation: 65 creator monomials, acceptance 1.1e-16.

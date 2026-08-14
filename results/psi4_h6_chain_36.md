# Psi4-dump ingestion -- h6_chain_36

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_chain_36.npz; invocation run_psi4_dump.py h6_chain_36.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 9.94e-12. E_SCF = -2.43121008; E_FCI = -2.86370077; Ecorr = -0.43249069.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -2.863701 | 6.263e-18 | |0u 0d 1u 1d 2u 2d> | 0.366499 |
| 1 | -2.847624 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.161154 |
| 2 | -2.828908 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.096624 |
| 3 | -2.821799 | 2.341e-17 | |0u 0d 1u 1d 3u 3d> | 0.105256 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 200.


sd_routed: length 225, ranks {2: 213, 1: 12}, max|theta| 1.430778, residual 0.0e+00. Prefix <S2> peak 1.9292. Constructive translation: 200 creator monomials, acceptance 2.2e-16.

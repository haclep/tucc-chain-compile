# Psi4-dump ingestion -- h6_ring_18

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_ring_18.npz; invocation run_psi4_dump.py h6_ring_18.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 3.10e-12. E_SCF = -3.16027827; E_FCI = -3.23502549; Ecorr = -0.07474722.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -3.235025 | -1.066e-18 | |0u 0d 1u 1d 2u 2d> | 0.949324 |
| 1 | -2.812274 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.162585 |
| 2 | -2.741655 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.226666 |
| 3 | -2.741655 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.226666 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 160.


sd_routed: length 319, ranks {2: 296, 1: 23}, max|theta| 0.481494, residual 1.3e-15. Prefix <S2> peak 0.4924. Constructive translation: 176 creator monomials, acceptance 9.0e-17.

# Psi4-dump ingestion -- h6_ring_30

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_ring_30.npz; invocation run_psi4_dump.py h6_ring_30.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 7.80e-12. E_SCF = -2.74285180; E_FCI = -2.97316389; Ecorr = -0.23031209.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -2.973164 | 8.735e-19 | |0u 0d 1u 1d 2u 2d> | 0.626378 |
| 1 | -2.901075 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.140712 |
| 2 | -2.861416 | 1.450e-18 | |0u 0d 1u 1d 2d 3u> | 0.111351 |
| 3 | -2.848913 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.104383 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 160.


sd_routed: length 284, ranks {2: 271, 1: 13}, max|theta| 0.466639, residual 0.0e+00. Prefix <S2> peak 1.0151. Constructive translation: 160 creator monomials, acceptance 2.2e-16.

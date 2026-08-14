# Psi4-dump ingestion -- h6_ring_36

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_ring_36.npz; invocation run_psi4_dump.py h6_ring_36.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 6.46e-12. E_SCF = -2.48528746; E_FCI = -2.86984028; Ecorr = -0.38455282.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -2.869840 | 1.579e-18 | |0u 0d 1u 1d 2u 2d> | 0.359851 |
| 1 | -2.845925 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.064987 |
| 2 | -2.827640 | 1.097e-18 | |0u 0d 1d 2u 2d 3u> | 0.046754 |
| 3 | -2.820760 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.076523 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 160.


sd_routed: length 358, ranks {2: 312, 1: 46}, max|theta| 1.136720, residual 0.0e+00. Prefix <S2> peak 0.9605. Constructive translation: 160 creator monomials, acceptance 2.2e-16.

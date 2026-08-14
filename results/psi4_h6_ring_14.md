# Psi4-dump ingestion -- h6_ring_14

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_ring_14.npz; invocation run_psi4_dump.py h6_ring_14.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 3.74e-12. E_SCF = -2.98063118; E_FCI = -3.03541458; Ecorr = -0.05478340.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -3.035415 | -8.959e-19 | |0u 0d 1u 1d 2u 2d> | 0.974601 |
| 1 | -2.345431 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.238079 |
| 2 | -2.284683 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.158639 |
| 3 | -2.284683 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.158639 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 160.


sd_routed: length 374, ranks {2: 358, 1: 16}, max|theta| 1.550632, residual 1.3e-15. Prefix <S2> peak 0.1192. Constructive translation: 160 creator monomials, acceptance 1.1e-16.

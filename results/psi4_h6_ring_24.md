# Psi4-dump ingestion -- h6_ring_24

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_ring_24.npz; invocation run_psi4_dump.py h6_ring_24.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 9.54e-12. E_SCF = -3.01146470; E_FCI = -3.13884100; Ecorr = -0.12737630.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -3.138841 | 7.249e-19 | |0u 0d 1u 1d 2u 2d> | 0.854228 |
| 1 | -2.946606 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.205723 |
| 2 | -2.880019 | 1.375e-20 | |0u 0d 1u 1d 2d 3u> | 0.181312 |
| 3 | -2.873866 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.148742 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 160.


sd_routed: length 284, ranks {2: 275, 1: 9}, max|theta| 0.608315, residual 0.0e+00. Prefix <S2> peak 0.6227. Constructive translation: 181 creator monomials, acceptance 1.1e-16.

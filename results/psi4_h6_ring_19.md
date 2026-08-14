# Psi4-dump ingestion -- h6_ring_19

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_ring_19.npz; invocation run_psi4_dump.py h6_ring_19.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 2.97e-12. E_SCF = -3.15605247; E_FCI = -3.23717026; Ecorr = -0.08111779.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -3.237170 | 2.990e-19 | |0u 0d 1u 1d 2u 2d> | 0.939748 |
| 1 | -2.863222 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.216352 |
| 2 | -2.790908 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.151344 |
| 3 | -2.790908 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.151344 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 160.


sd_routed: length 358, ranks {2: 345, 1: 13}, max|theta| 0.549433, residual 1.3e-15. Prefix <S2> peak 0.5767. Constructive translation: 160 creator monomials, acceptance 5.9e-17.

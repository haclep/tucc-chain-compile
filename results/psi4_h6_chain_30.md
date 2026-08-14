# Psi4-dump ingestion -- h6_chain_30

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_chain_30.npz; invocation run_psi4_dump.py h6_chain_30.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 1.02e-11. E_SCF = -2.67543226; E_FCI = -2.95764609; Ecorr = -0.28221382.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -2.957646 | 1.837e-18 | |0u 0d 1u 1d 2u 2d> | 0.573280 |
| 1 | -2.916260 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.261577 |
| 2 | -2.869089 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.154446 |
| 3 | -2.852980 | 5.225e-18 | |0u 0d 1u 1d 3u 3d> | 0.185413 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 200.


sd_routed: length 225, ranks {2: 208, 1: 17}, max|theta| 1.544656, residual 8.9e-16. Prefix <S2> peak 0.7681. Constructive translation: 200 creator monomials, acceptance 2.2e-16.

# Psi4-dump ingestion -- h6_chain_14

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_chain_14.npz; invocation run_psi4_dump.py h6_chain_14.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 1.52e-12. E_SCF = -3.08098467; E_FCI = -3.14350798; Ecorr = -0.06252331.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -3.143508 | 2.588e-20 | |0u 0d 1u 1d 2u 2d> | 0.959403 |
| 1 | -2.830348 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.473860 |
| 2 | -2.578815 | -9.090e-20 | |0u 0d 1u 1d 2d 3u> | 0.482029 |
| 3 | -2.535781 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.428552 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 200.


sd_routed: length 316, ranks {2: 300, 1: 16}, max|theta| 0.418321, residual 2.2e-15. Prefix <S2> peak 0.3175. Constructive translation: 200 creator monomials, acceptance 2.2e-16.

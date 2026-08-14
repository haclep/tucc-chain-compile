# Psi4-dump ingestion -- h6_chain_19

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_chain_19.npz; invocation run_psi4_dump.py h6_chain_19.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 1.53e-12. E_SCF = -3.13314975; E_FCI = -3.23468623; Ecorr = -0.10153648.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -3.234686 | -6.340e-19 | |0u 0d 1u 1d 2u 2d> | 0.900924 |
| 1 | -3.063199 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.437165 |
| 2 | -2.887407 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.341699 |
| 3 | -2.847925 | -4.162e-18 | |0u 0d 1u 1d 3u 3d> | 0.374156 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 200.


sd_routed: length 250, ranks {2: 234, 1: 16}, max|theta| 0.424276, residual 0.0e+00. Prefix <S2> peak 0.3854. Constructive translation: 200 creator monomials, acceptance 7.6e-17.

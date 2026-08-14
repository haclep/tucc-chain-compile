# Psi4-dump ingestion -- h6_chain_18

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_chain_18.npz; invocation run_psi4_dump.py h6_chain_18.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 1.49e-12. E_SCF = -3.15231625; E_FCI = -3.24451733; Ecorr = -0.09220108.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -3.244517 | 9.615e-19 | |0u 0d 1u 1d 2u 2d> | 0.916192 |
| 1 | -3.051884 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.446462 |
| 2 | -2.857383 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.361017 |
| 3 | -2.815080 | -2.146e-19 | |0u 0d 1u 1d 3u 3d> | 0.382180 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 200.


sd_routed: length 250, ranks {2: 228, 1: 22}, max|theta| 0.702954, residual 6.7e-16. Prefix <S2> peak 0.3878. Constructive translation: 200 creator monomials, acceptance 1.7e-16.

# Psi4-dump ingestion -- h6_chain_24

Source: tucc s-only closed forms; basis sto-3g; active nmo 6; sector (3,3) dim 400.

Provenance: dump file h6_chain_24.npz; invocation run_psi4_dump.py h6_chain_24.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 6.57e-12. E_SCF = -2.94947825; E_FCI = -3.11412088; Ecorr = -0.16464263.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -3.114121 | 1.261e-18 | |0u 0d 1u 1d 2u 2d> | 0.786743 |
| 1 | -3.020061 | 2.000000 | |0u 0d 1u 1d 2d 3u> | 0.372065 |
| 2 | -2.917497 | 2.000000 | |0u 0d 1d 2u 2d 3u> | 0.244824 |
| 3 | -2.889239 | -1.682e-18 | |0u 0d 1u 1d 3u 3d> | 0.299360 |


Symmetry blocks: HF-connected 200, ground-state-connected 200 of 400; ground support 200.


sd_routed: length 223, ranks {2: 207, 1: 16}, max|theta| 0.420059, residual 0.0e+00. Prefix <S2> peak 0.4953. Constructive translation: 200 creator monomials, acceptance 9.0e-17.

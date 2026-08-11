# Psi4-dump ingestion -- lih_30

Source: psi4 1.11; basis sto-3g; active nmo 6; sector (2,2) dim 225.

Provenance: dump file lih_sto3g.npz; invocation run_psi4_dump.py lih_sto3g.npz --mode sd_routed --nroots 4 --max-dim 4000 --n-core 0.

Certification: |<HF|H|HF> + Enuc - E_SCF(dump)| = 3.55e-15. E_SCF = -7.86224631; E_FCI = -7.88250433; Ecorr = -0.02025802.

| root | E_tot | S2 | dominant | weight |
|---|---|---|---|---|
| 0 | -7.882504 | -2.300e-22 | |0u 0d 1u 1d> | 0.974612 |
| 1 | -7.766035 | 2.000000 | |0u 0d 1d 2u> | 0.462380 |
| 2 | -7.748909 | -4.906e-21 | |0u 0d 1d 2u> | 0.448827 |
| 3 | -7.716244 | 2.000000 | |0u 0d 1d 4u> | 0.467521 |


Symmetry blocks: HF-connected 69, ground-state-connected 69 of 225; ground support 69.


sd_routed: length 95, ranks {2: 81, 1: 14}, max|theta| 0.874574, residual 2.7e-13. Prefix <S2> peak 0.0120. Constructive translation: 69 creator monomials, acceptance 1.1e-16.

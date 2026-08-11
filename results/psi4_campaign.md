# Psi4 ingestion campaign -- summary

All ingestions through the certified adapter (psi4 1.11), zero tucc
code changes. Identities in the 1e-16 to 1e-14 band; every constructive
translation at ~1e-16 with creator monomials at the state support.

## The block law (three molecules)

The HF-connected component of H equals the ground-state support
EXACTLY in every system measured: H4/6-31G 208 = 208 (of 784),
LiH/STO-3G 69 = 69 (of 225) at every bond length, H2O/STO-3G 133 = 133
(of 441). Ground states fill their symmetry blocks; support is
symmetry-determined, amplitudes carry the physics. The molecular
analogue of the lattice K-sector support law, now confirmed rather
than hypothesized.

## Master table (sd_routed unless marked)

| dump | basis | dim | E_SCF | E_FCI | Ecorr | c_dom | len (r1) | max_theta | S2 peak | block=sup |
|---|---|---|---|---|---|---|---|---|---|---|
| h4_rect | 6-31g | 784 | -2.043357 | -2.125153 | -0.081797 | 0.9485 | 293 (10) | 0.5925 | 0.291 | 208 |
| h2_14 | cc-pvdz | 100 | -1.128709 | -1.163399 | -0.034689 | 0.9915 | 21 (4) | 0.0531 | - | - |
| lih 3.0 | sto-3g | 225 | -7.862246 | -7.882504 | -0.020258 | 0.9872 | 95 (14) | 0.8746 | - | 69 |
| lih 4.5 | sto-3g | 225 | -7.785716 | -7.831979 | -0.046264 | 0.9440 | 85 (10) | 0.5970 | - | 69 |
| lih 6.0 | sto-3g | 225 | -7.691979 | -7.793859 | -0.101881 | 0.8208 | 106 (13) | 1.0099 | 0.833 | 69 |
| lih 6.0 (sd_paired) | sto-3g | 225 | " | " | " | " | 414 (312) | 0.8236 | 0.063 | 69 |
| lih 7.5 | sto-3g | 225 | -7.626862 | -7.784416 | -0.157554 | 0.7470 | 95 (12) | 1.3317 | 0.929 | 69 |
| lih 7.5 (sd_paired) | sto-3g | 225 | " | " | " | " | 224 (148) | 0.7767 | 0.483 | 69 |
| lih 9.0 | sto-3g | 225 | -7.591095 | -7.782719 | -0.191623 | 0.7203 | 127 (36) | 1.5310 | 1.907 | 69 |
| h2o | sto-3g | 441 | -74.962947 | -75.012438 | -0.049491 | 0.9867 | 186 (26) | 0.6776 | 0.085 | 133 |

## The completed LiH crossing (R = 3.0 -> 9.0 bohr)

Correlation energy 20 -> 192 mHa; dominant weight 0.975 -> 0.519 --
essentially the two-configuration dissociation limit (weight -> 1/2 as
Li(2S) + H(2S) separate); singlet-triplet gap 116.5 -> 54.2 -> 13.4 ->
2.36 -> 0.34 mHa, degenerate to sub-mHa at 9.0. Chain signatures:
max|theta| climbs 0.87 -> 1.53, pressing the pi/2 - 0.02 bound as the
target approaches the equal-superposition limit; the singles count
jumps to 36 at 9.0 (RHF orbitals degrading, relaxation content
exploding); prefix <S2> contamination rises 0.83 -> 1.91 as the
near-degenerate triplet mixes freely into truncations.

## sd_paired at molecular scale

At R = 6.0 the tied chains crush the contamination peak 0.833 -> 0.063
(13x) for a 3.9x length cost; at R = 7.5, 0.929 -> 0.483 (1.9x) for
2.4x -- confinement gets harder as the S-T degeneracy closes, exactly
as the (-1)^S grading predicts (the even sector still admits S = 2).
Four forced-overlap letters in both, matching the lattice count. A
structural surprise worth keeping: the paired solver builds its
molecular chains overwhelmingly from tied SINGLES pairs (312 of 414
letters at 6.0) -- spin-symmetric one-electron moves are its preferred
currency off-lattice.

## Water

First many-electron molecule: 186 letters, 26 singles (orbital
relaxation across five occupied MOs), block = support = 133, prefix
contamination only 0.085 under a ~0.4 Ha gap, translation 2.2e-16.
Literature E_RHF -74.9629 to the digit.

## C2 -- the baby Cr2 (rung two, direct-mode readout)

Frozen-core (8e, 8o), dim 4900, STO-3G. Equilibrium (2.348 bohr):
E_SCF -74.422037, E_FCI -74.689752, Ecorr -0.268 (5x water), ground
weight 0.667 -- the quadruple-bond multireference character at
EQUILIBRIUM -- degenerate low-lying triplet pair 50 mHa up. Block law
refined: support 1108 is a strict subset of the 1252-det block (144
allowed determinants below the amplitude floor) -- "support fills the
block" saturates only in small systems. Direct fill-in explodes with
the rank ceiling: 61,977 letters (56x support) with 25,549 rank-8
factors, still exact at 3.4e-13 -- quantitatively why direct chains
are the wrong object at many-electron scale. Stretched (3.0 bohr): the
model ground state is a degenerate TRIPLET pair with the singlet
(itself dominated by the sigma^2 -> pi^2 doubly excited configuration)
17 mHa above -- state reordering that exposed and fixed a blind spot
in the block check (now anchored at the ground state's own dominant
determinant, not only at HF). The repaired check then detected a
second effect: ground support 1216 = EXACTLY 2 x the 608-det block --
the eigensolver returned a basis-arbitrary mixture of the degenerate
Pi partners spanning two disconnected blocks; the ingestion script now
projects such mixtures onto the dominant determinant's block,
recovering a symmetry-pure exact eigenvector. C2's sd chain (support ~1100, dim 4900)
is rung three's first named target.

## Erratum (2026-08-11): report-file identity repair

A content audit (full enumeration of psi4_*.md Source and result
lines) found two ingestion reports decoupled from their filenames by
a curation slip in the generic-name workflow (custom-geometry runs
write psi4_custom*.md and were renamed by hand):

- psi4_h2o_sto3g.md actually held the LiH 6.0 sd_routed report ->
  renamed to psi4_lih_60.md, its true and previously missing name.
- psi4_custom.md actually held the water sd_routed report -> renamed
  to psi4_h2o_sto3g.md.
- psi4_custom_sd_paired.md was a byte-identical leftover duplicate of
  psi4_lih_60_sd_paired.md -> removed.
- psi4_lih_45.md never existed: the LiH 4.5 detail report is presumed
  overwritten in the generic slot before curation. Its master-table
  row and its dump (lih_45.npz) are intact; the report was
  regenerated from the dump on 2026-08-11.

Every number in the master table was and remains correct: rows were
written from run output at run time, and the water row was
independently re-derived on 2026-08-10/11 by the resumable driver
(same energy, support 133, length 186). Adjudication throughout was
by report content against the table -- the mechanism that motivates
stamping future reports with their dump stem and verbatim invocation.

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

## Provenance sweep completion (2026-08-11)

Every dense-path report was regenerated at the current commit and
checked against its committed version and its master-table row.

Scope and outcome: 12 reports -- h2_14, lih_30/45/60/75/90 (routed;
60 and 75 also sd_paired), h4_rect, h2o_sto3g, and both C2 directs
(--n-core 2 --max-dim 5000). Every digit reproduced: energies,
lengths, rank splits, max|theta|, residuals, and NOC acceptances to
the last printed figure. Nine reports gained format-only upgrades
(two-anchor block lines, prefix S2 peaks, active-space phrasing);
the two C2 directs reproduced BYTE-identical -- last runs of Aug 5,
already carrying the post-incident format -- so git records no
change and this note is the durable record that the reruns occurred
(file write times 2026-08-11 11:27). lih_45 was regenerated from its
dump (see erratum above).

New measurements filled in: prefix S2 peaks for lih_30 (0.0120),
lih_45 (0.3236), h2_14 (0.0022); block-law datum four -- H2/cc-pVDZ
block 22 = support 22; H4 and H2 block lines now in their reports.
The stretched-C2 two-anchor line makes the state reordering numeric:
HF-connected 660 vs ground-state-connected 608 of 4900.

Chain-composition fence: the dense path reproduces chain COMPOSITION
exactly across a week of library commits (h2o ranks {2:160, 1:26},
max|theta| 0.677582), while the sparse resumable driver on the same
target reproduces every invariant (length 186, support 133,
translation 133) with a different letter mix ({2:165, 1:21},
max|theta| 0.6309). Composition is optimizer-dependent; length,
support, and translation are not.

Davidson is not a census: dense diagonalization at equilibrium C2
puts the fourth state at -74.638974, 1.0 mHa above the degenerate
pair; the flagship Davidson run's fourth root was -74.58131327,
58 mHa higher -- roots 0-2 matched dense to every printed digit,
root 3 was a different, higher state. Rule adopted: trust the
Davidson target and its converged near-cluster; never treat the
root list as a census or index blindly past the converged cluster.
Retroactively strengthens the leaked-weight trigger over any
root-gap criterion.

Reading convention, verified on all eight systems: the master
table's c_dom column stores the dominant COEFFICIENT c; reports
store the dominant WEIGHT c^2 (lih_30: 0.9872^2 = 0.9746).

Cosmetic driver bug, queued for the stamp patch: the console's
"-> results/..." line prints the pre-suffix filename when mode or
core suffixes apply (three instances); written files were correct
throughout.

## H2O symmetric double dissociation series (2026-08-11)

Active space CAS(8e,6o): STO-3G, oxygen 1s frozen (--n-core 1),
sector (4,4) dim 225. Geometry: the equilibrium dump's experimental
geometry (R_OH = 1.80905 a0, angle 104.5 deg), both O-H vectors
scaled uniformly about O, so the stretch series is "the experimental
geometry scaled by 1.0 / 1.5 / 2.0". Export invocations
(upgradation side; dumps are bench files, regenerable from these):

  psi4_export.py --geom "O 0 0 0; H 1.4305 0 1.1074; H -1.4305 0 1.1074"
      --basis sto-3g --out h2o_sto3g.npz   (pre-existing, 1.0 Re)
  psi4_export.py --geom "O 0 0 0; H 2.14575 0 1.6611; H -2.14575 0 1.6611"
      --basis sto-3g --out h2o_15re.npz
  psi4_export.py --geom "O 0 0 0; H 2.8610 0 2.2148; H -2.8610 0 2.2148"
      --basis sto-3g --out h2o_20re.npz

Each point ran both drivers (dense run_psi4_dump --n-core 1; sparse
run_big_sd --n-core 1); all six compiles exact (five residuals
literally 0.0e+00, the sixth 3.9e-13).

| point | E_SCF | E_FCI | Ecorr | weight | len | ranks | max|th| dense/sparse | sup |
|---|---|---|---|---|---|---|---|---|
| 1.0 Re | -74.962947 | -75.012359 | -0.049 | 0.9736 | 81 | {2:67,1:14} | 0.916844 / 0.916814 | 65 |
| 1.5 Re | -74.747153 | -74.896645 | -0.149 | 0.8408 | 81 | {2:69,1:12} | 0.702330 / 0.702330 | 65 |
| 2.0 Re | -74.445661 | -74.771878 | -0.326 | 0.5246 | 73 | {2:61,1:12} | 1.458359 / 1.476334 | 65 |

Findings:
- Support pinned: 65 = block at every point and both walk floors,
  across simultaneous breaking of BOTH O-H bonds while Ecorr grows
  6.6x and the dominant weight collapses 0.97 -> 0.52. Second
  molecule (after LiH) with a dissociation-pinned support; first
  double-bond-breaking instance.
- Correlation is carried by ANGLE, not length: chain length is flat
  then falls (81, 81, 73) while max|theta| dips mid-scan then surges
  to 1.476, pressing the pi/2 - 0.02 = 1.5508 bound. The same
  mid-scan dip sits unremarked in the LiH table (4.5 bohr: 85
  letters, theta 0.597, both below the 3.0-bohr values). Refinement
  of the chain-length law: length tracks correlation ACROSS states
  at fixed geometry (C2 singlet vs triplet); along a pinned-support
  coordinate, growing correlation is absorbed by angle magnitude,
  with theta -> bound as the dissociation signature. Contrast at
  matched weight ~0.52: the LiH endpoint needs 127 letters with
  singles 36 (heteronuclear orbital degradation); H2O 2Re needs 73
  with singles 12 (the symmetric stretch spares the orbitals).
- Translation support-exact at all six runs (65 monomials, flat
  [65,65,65] tails), now proven at dominant weight 0.52. Routed =
  support - 1 throughout. Prefix S2 peaks (dense): 0.107 / 0.434 /
  0.222 across the scan.
- Optimizer fence has gradations: dense and sparse chains coincide
  to every printed digit at 1.5 Re; agree in length and rank split
  with angles differing at 3e-5 (1.0 Re) and 2e-2 (2.0 Re); the
  full-space equilibrium pair differs in rank split. Length,
  support, and translation reproduce on every rung.
- Sparse-path determinism, fourth confirmation: the fc-anchor
  recompile replayed the entire 2026-08-10 optimization trajectory
  line for line (every joint/growth residual); the report differs
  only by the new Source/Provenance stamp.
- Davidson (HF + 2 lowest-diag seeds) matched dense roots 0-2 to
  every printed digit at all three points; projected False, HF in
  dominant block True throughout -- no false leak triggers at
  stretched geometry. The outside-HF-block live branch still awaits
  stretched N2.
- 2.0 Re spectrum crowding on schedule: S-T gap 21.5 mHa, next
  singlet 3.6 mHa above the triplet.

  ## N2 equilibrium, CAS(10e,8o) (2026-08-12)

Triple-bond rung of the bond-order ladder. Dump n2_2074.npz
(psi4_export --geom "N 0 0 0; N 0 0 2.074" --basis sto-3g); STO-3G,
2 cores frozen, sector (5,5) dim 3136. Three passes: dense direct,
dense sd_routed, sparse resumable sd (both sd compiles exact;
residuals 2.9e-15 / 0.0e+00).

E_SCF -107.495842, E_FCI -107.652426, Ecorr -0.157, dominant weight
0.9174 -- energetically single-reference, yet compile-hard: grown
1019 >= routed 651 (the hard-target NOTE fires at a 0.92-weight
equilibrium state). S-T gap 298 mHa with a degenerate Pi triplet
pair -- the "normal multiple bond" foil to C2's 50 mHa crowd.

Headline: sd chain 1670 (sparse) / 1678 (dense) letters vs C2's
3202 at comparable dimension (per-support 2.56/2.57 vs 2.89) --
chain length measures correlation character, not space size.

Block law, strict-subset instance 2: support 652 of a 784-det block
(132 allowed determinants below floor; C2: 144 of 1252).

Davidson non-census, second conviction: seeds HF + 2 lowest-diag;
roots 0 and one Pi partner match dense to every digit; the second
Pi partner (-107.354070) and the -107.339601 triplet are skipped,
Davidson's third root landing at -107.303761. Standing rule
(trust target + converged near-cluster only) now measured twice.

Optimizer fence, major revision -- first LENGTH split: dense 1678
vs sparse 1670 (0.5%); singles 58 vs 34; max|theta| 1.5506 vs
1.2813, so theta_max is optimizer-dependent at fixed state (the
dense chain presses the pi/2 - 0.02 bound at EQUILIBRIUM, further
demoting absolute theta as a physics meter); translation monomials
676 vs 768 at the keep-floor. The dressing-grows-with-length
monotone (0 -> 24 -> 112) is FALSIFIED: dressing (24 vs 116 on the
same state) belongs to the factorization, not the length.
Invariants that survived: support (652 = 652), block walks, E0,
exactness. [Floor probe of the stored sparse U: RESULT HERE.]

Direct anatomy at a normal triple bond: 7535 letters, fill-in 11.6x
support (C2: 56x), ranks {1:2, 2:84, 3:260, 4:1281, 5:2484,
6:3424}, max|theta| 0.1273, residual 0.0e+00. Rank ceiling 6 is
imposed by the space (six virtual spin-orbitals), so the honest
cross-system comparison is distribution and fill-in, not ceiling.

Operational: growth rounds show long residual plateaus (2.283e-04
held for 150+ iterations before the next round) -- second exhibit
for the deferred plateau early-exit. Finished-state invocations
verified idempotent (repeated done-phase reruns rewrite the report
byte-identically).
# Psi4 ingestion campaign -- summary

All ingestions through the certified adapter (psi4 1.11), zero tucc
code changes. Identities in the 1e-16 to 1e-14 band; every constructive
translation accepted at ~1e-16, with monomial counts support-exact at
physical floors (keep-floor counts are factorization-dependent; see
the N2 series and the C2 flagship floor probe).

## The block law (current form; header updated 2026-08-20)

The HF-connected component of H BOUNDS the ground support from above:
support <= block always, with equality saturating only in small
systems -- H2/cc-pVDZ 22 = 22, H4/6-31G 208 = 208 (of 784), LiH/STO-3G
69 = 69 (of 225) at every bond length, H2O 133 = 133 full-space and
65 = 65 in CAS(8e,6o) at all three stretches, H6 chains 200 = 200 at
all six spacings, H8 chain 2468 = 2468. Strict subsets at C2
(1108 of 1252), N2 all three geometries (652 of 784), and as STANDING
families at the rings: H6 ring 160 of 200, H8 ring 2306 of 2468.
Support is symmetry-BOUNDED, not symmetry-determined; amplitudes carry
the physics. The original saturating statement ("support fills the
block") survives as the small-system limit of this law.

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
exactness. Floor probe of the stored sparse U: [652, 652, 652, 753] at
1e-8/-10/-12/-14 -- support-exact at every physical floor; all 116
dressing terms sub-noise (101 in (1e-14, 1e-12], 15 below 1e-14).
Target probe: [652, 652, 652, 750] -- the same four-decade
silhouette. Identity monomial 0.957796 = sqrt(dominant weight
0.917374).

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

## N2 1.5x equilibrium, 3.111 a0, CAS(10e,8o) (2026-08-12)

Same space and passes as equilibrium. E_SCF -107.144739, E_FCI
-107.525604, Ecorr -0.381 (2.4x equilibrium), dominant weight
0.6007. Spectrum crowding: S-T gap 40 mHa, and root 2 is a QUINTET
(S2 = 6.000) -- the triple bond's pairs decoupling together.

Davidson FULL CENSUS: four seeds (HF no longer among the three
lowest diagonals -- the seed count itself now a mean-field
degradation meter), and all four roots match dense to every digit,
quintet included. Refined census rule: failures observed only at
EXACT degeneracy (the equilibrium Pi pair); crowded but split
spectra are caught. 2x is the degeneracy stress test.

Support pinned: 652 = 652, gap to the 784 block pinned at 132,
through weight 0.92 -> 0.60. Routed 651. NOTE fired (grown 672 >=
651) but the growth fraction FELL (61% -> 51%) as correlation
deepened.

Fence: length split #2 and growing -- dense 1514 vs sparse 1323
(12.6%; equilibrium 0.5%). ROBUST across optimizers: the mid-scan
length dip (per-support 2.57 -> 2.32 dense, 2.56 -> 2.03 sparse).
NOT robust: max|theta| trends are OPPOSITE (dense 1.5506 -> 1.2100,
sparse 1.2813 -> 1.5493 pressing the bound) -- theta is fully
demoted to a factorization property; the dip law is stated in
length only. Singles rise in both (58 -> 80 dense, 34 -> 53
sparse): orbital relaxation growing, cross-optimizer.

Translation and the residual-currency finding: the sparse operator
carries 784 monomials = THE BLOCK exactly, tail [784, 784, 784],
and the floor probe reads [734, 784, 784, 784] at 1e-8/-10/-12/-14
-- these are NOT dust. The exact wave operator occupies its entire
symmetry block while the state it prepares occupies 652
determinants: 132 sub-floor determinants receive above-noise
operator contributions that cancel by destructive interference in
the final state. Operator footprint and state footprint DIVERGE as
correlation deepens (equilibrium: support-shaped operator, 652 +
sub-noise dust; 1.5x: block-shaped operator, interference-sculpted
state). Identity monomial 0.775068 = sqrt(0.600730). Target probe
[652, 652, 666, 1072]: Davidson-tolerance dust below 1e-10, which
the sparse compile reproduces to 8.0e-13 -- the chain carries even
the eigensolver's sub-tolerance tail faithfully.

Residual currencies, adjudicated (SUPERSEDED here; corrected form
below, measured at the H8 chain finish and carried into METHOD):
BOTH drivers report the FIDELITY DEFICIT 1 - fid^2. The sparse
driver's number is not a vector norm; it relates to the residual
norm as deficit ~ ||r||^2 (H8 one-line demonstration:
rn = 8.97e-07, rn^2 = 8.0e-13 = the reported residual). The
original paragraph's compile.py line-73 reading classified the
sparse currency backwards; the deficit-vs-norm CONVERSION it
warned about still stands -- never tabulate a deficit next to a
norm unconverted; deficit ~ norm^2. What survives unchanged:
dense sd 8.9e-16 (deficit) corresponds to a ~4e-8-amplitude
tail, so the 1029-monomial keep-floor reading legitimately
dissolves; dense sd exactness is certified by NOC acceptance
(3.5e-15 here) against the eigh vector, not by the deficit;
direct-mode entries are certified at the deficit level only.
Ledger residual columns are deficit-currency for both paths.

## N2 2.0x equilibrium, 4.148 a0 (2026-08-13) -- series complete

Same space and passes. E_SCF -106.754496, E_FCI -107.444981, Ecorr
-0.690 (4.4x equilibrium), dominant weight 0.1558 -- HF a minority
voice in its own reference state. The four lowest states are the
complete two-atom spin ladder S = 0, 1, 2, 3 (S2 = 0, 2, 6, 12;
the campaign's first septet) at 4.1 / 13.1 / 30.9 mHa above ground,
all dominant weights <= 0.156 -- the 4S + 4S dissociation manifold
closing.

Census, designed stress passed: Davidson (4 seeds) matched dense on
ALL FOUR roots to every digit at 4.1 mHa spacing. Rule measured at
three geometries: crowded-but-split spectra are caught in full; the
only observed failure remains exact degeneracy (equilibrium Pi
pair).

Pinned support, boldest test: 652 = 652 both drivers, block
784/784, gap 132, through weight 0.92 -> 0.60 -> 0.156. Routed 651
throughout; restarts 0 at every point of the series.

Endpoint length verdict: dip then partial recovery, ROBUST across
the fence -- per-support 2.57 -> 2.32 -> 2.45 (dense), 2.56 -> 2.03
-> 2.41 (sparse). N2 votes with LiH against H2O's monotone fall.
Dip law, full form: a length minimum at the correlation crossover,
partial recovery toward dissociation.

The crossover-peak family (every member maximal at 3.111, relaxed
at both ends): fence length split 0.5% -> 12.6% -> 1.5%; singles
58 -> 80 -> 69 (dense), 34 -> 53 -> 30 (sparse); operator
block-filling (below). Growth fraction non-monotone: 61% -> 51% ->
59%.

Operator footprint law, REVISED (corrects the 3111 section's
"diverges as correlation deepens"): sparse U floor probes across
the series read [652, 652, 652, 753] -> [734, 784, 784, 784] ->
[652, 652, 654, 776]. Block-filling with above-noise interference
weight on the 132 silent seats is a CROSSOVER phenomenon -- present
only at 3.111; at both ends the operator is support-exact at
physical floors (endpoint: 652 at 1e-8 and 1e-10; of 780 kept, 2 in
(1e-12, 1e-10], 122 in (1e-14, 1e-12], 4 below). Keep-floor counts
confirmed factorization-dependent (dense 676 -> 1029 -> 652; sparse
768 -> 784 -> 780). Identity monomial 0.394679 = sqrt(0.155772)
within the weight's rounding. Target probe [652, 652, 656, 1307]:
Davidson-tolerance dust only; the sparse compile reproduced the
vector to 4.4e-16 -- the series' deepest residual at its hardest
point.

Series table (dense/sparse where they split):

| R (a0) | E_FCI | Ecorr | weight | sd len | per-sup | max|th| | monomials |
|---|---|---|---|---|---|---|---|
| 2.074 | -107.652426 | -0.157 | 0.9174 | 1678/1670 | 2.57/2.56 | 1.551/1.281 | 676/768 |
| 3.111 | -107.525604 | -0.381 | 0.6007 | 1514/1323 | 2.32/2.03 | 1.210/1.549 | 1029/784 |
| 4.148 | -107.444981 | -0.690 | 0.1558 | 1597/1573 | 2.45/2.41 | 1.551/1.549 | 652/780 |

All six sd compiles exact; every invariant (E0, support, block,
routed) agreed across drivers at every point.

## H6 matched chain-vs-ring scan (2026-08-13) -- dump minter certified

Dumps minted Seneca-side by examples/make_h_dumps.py (internal
s-only closed-form integrals written in the tucc-psi4-dump-1
schema; dumps are bench files, regenerable from the script; ring
spacing = nearest-neighbor distance). C0 note for internal dumps:
the identity reads 1e-12 to 1e-11 -- the internal RHF loop's own
convergence floor (e_scf is the SCF iterate; <HF|H|HF> uses the
final orbitals), largest at the damp-0.5 stretched points; a
genuine convention error misses by 1e-2 to 1e-1 Ha. Selftest
precedent 8.5e-13.

Generator anchor, two routes: h6_ring_19 through the dump path
reproduces the committed internal-direct system -- support 160
exact, and length 358 = the recorded WINDOWS column of the
platform-determinism pair (METHOD: 298 Linux / 358 Windows), run
on Windows. Schema and pipeline certified end to end.

| chain s | E_FCI | Ecorr | weight | len | per-sup | sup=block | monom |
|---|---|---|---|---|---|---|---|
| 1.4 | -3.143508 | -0.0625 | 0.959 | 316 | 1.58 | 200 = 200 | 200 |
| 1.8 | -3.244517 | -0.0922 | 0.916 | 250 | 1.25 | 200 = 200 | 200 |
| 1.9 | -3.234686 | -0.1015 | 0.901 | 250 | 1.25 | 200 = 200 | 200 |
| 2.4 | -3.114121 | -0.1646 | 0.787 | 223 | 1.12 | 200 = 200 | 200 |
| 3.0 | -2.957646 | -0.2822 | 0.573 | 225 | 1.13 | 200 = 200 | 200 |
| 3.6 | -2.863701 | -0.4325 | 0.366 | 225 | 1.13 | 200 = 200 | 200 |

| ring s | E_FCI | Ecorr | weight | len | per-sup | sup (block 200) | monom |
|---|---|---|---|---|---|---|---|
| 1.4 | -3.035415 | -0.0548 | 0.975 | 374 | 2.34 | 160 | 160 |
| 1.8 | -3.235025 | -0.0747 | 0.949 | 319 | 1.99 | 160 | 176 |
| 1.9 | -3.237170 | -0.0811 | 0.940 | 358 | 2.24 | 160 | 160 |
| 2.4 | -3.138841 | -0.1274 | 0.854 | 284 | 1.78 | 160 | 181 |
| 3.0 | -2.973164 | -0.2303 | 0.626 | 284 | 1.78 | 160 | 160 |
| 3.6 | -2.869840 | -0.3846 | 0.360 | 358 | 2.24 | 160 | 160 |

Findings:
- Pinned support, family four, in stereo: chain 200 and ring 160
  at every spacing, weights collapsing to 0.37/0.36 -- the first
  matched topology pair.
- Boundary-condition answer, two-part: periodic wrap-around
  DELETES support (160 in the same-size 200-det block: RHF's
  degenerate ring orbitals mix K-partners, so the connectivity
  walk cannot see the momentum symmetry the amplitudes obey --
  the molecular K-sector law) yet COSTS letters (ring longer than
  chain at every spacing; per-support 1.8-2.3 vs 1.1-1.6).
  Symmetry shrinks the stage and hardens the play. The chain
  fills its block at all six points (the block law's original
  saturating form); the ring is the first STANDING strict-subset
  family.
- Dip law, vote four, per topology: chain minimum at 2.4 (223)
  with marginal recovery (+2); ring minimum flat across 2.4-3.0
  (284), recovery to 358 by 3.6. Robust core = the crossover
  minimum; recovery onset and amplitude are system properties.
- Length is only piecewise-smooth along a coordinate: ring 319 ->
  358 across the 1.8 -> 1.9 step -- jitter at the optimizer-fence
  scale.
- Ring dressing is a light crossover echo (0/16/0/21/0/0, peak at
  2.4); the chain is support-exact at every point.
- Census ambush, recorded for future sparse ring runs: the ring's
  excited spectrum carries EXACTLY degenerate triplet pairs at
  1.4/1.8/1.9 (lifted by 2.4) -- the one condition observed to
  break a Davidson census.
- Equilibria: chain binds near 1.8, ring near 1.9; S2 peaks rise
  monotonically in both (chain to 1.93 at 3.6).


## H8 chain, 1.9 bohr -- the beyond-C2 milestone opens (2026-08-13)

Dump minted Seneca-side (make_h_dumps.py h8_chain; the sandbox
twin's recipe verbatim: 8 H on z at 1.9 bohr spacing, STO-3G).
Sector (4,4) dim 4900 -- the C2 arena with opposite physics.

Dense census reference (probe_spectrum.py, console-only; this
entry is the durable record): C0 = 1.55e-12 (internal band);
blocks 2468 / 2468 of 4900; ground support 2468. Six roots, clean
split spectrum, NO degenerate pairs (gaps 137.0 / 146.2 / 26.5 /
66.4 / 23.6 mHa; S = 0,1,1,0,0,1). E_SCF -4.171555, E_FCI
-4.306049, Ecorr -0.134494, dominant weight 0.8662. Per-atom
Ecorr 16.8 mHa vs H6-chain-1.9's 16.9 -- near-perfect extensivity
at matched spacing.

Support adjudication: 2468. The inherited "2467" was almost
certainly the ROUTED count = support - 1; the sparse banner
adjudicates. Block = support: the chain FILLS its block, but the
H6 exact halving does not generalize -- 2468 of 4900 exceeds
dim/2 = 2450 by 18; the offset is recorded as an open structural
question.

Direct-mode frontier datum: the elimination pass exceeded its
20 x dim = 98,000-step budget (RuntimeError at the cap) -- the
direct chain needs > 98,000 letters, fill-in > 39.7x support,
C2-class (C2: 56x). The fill-in law is now enforced by the driver
itself; a cap raise is deferred as optional, the sd path being
the object of interest.

Sparse campaign launched 2026-08-13, pre-registered: E0 -4.306049
to the digit; routed 2467; support 2468; projected False, HF in
block True; identity monomial sqrt(0.866242) = 0.930722; length
in the 2,700-6,400 band (per-support 1.1-2.6), the H6 open-chain
band 1.1-1.6 the hopeful read; monomials near support, dressing
open; restarts 0 hoped; the measured cost becomes the second
point on the cost-vs-support curve that re-prices H10.

### H8 ring decision gate (dense reference, same day)

Dump minted at damp 0.4, first try (the refuse-to-converge
contingency never fired). C0 = 1.32e-11 -- the loosest internal
reading yet, tracking the hardest SCF; ten orders from a
convention error. Blocks 2468 / 2468 of 4900 -- block size is
topology-independent at matched N (as at H6); ground support 2306
(deletion 162, 6.6% vs H6-ring's 20% -- shallow enough to suggest
a partially symmetry-broken mean field mixing K labels; open
question, not adjudicated).

VERDICT: compilable, queued after the chain. The pre-registered
pathology relocated rather than vanished: the ground state is a
clean nondegenerate SINGLET in the HF block (no projection), 28.3
mHa below the first triplet -- but its dominant weight is 0.4466
AT EQUILIBRIUM, more multireference than C2's 0.667, the
anti-aromatic frontier degeneracy expressed as static correlation
with correlation beating Hund. Roots 0-3 are the complete e^2
frontier manifold (three singlets + one triplet, 143 mHa; roots 0
and 2 share a dominant determinant at ~0.45 weight). The census
ambush is REAL and located: an exactly degenerate triplet pair at
roots 4/5 (-3.868647 twice) -- on record for the future sparse
run. E_SCF -4.000538, E_FCI -4.177019, Ecorr -0.176481 (22.1
mHa/atom vs the chain's 16.8).

The 4n / 4n+2 rule in exact energies, matched N and spacing: H6
ring 2.5 mHa BELOW its chain (aromatic); H8 ring 129.0 mHa ABOVE
its chain (anti-aromatic). Weight at matched spacing: chain
0.8662, ring 0.4466.

### H8 chain -- day-4 progress, a census correction, and the deadline trap (2026-08-17)

Banner (launch 2026-08-13 23:18): support 2468, block 2468/2468, HF
in block, routed 2467 -- the inherited "2467" convicted as the
routed count. Davidson (3 seeds) matched dense root 0 to every
digit; its three roots were dense roots 0, 1, 3 -- the triplet at
-4.022918 was SKIPPED though split by 26.5 mHa from its neighbors.
CENSUS RULE CORRECTED (forward): the "only exact degeneracy"
refinement of the N2 3.111 section is falsified; skips are now
observed at exact degeneracy (N2 eq), near-degeneracy (C2, 1 mHa),
and a split spectrum (H8 chain, 26.5 mHa). The target root has
matched dense in every case, seven of seven. Hypothesis to test:
the two full censuses (N2 stretched) were the four-seed runs; a
--nroots knob on the sparse driver would adjudicate.

Progress: joint phase 3.8 h; then growth rounds (letters added,
per-support, residual at round start, invocations/hours): 1: +308
-> 2775, 1.12, 1.89e-3, 10/6.5; 2: +346 -> 3121, 1.26, 1.04e-3,
14/9.2; 3: +390 -> 3511, 1.42, 5.86e-4, 17/10.5; 4: +438 -> 3949,
1.60, 3.15e-4, 37/15.7; 5: +495 -> 4444, 1.80, 1.54e-4, 40/19.5;
6: +557 -> 5001, 2.03, 7.05e-5, 37/22.4; 7: +627 -> 5628, 2.28,
2.52e-5, in progress. Letters per round grow 13%/round; the
per-round residual factor is accelerating (0.55, 0.56, 0.54, 0.49,
0.46, 0.36); per-iteration cost scales ~length^2.8 (3.3 min at
5001, 4.6 min at 5628). Second point on the cost-vs-support curve:
3.7 days to 5628 letters at support 2468 (C2: ~35 h to 3202 at
1108) -- cost grows far faster than support.

Deadline trap (mechanism from run_big_sd.py lines 199-213): the
driver measures slice_t (seconds per 10-iteration slice) and
refuses to start a slice unless 1.3 x slice_t remains before the
deadline. At len 5628, slice_t = 2733 s, so 1.3 x 2733 = 3553 s >
the 3000 s deadline: every resume refused, no slice ran, slice_t
never re-measured -- 38 zero-work invocations (163-200) in 12 s
on 2026-08-17 16:23. State intact (idempotent re-saves). Remedy:
--deadline 14400 (clears rounds 7-9 with margin; checkpoint saves
every slice). Loop upgraded: utf-8 log, stop rule at round 10 =
the ceiling of the pre-registered length band (per-support ~2.88
at ~7,100 letters, C2's own ratio); if unfinished there, the band
is falsified and we stop by rule. Decision: continue, bounded;
no mid-run driver patch (one driver version per compile). Queued
after this run: plateau early-exit (each round burns most of its
400 iterations at <1% improvement) and a code-version stamp in
the Provenance line.

### H8 chain -- DONE (2026-08-18): the beyond-C2 milestone

E0 -4.30604886 = dense census reference to every digit. Chain 6333
letters, ranks {2: 6040, 1: 293}, max|theta| 1.534693, grown 3866 +
routed 2467, restarts 0; residual 8.0e-13 (deficit; rn = 8.97e-07,
rn^2 = 8.0e-13 -- the currency demonstrated in one line); round 8 of
a possible 9 under the stop rule. Translation: 2468 creator monomials,
tail [2468, 2468, 2468], acceptance 9.6e-16 -- the largest exact
translation on record. Floor probe of U: [2468, 2468, 2468, 2468],
support-exact at EVERY floor incl. 1e-14; identity monomial 0.930721
= sqrt(0.866242). Target probe [2468, 2468, 2528, 4686]: Davidson
dust only.

Round table (letters added -> total, per-support, residual at round
start): 1: +308 -> 2775, 1.12, 1.89e-3; 2: +346 -> 3121, 1.26,
1.04e-3; 3: +390 -> 3511, 1.42, 5.86e-4; 4: +438 -> 3949, 1.60,
3.15e-4; 5: +495 -> 4444, 1.80, 1.54e-4; 6: +557 -> 5001, 2.03,
7.05e-5; 7: +627 -> 5628, 2.28, 2.52e-5; 8: +705 -> 6333, 2.57,
then the quadratic finish to the gate. Per-round residual factors
0.55, 0.56, 0.54, 0.49, 0.46, 0.36, then convergence: the threshold
finish arrived one round before the pre-registered ceiling.
Per-support 2.57 = C2's dense ratio exactly; inside the 2,700-6,400
band with 67 to spare.

Cost-curve point two: ~4.6 days of compute to 6,333 letters at
support 2,468, vs C2's ~35 h to 3,202 at 1,108 -- letters x2.0 for
support x2.2, wall time x3.2 (per-iteration cost ~length^2.8). H10
re-priced from data: support 28,684 -> ~70,000 letters -> months.
The compile frontier is measured, not guessed. 210 invocations
total; the deadline trap cost 38 zero-work invocations and was
cured by loop policy (--deadline 14400), no driver change.

Singles 293 (4.6% of letters) vs <= 80 in every prior system
(N2: 34/53/69): the open-chain mean field is collectively poor --
orbital-relaxation content jumps fourfold at this topology. No
dense sd column by decision (unresumable at this length); this
length is the sparse driver's alone.

Census record: Davidson (3 seeds) returned dense roots 0, 1, 3 --
the -4.022918 triplet skipped at 26.5 mHa split (see the day-4
section); target right, seven of seven.
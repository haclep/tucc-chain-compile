# Schema

Seneca sample pack, version 1. Author: Dr. Luogen Xu, Seneca Labs.

Every quantity here is either read directly from a file or computed from
one by a formula given below. Nothing requires trusting a claim: the
included `verify.py` reconstructs each state from its own record using
numpy alone and reports how far it lands from the exact solution.

---

## 1. What a record is

One record is **one exact electronic state together with one exact
derivation of it**.

The state is the ground state of a molecular Hamiltonian in a defined
orbital space, obtained by exact diagonalization. Within that space it
is exact: not an approximation, not a variational estimate.

The derivation is an ordered sequence of elementary one- and two-body
rotations which, applied in order to a single reference determinant,
reproduces that state. The sequence is *not unique*. Several records in
this pack are different derivations of the same state, and the pack
reports how much they differ.

Each record ships as a pair of files sharing a name:

    records/<system>/<record_id>.json   metadata, labels, amplitudes
    records/<system>/<record_id>.npz    integrals, state, sequence, matrices

`<record_id>` is a content hash. Two records with the same id are the
same derivation of the same state.

---

## 2. Conventions used throughout

**Spin-orbitals.** Orbitals are indexed `0, 1, 2, ...` over spin-orbitals.
Spin-orbital `p` belongs to spatial orbital `p // 2` and spin `p % 2`
(0 = alpha, 1 = beta). A system with `n_orbitals = 6` therefore has
spin-orbitals `0..11`.

**Determinants as integers.** A determinant is a bit mask: bit `p` set
means spin-orbital `p` is occupied. `reference_determinant = 255` is
`0b11111111`, spin-orbitals 0 through 7 occupied.

**Excitation operators.** An operator is written `holes -> particles`.
`[2,3] -> [6,7]` annihilates spin-orbitals 2 and 3 and creates 6 and 7.
Its *rank* is the number of electrons it moves, equal to the length of
`holes`. Rank 1 is a single excitation, rank 2 a double.

**Energies** are in Hartree. See section 3 for what the zero is.

**Sign convention.** Operators annihilate holes in ascending index order,
then create particles in ascending index order, with the usual fermionic
sign. `verify.py` implements this in twenty lines and is the normative
statement of the convention.

---

## 3. `records/<system>/<record_id>.json`

### Identity

| field | meaning |
|---|---|
| `record_id` | content hash of this derivation; the file name |
| `system` | the system label, e.g. `lih-9p0bohr` |
| `family_id` | records sharing this value are derivations of the same state |
| `formula`, `geometry`, `basis` | the chemical system as specified |

### Orbital space

| field | meaning |
|---|---|
| `n_orbitals` | spatial orbitals in the space; spin-orbitals are twice this |
| `n_electrons`, `n_alpha`, `n_beta` | electron counts inside the space |
| `sector_dimension` | number of determinants, `C(n_orbitals, n_alpha) * C(n_orbitals, n_beta)` |
| `reference_determinant` | bit mask of the determinant the sequence starts from |

### Energies

| field | meaning |
|---|---|
| `energy_exact` | exact ground-state eigenvalue in this space |
| `energy_reference` | mean-field (self-consistent field) energy |
| `energy_correlation` | `energy_exact - energy_reference`: what the mean field misses |
| `energy_nuclear` | nuclear repulsion, a constant |

`energy_exact` and `energy_reference` are both **total** energies, with
nuclear repulsion included, so `energy_correlation` is the difference
between them and nothing else. `energy_nuclear` is given separately for
readers who work with electronic energies alone.

### The derivation

| field | meaning |
|---|---|
| `sequence_length` | number of rotations |
| `rank_counts` | how many are rank 1 and rank 2, e.g. `{"1": 24, "2": 419}` |
| `circuit_depth` | number of layers when rotations that share no spin-orbital index are applied simultaneously; the standard circuit-depth measure |

The rotations themselves are in the `.npz`; see section 4.

### Certification

| field | meaning |
|---|---|
| `fidelity_deficit` | `1 - |<exact | rebuilt>|^2`, where `rebuilt` is the sequence applied to the reference |
| `energy_error` | expectation value of the rebuilt state minus `energy_exact` |

A record is included only if `fidelity_deficit < 1e-11`; the exact
threshold is recorded in `MANIFEST.json` under `screens`. The largest
value observed in this pack is 8.6e-13, comfortably inside it, and many
records reconstruct to exactly zero in double precision. `verify.py`
recomputes the deficit independently.

### `hardness`

Numbers describing how strongly correlated the state is and how
well-conditioned its coupled-cluster reading is.

Three are properties of the *state* and are identical across every
derivation of it: `max_natural_occupation_deviation`,
`correlation_energy`, and `support_size` / `support_fraction`.

Three are properties of *this derivation*: `reference_weight`, which
depends on which determinant the derivation starts from; `max_angle`; and
`max_cc_amplitude_bound`.

| field | meaning |
|---|---|
| `reference_weight` | squared amplitude of *this derivation's* reference determinant in the normalized exact state. 1 for a single-determinant system; smaller when no single determinant dominates. Derivations of one state that start from different determinants report different values |
| `max_natural_occupation_deviation` | `max over orbitals of min(n, 2-n) / 2` using the natural occupations. 0 when every orbital is cleanly full or empty, and at most 0.5, reached when an orbital is exactly half-occupied. Fractional occupation is the signature of multireference character; density-functional methods cannot produce this quantity |
| `correlation_energy` | as above, in Hartree |
| `support_size`, `support_fraction` | determinants carrying amplitude above `1e-10`, absolute and as a fraction of `sector_dimension`: how spread the state is over configuration space |
| `max_angle` | largest rotation angle in this derivation, in radians |
| `max_cc_amplitude_bound` | `tan(max_angle)`: the largest coupled-cluster amplitude this derivation can carry (section 5) |

### `labels`

| field | meaning |
|---|---|
| `natural_occupations` | eigenvalues of the one-body reduced density matrix, descending, each in `[0, 2]`. Values away from 0 and 2 indicate fractional occupation, the signature of multireference character |

### `cc_amplitudes` and `cc_status`

See section 5. `cc_amplitudes` is `null` where the amplitudes were
withheld, and `cc_status` always states why.

---

## 4. `records/<system>/<record_id>.npz`

| array | shape | meaning |
|---|---|---|
| `h_mo` | `(n_orbitals, n_orbitals)` | one-electron integrals in the orbital basis |
| `eri_mo` | `(n_orbitals,)*4` | two-electron integrals, `eri_mo[p,q,r,s] = (pq|rs)` in chemist notation |
| `e_nuc` | scalar | nuclear repulsion |
| `determinants` | `(sector_dimension,)` int64 | the determinant basis, as bit masks, in the order the state vector uses |
| `exact_vector` | `(sector_dimension,)` | the exact ground state, coefficient per determinant |
| `reference_determinant` | scalar int64 | as in the JSON |
| `seq_holes`, `seq_parts` | `(sequence_length, 2)` int16 | the rotations, in application order. A rank-1 rotation is padded with `-1`, which must be stripped |
| `seq_angle` | `(sequence_length,)` | the angle of each rotation, radians |
| `rdm1` | `(n_orbitals, n_orbitals)` | spin-summed one-body reduced density matrix |
| `natural_occupations` | `(n_orbitals,)` | its eigenvalues, descending |

Rotation `k` is `exp(t_k (A_k - A_k^dagger))` where `A_k` annihilates
`seq_holes[k]` and creates `seq_parts[k]`, and `t_k = seq_angle[k]`.
Applied in order `0, 1, ..., sequence_length-1` to the reference
determinant, they give the state.

With `h_mo`, `eri_mo` and `determinants` a reader can build the
Hamiltonian and check the state independently of anything else here.

---

## 5. Coupled-cluster amplitudes

### What they are

`cc_amplitudes` is the conventional cluster operator `T` for this state:

    |Psi> proportional to exp(T) |reference>,   T = sum_mu t_mu A_mu

Each entry is one term:

```json
{ "holes": [2, 3], "particles": [6, 7], "rank": 2, "amplitude": 0.11202613 }
```

which is the amplitude of that excitation in `T`, in the standard
coupled-cluster sense (`t_ij^ab` for a rank-2 term).

**These are not the rotations.** The rotations are an ordered product and
there are hundreds of them; the amplitudes are an unordered sum and there
are fewer. They are different representations of the same state, and the
relation between them is not one-to-one. Two consequences visible in this
pack: the amplitude list contains excitations that appear in no rotation
of the sequence, and although every rotation is rank 1 or 2, `T` reaches
rank 6 on the six-electron systems.

`T` is determined by the state **and its reference determinant**, not by
the derivation. Any two derivations of one state that start from the same
reference yield the same amplitudes, while their sequences differ
substantially. Derivations starting from a different reference yield a
different `T`, since `T` is defined relative to what it is expanded around.

That agreement is limited by certification, not by the method. A
derivation reproduces its state to a fidelity deficit below the threshold
rather than exactly; a deficit `R` corresponds to a difference of order
`sqrt(R)` in the state, and extracting `T` divides by the reference
amplitude, amplifying it further. `report/SUMMARY.md` measures the
resulting agreement across every same-reference pair in this pack and
states both the largest and the mean disagreement. Records with smaller
`fidelity_deficit` agree more closely.

### Why some records have none

Each rotation contributes an amplitude `tan(theta)` to the
coupled-cluster picture, which diverges as `|theta|` approaches `pi/2`.
The quantity `cos(theta)` is the weight that rotation leaves on the
reference determinant, so the divergence is the point at which the
reference has been rotated out of the state entirely, and a
single-reference coupled-cluster description no longer has a reference to
be defined against.

Amplitudes are therefore included only where two conditions hold:

1. `max_cc_amplitude_bound = tan(max_angle)` is below a stated threshold,
   recorded in `MANIFEST.json` under `screens`;
2. the reconstruction residual, `cc_status.acceptance`, is below a stated
   threshold: rebuilding the state from `T` alone must return the
   certified state.

`cc_status` reports the outcome either way:

| field | meaning |
|---|---|
| `included` | whether amplitudes are present |
| `acceptance` | reconstruction residual, when computed |
| `n_amplitudes`, `max_rank`, `largest_amplitude` | summary, when included |
| `reason` | why they were withheld, when not |

Whether a derivation is well-conditioned depends on **which determinant
it is expanded around**, not on how strongly correlated the state is. A
derivation built on a low-weight determinant drives rotations toward the
bound even for a state with a clearly dominant configuration, while a
derivation built on the dominant determinant of a strongly correlated
state can be perfectly well-conditioned. Both kinds are present in this
pack: every LiH record carries amplitudes despite LiH at the longest bond
length being the most correlated state here, and a substantial fraction of
hydrogen-system records does not despite those states having the most
dominant references. Read conditioning from `hardness.max_cc_amplitude_bound`
and `cc_status`, not from the correlation diagnostics.

---

## 6. `families/<system>.json`

A family is the set of records that are derivations of the same state.
This file reports how much they differ.

### Membership and summary

| field | meaning |
|---|---|
| `n_members`, `n_pairs` | records in the family, and pairs compared |
| `n_reference_groups` | distinct reference determinants used |
| `content_f1_mean`, `_min`, `_max` | distribution of pairwise content overlap |
| `invariant_core` | rotations common to every member of the largest reference group |

### `pairs`: metrics, and why they are these metrics

Each entry compares two derivations. The question these metrics answer is
whether the derivations differ substantively or are merely reorderings of
one another.

**Content overlap.** Treat each sequence as a *multiset* of rotations,
ignoring order but counting repeats. With `I` the size of the
intersection,

    precision = I / |B|,  recall = I / |A|,  F1 = 2 PR / (P + R)

F1 is 1 if two sequences use exactly the same rotations with the same
multiplicities, 0 if they share none. **Content overlap is blind to
order by construction.** If two derivations differed only by reordering,
F1 would be exactly 1 and the metric would say so immediately. Observed
means in this pack are near 0.6, with minima near 0.30.

**Order agreement.** Take the rotations two sequences share, note where
each first appears as a fraction of the sequence length, and compute the
rank correlation of those two position lists. 1 means the shared
rotations occur in the same relative order, 0 means unrelated.

**Order agreement after canonicalization.** Two rotations *commute* when
their spin-orbital index sets are disjoint; the order of a commuting pair
is arbitrary and carries no information. That freedom is exactly
computable: sliding each rotation past its commuting neighbours into a
fixed key order produces a unique normal form, and two sequences related
only by such reorderings have the same normal form. `order_agreement_canonical`
is the same rank correlation computed on the normal forms.

The pair of numbers is the point. If the derivations were related by
commuting reorderings, canonicalization would collapse them and the
canonical agreement would jump to 1. Across this pack the two values
differ by 0.0014 on average and by at most 0.03 on any pair, and circuit
depth is unchanged by
canonicalization. The differences between derivations therefore survive
the commuting algebra: they are different content, or non-commuting order
with compensating angles, and neither is reachable by permuting operators.

**`same_reference`** flags whether the two derivations start from the same
reference determinant, since cross-reference pairs differ for an
additional reason.

### `invariant_core`

Rotations present in *every* member of the largest reference group, with
the count of letters and of distinct operators. It shrinks as more
derivations are added, since a rotation must survive all of them. It is
reported within a single reference group because derivations expanded
around different determinants are not comparable letter by letter.

---

## 7. `MANIFEST.json`

One entry per record with its id, system, family, sequence length,
fidelity deficit, reference determinant, whether amplitudes are included,
and its hardness scalars. Enough to select records without opening any of
them. `screens` records the thresholds applied.

---

## 8. `verify.py`

Requires numpy and nothing else; imports none of the software that
produced the data.

    python verify.py records/<system>/

For each record it reads the reference determinant, applies the sequence
of rotations, and reports `1 - |<exact | rebuilt>|^2` against the exact
vector in the record. Its docstring states the rotation convention in
full, so a reader can reimplement the check independently.

An energy path exists behind `--energy`, using a Hamiltonian assembled
from `h_mo` and `eri_mo`. That assembly is not yet validated in this
release: it prints an `assembly check`, the residual of the *exact*
vector under its own Hamiltonian, which is zero only if the assembly is
correct. A large value there indicts the script, not the record. The
fidelity check does not use a Hamiltonian and is unaffected.

---

## 9. Scope

Every state is exact **within its stated orbital space**. That is the
regime where methods in general use become unreliable, and it is the
regime these records are drawn from. It is not a claim of agreement with
experiment, which would additionally require a complete basis and all
electrons correlated.

Systems here are small by design: a sample demonstrating a property, not a
production corpus.

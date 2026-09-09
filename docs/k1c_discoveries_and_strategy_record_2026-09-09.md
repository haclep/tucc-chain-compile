# K1c Discoveries, Strategy, and Product Record

**Project:** tucc-chain-compile | Seneca Labs (formerly Senecae Inc.)
**Period covered:** 30 August to 9 September 2026 working sessions
**Written:** 9 September 2026
**Status of this document:** permanent record. Measurements are marked as such; forecasts are marked as forecasts and are to be audited by name; proposals are Claude's unless marked as Logan's decisions.

---

## 0. One-paragraph summary

The K1b-T4 warm-start race on H8 is resolving as a fail on its frozen rule: the learned proposal saved 18.9 percent against a 30 percent bar. While the race ran, a parallel engineering pass on a separate checkout read the compiler's growth code, reproduced its state at proposal time, and measured what growth actually does. Three structural findings followed: the chain's alphabet was keyed by absolute orbital index, so letters did not mean the same thing across molecules; the grown half of a chain is a long tail of tiny-angle re-selections rather than angle-splits; and nearly everything growth will ever add is already visible in the compiler's own round-one candidate pool after the first joint solve. Using that pool, weighted by the compiler's own first-order fidelity gradient, as a warm start with no learned parameters removed 89 to 98 percent of the cost on every hard H6 system and beat the exact chain content itself on 11 of 12. The H8 pool has been built and shows the same containment. The strategic consequence: "predict the chain" was the wrong target; the right target is the gradient field derived from certified chains, and the corpus's gauge freedom, which was a defect for K1, is the engine for learning representation-independent physics. Commercially, the cost of generating certified states is forecast to fall roughly tenfold pending H8, the referee position gained an instrument (fidelity scoring), and the number of paying customers remains zero.

---

## 1. K1b-T4 status at time of writing (measured)

| arm | rotations | GN it | rounds | length | R | status |
|---|---|---|---|---|---|---|
| oracle_full | 1.857e10 | 2 | 0 | 6333 | 7.6e-13 | banked 27 Aug |
| cold | 1.2256e13 | 1612 | 9 | 7113 (2467 routed + 4646 grown) | 8.9e-13 | banked 2 Sep, 31 invocations, wall_opt 369,560 s |
| pred (seed 0) | 9.9446e12 | 1432 | 7 | 6495 (2467 + 383 proposed + 3645 grown) | 9.3e-13 | banked 5 Sep, 25 invocations, wall_opt 297,641 s |
| b2 | running; at it 1042 in round 7 (6444 letters) at 6.654e12 after a plateau exit of round 6 at it 1012 (6.291e12, r 1.462e-05) | | | | | forecast bimodal, 9.6e12 or 1.15e13 |
| oracle_content | queued | | | | | |

**Verdict on P1.** Pred saved 18.9 percent of rotations, 11.2 percent of iterations, 8.7 percent of final length, 21.5 percent of grown letters, and two growth rounds. The rotation leg (at least 30 percent, i.e. at most 8.58e12) fails. The comparative clause (pred saving at least 1.3 times b2's) requires b2 at or above 1.048e13, equivalently a b2 saving at or below 14.5 percent; open pending b2. The verdict is single-seed (pred at seed 0 per the frozen protocol; the umbrella K1 document specifies five seeds), to be stated as such.

**Cold's staircase (measured).** Rounds 6 to 9 are 87 percent of cost. Round 8 (6323 letters) never met the 1 percent plateau rule and ran its full 400-iteration budget at 4.4e12 rotations, 36 percent of the arm, for a residual contraction of about 3x. Cold's cost is within 1 percent of the campaign's own compile of the same state (6333 letters, about 1.21e13); the plateau rule did not reduce cold cost on H8 as it did on N2.

**Seed lines (measured).** Pred's 383 proposed letters at predicted angles moved the routed residual from 2.165e-02 to 3.585e-01 (16.6x worse); b2's 360 MP2-ranked letters moved it to 2.242e-01 (10.4x worse). Both recovered in about 12 cheap joint iterations. Proposed angles from any source are harmful and costless to undo; content transfers.

**Exit-rule variance (measured).** The plateau rule fired on b2's round 6 and not on pred's; that single difference is worth about 1e12, roughly 40 percent of the measured proposal effect. Recorded as a limitation and as the strongest argument for a cost-to-gate exit rule in K1c.

**Forecast audit for this race.** Milestone projection of 5.5 to 7e12 for cold: falsified (actual 1.2256e13). In-session forecasts: cold 11 to 27 h remaining on 31 Aug, falsified; 1.25e13 same-day on 2 Sep, hit. Pred 6 to 14, then 16, then 19 to 24 percent; actual 18.9. B2 1.03e13 then 1.07e13 then bimodal; pending.

---

## 2. K1c discoveries (measured unless marked)

### 2.1 The alphabet was keyed by absolute spin-orbital index

Letters are stored as `((holes), (particles))` in raw spin-orbital indices. In H6 the occupied orbitals are 0 to 5, in H8 0 to 7, so the key `((6,7),(8,9))` is an excitation out of the LUMO pair in H6 and out of the HOMO pair in H8. Cross-size vocabulary transfer by raw key is physically meaningless, and M1's index features (min, max, span) were size-dependent. Reproduced to the digit: the frozen Split-C universe was 619 letters covering 48.0 percent of H8's grown multiset mass and 35.1 percent of its distinct letters (milestone Sec. 8.2a). Only 1367 of 3866 grown letters (35.4 percent) are pivot-referenced occ-to-virt excitations, which is all the MP2 window can nominate.

### 2.2 What the grown half of a chain is

On H8 the grown multiset (3866 letters, 921 distinct) decomposes into 2004 copies of routed keys (52 percent, 358 distinct) and 1862 new letters (48 percent, 563 distinct), of which zero are pivot-referenced. Angles per copy are tiny: mean 0.011 for singletons, 0.005 at multiplicity 2 to 4, 0.003 at 5 to 9, 0.002 at 10 to 24. The 51 letters with 10 or more copies carry a median total rotation of 0.02 rad (max 0.20) against a bound of 1.55. These are not angle-splits; the saturation-split rule contributes little. They are the same substitution direction re-selected by the tangent rule round after round, each time as a small correction. Multiplicity means the number of rounds a direction won. The saturation hypothesis (Claude's, 8 Sep) is falsified; the "copy head" design built on it is withdrawn.

### 2.3 The compiler's future is visible at round one, after the joint solve

Reproducing the compiler's state exactly (routing plus greedy ordering, verified equal to every label's prefix), then running the joint Gauss-Newton solve, then enumerating the edge pool from the largest-residual determinants:

| system | pool seeds | pool size | grown mass in pool | distinct in pool | tangent top-N recall (mass) |
|---|---|---|---|---|---|
| H6, all 50 | 12 | ~500 to 546 | 0.82 to 1.00 | 0.85 to 1.00 | 32 to 100 percent |
| N2 (n2_3111) | 24 | 1981 | 0.984 | 0.973 | 56 percent |
| H8 (h8_chain) | 24 | 1998 | 0.961 | 0.974 | 91 percent |

At the greedy state (before the joint solve) the same tangent ranking recalls roughly 0 percent of new letters; the joint solve, about 1 percent of cold's cost, is what makes the residual informative. Pool width 24 was fixed from N2 before H8 was examined; the H8 containment number is a look at the test system's label of the same class as milestone Sec. 8.2a and is recorded here as a design input.

### 2.4 The compiler warm-starts itself (measured on H6, 12 systems, Logan's machine)

All arms under post-joint insertion, dense target, rotations from the first charged Gauss-Newton solve to the gate. The pre-insertion joint solve is identical in every arm and uncharged.

| system | cold | tangent | model_s0 | poolall | oracle_content |
|---|---|---|---|---|---|
| chain_14 | 3.38e8 (230 it, 4 rounds) | +96.6% | +71.0% | +87.4% | +92.9% |
| chain_19 | 1.25e8 (102, 2) | +93.3% | +80.7% | +81.9% | +78.1% |
| chain_22 | 4.34e7 (40, 1) | +89.6% | +39.4% | +48.4% | +44.5% |
| chain_26 | 6.39e6 (6, 1) | +29.2% | -70.8% | -263.5% | -24.0% |
| chain_30 | 9.68e6 (9, 1) | +60.4% | -161.5% | -117.4% | -42.3% |
| chain_34 | 4.75e6 (4, 1) | +8.5% | +9.4% | -350.6% | +53.3% |
| ring_14 | 1.25e9 (557, 8) | +97.7% | +82.0% | +95.2% | +97.3% |
| ring_19 | 1.91e8 (166, 6) | +90.0% | +26.6% | +75.2% | +89.2% |
| ring_22 | 2.80e8 (182, 6) | +93.7% | +47.7% | +82.3% | +89.3% |
| ring_26 | 1.41e8 (122, 5) | +92.7% | -20.2% | +73.2% | +86.5% |
| ring_30 | 1.68e8 (118, 6) | +93.3% | +72.1% | +77.0% | +90.8% |
| ring_34 | 1.13e8 (106, 5) | +89.3% | +20.5% | +64.0% | +89.0% |

Tangent: the round-one pool at the post-joint state, copies allocated proportional to the first-order fidelity gradient at zero angle, total set by a scale law; no learned parameters. It is best on 12 of 12, matches or beats the exact chain content on 11 of 12, and removes growth entirely on every system. It is weak only where cold was already cheap (stretched chains needing 4 to 9 iterations), where any longer chain is overhead: a proposer needs a floor keyed to the post-joint residual.

The rule was designed on two systems (chain_19, ring_19) and applied unchanged to ten others.

### 2.5 The learned model wins F1 and loses cost

Cross-topology and within-family development on H6, H8 untouched:

| split | model F1 | tangent F1 | note |
|---|---|---|---|
| train chain, test ring | 0.160 | 0.319 | scale predicted 1.15x |
| train ring, test chain | 0.326 | 0.344 | scale predicted 3.14x |
| train ring, test chain, oracle scale | 0.549 | 0.344 | +0.206 +- 0.052 |
| leave-one-out within chain | 0.645 +- 0.065 | 0.344 | +0.301 +- 0.069, scale 1.01x |
| leave-one-out within ring | 0.264 +- 0.025 | 0.319 | -0.055 +- 0.021 |

Ablations at oracle scale: dropping the compiler-native features collapses the model to 0.09; dropping the physics block (B4) costs about 0.03. The pool model learns how the round-one tangent score maps to multi-round selection; the frozen K1b model had only MP2 to ride on. In rotations the model is worse than tangent on all 12 systems and worse than cold on 4. F1 against the certified chain rewards matching the compiler's path; cost rewards spanning the subspace Gauss-Newton needs. The F1 objective is retired for this purpose.

Ring weakness is attributed (Claude's inference, testable) to symmetry ties: sixfold-symmetric candidates have identical features and identical scores, the compiler's canonical tie-break selects one, and a classifier cannot learn which. Tangent-proportional allocation spreads mass across the tied set.

Scale is the unsolved piece: the power law misses by 3 to 4x across topologies; the post-joint residual correlates at 0.71 with log grown-count across H6 but has near-zero slope within a family; H8 extrapolates 12x in support.

### 2.6 Platform sensitivity of cold on symmetric systems

| arm, ring_19 | Logan's machine | sandbox |
|---|---|---|
| cold | 1.912e8, 166 it, len 319 | 6.243e8, 415 it, len 337 |
| tangent | 1.9057e7 | 1.9057e7 |
| oracle_content | 2.0616e7 | 2.0604e7 |
| poolall | 4.749e7 | 4.758e7 |

Small differences are the known line-search effect (N2 shakedown, 0.07 percent). The cold ring is a discrete divergence in growth selection: exact ties resolved on platform-dependent rounding before the canonical tie-break. Arms with a proposal skip growth and never hit ties. The K1b-T4 H8 race is unaffected (single machine). The platform-reproducibility claim needs its scope stated: reproducible to a fraction of a percent absent exact ties. Same-platform determinism of cold on ring_19 is to be confirmed by a repeat run (open).

---

## 3. The K1c toolkit (delivered, tested on both platforms)

All files live in the `tucc-k1c` checkout (branch `k1c`, environment `.venv-k1c`, `pip install -e . numba scikit-learn scipy`). None writes to the campaign checkout. Outputs: `k1c_cache/` (phase-1 and pool caches), `k1c_proposals/`, `k1c_runs/`. The frozen harness's own paths for chain `.npz` (`k1b/`) and reports (`results/`) apply inside the k1c checkout; leave uncommitted until a K1c ledger exists.

| file | purpose | key facts |
|---|---|---|
| `k1c_universe.py` | full spin-conserving S/D universe; index-invariant structural and physics features; coverage audit | H8 universe 4088 letters; reproduces the 619-letter, 48.0 percent cap |
| `k1c_phase1.py` | routing plus greedy ordering with the driver's own functions; asserts equality with the label prefix; greedy-state diagnostics | prefix equality held on every system tested |
| `k1c_pool.py` | joint solve, round-one pool at the post-joint state, compiler-native features, cached per system | `TOP = 24` (set 8 Sep from N2 before the H8 build); known mismatch: runs the joint solve to 300 iterations (H8 r 3.31e-03) while the race harness plateau-exits (3.53e-03 at 92 it) |
| `k1c_model.py` | pool proposer (presence classifier, conditional count regressor, power-law scale), dev splits that never touch H8, baselines, ablations, `--write-proposals` | `--split C --score` is a one-touch event, refused by default |
| `k1c_warmstart.py` | cost harness: wraps the frozen `k1b_warmstart.py`; adds `--pred-file` (any stem) and `--insert post-joint`; signature-agnostic pass-through because the driver recurses positionally | same rotation accounting, gate, plateau rule, report |
| `k1c_race.py` | runs all arms on a list of systems and tabulates from summaries | |

Machine facts: the campaign harness is single-threaded (1 of 24 logical cores busy); 19.3 GB free during the b2 arm; parallel K1c work costs the race nothing in rotations (arithmetic-deterministic) and negligible wall.

Next delivery (Claude): an in-harness `--arm tangent --scale N` that builds the pool and allocates at the actual insertion state, removing the mismatch above; `k1c_gauge.py`, the gauge-orbit factory.

---

## 4. Strategic reframing

### 4.1 Two goals that had been conflated

**Goal A: compile a molecule already solved exactly, cheaply.** The target is known; the question is cost to a certified chain. This is what K1b-T4 and the H6 races test. The tangent warm start, which needs the exact state's residual, answers it without learning.

**Goal B: predict the wavefunction, as a chain, for a molecule not yet solved.** Nothing in K1c tests it. The retrained pool model uses post-joint features and so needs the target. K1b's pred, with Hamiltonian-only features, is the only goal-B-capable model in the program, and its 18.9 percent is the only goal-B number that exists.

### 4.2 The three-phase sequence for anyone who receives the data

Phase 1, requires the exact state (Seneca): choose a configuration; solve exactly within the envelope; compile to a certified chain; derive labels (the field at the post-joint state, the invariant core, reduced density matrices, natural occupations); generate the gauge orbit; package Hamiltonian features against labels.

Phase 2, solved molecules only: train Hamiltonian features to labels; validate on held-out solved molecules by racing the predicted field as a warm start in rotations, with tangent as the ceiling.

Phase 3, unsolved molecule: compute Hamiltonian features; predict the field; the operator set is the whole ansatz applied to the reference (no support, so no routed prefix); fit angles variationally against the energy or the Schrodinger residual, classically inside the envelope and on a quantum device beyond it; certify by the variational energy and the Schrodinger residual norm, which certify an eigenstate, not by itself the ground state. Whether the variational mode lands on the certified states is K2-VAR's registered question.

### 4.3 Convention (gauge)

The exact state is unique; its factorization is not. Routing order, greedy criterion, growth batch, plateau threshold, pool seeds, tie-breaks, and orbital basis each change the chain without changing the state. Measured: two legitimate N2 compiles share 49 percent of content (F1 0.492); H8 has been certified by chains of 6333 and 7113 letters. Order is almost entirely convention (Chen, Cheng and Freericks 2021 state ordering dependence in print); angles inherit it; content is about half convention with an invariant core. The field is expected to carry less gauge than the chain (Claude's expectation, to be measured under perturbed prefixes).

### 4.4 What the chain is for, use by use

| use | status |
|---|---|
| certificate: replayed on an independent machine to 1e-12 | unchanged |
| the exact wavefunction in executable form; source of every observable label | unchanged |
| the state-preparation circuit for the quantum-computing customer | unchanged |
| raw material for the field labels and the gauge orbit | new, required |
| the learning target itself (content, order, angles) | demoted: "learnable sequences" as literally stated is retired; "learnable gradient fields derived from certified sequences" replaces it |
| process supervision (DV-PS) | untested; the auxiliary target should be the derived field or the invariant core rather than raw chain content |

### 4.5 Corrections to earlier framing in this record

Claude's suggestion list of 6 September: item one (score the full pool) was right in principle and wrong in detail (the right universe is the round-one pool, one-eighth the size); item two (shape times scale) survives with scale unsolved; item five (the tangent score) was named at the greedy state and is decisive only at the post-joint state; the copy-head design was built on a falsified mechanism; every F1-based claim of a learned advantage was true in F1 and false in cost. The first `k1c_model.py` (full-universe, greedy-state) reached F1 0.02 on H4-to-H6 and is superseded; recorded as a negative result.

---

## 5. The research program (Claude's proposal, 9 Sep)

**Unifying idea.** Gauge freedom is a generator of physically exact equivalences: any state admits as many certified factorizations as one cares to produce, by perturbing compiler conventions (discrete) or rotating orbitals (continuous). Contrastive learning over gauge orbits, positives from one state's orbit and negatives from other configurations, forces an encoder to discard route, convention and basis and keep what is invariant, which is the physics. Unlike image augmentations, these augmentations preserve the label to 1e-12 with proof. The probe: does the embedding of a held-out molecule predict energy, natural occupations, multireference character and spin gaps better than the Hamiltonian features do.

**Three programs.**
1. Learn the gauge: exact canonicalization of commuting blocks (no learning) and measurement of the residual gauge; same-state classification whose inner representation is the invariant embedding; learn which gauge yields the shallowest circuit, which is circuit optimization for the quantum-computing customer trained on certified equivalences.
2. Learn commutativity: build the model on the commutation graph (nodes are operators; edges connect non-commuting pairs; edge features from shared indices and integrals); the exact combinatorics are the inductive bias and only magnitudes are learned; the natural output is the field (goal B) and the natural reformulation of ordering is minimum-fill-in ordering.
3. Learn representation-independent observables: reduced density matrices, cumulants, natural occupations, orbital-pair mutual information, spin and charge correlation functions, exact spectral data; the labels the DV-LC learning curves should use and the probes the encoder is judged by.

**Scaling to millions.** By breadth of Hamiltonians and depth of gauge, not count of molecules: lattice and model Hamiltonians (Hubbard, extended Hubbard, PPP, impurity models) across continuous parameters, each solved exactly within the envelope, each with a gauge orbit; the selected-CI front end for molecular envelope growth.

**First tests.**

| step | what | decides | cost |
|---|---|---|---|
| 1 | gauge-orbit factory on Tier A (perturbed conventions, orbital rotations) | invariant core after exact canonicalization; gauge of the field | days |
| 2 | fidelity scoring against the corpus | internal tool (Logan's decision) | days, no learning |
| 3 | contrastive encoder on gauge orbits, probed on held-out H8, N2, C2 | whether invariant physics is learnable from factorizations | weeks |
| 4 | commutation-graph field predictor, Hamiltonian-only, scored in rotations against tangent | goal B | weeks |
| 5 | lattice-model corpus expansion | the millions | ongoing |

**Goal B start plan.** Stage 0 (days): trees or a small MLP on the full universe with invariant Hamiltonian-only features, labels from the pool caches (Tier B pools to be built), H4 and H6 to train, H8 prediction frozen unscored. Stage 1 (two to four weeks): the commutation-graph network. Both race on H8 inside the registered K1c-T4 race after its freeze. Deployment (variational mode) is K2-VAR, after 30 September.

---

## 6. Commercial evaluation (9 Sep), with Logan's decisions applied

**What changed.** Cost of goods forecast to fall about tenfold pending H8 (unit economics, not a product). The learned-compiler story as pitched is replaced by a compiler that warm-starts itself plus a defined research bet. The referee position gained an instrument, fidelity scoring.

| product | who buys | willingness-to-pay evidence | moat | time to revenue | Logan's decision |
|---|---|---|---|---|---|
| fidelity scoring and certification | quantum-computing groups; wavefunction-method developers | none yet; adjacent: certified reference products are paid | exact states in strong correlation | months | **internal tool now; publication is a separate effort** |
| certified reference data (DV-LC line) | AI-for-chemistry builders | none; bulk DFT data is free | exactness plus certificate | months to a year | **byproduct only; not a mainline product** |
| gauge-optimized circuits | quantum hardware and software companies | depth is their constraint; no one else has certified equivalences | unique data | six to twelve months of R&D | after the gauge factory |
| gauge orbits as augmentation data | foundation-model builders | none; novel category | certified equivalences | after step 3 | after the gauge factory |
| invariant embeddings, backbone | the same builders | none; contested space | the augmentation engine, if step 3 shows signal | a year or more | **later; predicated on the two items above** |
| goal-B learned compiler, learned VQE initialization | quantum-computing customer | none | field labels only Seneca can make | a year or more | **start now (stages above)** |
| compiler cost reduction | Seneca | n/a | n/a | immediate | in force pending H8 |

**Verdicts.** Viable as a company that exists: yes. Viable as a business: requires paying customers, of which there are zero conversations. Marketable: more than before; the sentences are testable and none waits on a verdict. Profitable: as a grants-and-design-partners company, plausibly; at venture scale, only if the backbone line succeeds. Capitalizable: pre-seed and non-dilutive now; seed on good terms needs one paying customer and one learnability result (contrastive probe or goal B on H8).

**Falsifiers.** Quantum-computing groups will not pay for fidelity certification; buyers accept DFT error; the encoder learns nothing beyond energy; the field cannot be predicted across sizes; the front end does not extend the envelope past competitors. Each narrows the company; none kills the compiler or the corpus.

---

## 7. Other threads in this period

- **DOE Genesis Mission SBIR pitch** (due 10 Sep 2026, 2 PM ET, via AMP; text only; no proprietary detail; one optional bibliography PDF): title changed by Logan to "Automated Compilation of Exact Quantum States into Learnable Sequences for Foundational Models and Quantum Resource Estimation and Validation"; Summary (97 words), Technical Promise (199), Commercialization (198) drafted in the DOE example's register; Team Qualifications, bibliography PDF, and AMP access confirmation were open. The pitch remains accurate at its level of generality after the K1c findings.
- **Activate Fellowship Cohort 2027** (opens 15 Sep): interest form, fit email to apply@activate.org, Anywhere versus Berkeley, principal applicant, laboratory-access answer as compute.
- **NVIDIA Inception** profile text delivered (956 characters); GPU value depends on the kernel rewrite and data-center FP64; the harness is single-threaded, so threading is the cheaper first speedup.
- **Company rename** to Seneca Labs recorded; federal submissions must use the legal entity name.
- **Plan documents delivered:** Product Strategy Addendum B (registers DV-LC and DV-PS, decouples D3 from the K1 verdict, sequencing DV before K1c); K1 Pre-registration Addendum B (D3 decoupling, ledger items including the non-positive-B2 rule and the single-seed statement); DV pre-registration draft. NPE per scan, the C2 singlet-triplet gap, and natural occupation numbers were proposed as DV-LC observables.
- **Market research** on who pays for computed reference data was launched; results pending and to be read against Section 6.
- **Marketplaces:** none of Toloka, DataAnnotation, AlphaSense, Massive, AWS Data Exchange, Shaip, Bright Data fit; discovery venues that do: PennyLane Datasets, MolSSI QCArchive, Materials Data Facility, the Argonne dataset list, Zenodo, gated Hugging Face; the Genesis Mission platform's provenance requirements match the certificates.
- **Delta-training a SOTA model** was evaluated and not pursued: the basis and model-space mismatch between minimal-basis exact references and triple-zeta real-space models makes the delta a mixture rather than a correlation correction; the reliability-layer variant was declined by Logan.

---

## 8. Forecasts on record (to be audited by name)

| forecast | made | value |
|---|---|---|
| tangent warm start on H8, post-joint, pool-sized proposal | 9 Sep, Claude | 85 to 97 percent saving, central 92 |
| b2 final cost | 8 Sep, Claude | bimodal: about 9.6e12 if round 7 reaches the gate, about 1.15e13 if a round 8 is needed; pred clears the comparative clause at about 40 percent |
| same-platform determinism of cold on ring_19 | 8 Sep, Claude | identical on repeat |
| the field carries less gauge than the chain | 9 Sep, Claude | expectation, unmeasured |

---

## 9. Open items and discipline

- Confirm same-platform determinism of cold on ring_19 (repeat run).
- Deliver the in-harness tangent arm and the gauge-orbit factory.
- Build Tier B pool caches; freeze the K1c pre-registration after the K1b scoreboard closes; arms all post-joint: cold, tangent at scale-law size, tangent at pool size, pool-all, model, goal-B stage 0, oracle_content; pass criterion in rotations; named risks: the scale law at 12x extrapolation, symmetry ties.
- H8 is a one-touch test system for every frozen model; the H8 pool containment look is ledgered here as a design input with pool width fixed beforehand from N2.
- Ledger lines still owed: platform-reproducibility scope; exit-rule variance; the H8 pool look.
- The K1b scoreboard closes on oracle_content; the three-file commit and ledger entry for b2 come first.
- Customer conversations: five, with quantum-computing groups, using only banked claims, this month (Claude's recommendation; Logan deferred grants and commercial actions).

---

*Measurements in this document were produced on Logan's campaign machine (Windows, PowerShell 5.1) and in Claude's Linux sandbox from the public repository at haclep/tucc-chain-compile; where they differ, both values are given. Proposals and forecasts are Claude's. Decisions are Logan's and are marked as such.*

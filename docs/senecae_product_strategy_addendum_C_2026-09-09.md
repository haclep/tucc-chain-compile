# Addendum C to the Product Strategy Memo — Product Line Decision and DOE Pitch Record

**Project:** tucc-chain-compile | Seneca Labs
**Date:** 9 September 2026
**Amends:** `senecae_product_strategy_2026-08-30.md`, Addendum A (30 Aug), Addendum B (7 Sep)
**Companion record:** `k1c_discoveries_and_strategy_record_2026-09-08.md`
**Status:** decisions in Sections 1 and 3 are Logan's and are in force; drafts in Section 3 are final as submitted unless noted; the rest is Claude's record and recommendation.

---

## 0. Scope

This addendum banks three things: the product-line decision taken on 9 September after the K1c findings, the DOE Genesis Mission pitch decision (two pitches, two topics) with the final texts, and the external-claims discipline that governs every document from here on. It supersedes the product ladder of the base memo where the two conflict (Section 2).

---

## 1. Product-line decision (Logan, 9 September 2026)

| tier | product | what it is | customer |
|---|---|---|---|
| **Main** | Certified equivalence families as training data | For each exactly solved state, many certified factorizations produced by varying compiler conventions and orbital basis; every member reproduces the same state to 1e-12 with a replayable certificate. Training data that any materials or chemistry model can absorb, teaching it which differences are physical and which are bookkeeping | builders of AI models for materials and chemistry |
| **Main** | Pre-trained model of correlated electrons (invariant representation) | An encoder trained on the equivalence families to discard convention and basis and keep the physics; delivered as a model others build on | the same builders; national-lab AI programs |
| By-product | Learned compiler / learned initialization for variational quantum algorithms (goal B) | A model that predicts, from the Hamiltonian alone, the operator set and weights an unsolved molecule needs; angles fit variationally; certified by energy and Schrodinger residual | quantum-computing groups |
| By-product | Gauge-optimized circuits | Choosing, among certified equivalent factorizations, the one with the least depth or gate count | quantum hardware and software companies |
| By-product | Certified reference data (DV-LC line) | Exact labels, reduced density matrices, natural occupations, observables, sold as reference and evaluation sets | AI-for-chemistry builders |
| **Internal toolkit** | Fidelity scoring and certification | Overlap of any method's state or circuit with the certified exact state; the referee's instrument | Seneca, for development and publication; not a product |

Rationale as recorded: the main products are the only ones that use the corpus's unique property, certified equivalence, directly; the by-products fall out of building them; the toolkit certifies every family member and is needed anyway. Grants are to fund by-products and toolkit non-dilutively; the main line is the investor story.

---

## 2. What this supersedes

- The base memo's data-first ladder (D1 certified chains, D2 exact amplitude sets, D3 process-supervision data, D4 verification data) is replaced by the tiers above. D2 and D4 survive as the DV-LC by-product and the internal toolkit respectively. D1 as a chain product is absorbed into the equivalence families. D3 as "process supervision on raw chains" is retired; its successor is the invariant representation.
- "Learnable sequences" as a product claim is retired. The sequence is not the learning target; the family of equivalent sequences is. The phrase does not appear in any external document from this date.
- The referee positioning remains true and remains the company's stance, but its instrument (fidelity scoring) is an internal toolkit rather than a product line.
- Addendum B's DV experiments remain registered; DV-PS's auxiliary target should be the invariant core or derived field rather than raw chain content (see the companion record, Section 4.4).
- K1b-T4 continues to completion on its own schedule; its result informs the goal-B by-product and nothing in the main line.

---

## 3. DOE Genesis Mission SBIR pitch decision (Logan, 9 September; due 10 September 2026, 2 PM ET)

**Decision:** submit two pitches. Pitch A on Topic 3 (Designing Materials with Predictable Functionality) carries the main line. Pitch B on Topic 2 (Realizing Quantum Systems for Discovery: AI for Quantum Computing and Networking) carries the by-products and the toolkit. DOE permits up to three pitches per company on any combination of topics, with only the last three reviewed.

### 3.1 Pitch A, Topic 3 — final texts

**Title**

Certified Equivalence Classes of Exact Correlated States as Training Data and an Invariant Representation for Predictable Materials Properties

**Summary, Topic, and Mission Alignment (99 words)**

AI models now design catalysts, batteries, and magnets, but they are trained on approximate quantum chemistry that fails where those materials are hardest: strongly correlated electrons. Seneca Labs solves small molecules exactly and compiles each exact state into a certified sequence of quantum operations. Every state admits many certified equivalent sequences, and a model trained to see through those equivalences learns the physics rather than the bookkeeping. We deliver that data and the resulting representation as a backbone for property prediction, serving the Designing Materials with Predictable Functionality topic and the Genesis Mission's goal of trustworthy AI for discovery.

*(Note: "backbone" appears once here; if the reviewer-facing rule of Section 4 is applied strictly, replace "as a backbone for property prediction" with "as a pre-trained model others build on".)*

**Technical Promise (199 words)**

**Significance.** Catalysts, batteries, and magnets are governed by strongly correlated electrons, and the AI models that design them learn from density functional theory, which fails there. Those models train on over a hundred million approximate calculations, locking in errors. Exact signal must arrive during training; none exists at scale.

**Innovation.** Our compiler writes an exactly solved state as a sequence of quantum operations reproducing it to one part in a trillion, with proof. The sequence is not unique: distinct compilations of one state yield distinct certified sequences; only what they share is physics. We generate each state's family of equivalent sequences by varying conventions and basis, then train a model to tell physical differences from bookkeeping, as image models learn from rotated copies; ours are exact. The products: training data any materials model can absorb, and a pre-trained model of correlated electrons others build on.

**Feasibility.** The compiler, its certificate, and 116 certified systems exist. Generating the families is repeated compilation of solved states: bounded compute, no new physics. Phase I delivers the families, the pre-trained model, and a held-out test against standard inputs on energies, spin gaps, and correlation strength, within its period and budget.

**Commercialization Potential (193 words)**

Groups building AI models for materials train on the largest datasets they can get, and the largest are free: over a hundred million density functional calculations released openly. What no one can get is training signal that is correct where those calculations fail, and a representation that stays trustworthy there. Our products are complementary to theirs: augmentation data that teaches an existing model which differences are physical and which are bookkeeping, and a backbone representation of correlated electrons that plugs into their architectures. Because we hold exact states, verification and circuit-cost tools for quantum computing groups follow as by-products.

To our knowledge, no one sells certified equivalence classes of exact states; the category is new, which is both our opening and an honest risk. The product is digital, so there is no physical supply chain. We will sell directly, first through design partnerships with two or three model-building groups who test the backbone on their own benchmarks, then as licensed datasets and model weights; quantum computing groups are a second channel for the by-products. Phase I includes customer discovery interviews with both groups, and revenue begins with pilot licenses.

*(Note: contains "augmentation data" and "backbone" twice; apply the same plain-language substitutions as the Technical Promise if desired: "training data any materials model can absorb" and "a pre-trained model of correlated electrons others build on".)*

**Team Qualifications (draft; word limit to be checked in the portal)**

Seneca Labs is two founders. Logan Xu (PhD, physics, Georgetown) is a co-author of the factorized unitary coupled-cluster construction this compiler automates and of subsequent work in Physical Review X and Nature Materials on strongly correlated quantum chemistry. He spent eighteen months in quantitative model validation at Ernst & Young, the discipline behind the pre-registered, ledgered experiments that produced every number in this pitch. He built the compiler and its certification. Huakun (Quin) Hu (PhD, computational chemistry, University of Minnesota) leads the chemistry front end that extends the corpus beyond exact diagonalization. The compiler, the 116-system certified corpus, and the benchmark suite exist today and were produced entirely by this team.

### 3.2 Pitch B, Topic 2 — edits to the 8 September drafts

- Title: "Certified Compilation of Exact Molecular States: Verification, Resource Estimation, and Learned Circuit Optimization for Quantum Simulation".
- Technical Promise: replace the two sentences on "a worked solution an AI can study" and the sixtyfold/tenfold oracle results with: "Because each state admits many certified equivalent sequences, machine learning is applied to choosing the shallowest circuit among them and to initializing variational algorithms on unsolved molecules." (The sentence citing the warm-start rate is withdrawn under Section 4.)
- Commercialization: quantum computing teams lead; "revenue begins with pilot verification and resource-estimation licenses."
- Summary: "and is a worked solution AI can learn from" becomes "and has many certified equivalents from which the cheapest circuit can be learned."

---

## 4. External-claims discipline (in force from 9 September)

1. No ongoing or unpublished test appears in any external document. This excludes, until written up: the K1b-T4 arm results (18.9 percent; oracle 99.85 percent), the H6 twelve-system warm-start race (89 to 98 percent), pool containment statistics, and every forecast.
2. Settled facts that may be stated: certification to one part in a trillion with a replayable certificate; 116 certified systems; non-uniqueness of the factorization (distinct compilations of one state yield distinct certified sequences), measured.
3. Statements are made precisely and without hedging. No "to our knowledge" in technical claims (the phrase survives only in the Commercialization market claim, where it is accurate and protective).
4. Internal jargon is not used with external readers: "augmentation data" is "training data any model can absorb"; "backbone" is "a pre-trained model others build on"; "equivalence class" is "family of equivalent sequences"; "gauge" is "convention".
5. Method is described in the present tense as method; completion is claimed only for what exists.

---

## 5. Downstream implications

**NVIDIA Inception product page.** Update from a single compiler entry to the engine plus the two main products; the NVIDIA-use statement gains a real GPU workload (training the invariant representation).

**Activate Fellowship (opens 15 September; close date unpublished; fellowship begins 1 June 2027).** Technical Vision and Technical Reality are built on the main line under the Section 4 discipline. Laboratory access is answered as compute. Principal applicant: Logan. Community: Anywhere by default, Berkeley considered for Berkeley Lab compute.

**Y Combinator Winter 2027 (deadline 2 November 2026, 8 PM PT; decisions by 11 December; batch January to March 2027 in San Francisco, in person).** YC's strongest predictor is momentum: a launched thing with users. The plan is to have a public sample family set and the fidelity toolkit in use by two or three groups before 2 November. YC's standard deal ($500K) is under Activate's $2M cap; Activate's "already on a successful path" concern and YC's in-person requirement are to be weighed consciously.

**Research sequence.** Gauge-orbit factory first (safe; produces data regardless of outcome). Fidelity toolkit alongside. Contrastive representation and its probes next. Goal-B stage 0 as a by-product on the same caches. K1b-T4 to completion; K2-VAR after 30 September; DV as registered.

---

## 6. Summary of changes

| item | status |
|---|---|
| Product tiers (main, by-product, internal) | decided; in force |
| Base memo product ladder D1–D4 | superseded (Section 2) |
| "Learnable sequences" as external claim | retired |
| DOE: two pitches, Topics 3 and 2 | decided; texts final in 3.1, edits in 3.2 |
| External-claims discipline | in force |
| Inception, Activate, YC | to be updated per Section 5 |

---

*Decisions are Logan's. Texts in Section 3 are as finalized with Claude on 9 September 2026. Notes in italics are Claude's and are optional.*

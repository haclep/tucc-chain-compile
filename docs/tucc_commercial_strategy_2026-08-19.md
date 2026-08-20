# Commercial Strategy and Vision

**Project:** `tucc-chain-compile` / exact dUCC chain compilation
**Author of record:** Logan Xu
**Date:** 19 August 2026
**Status:** Working strategy memo. Supersedes the Procopius v2 seed deck framing.

---

## 0. Executive summary

The commercial thesis has moved through three framings during this analysis. The final one is:

> **We industrialize exact quantum ground truth, and we sell the representation that makes it learnable.**

Three claims support it, and each is falsifiable:

1. **The market for computational chemistry *software* is small (~$1.7B in 2026, ~$4.4B by 2034). The market for *ground truth that trains models of matter* is roughly an order of magnitude larger and growing several times faster.** Which market we are in is a framing choice, and it sets the ceiling.
2. **The "quantum-accurate energy data" layer is already crowded. The "structure of the correlation" layer is empty.** Every competitor sells or predicts energies. Nobody sells the operator decomposition that produced the energy. That gap is the whole company.
3. **Our compiler emits training trajectories, not just labels.** One expensive exact solve yields thousands of supervised `(state, operator, angle) → next state` examples. That is process supervision for quantum chemistry, and no one else in the field has a mechanism that produces it.

The rest of this memo lays out the evidence, the competitive landscape, an honest grading of our edge, the product sequence, the five-year outlook with probabilities, and the single experiment that decides whether any of it is real.

---

## 1. The reframe: we are not in the FCI business

The earlier framing — "the oracle is the moat," where the oracle was the ability to produce FCI-grade data — is wrong and would not survive a technical investor.

We are not the best in the world at producing exact eigenstates and will not become so. Block2 (DMRG), Dice (SHCI), NECI (FCIQMC), and ph-AFQMC all reach active spaces vastly larger than a dense Davidson at CAS(8e,8o). That gap represents twenty years of other people's engineering and is not closeable by us.

**What is uncontested is the layer above the solver.** Given a state — from *any* solver — we can:

- compile it into an ordered chain of rank ≤ 2 dUCC factors, certified exact;
- translate that chain exactly into conventional CC amplitudes, including the higher-body content that truncated CC discards;
- emit every intermediate state along the way;
- attach a two-route certificate and last-digit-reproducible provenance to all of it.

Freericks (Symmetry 2022) states in print that the operator algebra is too daunting by hand and tractable only automated. We are the party that automated it, at 4,900 determinants.

This reframe does three things at once. It removes the "compilation free-rides on FCI" referee objection from the flagship paper (FCI is the *input* by design). It makes us a complement to the Block2 / Dice / PySCF / AFQMC ecosystem rather than a hopeless competitor. And it makes a small team viable, because we consume other people's compute instead of racing it.

---

## 2. Market sizing

### 2.1 The market we are *not* in

The computational chemistry software market is projected to grow from about **$1.74B in 2026 to $4.44B by 2034**, split among Schrödinger, Dassault Systèmes, Chemical Computing Group, Q-Chem and others. Adjacent "molecular modeling" estimates range from under $1B to nearly $11B depending on the research house, which itself indicates the reports are low quality.

Selling a comp-chem tool into this market caps out, realistically, at a good hundred-million-dollar company over a long horizon, against incumbents with thirty-year head starts. This is the correct read and it is why the narrow "sell chains to quantum computing vendors" thesis was abandoned.

### 2.2 The market next door

- Roughly **$10B/year** flows into AI training-data providers.
- Approximately **28 startups in that sector generate ~$8.5B combined annual revenue** against combined valuations approaching **$100B**.
- Mercor: **$2B annualized revenue, in talks at a $20B valuation**, having doubled in under a year. Handshake went from single-digit millions in early 2025 to roughly **$1.1B annualized by April 2026**. Surge reportedly in talks at $25B.
- The operative logic, per Mercor's own leadership: *frontier model builders treat data spend as a direct input to model performance, not an operating cost. As long as they spend less on data than the revenue it generates, they keep pulling the lever.*

### 2.3 The AI-for-science adjacency

- **Periodic Labs**: $200M seed, $350M Series A at >$1.3B, and by May 2026 in advanced talks at a **$7.5B valuation** on a round of at least $500M, significantly oversubscribed — with essentially no revenue.
- **Lila Sciences**: $550M raised, $1.3B valuation.
- Collectively, **AI-materials startups have raised over $1.3B in two years.**

Their shared thesis, in Periodic's own words: LLMs have exhausted the internet as a data source, so new ground truth must be *generated*. Periodic and Lila generate it with furnaces and robots — slow, capital-heavy, physical.

**There is a second infinite source of true data about matter that needs no furnace: the Schrödinger equation itself.** The only reason it is not used as a data factory is that exact solution costs exponentially. That is the arithmetic we attack.

### 2.4 The stated demand

The MLIP literature names its own bottleneck explicitly: current work fails to impactfully utilize MLIPs because of **overreliance on DFT for training data creation**, and requires higher-quality datasets using more accurate methods such as coupled cluster theory.

Two useful de-risking findings from that same literature:

- Multi-fidelity training works: **high-fidelity energies combined with low-fidelity forces perform nearly as well as high fidelity for both.** Our current lack of analytic gradients is therefore less disqualifying than it first appears.
- The field is currently climbing DFT → CCSD(T). Our regime is where **CCSD(T) itself fails**. That is one rung further up: uncontested, smaller today, and we would be selling slightly ahead of demand.

---

## 3. Competitive landscape

### Tier 1 — The giants, and they give it away free

| Asset | Owner | Scale | Price |
|---|---|---|---|
| OMol25 | Meta FAIR | >100M DFT calcs @ ωB97M-V/def2-TZVPD, billions of CPU core-hours | Free |
| OMol25 Electronic Structures | Meta + Argonne | ~500 TB: raw DFT outputs, densities, wavefunctions, MO info, >4M calcs | Free |
| QCML | Google | 33.5M DFT + 14.7B semi-empirical | Free |
| THEMol | ByteDance | Torsion/Hessian/energy corpus on HuggingFace | Free |

**Implication: the price of DFT-grade quantum chemistry data is zero and will stay zero.** Hyperscalers commoditize the data layer deliberately in order to compete at the model layer.

**But note what none of it contains.** All of it is DFT. Meta's own paper concedes only double-hybrid functionals consistently outperform ωB97M-V, at prohibitive cost. **No large corpus exists that is beyond-DFT in the strongly correlated regime** — because nobody can afford to make one.

### Tier 2 — Direct competitors: small, early, already on the adjacent thesis

- **Simulacra AI** (London / Chicago) — closest competitor. Explicitly markets a "Large Wavefunction Model" and sells quantum-accurate synthetic data. Benchmark claims: 15–50× lower data-generation cost vs. a Microsoft pipeline at parity energy accuracy; 2–3× vs. traditional CCSD at amino-acid scale; investor materials claim ~29× cheaper than Orbformer and 100–1,000× beyond 30 atoms. Funding: **~$2M**. Small team.
- **QSimulate** (Boston) — founded by Toru Shiozaki and **Garnet Chan** (author of Block2). **$11M total**, in collaborations with Google, Mitsui, JT Pharma, and five of the world's top 20 pharmaceutical companies.
- **Qubit Pharmaceuticals** — FeNNix-Bio1, a foundation model built entirely on synthetic quantum chemistry generated on exascale supercomputers.
- **Academic front**: Orbformer (pretrained on 22,000 structures, the only method consistently converging to chemical accuracy on hard bond dissociations), FermiNet / Psiformer (DeepMind), QERNEL ("Large Electron Model").

### Tier 3 — The empty layer

Every player above sells or predicts **energies**, sometimes forces and densities. **Not one produces a structured decomposition of the correlation itself.** Nobody sells chains, because nobody has a compiler.

### Honest read

The "quantum-accurate energy data" layer is **crowded and getting more so**. The "structure of the correlation" layer is **empty**. Crowded means we are late. Empty means demand is unproven. Both are genuine risks and should be named unprompted in any investor conversation.

---

## 4. The asset

### 4.1 What exists today

- A working, resumable chain compiler producing certified-exact ordered dUCC decompositions.
- A constructive CC translator (Wick's theorem) mapping chains to exact amplitudes.
- Banked certified systems: C₂ at CAS(8e,8o) equilibrium (3,202 factors, ~6e-15 residual); H₂O symmetric dissociation at CAS(8e,6o); N₂ triple-bond series at CAS(10e,8o); matched H₆ chain/ring scans; H₈ chain and ring dense references; LiH full dissociation scan; H₄ and H₁₀.
- A C0–C3 certificate chain, two-route certification doctrine, self-stamping provenance, and reproduction verified digit-identical across a week of library commits.
- Measured empirical laws: rank-cost (4^r + 2 monomials, verified r = 1–4), fill-in, block, molecular K-sector, dip-then-recovery, degenerate-mixture detection, 4n/4n+2 aromaticity at FCI, constant-support pinning (LiH at 69 across the entire scan).

### 4.2 Counting the data correctly

Systems is the wrong unit. **Factors are the unit.**

C₂ alone is 3,202 factors. The H₈ chain campaign reached ~5,600 letters. Across all banked families we are already on the order of **tens of thousands of factor-level training examples**, each a `(partial state, chosen operator, angle)` triple with a fully determined successor state.

For calibration: Orbformer was pretrained on 22,000 structures. We will never approach OMol25 scale (100M calculations, billions of core-hours). But we are within striking distance of *enough to test whether the representation learns at all*, which is the only question that currently matters.

**The multiplier is the point.** One expensive exact solve yields thousands of supervised examples. That is a data-efficiency advantage of roughly three orders of magnitude per expensive calculation over anyone training on energies alone.

---

## 5. The technical bet

### 5.1 The chain is a tokenization of the wavefunction

Every serious neural-wavefunction effort — FermiNet, Psiformer, Orbformer, QERNEL — represents the wavefunction as a black-box continuous function in 3N-dimensional space. Molecule in, number out. You cannot read the structure of the correlation off the weights, and each new system needs its own expensive optimization.

Our compiler produces something categorically different: **an ordered sequence of discrete primitives, each carrying one continuous angle.** Rank ≤ 2 factors are the vocabulary; the chain is the grammar; the angles are the emphasis.

This is a *sequence*, which is the native input format of the entire modern ML stack. And we have already measured that the language has statistics — support pinning along dissociation coordinates, chain-length dip-then-recovery at the Mott crossover, rank cost obeying 4^r + 2, correlation carried by angle rather than length. Those are exactly the regularities a sequence model learns.

### 5.2 The intermediates are process supervision

This is the strongest and most under-weighted asset.

All competing training data is **outcome supervision**: molecule in, energy out. One expensive calculation yields one label.

Our compiler emits a **trajectory**: Hartree–Fock at step 0, the exact state at step N, and every partial product in between — each a legitimate physical state with well-defined energy, support, and correlation content.

The dominant lesson of the last three years of machine learning is that models trained on the reasoning trace beat models trained on the answer, by a wide margin. **Quantum chemistry has never had reasoning traces, because nobody could produce them.** We can.

We are not sitting on a small dataset of hard molecules. We are sitting on a small dataset of *worked solutions*.

### 5.3 The hard objection, and why it is also the moat

**The factorization is not unique.** Many chains produce the same exact state; different routing choices, orderings, and pool restrictions all yield valid decompositions. A model trained to "predict the chain" is therefore learning *our compiler*, not a property of nature. Our own gauge-versus-physics principle already says this: chain composition and translated amplitudes are distinct objects.

Two consequences.

**The worrying one.** Some measured laws may be partly properties of the SD routing rather than of nature. Support pinning is probably physical (a statement about which determinants carry weight). Chain length and dip-then-recovery are more suspect, since they depend on how efficiently the algorithm finds a path. This distinction must be stated precisely in the flagship paper before a referee states it for us.

**The good one.** *Determinism is sufficient for learnability, and we control the convention.* The pipeline is reproducible to the last digit. That makes `chain = f(molecule)` a well-defined function, and a model can learn a well-defined function whether or not it is the unique one. Better still: **defining the canonical chain is the durable position.** SMILES is not the only way to write a molecule as a string; it is the one that got standardized, and that was worth more than any particular algorithm.

Correct framing: we are not discovering the canonical form of correlation. **We are proposing one, first, with a working compiler and a certificate behind every entry.**

---

## 6. Edge and moat, honestly graded

### Real edges

1. **The compiler is unique.** Nobody else can take an exact state and emit a certified ordered chain plus exact CC amplitudes. The theory is public and says it is only tractable automated; publishing the theorem is not building the engine.
2. **Authorship.** Logan is the "Xu" in Xu–Lee–Freericks. Being the named author of the representation is worth real money if the representation is adopted, and costs nothing extra since publication is happening anyway.
3. **Certification discipline.** Two-route certification, self-stamped provenance, last-digit reproducibility. In a data market where supply concentration means buyers lose control over quality and provenance, this is a genuine differentiator — and precisely what a pharma QA function asks for.
4. **The gap in the free corpora is real and structural.** All free data is DFT. Simulacra's is VMC/neural. Strong correlation, done exactly, is covered by nobody.
5. **Trajectory data.** No competitor has a mechanism producing intermediate states.

### Not edges — stop claiming them

- The eigensolver. Block2 and Dice beat it outright. (Note: Chan, who wrote Block2, is a competitor's cofounder.)
- Generic "quantum-accurate data." Simulacra, Qubit, QSimulate, plus free corpora.
- Compute. One workstation.
- Speed. Python.

### The moat, if it exists

**The chain corpus plus the chain model.** Three reasons that survive a skeptic:

- Every entry has a real cost of production and does not leak when the method is published.
- The corpus compounds: each chain is simultaneously a sellable label and a training example.
- If the representation becomes the standard grammar for expressing correlation, authorship is durable in a way that software is not.

**Commercial bonus:** chains are *complementary* to everything on the market. Simulacra sells an energy. A chain contains the energy **plus** the derivation. Their customers are our customers — and so are they.

### The clock

Roughly **18–24 months** before someone with an ML team notices that neural wavefunctions can be compiled into chains too. Defense: corpus depth, publication priority, and getting the certification standard adopted before anyone else defines one.

---

## 7. Product sequencing

Three distinct products hide inside "make an AI-for-science model," with very different odds.

### (a) Molecule → full chain, one shot
The full prize. Predict the chain, recover the exact state, get every observable free. Hardest; requires transfer across system size, which was Orbformer's entire contribution.

### (b) Current state → next factor — **build this first**
A **learned compiler**. Instead of gradient-and-screening search over the operator pool at every step, a model proposes the top candidates and the existing machinery verifies. Far easier: a ranking problem over a discrete pool plus a scalar regression on the angle — a completely standard architecture. Requires **no cross-system generalization** to be useful; it only has to beat the current selector.

**This is the flywheel, stated concretely:** learned selector → faster compilation → more chains → better selector. It converts our throughput bottleneck into a compounding asset without out-scaling anyone. It is also the demo that makes (a) fundable, because a model that has learned to *choose the next factor* has demonstrably learned something about the structure of correlation.

### (c) Molecule → energies and properties directly
Head-on competition with UMA, MACE, Orbformer, Simulacra. We lose on compute and corpus size. **Do not build this.**

### (d) Correlation attribution — uncontested side product
Each factor carries an identifiable amount of correlation energy, so correlation can be attributed to specific orbital interactions. That is a chemically meaningful answer to *why* a barrier is what it is. No energy-predicting model, however accurate, can produce it. Sellable interpretability, zero competition.

---

## 8. Positioning: substrate, not model

We will not build the best general model of molecules. One physicist with a workstation does not out-compete a field where Periodic Labs raises at multi-billion valuations and Meta releases 500 TB for free.

**The better position: make exact solutions cheap enough that everyone else's models train on our output.**

Nvidia, not OpenAI. We do not need to win the model race if every entrant needs our data to run it. That position is available specifically because our representation is *orthogonal* to what everyone else produces.

---

## 9. Customers, ranked by time-to-revenue

| Segment | Horizon | Notes |
|---|---|---|
| **Quantum-computing groups** (Quantinuum, QunaSys, Algorithmiq, Phasecraft, IBM chemistry) | Soonest | Work at exactly our envelope. Need certified exact references and cheap ansatz construction. Buyer is a physicist who can evaluate the claim in one meeting. |
| **MLIP / chemistry foundation-model builders** | Medium, biggest ceiling | Field has named its own DFT bottleneck. Multi-fidelity findings de-risk our gradient gap. |
| **Method developers / academia** | Now, but no budget | Citation and EB-1A market, not revenue. Treat as marketing spend. |
| **Pharma / materials enterprise** | Year 3+ | Needs open-shell, transition metals, gradients, and a vendor track record. |

Revenue lines at maturity: reference-data licensing to model builders; an inference API for the hard tail; enterprise contracts in catalysis, battery chemistry, and semiconductor thermal.

---

## 10. Five-year outlook

**Good case — ~15–20%.** 40–60 people. Open-shell, gradients, periodic systems shipped. C++/GPU compiler consuming DMRG, SHCI, and AFQMC output as front-ends rather than competing with them. The world's only certified corpus of exact chains across strongly correlated chemistry. A chain-prediction model as flagship product. Series B, nine-figure valuation. Not a Periodic Labs.

**Modal case — ~40%.** 15–25 people. A strong, profitable niche data-and-tools business with national-lab and pharma customers. Acquisition by Schrödinger, Dassault, or a foundation-model company that wants the corpus and the person who built it.

**Downside — ~40%.** The chain does not generalize, the corpus finds no buyer. Outcome: a superb series of papers, an EB-1A, and a faculty or industry-research position. Not a catastrophe, and it is the honest floor.

---

## 11. The decisive experiment

The central question can be settled in about a week, on a laptop, with data already on disk.

1. **Within-scan.** Take the LiH dissociation scan (support pinned at 69 across the whole thing — the cleanest signal we have). Hold out one geometry. Train the smallest reasonable model to predict factor *k+1* from `(geometry, partial state, factors 1..k)`. Does it reproduce the held-out chain, or at least rank the true next factor in its top few candidates?
2. **Cross-topology.** Train on H₆ chains, test on an H₆ ring.
3. **Cross-size.** Train on H₆, test on H₈.

**Reading the outcome:**

| Result | Interpretation | Action |
|---|---|---|
| Generalizes across geometry **and** topology | There is a company here | Stop writing papers for a month and raise |
| Works within a scan, not across systems | We have a learned compiler — product (b) | Real business, strong Series A story |
| Fails within a scan | Chains are gauge-noise dressed as structure | Two years saved; return to the research program |

This result, either way, is worth more in an investor conversation than any amount of narrative. Walking in with a curve showing a model predicting factors it has never seen converts a pitch into a demonstration.

---

## 12. Pitch language

### One sentence

> Every AI model of molecules is trained on labels from a physics approximation that's known to be wrong exactly where the hard chemistry is — metals, spin states, bond-breaking — and we can compute the right answer in a form cheap enough to sell.

### One paragraph

> AI is now the default tool for designing drugs and materials, and essentially every model in that stack — Meta's, Microsoft's, the pharma platforms, the AI-scientist startups — is trained on the same source of truth: density functional theory. DFT is an approximation, and it fails precisely where the valuable chemistry lives: transition-metal catalysis, spin states, bond-breaking, battery electrolytes. So the industry is training on labels that are wrong in the hardest cases, with no systematic way to know which ones. Solving the underlying equation exactly would fix it, but the cost grows exponentially, so nobody does it at scale. I've spent six years building the one piece of machinery that changes that arithmetic: a compiler that takes an exact quantum state and reduces it to a short, ordered sequence of elementary rotations — a compact, verifiable, machine-readable description of what the electrons are actually doing. It's the difference between storing a number and storing the reason for the number. Every sequence we produce is both a certified reference label we can sell today into the gap the free datasets don't cover, and — because it's a sequence — a training example for a model that eventually predicts the answer outright. We start as the supplier of verified ground truth where the free data is wrong, and we end up owning the representation everyone else's models learn from.

### Alternate framing for a technical audience

> Language models learned language by reading the internet. Nobody has taught a model the grammar of matter, because nobody could generate the ground truth. We compile exact quantum states into sequences, and we're building the model that speaks them.

---

## 13. Objection handling

| Question | Answer |
|---|---|
| **Who else is doing this?** | Name Simulacra, QSimulate, and Qubit unprompted. They all sell energies; we sell the structure, which contains the energy. Volunteering competitors is the cheapest credibility purchase available. |
| **Do you own the IP?** | Must be resolved before any pitch. "I need to check" ends the meeting. See §14. |
| **Has anyone paid you?** | Not yet — pre-empt by naming the first paid conversation and its date. |
| **Why won't Meta just do this?** | Different objective function: they optimize coverage and scale; this is depth in a regime their functional doesn't reach. True, but it's the answer every startup gives about a hyperscaler. Deliver briefly and move on. |
| **Can you hire the ML half?** | We don't have it. Say so first and ask for the introduction. |
| **Isn't the factorization non-unique?** | Yes. Determinism is sufficient for learnability, and defining the canonical form is the durable position. See §5.3. |

---

## 14. Blockers, in priority order

1. **IP ownership (Emory OTT).** Gates everything: cannot license, sell, raise, or apply for SBIR on IP we may not own. The specific factual question is narrow: was the `chaincompile` codebase written after January 2025, on personal equipment and time, without institutional support? If yes, the claim is weak and we need that in writing. If material work predates departure, a license is required first. **A two-week task blocking an eighteen-month plan — and also blocking the v0.1.0 tag.**
2. **ML co-founder.** We have the physics half of a two-half company. The missing half is the one that makes this venture-scale. A US citizen or permanent resident also resolves the SBIR/STTR 51% ownership requirement.
3. **The decisive experiment (§11).** Nothing else should be prioritized above it.
4. **Envelope scaling.** CAS(8e,8o) is a demo. Path: consume better front-end solvers plus a C++/GPU rewrite. Engineering, not research — therefore hireable, therefore fundable.
5. **Open-shell and gradients.** Not features; the entry ticket to the largest buyer class.

---

## 15. Kill criteria

The company should be abandoned, or converted to a research program, if any of the following resolve negatively:

- **K1 — Learnability.** Chain structure does not generalize even within a single dissociation scan. (Testable this month; see §11.)
- **K2 — Materiality.** No buyer will pay for beyond-DFT labels in the strongly correlated regime. Two paid conversations settle this.
- **K3 — Ownership.** Emory retains a claim that cannot be licensed on workable terms.
- **K4 — Timing.** A funded team publishes chain-style tokenization of neural wavefunctions before our corpus and priority are established.

---

## 16. Sequenced plan

**Months 0–3.** Resolve OTT. Run the decisive experiment. Publish the flagship (JCTC) with the downstream demonstration and an explicit gauge-versus-physics statement. Formally ledger the ~30 existing certified entries. Release the harness publicly under a permissive license as positioning — it is public physics, it commoditizes, and giving it away buys standing.

**Months 3–9.** Build product (b), the learned compiler. Two paid pilots with quantum-computing groups as billed customer discovery. Recruit the ML co-founder. Submit SBIR/STTR Phase I.

**Months 9–18.** Open-shell and gradients, grant-funded — simultaneously the capability build and the entry ticket to the MLIP data market. Begin cross-system chain transfer work toward product (a).

---

## Appendix: sources for market figures

All figures in §2 and §3 are drawn from public reporting current as of August 2026. Principal sources: Fortune Business Insights (comp-chem market sizing); Grand View Research and sector reporting on AI training data; Reuters, Forbes, PitchBook and Contrary Research (Periodic Labs, Lila Sciences); Meta FAIR / Materials Data Facility (OMol25 and OMol25 Electronic Structures); arXiv 2511.07433 and Forbes (Simulacra AI); BusinessWire and C&EN (QSimulate); arXiv 2506.19960 (Orbformer); arXiv 2502.03660 (MLIP DFT-reliance critique). Private-company revenue and valuation figures are estimates and are not independently audited.

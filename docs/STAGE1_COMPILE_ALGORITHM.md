# Stage 1 of the `tucc` compiler: from an exact eigenvector to a rank-≤2 dUCC chain

**Algorithm reference with a fully worked example (four-site Hubbard ring, the XLF 2020 system)**

*Document status:* reference / tutorial. Written 2026-08-18 for `docs/`. Every number quoted in Section 9 was produced by the two scripts named in Section 12 (`hub4_sd_compile.py`, `growth_anatomy.py`), run in a clean numpy/scipy sandbox, and can be regenerated in seconds. The scripts are a compact re-implementation of the Stage-1 logic for exposition; where their conventions might differ from the production driver (`examples/run_big_sd.py`, `chaincompile.sd_routed`, `chaincompile.grow_gn`), the difference is flagged explicitly and collected in the checklist of Section 12.3.

---

## 0. Purpose, scope, how to read

Stage 1 answers one question: given an exact many-electron eigenvector in a determinant basis, produce an ordered product of *primitive* unitary coupled-cluster factors of rank at most two that prepares it from a single reference determinant, exactly, with a certificate. Stage 2 (the exact Wick-algebra translation of that product into conventional coupled-cluster amplitudes) is documented in `METHOD.md` and is referenced here only where its cost law shapes Stage 1.

The document has three layers, and it is safe to read them independently:

- **Concept layer** (Sections 1–4): what a chain is, why one factor is a *batch* of rotations, and why that single fact forces the two-phase design.
- **Algorithm layer** (Sections 5–8): Stage 0 (certified target), Stage 1a (routing sweep), Stage 1b (growth), Stage 1c (certificates), each with pseudocode and the reasoning behind every rule.
- **Example layer** (Section 9): the four-site Hubbard ring at *U/t* = 4, every letter, every angle, every score, every residual, side by side with the hand-built chain of Xu–Lee–Freericks (2020) and with the straight-shot ("direct") construction.

Sections 10–12 collect diagnostics, the genealogy (what is inherited, what is new), and reproduction instructions. Appendix A holds the derivations; Appendix B is a glossary.

Terminology used throughout: a **letter** is one primitive factor $e^{\theta\hat\kappa_\mu}$; a **chain** is an ordered product of letters; the **support** of a state is the set of determinants with coefficient above the amplitude floor; **level** is excitation level relative to the reference; **routed** and **grown** name the two phases that produce letters.

---

## 1. The problem

### 1.1 Input and output

Input: a certified eigenvector

$$|\Psi\rangle=\sum_{D} c_D\,|D\rangle,\qquad \sum_D c_D^2=1,\qquad c_D\in\mathbb R,$$

over an orthonormal determinant basis $\{|D\rangle\}$ (occupation-number strings over $2M$ spin-orbitals), together with a reference determinant $|\Phi_0\rangle$ (in the campaign: the Hartree–Fock determinant of the active space; in the example: the determinant XLF chose).

Output: an ordered list of letters $(\mu_1,\theta_1),\dots,(\mu_n,\theta_n)$ with

$$U=\prod_{k=1}^{n} e^{\theta_k\hat\kappa_{\mu_k}},\qquad U|\Phi_0\rangle=|\Psi\rangle\quad\text{to a certified residual},$$

each $\hat\kappa_\mu=\hat E_\mu-\hat E_\mu^\dagger$ a *single* substitution of rank $\le 2$ (Section 2.3). The certificate is per instance and numerical (Section 1.3); no theorem is invoked to claim exactness.

### 1.2 The fence: three rails

The problem would be trivial without constraints (one dense unitary rotates $\Phi_0$ into $\Psi$). Three rails make it a problem, and each rail is there for a reason.

1. **Only substitution rotations.** A letter may rotate a determinant only into a determinant that differs from it by moving specific electrons between specific spin-orbitals. Arbitrary Givens rotations between arbitrary determinant pairs are not admitted, because they are not UCC factors and have no coupled-cluster translation.
2. **Rank ≤ 2.** Stage 2 prices a rank-$r$ letter at exactly $4^r+2$ normal-ordered monomials (the **rank-cost law**, verified 6/18/66/258 for $r=0,1,2,3$). A rank-8 letter costs $65{,}538$ monomials; a chain of such letters is exact and untranslatable (the measured C₂ direct chain: 61,977 letters, 25,549 of rank 8, 56× the support). The translation's cost law is what fixes the compiler's rank ceiling; the two stages are co-designed.
3. **Uncontrolled rotations.** A physical UCC factor acts on *every* determinant pair that matches its substitution pattern, all with the same angle. It is not a controlled gate acting on one pair. This is the rail that generates all of the actual difficulty (Section 3.3), and it is also what makes the factor translatable.

### 1.3 Certificate currency

The compile residual is the fidelity deficit against the reference in the compile direction (Section 4),

$$R \;=\; 1-\big|\langle\Phi_0|U^\dagger|\Psi\rangle\big|^2 \;=\;\sum_{D\ne\Phi_0}\big(U^\dagger\Psi\big)_D^2 ,$$

with gate $R<10^{-12}$ (the dense driver's currency; the flagship C₂ chain closed at $6.4\times10^{-15}$). Two practical notes. First, computed as $1-\mathrm{fid}^2$ the number floors near $10^{-16}$ from floating-point cancellation, whereas the sum of off-reference squares reads the true value (in the example: $10^{-31}$); both are printed. Second, $R$ is quadratic in the vector error: $R\approx\|\delta\|^2$, so $R=10^{-12}$ corresponds to a vector error of $10^{-6}$ per component and $R=10^{-15}$ to about $3\times10^{-8}$.

---

## 2. Objects and notation

### 2.1 Determinants as occupation-number strings

Spin-orbitals are indexed $p=0,\dots,2M-1$. A determinant is a bit string $D\in\{0,1\}^{2M}$; the canonical state is

$$|D\rangle=\hat a^\dagger_{p_1}\hat a^\dagger_{p_2}\cdots\hat a^\dagger_{p_N}|0\rangle,\qquad p_1<p_2<\dots<p_N ,$$

i.e. creation operators applied in increasing index order (in the example: all spin-up momenta first, then spin-down, matching XLF). Applying $\hat a^\dagger_p$ or $\hat a_p$ to $|D\rangle$ carries the parity sign $(-1)^{\#\{q<p:\;D_q=1\}}$ (Jordan–Wigner counting). Every sign in the algorithm reduces to this rule.

The **level** of a determinant relative to the reference is

$$\ell(D)=\#\{p:\;D_p=1,\;(\Phi_0)_p=0\},$$

the number of electrons sitting outside the reference's occupied set (0 for $\Phi_0$; 2 for a double; 4 for a quadruple).

### 2.2 Substitutions and their generators

A **primitive substitution** is a pair of disjoint spin-orbital sets $\mu=(I,A)$ with $|I|=|A|=r$ (its rank): annihilate the electrons in $I$, create them in $A$,

$$\hat E_\mu=\hat a^\dagger_{a_1}\hat a^\dagger_{a_2}\cdots\hat a_{i_2}\hat a_{i_1},\qquad \hat E_\mu^2=0,\qquad \hat\kappa_\mu=\hat E_\mu-\hat E_\mu^\dagger .$$

$\hat E_\mu$ maps a determinant to a determinant (times a sign) or to zero; $\hat\kappa_\mu$ is real antisymmetric. Note that $I$ need not lie inside the reference's occupied set: letters are *general* substitutions between arbitrary determinant pairs (XLF's $A(1\!\uparrow 2\!\uparrow\leftarrow 0\!\uparrow 3\!\uparrow)$ is such a letter; $3\!\uparrow$ is empty in the reference). The generator satisfies the cubic self-relation $\hat\kappa_\mu^3=-\hat\kappa_\mu$, and therefore (Freericks, *Symmetry* 2022)

$$e^{\theta\hat\kappa_\mu}=1+\sin\theta\,\hat\kappa_\mu+(1-\cos\theta)\,\hat\kappa_\mu^2 ,$$

exactly, three terms, no series. This closed form is why a product of thousands of letters is a finite algebra problem in Stage 2; in Stage 1 its consequence is Section 3.1.

### 2.3 The pool

The **pool** $\mathcal P$ is the set of admissible letters: all primitive substitutions of rank 1 or 2 that conserve the symmetries the Hamiltonian conserves (particle number and $S_z$ always; total crystal momentum $K$ in the example; point-group irreps in molecules). Equivalently, $\mathcal P$ is the set of single- and double-substitution edges of the Hamiltonian's own coupling graph: by Slater–Condon a two-body $\hat H$ couples determinants only through such substitutions, and it does so only within a symmetry sector. Letters outside $\mathcal P$ would carry weight out of the target's sector, where the target has none; they can never help and are excluded (in the example they receive a selection score of exactly zero, Section 7.2). Generators come in $\pm$ pairs, $\hat\kappa_{(A,I)}=-\hat\kappa_{(I,A)}$; one representative is kept and the sign of $\theta$ does the rest.

### 2.4 Pairs, domains, siblings

Fix a letter $\mu=(I,A)$. Its **domain** is the set of determinants with all of $I$ occupied and all of $A$ empty; for each domain determinant $D$ the **partner** is $D'=D-I+A$ with sign $s_p=\pm1$ defined by $\hat E_\mu|D\rangle=s_p|D'\rangle$. The **pairs** of $\mu$ are the disjoint two-element sets $\{D,D'\}$; two pairs of the same letter are called **siblings** of one another. On every determinant that is neither a domain nor a range member, $\hat\kappa_\mu$ acts as zero and $e^{\theta\hat\kappa_\mu}$ as the identity.

*Example.* In the four-site ring the letter $(2\!\uparrow 2\!\downarrow \leftarrow 0\!\uparrow 0\!\downarrow)$ has, inside the $K=\pi$ sector, exactly two pairs: $\{|01\,\bar0\bar1\rangle,\ |12\,\bar1\bar2\rangle\}$ and $\{|03\,\bar0\bar3\rangle,\ |23\,\bar2\bar3\rangle\}$. Rotating one rotates the other, by the same angle.

---

## 3. The atom: one letter is a batch of synchronized plane rotations

### 3.1 A letter on a single pair

On a pair $\{D,D'\}$ with sign $s$, using $\hat E^\dagger_\mu\hat E_\mu|D\rangle=|D\rangle$ and $\hat E_\mu\hat E^\dagger_\mu|D'\rangle=|D'\rangle$,

$$\hat\kappa_\mu|D\rangle=s|D'\rangle,\qquad \hat\kappa_\mu|D'\rangle=-s|D\rangle,\qquad
\hat\kappa_\mu\big|_{\{D,D'\}}=s\begin{pmatrix}0&-1\\1&0\end{pmatrix},\qquad \hat\kappa_\mu^2\big|_{\{D,D'\}}=-1 ,$$

so the three-term exponential collapses to a plane (Givens) rotation by the angle $s\theta$:

$$\begin{pmatrix}c'_{D}\\ c'_{D'}\end{pmatrix}=\begin{pmatrix}\cos\theta&-s\sin\theta\\ s\sin\theta&\cos\theta\end{pmatrix}\begin{pmatrix}c_D\\ c_{D'}\end{pmatrix}.$$

Amplitude is conserved within the pair, $c_D'^2+c_{D'}'^2=c_D^2+c_{D'}^2$. This is the elementary move of Givens QR (Givens 1958; Golub–Van Loan), which is what `chaincompile.factors` implements as "exact block-rotation application".

### 3.2 The closed-form zeroing angle

To annihilate the coefficient of one member of the pair, moving its amplitude entirely into the other:

$$\text{zero } D':\ \ \tan\theta=-\frac{c_{D'}}{s\,c_D},\qquad\qquad \text{zero } D:\ \ \tan\theta=\frac{c_D}{s\,c_{D'}} ,$$

taking the principal branch $\theta\in(-\pi/2,\pi/2]$ (the zeroing condition is $\pi$-periodic). The survivor becomes $\pm\sqrt{c_D^2+c_{D'}^2}$. Two limits are worth naming: when the survivor was already large, $\theta$ is small; when the survivor was near zero, $|\theta|\to\pi/2$, and the coupled-cluster amplitude that Stage 2 will assign to that letter, $t=\tan\theta$, diverges. This is the mechanism behind "correlation is carried by rotation angle, not chain length" along pinned-support coordinates, and behind CC-side amplitudes like the flagship's $t\approx 34$ from $\theta=1.5417$.

### 3.3 The batch, and why it is the whole difficulty

The formula of Section 3.1 is applied *simultaneously* to every pair of the letter, with the same $\theta$ but with each pair's own sign $s_p$. Choosing $\theta$ to zero one coefficient therefore moves the coefficients of every sibling pair as collateral. Three consequences follow, and the algorithm is shaped by all three:

- A rotation that zeroes a determinant can refill a determinant that an earlier rotation zeroed (**collateral**). A single closed-form pass therefore does not, in general, terminate on the reference.
- A rotation whose siblings connect a nonzero determinant to a determinant *outside* the support creates new nonzero coefficients (**fill-in**), which then need letters of their own. With high-rank letters this cascades (the fill-in law; Section 10.1).
- Occasionally symmetry locks a sibling pair to the target pair so that one angle zeroes both (a "gift"; it happens in the example, Section 9.4).

The hand construction of XLF already contains both faces of this: their $\theta_1=\tfrac12\sin^{-1}(4\beta)$ is a transport solve whose $\tfrac12$ and $4$ come from batch coupling, and their $\tan\theta_2=-\tan^2\theta_1$ chooses the quadruple's angle to cancel a determinant that the earlier letters' siblings created. Stage 1 mechanizes exactly those two moves — transport, then cleanup — at scale.

### 3.4 Why not controlled rotations

The quantum-circuit literature preps fixed-particle-number states by Givens elimination with *controlled* single-excitation gates (Arrazola et al., *Quantum* 6, 742, 2022): a controlled rotation touches exactly one determinant pair, has no siblings, and pure elimination finishes. Those gates, however, are not UCC substitution factors and have no coupled-cluster translation, so they are outside the fence of Section 1.2. The uncontrolled letters used here are translatable; the price of translatability is the batch, and the growth phase is how the price is paid.

---

## 4. Directions and bookkeeping

Three vectors live in the same determinant basis and must never be confused.

**Compile (annihilation) direction.** Letters are applied to the eigenvector and drain it toward the reference:

$$v_k=R_k R_{k-1}\cdots R_1\,\Psi,\qquad R_k=e^{\theta_k\hat\kappa_{\mu_k}},\qquad W=R_n\cdots R_1,\qquad v=W\Psi\approx\Phi_0 .$$

The routing tables of Section 9.4 print $v_k$ row by row; their entries are amplitudes, not fidelities. The compile residual is $R=1-v_{\Phi_0}^2=\sum_{D\ne\Phi_0}v_D^2$.

**Preparation direction.** The same letters, order reversed and angles negated, prepare the eigenvector from the reference:

$$\Psi=W^\dagger\Phi_0=R_1^\dagger R_2^\dagger\cdots R_n^\dagger\,\Phi_0,\qquad R_k^\dagger=e^{-\theta_k\hat\kappa_{\mu_k}}\ (\text{apply }R_n^\dagger\text{ first}).$$

Every "preparation chain" listing in the outputs is this reversal; step 1 of such a listing acts first on $\Phi_0$ (it is the rightmost factor of the operator product).

**Prepared state of a partial chain.** For the chain built so far, $w=W^\dagger\Phi_0$ is what the chain currently prepares — its approximation to $\Psi$. Two identities connect it to the compiled vector:

$$v_{\Phi_0}=\langle\Phi_0|W\Psi\rangle=\langle W^\dagger\Phi_0|\Psi\rangle=w\cdot\Psi,\qquad\qquad W(\Psi-w)=v-\Phi_0 .$$

So $v$ measures how far the eigenvector is from having been drained into the reference, and $w$ measures how far the chain's prepared state is from the eigenvector; they are the same information seen from opposite ends of the unitary. Growth (Section 7) works in the $w$-versus-$\Psi$ frame because a new outermost letter is inserted there; its reported residuals are the same $R$.

The example after eight routing letters (Section 9.4) makes the three vectors concrete:

| determinant | $\Psi$ (exact) | $w=W^\dagger\Phi_0$ (prepared) | $v=W\Psi$ (compiled) | $\Phi_0$ |
|---|---|---|---|---|
| \|01 0̄1̄⟩ | +0.651854 | +0.653958 | +0.996782 | 1 |
| \|23 0̄1̄⟩ | +0.097193 | +0.097507 | −0.005512 | 0 |
| \|13 0̄2̄⟩ | +0.194386 | +0.195013 | −0.010712 | 0 |
| \|12 1̄2̄⟩ | −0.135674 | −0.136112 | +0.054321 | 0 |
| \|03 1̄2̄⟩ | +0.097193 | +0.097507 | −0.009788 | 0 |
| \|12 0̄3̄⟩ | +0.097193 | +0.086453 | 0 | 0 |
| \|03 0̄3̄⟩ | −0.651854 | −0.638529 | 0 | 0 |
| \|02 1̄3̄⟩ | +0.194386 | +0.172907 | 0 | 0 |
| \|01 2̄3̄⟩ | +0.097193 | +0.086453 | 0 | 0 |
| \|23 2̄3̄⟩ | +0.135674 | +0.210243 | −0.056862 | 0 |

$w\cdot\Psi=0.996782=v_{\Phi_0}$; $R=1-0.996782^2=6.4\times10^{-3}$; and the quad row shows the collateral the routed letters left (0.210 prepared against 0.136 wanted).

---

## 5. Stage 0: the certified target

Everything downstream assumes the input is a single eigenvector of a single symmetry block. The production driver enforces this before compiling (details in `METHOD.md`, "genealogy and certificates", C0–C1); the summary:

- **Eigensolver hygiene.** Davidson with the seeding policy and the gap-based purity trigger introduced after the C₂ wrong-root incident (a triplet $\Pi$ pair compiled as if it were the ground state; caught by the compiler's chain observables, not by the energy).
- **Degenerate-mixture detection.** An arbitrary rotation inside a degenerate pair spanning disconnected blocks cannot be routed; the compiler sees it arithmetically (stretched C₂: support $1216=2\times608$). `dominant_block_projection` recovers a symmetry-pure vector first (on the stretched-C₂ direct chain: 50,652 letters → 11,967 at residual 0.0).
- **Block law check.** The support must lie inside the H-connected block of the reference (equality in every small system; first strict subset at C₂, 1108 of 1252, the six sub-$10^{-12}$ stragglers being eigensolver dust).

In the example the target comes from dense diagonalization, and Stage 0 reduces to two checks: the ground energy against the closed-form cubic of XLF eq. (10) (agreement to all printed digits), and the support against the symmetry sector (support 10 = the entire $K=\pi$, $S_z=0$ sector; block law with equality).

---

## 6. Stage 1a: the routing sweep

### 6.1 What it does

Givens elimination restricted to the Hamiltonian's coupling graph, in the compile direction: each non-reference support determinant is drained, by one closed-form letter, into a neighbor one step closer to the reference, outermost level first, so that amplitude cascades shell by shell toward $\Phi_0$. Every angle is a formula; no optimization occurs; the sweep is deterministic given the canonical rules.

### 6.2 Pseudocode

```
ROUTE(Ψ, Φ0, pool P, floor ε):
    v ← Ψ ; routed ← []
    S ← { D : |c_D| > ε, D ≠ Φ0 }                       # support minus pivot
    order S by ( −level(D), canonical_index(D) )        # outermost first, then canonical
    for D in S:
        if |v_D| < ε_zero:                               # already killed by a sibling rotation
            log "already zero (collateral) — skipped" ; continue
        candidates ← { (μ, D') : μ ∈ P, {D, D'} is a pair of μ, level(D') < level(D) }
        choose (μ, D') minimizing ( level(D'), −|v_{D'}|, canonical_index(D') )
        θ ← closed-form angle that zeroes v_D by rotating into D'  (Section 3.2)
        v ← apply_letter(v, μ, θ)                       # ALL pairs of μ rotate
        log the sibling pairs that moved
        routed.append( (μ, θ) )
    return v, routed
```

`apply_letter` is Section 3.1 applied to every pair of $\mu$; the letters are recorded in compile order.

### 6.3 The rules and their reasons

- **Outermost first.** Draining high-level determinants first means their letters' siblings act on determinants that are still to be processed rather than on ones already zeroed; it is the analogue of choosing an elimination order that limits fill-in. (The toy shows that even so, collateral lands on already-processed determinants — Section 9.4, letter 2 — which is exactly why growth exists.)
- **Partner: closest level, then largest current coefficient.** Closest level keeps the cascade short (one SD hop inward per letter); among equals, draining into the strongest channel keeps angles away from $\pm\pi/2$ and keeps the sweep numerically tame. The canonical index is the final tie-break; it makes the sweep deterministic, and it is where two runs on symmetry-twin systems can legitimately differ in composition while agreeing on every invariant.
- **One letter per support determinant minus pivot.** Generically each rotation zeroes exactly one coefficient, so routed $=$ support $-1$; the flagship (1107 = 1108 − 1) and the triplet night (1215 = 1216 − 1) both landed this arithmetic as a *prediction*, which is what makes it a diagnostic. When symmetry locks a sibling pair to the target pair, one angle zeroes two determinants and the count drops (example: routed 8 = 10 − 2, Section 9.4). Footnote for the count law: *minus symmetry-locked siblings*.
- **Angle branch.** Principal branch $(-\pi/2,\pi/2]$; angles near the boundary are physics (a near-empty survivor), not a bug (Section 3.2).

### 6.4 What routing achieves, and what it provably cannot

After the sweep the compiled vector has a large reference coefficient and a small remainder scattered over determinants that were zeroed and refilled. In the prepared-state frame this reads: routing has aligned $w$ and $\Psi$ *plane by plane in the planes it used* (zero torque there, Section 7.2), and left misalignment in the sibling planes. The size of that remainder tracks correlation strength, not system size (the $U$-scan of Section 9.9), which is the microscopic content of the record's "growth ratio measures multireference hardness".

Why no closed-form pass can finish in general: routed $=$ support $-1$ is exactly the dimension of the unit sphere the target lives on, so the routed chain has the *minimal* number of parameters and, since its angles were spent zeroing rather than steering, the wrong directions. Worse, the missing directions are typically commutator words of non-commuting SD generators (the toy's connected-quadruple content), which no single pass of one-letter-per-determinant builds. Iterating the sweep is possible but comes with no monotone-decrease guarantee and no convergence theorem. This is the precise sense in which existence (Evangelista–Chan–Scuseria 2019) is not an algorithm.

---

## 7. Stage 1b: growth

### 7.1 What it does

Rounds of *add letters, re-solve angles* until the residual passes the gate. Each round scores every pool letter by how fast the fidelity would rise if that letter were inserted at the growth position, adds the top few, and re-solves the grown angles by nonlinear least squares. The residual falls fast, flattens at the variational floor of the current letter set (the plateau), and the next round adds letters. Its ancestry is the ADAPT family (Section 7.5); what is specific here is the closed-form routed seed, the exactness target, and the certificate.

### 7.2 Pseudocode

```
GROW(Ψ, Φ0, routed, pool P, gate=1e-12, batch=3, freeze_routed=True):
    grown ← [] ; θ_g ← []
    loop:
        chain ← grown ⊕ routed                            # compile order: grown letters act on Ψ first
        v ← compile(chain) ; R ← Σ_{D≠Φ0} v_D²
        if R < gate: break
        w ← prepare(chain)                                # w = W†Φ0
        for μ in P: score(μ) ← | 2 (w·Ψ) (w · κ_μ Ψ) |    # Section 7.3
        exclude μ identical to the letter it would sit next to (chain[0])   # Section 7.4
        picks ← top-`batch` distinct μ by score (ties by canonical order)
        prepend picks to grown (each becomes the first letter applied to Ψ)
        θ_g ← LEAST_SQUARES( r(θ) = off-reference components of compile(chain(θ)),
                             variables = grown angles [ + routed angles if not freeze_routed ],
                             start = current values, new angles = 0 )                # Section 7.6
        log (letters added, R, singular values of the Jacobian)
    return chain
```

### 7.3 The selection score, derived

Insert a candidate letter with angle $\theta$ as the outermost preparation letter; the fidelity is $F(\theta)=(w\cdot e^{\theta\hat\kappa_\mu}\Psi)^2$. Since $\frac{d}{d\theta}e^{\theta\hat\kappa}=\hat\kappa e^{\theta\hat\kappa}$,

$$F'(0)=2\,(w\cdot\Psi)\,(w\cdot\hat\kappa_\mu\Psi)=2\,(w\cdot\Psi)\,\big[(w-\Psi)\cdot\hat\kappa_\mu\Psi\big],$$

the second form because $\hat\kappa_\mu$ is antisymmetric, so $\Psi\cdot\hat\kappa_\mu\Psi=0$. In words: the discrepancy between what the chain prepares and what it should prepare, projected onto the direction that letter can move the state. It is the steepest first-order gain, and it decomposes over the letter's pairs. Writing $\hat\kappa_\mu=\sum_p s_p\big(|D'_p\rangle\langle D_p|-|D_p\rangle\langle D'_p|\big)$,

$$w\cdot\hat\kappa_\mu\Psi=\sum_{p\in\text{pairs}(\mu)} s_p\big(w_{D'_p}\Psi_{D_p}-w_{D_p}\Psi_{D'_p}\big),$$

each term the $2\times2$ determinant of $(w_D,w_{D'})$ and $(\Psi_D,\Psi_{D'})$, i.e. $|w_p||\Psi_p|\sin\varphi_p$ with $\varphi_p$ the misalignment angle between $w$ and $\Psi$ inside that pair's plane — a **torque**. Because routing zeroed coefficients in the planes it used, those planes contribute zero torque; the score therefore reads precisely the misalignment routing left in the sibling planes. Letters outside the pool score identically zero (both vectors vanish on the determinants they touch), which is the numerical form of the pool rule.

*Worked instance (Section 9.5, round 1).* Letter $(3\!\uparrow 2\!\downarrow\leftarrow 0\!\uparrow 1\!\downarrow)$ has two sector pairs. Pair $\{\Phi_0,|13\,\bar0\bar2\rangle\}$: $0.195013\cdot0.651854-0.653958\cdot0.194386\approx0$ (routing letter 3 aligned exactly this plane). Pair $\{|02\,\bar1\bar3\rangle,|23\,\bar2\bar3\rangle\}$, $s=-1$: $-(0.210243\cdot0.194386-0.172907\cdot0.135674)=-0.0174$. Score $=2\cdot0.996782\cdot0.0174=0.0347$.

### 7.4 Selection rules and their reasons

- **Greedy and first-order.** The score ranks *directions at zero angle*; it does not rank *sets*, and the letter with the largest score need not belong to the shortest final chain (Section 9.5 records a case). Rounds, not single letters, are the unit of progress.
- **Batch.** Adding several letters per round amortizes the least-squares solve; the toy uses three (its dimension is nine); the driver's batch is its own parameter (`grow_gn`).
- **Ties.** Exact ties are symmetry twins (letters related by a symmetry of the target); the canonical pool order breaks them. This is a discrete gauge choice: it changes the letter list, not the endpoint (Section 10.6).
- **No adjacent duplicates.** A letter placed next to an identical letter merges with it, $e^{a\hat\kappa}e^{b\hat\kappa}=e^{(a+b)\hat\kappa}$; it adds no new direction to the reachable set. With routed angles frozen, admitting the twin of the adjacent routed letter would silently un-freeze that routed angle. The rule keeps the frozen experiment honest; in the free-angle mode (Section 7.7) it is unnecessary. In the example the twin scores highest in round 1, is excluded, is admitted in round 2 (no longer adjacent), and produces the round's large drop.

### 7.5 Ancestry

The score is the gradient criterion of ADAPT-VQE (Grimsley, Economou, Barnes, Mayhall, *Nat. Commun.* 10, 3007, 2019), where the objective is the energy and the gradient $\langle\psi|[\hat H,\hat A_\mu]|\psi\rangle$; Overlap-ADAPT-VQE (Feniou, Claudon, Hassan, Traoré, Giner, Piquemal, *Commun. Phys.* 6, 192, 2023) keeps the loop and replaces the energy by overlap with a target state, which is $F$ above with $\Psi$ the exact eigenvector. Its older ancestor is matching pursuit (Mallat–Zhang 1993): pick the dictionary element most correlated with the residual. The paper cites the selector; it does not claim it. What is specific to Stage 1 is running it classically against a *known exact* target, seeded by the closed-form routed chain, to an exactness gate rather than to a compact approximate ansatz.

### 7.6 The angle solve as nonlinear least squares

After letters are chosen their angles must be set, and the structure of the problem — an exact zero of a *vector* is wanted — makes it a nonlinear least-squares problem rather than a generic scalar minimization. With $G(\theta)$ the product of grown letters (and, in free mode, the routed letters too),

$$v(\theta)=W\,G(\theta)\,\Psi,\qquad r(\theta)=\big(v_D(\theta)\big)_{D\ne\Phi_0},\qquad \tfrac12\|r(\theta)\|^2=\tfrac12\big(1-\mathrm{fid}^2\big).$$

Gauss–Newton (Nocedal–Wright, *Numerical Optimization*, ch. 10) linearizes $r(\theta+\delta)\approx r(\theta)+J\delta$ with the Jacobian $J=\partial r/\partial\theta$ and solves $(J^{\!\top}J)\,\delta=-J^{\!\top}r$; Levenberg (1944)–Marquardt (1963) adds a damping $\lambda I$ so that far-from-solution steps stay safe. The Jacobian is exact and cheap: with $s_k$ the partial products,

$$\frac{\partial v}{\partial\theta_k}=R_n\cdots R_{k+1}\,\hat\kappa_{\mu_k}\,\big(R_k\cdots R_1\Psi\big),$$

so column $k$ is the compiled vector's velocity when angle $k$ turns; each column costs one pass over the tail of the chain. One residual evaluation is one pass of the whole chain over $\Psi$ (`nfev` in the logs counts these).

**Singular values as the rank diagnostic.** With $J=U\Sigma V^{\!\top}$, the number of nonzero singular values is the number of independent directions in the $(\dim-1)$-dimensional residual space that the current angles can move the compiled vector, and their sizes measure how strongly. If rank $<\dim-1$, the least-squares optimum leaves the component of $r$ orthogonal to the column space untouched ($J^{\!\top}r=0$ with $r\ne0$): that leftover **is** the plateau, the variational floor of a fixed letter set. If rank $=\dim-1$ with a healthy smallest singular value, the Gauss–Newton step is the Newton step for $r(\theta)=0$ and converges quadratically to an exact zero. A near-zero singular value flags redundant letters (adjacent duplicates, symmetry twins) — the letter set cannot finish however long one iterates. This is the numerical form of the tangent-space count of Section 6.4.

**Angles are $2\pi$-periodic**; solutions are wrapped to $(-\pi,\pi]$ so that logs and CC-side $\tan\theta$ values are interpretable.

### 7.7 Frozen versus free routed angles

Two modes are meaningful. *Frozen*: the routed angles keep their closed-form values and only grown angles vary — the closed-form part stays closed-form, and growth alone pays for the collateral. *Free*: routed angles are re-optimized too (initialized at closed form). By parameter counting the free mode reaches the gate with far fewer grown letters (the toy: 2 versus 9), at the price that the final routed angles are no longer the closed-form ones. Which mode `grow_gn` runs is a driver fact to verify (Section 12.3); the growth-ratio law would need re-baselining if the mode changed, since the mode changes what "grown" counts.

### 7.8 Stopping and what "exact" means

The loop stops when $R<10^{-12}$; a final polish typically lands at the floating floor. Exactness is certified per instance (the gate, then Stage 2's translation acceptance), not inherited from a theorem: the ECS existence proof concerns one-factor-per-determinant chains of unbounded rank, and their own negative result says single SD passes are order-dependent and generally inexact. Stage 1's SD chains are exact *because each one is checked*.

---

## 8. Stage 1c: certificates and outputs

A finished chain is accompanied by:

1. **Compile residual** $R=1-|\langle\Phi_0|W\Psi\rangle|^2$ below the gate (both currencies printed).
2. **Preparation check.** The listed preparation chain (reversed order, negated angles) applied to $\Phi_0$; report $1-|\langle\Psi|\Psi_{\text{chain}}\rangle|^2$ and the energy $\langle\Psi_{\text{chain}}|\hat H|\Psi_{\text{chain}}\rangle$ against $E_0$.
3. **Count identities.** routed $=$ support $-1$ (minus symmetry-locked siblings); support of the compiled state versus the target's; later, translation monomial count $=$ support at matched floors.
4. **Chain record.** For each letter: substitution $(I,A)$, rank, angle, provenance tag (routed/grown, round), and for the whole chain: max$|\theta|$ and the corresponding $t=\tan\theta$, letter counts by rank, staircase of round residuals, wall-clock and invocation count (the flagship: 42 unattended invocations, zero restarts).

The record then passes to Stage 2, whose own acceptance (reconstruct the state from the translated amplitudes; flagship $2.6\times10^{-16}$) closes the second route to the same number.

---

## 9. Worked example: the XLF four-site Hubbard ring at *U/t* = 4

This is the system of Xu, Lee & Freericks, *Mod. Phys. Lett. B* 34, 2040049 (2020) — the ground state that paper prepared by hand with eight doubles and one quadruple factor. It is small enough to print every number and rich enough to show every phenomenon: sibling batches, collateral, a symmetry gift, the plateau, the exact finish, and the unavoidable rank-4 letter of any straight-shot construction. Everything below is copied from `transcript_U4.txt` and `growth_anatomy_U4.txt`.

### 9.1 Model, basis, reference

Four sites, periodic, hopping $t=1$, on-site $U$, half filling, $S_z=0$, momentum basis $k=0,1,2,3$ (in units of $\pi/2$), $\varepsilon_k=-2t\cos(\pi k/2)=(-2,0,2,0)$. Spin-orbital $p=k+4\sigma$ ($\sigma=0$ up, $1$ down); determinants written as bit strings $(n_{0\uparrow}n_{1\uparrow}n_{2\uparrow}n_{3\uparrow}\,|\,n_{0\downarrow}n_{1\downarrow}n_{2\downarrow}n_{3\downarrow})$ and, in XLF's notation, as $|ij\,\bar k\bar l\rangle$ (up momenta plain, down momenta barred). Creation order: all up first, then down, increasing $k$ (XLF's convention). The Hamiltonian is XLF eq. (9), $\hat H=\sum_k\varepsilon_k(\hat n_{k\uparrow}+\hat n_{k\downarrow})+\frac U4\sum_{ijk}\hat c^\dagger_{k_i+k_k\uparrow}\hat c_{k_i\uparrow}\hat c^\dagger_{k_j-k_k\downarrow}\hat c_{k_j\downarrow}$, built directly on the 36-determinant $S_z=0$ space. Reference: $\Phi_0=|01\,\bar0\bar1\rangle=(1100|1100)$, total momentum $K=\pi$ (index 2 mod 4). Ground energy from dense diagonalization $E_0=-2.102748483462$; lowest root of XLF eq. (10), $E^3-3E^2U+2E(U^2-8)+24U=0$: $-2.102748483462$. Gap to the next root in the sector: 0.296.

### 9.2 The exact eigenvector

| determinant | bits | $K$ | level | coefficient | XLF label |
|---|---|---|---|---|---|
| \|01 0̄1̄⟩ | 1100\|1100 | 2 | 0 | +0.6518541365 | $\alpha$ |
| \|23 0̄1̄⟩ | 0011\|1100 | 2 | 2 | +0.0971927776 | $\beta$ |
| \|13 0̄2̄⟩ | 0101\|1010 | 2 | 2 | +0.1943855552 | $2\beta$ |
| \|12 1̄2̄⟩ | 0110\|0110 | 2 | 2 | −0.1356744948 | $-\gamma$ |
| \|03 1̄2̄⟩ | 1001\|0110 | 2 | 2 | +0.0971927776 | $\beta$ |
| \|12 0̄3̄⟩ | 0110\|1001 | 2 | 2 | +0.0971927776 | $\beta$ |
| \|03 0̄3̄⟩ | 1001\|1001 | 2 | 2 | −0.6518541365 | $-\alpha$ |
| \|02 1̄3̄⟩ | 1010\|0101 | 2 | 2 | +0.1943855552 | $2\beta$ |
| \|01 2̄3̄⟩ | 1100\|0011 | 2 | 2 | +0.0971927776 | $\beta$ |
| \|23 2̄3̄⟩ | 0011\|0011 | 2 | 4 | +0.1356744948 | $\gamma$ |

Support 10 = the whole $(K=\pi,S_z=0)$ sector: block law with equality. The $\alpha,\beta,2\beta,\gamma$ pattern and signs of XLF eq. (12) are reproduced exactly, which certifies that the sign conventions of the scripts are XLF's. Nine determinants are doubles from the reference; one, $|23\,\bar2\bar3\rangle$, is a quadruple.

### 9.3 The pool

Of the 12 singles and 78 doubles that conserve $S_z$ on eight spin-orbitals, exactly 0 singles and 28 doubles also conserve $K$; those 28 are the pool. Twenty of them have exactly two pairs inside the sector; eight have none there and score identically zero throughout. Nothing of rank 3 or 4 is admitted.

### 9.4 Routing sweep

Order: the quadruple first (level 4), then the eight doubles in canonical index order. Letters (compile direction), with the closed-form angle, the determinant zeroed, the partner it drains into, and the sibling pair that rotated as collateral:

| letter | generator $(A\leftarrow I)$ | $\theta$ | zeroes | into | siblings also rotated |
|---|---|---|---|---|---|
| 1 | (2↑2↓ ← 0↑0↓) | +0.205207 | \|23 2̄3̄⟩ | \|03 0̄3̄⟩ | \|01 0̄1̄⟩ ↔ \|12 1̄2̄⟩ |
| 2 | (2↑3↑ ← 0↑1↑) | −0.144950 | \|23 0̄1̄⟩ | \|01 0̄1̄⟩ | \|01 2̄3̄⟩ ↔ \|23 2̄3̄⟩ |
| 3 | (3↑2↓ ← 0↑1↓) | +0.281229 | \|13 0̄2̄⟩ | \|01 0̄1̄⟩ | \|02 1̄3̄⟩ ↔ \|23 2̄3̄⟩ |
| — | *\|12 1̄2̄⟩ already zero (collateral of letter 1) — skipped* | | | | |
| 4 | (3↑2↓ ← 1↑0↓) | +0.137888 | \|03 1̄2̄⟩ | \|01 0̄1̄⟩ | \|12 0̄3̄⟩ ↔ \|23 2̄3̄⟩ |
| 5 | (2↑3↓ ← 0↑1↓) | +0.122423 | \|12 0̄3̄⟩ | \|01 0̄1̄⟩ | \|03 1̄2̄⟩ ↔ \|23 2̄3̄⟩ |
| 6 | (3↑3↓ ← 1↑1↓) | +0.751589 | \|03 0̄3̄⟩ | \|01 0̄1̄⟩ | \|12 1̄2̄⟩ ↔ \|23 2̄3̄⟩ |
| 7 | (2↑3↓ ← 1↑0↓) | +0.185363 | \|02 1̄3̄⟩ | \|01 0̄1̄⟩ | \|13 0̄2̄⟩ ↔ \|23 2̄3̄⟩ |
| 8 | (2↓3↓ ← 0↓1↓) | −0.096634 | \|01 2̄3̄⟩ | \|01 0̄1̄⟩ | \|23 0̄1̄⟩ ↔ \|23 2̄3̄⟩ |

The compiled vector $v_k$ after each letter (amplitudes; columns in the sector's canonical order):

| after | \|01 0̄1̄⟩ | \|23 0̄1̄⟩ | \|13 0̄2̄⟩ | \|12 1̄2̄⟩ | \|03 1̄2̄⟩ | \|12 0̄3̄⟩ | \|03 0̄3̄⟩ | \|02 1̄3̄⟩ | \|01 2̄3̄⟩ | \|23 2̄3̄⟩ |
|---|---|---|---|---|---|---|---|---|---|---|
| start ($\Psi$) | +0.651854 | +0.097193 | +0.194386 | −0.135674 | +0.097193 | +0.097193 | −0.651854 | +0.194386 | +0.097193 | +0.135674 |
| 1 | +0.665824 | +0.097193 | +0.194386 | 0 | +0.097193 | +0.097193 | −0.665824 | +0.194386 | +0.097193 | 0 |
| 2 | +0.672880 | 0 | +0.194386 | 0 | +0.097193 | +0.097193 | −0.665824 | +0.194386 | +0.096174 | −0.014039 |
| 3 | +0.700395 | 0 | 0 | 0 | +0.097193 | +0.097193 | −0.665824 | +0.182853 | +0.096174 | −0.067436 |
| 4 | +0.707107 | 0 | 0 | 0 | 0 | +0.087001 | −0.665824 | +0.182853 | +0.096174 | −0.080156 |
| 5 | +0.712439 | 0 | 0 | 0 | −0.009788 | 0 | −0.665824 | +0.182853 | +0.096174 | −0.079556 |
| 6 | +0.975136 | 0 | 0 | +0.054321 | −0.009788 | 0 | 0 | +0.182853 | +0.096174 | −0.058124 |
| 7 | +0.992132 | 0 | −0.010712 | +0.054321 | −0.009788 | 0 | 0 | 0 | +0.096174 | −0.057128 |
| 8 | +0.996782 | −0.005512 | −0.010712 | +0.054321 | −0.009788 | 0 | 0 | 0 | 0 | −0.056862 |

Reading the table:

- **Letter 1 — transport plus a symmetry gift.** The quad (0.1357) is drained into $|03\,\bar0\bar3\rangle$ ($-0.6519$) with $\theta=\arctan(0.1357/0.6519)=0.2052$; the survivor becomes $-\sqrt{0.6519^2+0.1357^2}=-0.6658$. The sibling pair $\{\Phi_0,|12\,\bar1\bar2\rangle\}$ rotates by the same angle, and because pseudospin locks $\gamma/\alpha$ across both pairs, $|12\,\bar1\bar2\rangle$ ($-0.1357$) lands on exactly zero too. One letter, two support determinants killed; the count law reads routed $=10-2=8$. This is XLF's last operator, $\theta_4\,\hat A_{2\uparrow2\downarrow\leftarrow0\uparrow0\downarrow}$, rediscovered by the machine as its first move.
- **Letter 2 — collateral.** Draining $|23\,\bar0\bar1\rangle$ into $\Phi_0$ ($0.6658\to0.6729=\sqrt{0.6658^2+0.0972^2}$) rotates the sibling pair $\{|01\,\bar2\bar3\rangle,|23\,\bar2\bar3\rangle\}$: the quad, zeroed by letter 1, comes back at $-0.0140$. Same mechanism as the $\sin^2\theta_1$ ghost of XLF's Table 1, produced here by a same-spin double.
- **Letters 3–8** drain the remaining doubles into $\Phi_0$; each refills a sibling. Letter 6 is the two-reference rotation $\Phi_0\leftrightarrow|03\,\bar0\bar3\rangle$ at $0.7516$ (XLF's $\pi/4$ factor; here the angle differs from $\pi/4$ because at that stage the reference has already grown to $0.7124$), and its sibling pair puts $+0.0543$ back on $|12\,\bar1\bar2\rangle$: the $\gamma$ content, transported and re-deposited.
- **After eight letters:** $v_{\Phi_0}=0.996782$, fidelity 0.993575, $R=6.425\times10^{-3}$, weight left on $|23\,\bar2\bar3\rangle$ ($3.2\times10^{-3}$), $|12\,\bar1\bar2\rangle$ ($2.9\times10^{-3}$), $|13\,\bar0\bar2\rangle$ ($1.1\times10^{-4}$), $|03\,\bar1\bar2\rangle$ ($9.6\times10^{-5}$), $|23\,\bar0\bar1\rangle$ ($3.0\times10^{-5}$). Almost all of it is the connected-quadruple content that XLF's quad factor carried; no closed-form pass finishes it.

### 9.5 Growth, round by round (routed angles frozen; batch 3)

Each round: prepared state $w$ (routed$+$grown chain run backwards from $\Phi_0$), discrepancy $w-\Psi$, compiled $v$; the ranked scores $|F'(0)|=2\,(w\cdot\Psi)\,|w\cdot\hat\kappa_\mu\Psi|$ with the pair torques $s_p(w_{D'}\Psi_D-w_D\Psi_{D'})$; the picks; the least-squares outcome. Columns of the vectors are in the order of the routing table.

**Round 1.** $w\cdot\Psi=0.996782$.

| | \|01 0̄1̄⟩ | \|23 0̄1̄⟩ | \|13 0̄2̄⟩ | \|12 1̄2̄⟩ | \|03 1̄2̄⟩ | \|12 0̄3̄⟩ | \|03 0̄3̄⟩ | \|02 1̄3̄⟩ | \|01 2̄3̄⟩ | \|23 2̄3̄⟩ |
|---|---|---|---|---|---|---|---|---|---|---|
| $w$ | +0.653958 | +0.097507 | +0.195013 | −0.136112 | +0.097507 | +0.086453 | −0.638529 | +0.172907 | +0.086453 | +0.210243 |
| $w-\Psi$ | +0.002104 | +0.000314 | +0.000627 | −0.000438 | +0.000314 | −0.010739 | +0.013325 | −0.021479 | −0.010739 | +0.074569 |
| $v$ | +0.996782 | −0.005512 | −0.010712 | +0.054321 | −0.009788 | 0 | 0 | 0 | 0 | −0.056862 |

| rank | letter | score | pair torques | decision |
|---|---|---|---|---|
| 1 | (2↑2↓ ← 0↑0↓) | 1.005e−01 | \|03 0̄3̄⟩↔\|23 2̄3̄⟩: −0.0504 | excluded: twin of adjacent routed letter 1 |
| 2 | (3↑2↓ ← 0↑1↓) | 3.471e−02 | \|02 1̄3̄⟩↔\|23 2̄3̄⟩: −0.0174 | picked |
| 3 | (3↑0↓ ← 2↑1↓) | 2.275e−02 | \|02 1̄3̄⟩↔\|03 0̄3̄⟩: −0.0114 | picked |
| 4 | (2↑3↑ ← 0↑1↑) | 1.735e−02 | \|01 2̄3̄⟩↔\|23 2̄3̄⟩: +0.0087 | picked |
| 5 | (3↑2↓ ← 1↑0↓) | 1.735e−02 | \|12 0̄3̄⟩↔\|23 2̄3̄⟩: −0.0087 | exact tie with rank 4 (symmetry twin) |
| 6 | (1↑2↓ ← 0↑3↓) | 1.196e−02 | \|03 0̄3̄⟩↔\|13 0̄2̄⟩: −0.0030; \|02 1̄3̄⟩↔\|12 1̄2̄⟩: −0.0030 | |
| 7 | (3↑0↓ ← 1↑2↓) | 1.137e−02 | \|01 2̄3̄⟩↔\|03 0̄3̄⟩: −0.0057 | |
| 8 | (1↑2↑ ← 0↑3↑) | 1.137e−02 | \|03 0̄3̄⟩↔\|12 0̄3̄⟩: +0.0057 | |

Every strong torque involves the over-weighted quad or the under-weighted $2\beta$ determinant $|02\,\bar1\bar3\rangle$; the selector never knows "quad" as a concept, only per-pair torque. Least squares over the 3 grown angles: 11 residual evaluations; compile-direction angles $+0.01627,-0.01035,-0.02759$; Jacobian $9\times3$ singular values $0.835,\ 0.682,\ 0.578$; $R:\ 6.425\times10^{-3}\to5.687\times10^{-3}$. Three healthy directions, but only three of nine: the plateau.

**Round 2.** $w\cdot\Psi=0.997152$.

| | \|01 0̄1̄⟩ | \|23 0̄1̄⟩ | \|13 0̄2̄⟩ | \|12 1̄2̄⟩ | \|03 1̄2̄⟩ | \|12 0̄3̄⟩ | \|03 0̄3̄⟩ | \|02 1̄3̄⟩ | \|01 2̄3̄⟩ | \|23 2̄3̄⟩ |
|---|---|---|---|---|---|---|---|---|---|---|
| $w$ | +0.660589 | +0.086772 | +0.175477 | −0.137936 | +0.097507 | +0.086453 | −0.636646 | +0.185241 | +0.089783 | +0.203959 |
| $w-\Psi$ | +0.008735 | −0.010421 | −0.018908 | −0.002261 | +0.000314 | −0.010739 | +0.015208 | −0.009145 | −0.007409 | +0.068285 |
| $v$ | +0.997152 | +0.006301 | +0.010364 | +0.048575 | −0.008636 | +0.001288 | −0.002564 | −0.008661 | −0.001351 | −0.054965 |

| rank | letter | score | pair torques | decision |
|---|---|---|---|---|
| 1 | (2↑2↓ ← 0↑0↓) | 9.346e−02 | \|01 0̄1̄⟩↔\|12 1̄2̄⟩: −0.0003; \|03 0̄3̄⟩↔\|23 2̄3̄⟩: −0.0466 | picked (no longer adjacent to its twin) |
| 2 | (2↑3↓ ← 1↑0↓) | 1.631e−02 | \|01 0̄1̄⟩↔\|02 1̄3̄⟩: +0.0077; \|13 0̄2̄⟩↔\|23 2̄3̄⟩: −0.0158 | picked |
| 3 | (1↑2↓ ← 0↑3↓) | 1.533e−02 | \|03 0̄3̄⟩↔\|13 0̄2̄⟩: +0.0094; \|02 1̄3̄⟩↔\|12 1̄2̄⟩: −0.0017 | picked |
| 4 | (3↑2↓ ← 1↑0↓) | 1.486e−02 | \|01 0̄1̄⟩↔\|03 1̄2̄⟩: +0.0006; \|12 0̄3̄⟩↔\|23 2̄3̄⟩: −0.0081 | |
| 5 | (3↑3↓ ← 1↑1↓) | 1.326e−02 | \|01 0̄1̄⟩↔\|03 0̄3̄⟩: +0.0156; \|12 1̄2̄⟩↔\|23 2̄3̄⟩: −0.0090 | |
| 6 | (1↑2↑ ← 0↑3↑) | 1.066e−02 | \|03 1̄2̄⟩↔\|12 1̄2̄⟩: −0.0002; \|03 0̄3̄⟩↔\|12 0̄3̄⟩: +0.0055 | |
| 7 | (2↑1↓ ← 0↑3↓) | 8.156e−03 | \|03 0̄3̄⟩↔\|23 0̄1̄⟩: +0.0053; \|01 2̄3̄⟩↔\|12 1̄2̄⟩: −0.0012 | |
| 8 | (1↓2↓ ← 0↓3↓) | 6.700e−03 | \|12 0̄3̄⟩↔\|12 1̄2̄⟩: −0.0017; \|03 0̄3̄⟩↔\|03 1̄2̄⟩: −0.0017 | |

The rank-2 letter shows the batch inside the score: its two pairs both help. Least squares over 6 angles: 19 evaluations; angles $-0.20130,-0.19360,-0.08103,+0.00662,-0.26906,+0.22784$ (round-1 angles re-tuned from $\sim0.02$ to $\sim0.2$); singular values $1.12,\ 1.08,\ 0.657,\ 0.498,\ 0.493,\ 0.210$; $R:\ 5.687\times10^{-3}\to2.166\times10^{-4}$ — the quad-versus-$\alpha$ direction is finally in the set.

**Round 3.** $w\cdot\Psi=0.999892$.

| | \|01 0̄1̄⟩ | \|23 0̄1̄⟩ | \|13 0̄2̄⟩ | \|12 1̄2̄⟩ | \|03 1̄2̄⟩ | \|12 0̄3̄⟩ | \|03 0̄3̄⟩ | \|02 1̄3̄⟩ | \|01 2̄3̄⟩ | \|23 2̄3̄⟩ |
|---|---|---|---|---|---|---|---|---|---|---|
| $w$ | +0.653283 | +0.093579 | +0.194821 | −0.135998 | +0.097507 | +0.086453 | −0.653326 | +0.194831 | +0.088066 | +0.135951 |
| $w-\Psi$ | +0.001429 | −0.003613 | +0.000435 | −0.000323 | +0.000314 | −0.010739 | −0.001471 | +0.000446 | −0.009127 | +0.000276 |
| $v$ | +0.999892 | +0.003584 | −0.000521 | +0.001835 | −0.000497 | +0.010519 | +0.001231 | −0.000567 | +0.009075 | −0.002231 |

| rank | letter | score | pair torques | decision |
|---|---|---|---|---|
| 1 | (2↑3↓ ← 0↑1↓) | 1.431e−02 | \|01 0̄1̄⟩↔\|12 0̄3̄⟩: +0.0071; \|03 1̄2̄⟩↔\|23 2̄3̄⟩: 0 | picked |
| 2 | (1↑2↑ ← 0↑3↑) | 1.431e−02 | \|03 1̄2̄⟩↔\|12 1̄2̄⟩: 0; \|03 0̄3̄⟩↔\|12 0̄3̄⟩: +0.0071 | picked (exact tie: twin feeding the same determinant from the other $\alpha$ state) |
| 3 | (2↓3↓ ← 0↓1↓) | 1.114e−02 | \|01 0̄1̄⟩↔\|01 2̄3̄⟩: −0.0061; \|23 0̄1̄⟩↔\|23 2̄3̄⟩: +0.0005 | picked |
| 4 | (3↑0↓ ← 1↑2↓) | 1.114e−02 | \|12 1̄2̄⟩↔\|23 0̄1̄⟩: +0.0005; \|01 2̄3̄⟩↔\|03 0̄3̄⟩: −0.0061 | exact tie with rank 3 |
| 5 | (1↑0↓ ← 0↑1↓) | 4.299e−03 | \|02 1̄3̄⟩↔\|12 0̄3̄⟩: −0.0021 | |
| 6 | (3↑2↓ ← 2↑3↓) | 4.295e−03 | \|12 0̄3̄⟩↔\|13 0̄2̄⟩: +0.0021 | |
| 7 | (3↑1↓ ← 1↑3↓) | 3.220e−03 | \|12 0̄3̄⟩↔\|23 0̄1̄⟩: −0.0007; \|01 2̄3̄⟩↔\|03 1̄2̄⟩: −0.0009 | |
| 8 | (1↓2↓ ← 0↓3↓) | 3.100e−03 | \|12 0̄3̄⟩↔\|12 1̄2̄⟩: −0.0015; \|03 0̄3̄⟩↔\|03 1̄2̄⟩: −0.0001 | |

The discrepancy is now essentially two starved $\beta$ determinants, $|12\,\bar0\bar3\rangle$ ($-0.0107$) and $|01\,\bar2\bar3\rangle$ ($-0.0091$), which the frozen routed letters cannot feed; the picks are exactly the letters that feed them. Least squares over 9 angles: 17 evaluations; angles $-0.01773,+0.14444,-0.12908,-0.18126,-0.14770,-0.08139,-0.00345,-0.21913,+0.20189$; the $9\times9$ Jacobian has singular values $1.13,\ 1.11,\ 0.931,\ 0.819,\ 0.548,\ 0.518,\ 0.403,\ 0.208,\ 0.0181$ — full rank — so Gauss–Newton is Newton for a square system and $R:\ 2.166\times10^{-4}\to2.212\times10^{-31}$.

Staircase summary: $6.4\times10^{-3}\ (\text{routed})\to5.7\times10^{-3}\to2.2\times10^{-4}\to2.2\times10^{-31}$, gate $10^{-12}$ crossed at round 3.

### 9.6 Final chain and certificates

17 letters $=$ 8 routed $+$ 9 grown, all rank 2. Preparation order (apply step 1 first to $\Phi_0$; angles are the negated compile angles):

| step | letter | $\theta$ | tag |
|---|---|---|---|
| 1 | (2↓3↓ ← 0↓1↓) | +0.09663431 | routed 8 |
| 2 | (2↑3↓ ← 1↑0↓) | −0.18536260 | routed 7 |
| 3 | (3↑3↓ ← 1↑1↓) | −0.75158945 | routed 6 |
| 4 | (2↑3↓ ← 0↑1↓) | −0.12242277 | routed 5 |
| 5 | (3↑2↓ ← 1↑0↓) | −0.13788787 | routed 4 |
| 6 | (3↑2↓ ← 0↑1↓) | −0.28122936 | routed 3 |
| 7 | (2↑3↑ ← 0↑1↑) | +0.14494995 | routed 2 |
| 8 | (2↑2↓ ← 0↑0↓) | −0.20520652 | routed 1 |
| 9 | (3↑2↓ ← 0↑1↓) | −0.20189049 | grown, round 1 |
| 10 | (3↑0↓ ← 2↑1↓) | +0.21912627 | grown, round 1 |
| 11 | (2↑3↑ ← 0↑1↑) | +0.00345203 | grown, round 1 |
| 12 | (2↑2↓ ← 0↑0↓) | +0.08138799 | grown, round 2 |
| 13 | (2↑3↓ ← 1↑0↓) | +0.14769664 | grown, round 2 |
| 14 | (1↑2↓ ← 0↑3↓) | +0.18125519 | grown, round 2 |
| 15 | (2↑3↓ ← 0↑1↓) | +0.12908200 | grown, round 3 |
| 16 | (1↑2↑ ← 0↑3↑) | −0.14443791 | grown, round 3 |
| 17 | (2↓3↓ ← 0↓1↓) | +0.01772772 | grown, round 3 |

Certificates: compile fidelity $|\langle\Phi_0|W\Psi\rangle|^2=1.0000000000000000$ ($R=0.0$ in the $1-\mathrm{fid}^2$ currency, $2.2\times10^{-31}$ as the off-reference sum); preparation check $1-|\langle\Psi|\Psi_{\text{chain}}\rangle|^2=4.4\times10^{-16}$; $E(\Psi_{\text{chain}})=-2.102748483462$, $\Delta E=8.9\times10^{-16}$. Max$|\theta|=0.751589$ on the two-reference rotation (3↑3↓ ← 1↑1↓), CC-side $t=\tan\theta=0.9346$. Grown letters of the type (3↑0↓ ← 2↑1↓) act on excited determinants only; they are the commutator-word builders that stand in for the quadruple.

### 9.7 The free-angle variant

Same seed, same selector, batch 1, routed angles unfrozen during least squares. Result: 10 letters $=$ 8 routed $+$ 2 grown, all rank 2, staircase $6.4\times10^{-3}\to3.2\times10^{-3}\to3.7\times10^{-31}$. Preparation order:

| step | letter | $\theta$ | tag |
|---|---|---|---|
| 1 | (2↓3↓ ← 0↓1↓) | +0.10145033 | routed (re-optimized) |
| 2 | (2↑3↓ ← 1↑0↓) | −0.07176192 | routed (re-optimized) |
| 3 | (3↑3↓ ← 1↑1↓) | −0.76782402 | routed (re-optimized) |
| 4 | (2↑3↓ ← 0↑1↓) | −0.13788787 | routed |
| 5 | (3↑2↓ ← 1↑0↓) | −0.13788787 | routed |
| 6 | (3↑2↓ ← 0↑1↓) | −0.12235761 | routed (re-optimized) |
| 7 | (2↑3↑ ← 0↑1↑) | +0.14027332 | routed (re-optimized) |
| 8 | (2↑2↓ ← 0↑0↓) | −0.12897485 | routed (re-optimized) |
| 9 | (3↑2↓ ← 0↑1↓) | −0.20077214 | grown |
| 10 | (3↑0↓ ← 2↑1↓) | +0.22661306 | grown |

Why two letters suffice: parameter counting. The target lives on a nine-dimensional sphere; frozen routing contributes zero free parameters (hence nine grown letters above); free routing contributes eight, so one or two more letters close the tangent space provided their directions are the missing ones — the selector supplied them and Gauss–Newton found the exact point. The price is that the routed angles are no longer the closed-form ones.

### 9.8 Against the hand-built chain and the straight-shot recipe

**XLF Table 1** (preparation order, their factor convention $\exp[i\theta(\hat A+\hat A^\dagger)]$): $-\theta_1\hat A_{2\uparrow3\downarrow\leftarrow1\uparrow0\downarrow}$, $-\theta_1\hat A_{3\uparrow2\downarrow\leftarrow0\uparrow1\downarrow}$, $\theta_2\hat A_{2\uparrow3\uparrow2\downarrow3\downarrow\leftarrow0\uparrow1\uparrow0\downarrow1\downarrow}$ (the quadruple), $-\tfrac\pi4\hat A_{3\uparrow3\downarrow\leftarrow1\uparrow1\downarrow}$, $\theta_3\hat A_{2\uparrow3\uparrow\leftarrow0\uparrow1\uparrow}$, $\theta_3\hat A_{2\downarrow3\downarrow\leftarrow0\downarrow1\downarrow}$, $-\theta_3\hat A_{1\uparrow2\uparrow\leftarrow0\uparrow3\uparrow}$, $-\theta_3\hat A_{1\downarrow2\downarrow\leftarrow0\downarrow3\downarrow}$, $-\theta_4\hat A_{2\uparrow2\downarrow\leftarrow0\uparrow0\downarrow}$; angles from their eqs. (13)–(16), $\theta_1=\tfrac12\sin^{-1}(4\beta)$, $\theta_2=\tan^{-1}(-\tan^2\theta_1)$, $\theta_3=\tfrac12\sin^{-1}(2\sqrt2\beta/\mu_{12})$, $\theta_4=\tan^{-1}(\gamma/\alpha)-\tan^{-1}(\tan^2\theta_3)$. Nine letters, eight doubles and one quadruple, exact; the quadruple exists to cancel the $\sin^2\theta_1$ term on $|23\,\bar2\bar3\rangle$ that the first two letters' siblings created.

**Mechanized SD-only** (this document): 10 letters (free mode) or 17 (frozen mode), all doubles, no quadruple, exact to the floating floor. Most routed generators coincide with XLF's letters (they are the direct excitations from the reference); the growth letters replace the quadruple with words in non-commuting doubles.

**Naive direct sweep** (one straight-shot letter per support determinant of whatever rank, ascending level, canonical order): letters 1–4 zero four doubles cleanly; letters 5–8 zero four more but each refills an already-zeroed double through a sibling pair ($|03\,\bar1\bar2\rangle$, $|12\,\bar1\bar2\rangle$, $|13\,\bar0\bar2\rangle$, $|23\,\bar0\bar1\rangle$); letter 9 is the rank-4 $(2\uparrow3\uparrow2\downarrow3\downarrow\leftarrow0\uparrow1\uparrow0\downarrow1\downarrow)$ zeroing the quad (it has no siblings, so it is clean); letters 10–13 re-zero the four refilled doubles. Total 13 letters, ranks $\{2:12,\ 4:1\}$, residual $2.2\times10^{-16}$. XLF's hand ordering achieves 9 with the quad; either way the rank-4 letter is unavoidable in any straight-shot construction, because $|23\,\bar2\bar3\rangle$ is level 4 and reachable in one shot only by rank 4, and it costs $4^4+2=258$ monomials in translation against 18 for a double. In the campaign's language this is the fill-in law in miniature; at C₂ the same mechanism produced 25,549 rank-8 letters.

### 9.9 Along the interaction

Same scripts, $U/t\in\{0.5,2,4,8,16\}$:

| $U/t$ | support | routed | $R$ after routing | grown (free) / total | grown (frozen) / total |
|---|---|---|---|---|---|
| 0.5 | 10 | 8 | 1.2 × 10⁻⁵ | 2 / 10 | 9 / 17 |
| 2 | 10 | 8 | 1.2 × 10⁻³ | 2 / 10 | 9 / 17 |
| 4 | 10 | 8 | 6.4 × 10⁻³ | 2 / 10 | 9 / 17 |
| 8 | 10 | 8 | 1.7 × 10⁻² | 2 / 10 | 12 / 20 |
| 16 | 10 | 8 | 2.6 × 10⁻² | 2 / 10 | 9 / 17 |

Support pinned at 10 for every $U$ (the $K$-sector law), routed count pinned at 8, and the residual routing leaves behind rising monotonically with correlation strength: chain length and residual track correlation, not size — the miniature of the LiH, H₂O, N₂ and H₆ support-pinning findings and of "growth ratio measures hardness".

### 9.10 What the example teaches

One factor is a batch (letter 1's gift, letter 2's collateral). Routing is a closed-form Givens sweep that aligns the two states plane by plane in the planes it uses and misaligns the sibling planes; its remainder is the connected high-rank content, and it grows with correlation. Growth reads exactly that misalignment as torque, adds directions, and finishes when — and only when — the letter set's Jacobian reaches full rank on the target's sphere. Every straight-shot construction needs the rank-4 letter; the SD compiler never does. And the exactness of the result is a certificate, printed, not a theorem, assumed.

---

## 10. Diagnostics and failure modes

### 10.1 Fill-in (the direct-mode failure)

Symptom: letter count far above support, high-rank letters proliferating; the C₂ measurement is 61,977 letters, 25,549 of rank 8, 56× the support, exact and untranslatable. Cause: high-rank straight-shot rotations whose siblings scatter amplitude onto determinants outside the support, each of which then needs a letter of its own. Direct mode is retained as a control arm and as an instrument (it produced the fill-in law and validated the degeneracy fix by collapsing 50,652 → 11,967 letters on projection); it is never the route. The toy shows the same mechanism as sibling refills requiring a second pass and an unavoidable rank-4 letter (Section 9.8).

### 10.2 Wrong eigenstate

An eigensolver can return the wrong root with a plausible energy (C₂: the first excited triplet $\Pi$ pair). The compiler's chain observables see it: routed count against support $-1$, growth ratio, spin/point-group signatures of the letters, and the translation's structure. This is the "compiler as state analyzer" role; the remedy is the Stage-0 hygiene of Section 5.

### 10.3 Degenerate mixture

Support arithmetic doubles (stretched C₂: $1216=2\times608$); routing cannot cross disconnected blocks; letter counts balloon. Remedy: `dominant_block_projection` before compiling. Skips in the Davidson census at exact and near degeneracy belong to the same family.

### 10.4 Plateau and rank deficiency

A round that lowers $R$ only marginally is expected (rounds 1 and 2 of Section 9.5); a run that stops improving *across* rounds is a rank problem: the letters being added are redundant with the set (adjacent duplicates, symmetry twins, or letters whose pairs all lie in already-aligned planes). Diagnostic: the smallest singular values of the Jacobian at the plateau. Remedies: enforce the no-adjacent-duplicate rule, increase the batch, allow letters that act on excited determinants only (they build the commutator words), or free the routed angles.

### 10.5 Angles near $\pm\pi/2$

Not a numerical fault: a survivor near zero forces the zeroing angle toward $\pi/2$ (Section 3.2). The compile stays exact; the CC-side amplitude $t=\tan\theta$ becomes large (flagship $t\approx34$). This is the mechanism of "correlation carried by angle, not chain length" and should be reported, not suppressed.

### 10.6 Composition dependence versus invariants

The chain is a gauge choice: tie-breaks among symmetry twins (exact ties in Section 9.5), optimizer, batch, freeze/free mode, and even the operating system (H₆: 298 letters on Linux versus 358 on Windows at strong correlation, both exact, both translating to $\sim10^{-16}$) can change the letter list. What must agree between two runs on the same certified target: the support, the residual gate, the preparation and energy checks, the length band, and above all the translated amplitudes, which are a property of the state. Compare invariants, never letter lists.

### 10.7 Residual currencies

| quantity | formula | floor | use |
|---|---|---|---|
| fidelity deficit | $1-\lvert\langle\Phi_0\vert W\Psi\rangle\rvert^2$ | $\sim10^{-16}$ (cancellation) | gate, cross-driver comparison |
| off-reference sum | $\sum_{D\ne\Phi_0}v_D^2$ | machine precision squared | polishing, least-squares objective |
| vector error | $\lVert v-\Phi_0\rVert\approx\sqrt{R}$ | — | interpreting the gate ($10^{-12}\to10^{-6}$ per component) |

### 10.8 Symmetry gifts and the count law

When symmetry locks a sibling pair to the target pair, one letter zeroes two determinants and routed $<$ support $-1$ (Section 9.4). Record the skip; report the count law as routed $=$ support $-1-$(symmetry-locked siblings). A routed count *above* support $-1$ is impossible and indicates a bug.

---

## 11. Genealogy: inherited and new

Inherited, and cited as such: Wick's theorem (1950) and the Fermi-vacuum contraction calculus (Stage 2); the closed three-term factor and the first-order operator relations (Freericks, *Symmetry* 14, 494, 2022); the disentangled-UCC existence theorem and its negative result on single SD passes (Evangelista, Chan, Scuseria, *J. Chem. Phys.* 151, 244112, 2019); the hand-built backward construction and its stated open problems of factor placement and ordering (Xu, Lee, Freericks, *Mod. Phys. Lett. B* 34, 2040049, 2020); Givens rotations and QR (Givens 1958; Golub & Van Loan); the gradient selector (Grimsley et al., *Nat. Commun.* 10, 3007, 2019; Feniou et al., *Commun. Phys.* 6, 192, 2023) and its matching-pursuit ancestor (Mallat & Zhang 1993); Gauss–Newton/Levenberg–Marquardt (Levenberg 1944; Marquardt 1963; Nocedal & Wright ch. 10); Givens-elimination state preparation with *controlled* single-excitation gates (Arrazola et al., *Quantum* 6, 742, 2022) as the nearest quantum-circuit cousin.

New here, and claimed as a construction plus its phenomenology, not as a theorem: the rank-≤2 fence derived from the translation's cost law; the closed-form SD routing sweep on the Hamiltonian's coupling graph with its one-letter-per-support-determinant count as a diagnostic; growth seeded by that sweep and run against a known exact target to a certified exactness gate, with the least-squares/rank view of the plateau; the spin-hygiene pairing (`sd_paired`), degeneracy detection and dominant-block projection; the determinism layer that lets the chain's arithmetic serve as an instrument; the exact constructive translation of the result to CC amplitudes at scale (Stage 2); and the measured laws — rank-cost, fill-in, block, degenerate-mixture, support pinning, growth-ratio-as-hardness — none of which is derivable from the algebra alone.

One-sentence genealogy for a methods section: *chains after Xu–Lee–Freericks 2020, exact factor algebra after Freericks 2022, gradient growth after ADAPT/Overlap-ADAPT, exact SD construction-plus-translation at scale new here.*

---

## 12. Reproduction

### 12.1 Files

- `hub4_sd_compile.py` — builds the four-site ring in the momentum basis, diagonalizes, runs routing, growth (frozen), the free-angle variant, and the naive direct sweep; prints the transcript. Usage: `python3 hub4_sd_compile.py [U/t]` (default 4.0). Requirements: numpy, scipy. Runtime: seconds.
- `growth_anatomy.py` — re-runs routing silently and prints, for three growth rounds, the prepared state, discrepancy, compiled vector, all ranked scores with pair torques, the picks, the least-squares angles, Jacobian singular values, and residual. Expects `hub4_sd_compile.py` in the same directory.
- `transcript_U4.txt`, `growth_anatomy_U4.txt` — the outputs quoted in Section 9.

### 12.2 Expected checkpoints at *U/t* = 4

$E_0=-2.102748483462$ (matches the cubic); support 10 = sector; pool 28 doubles, 0 singles; routed 8 with the "already zero" skip after letter 3; $R$ after routing $6.425\times10^{-3}$; frozen growth $5.687\times10^{-3}\to2.166\times10^{-4}\to2.212\times10^{-31}$, 17 letters; free variant 10 letters; direct 13 letters with one rank-4; preparation deficit $4.4\times10^{-16}$; $\Delta E=8.9\times10^{-16}$.

### 12.3 Conventions of the scripts to verify against the production driver before quoting either as the other

1. Routing order: outermost level first, canonical index tie-break — check `sd_routed`'s ordering.
2. Partner rule: lowest level, then largest current $|c|$, then canonical index — check the driver's edge choice.
3. Handling of a support determinant already zeroed by a sibling: skipped here (count law reads support $-2$); the driver may emit a zero-angle letter instead.
4. Growth position: new letters are outermost in preparation (first applied to $\Psi$ in compile) — check `grow_gn`'s insertion point.
5. Selector: overlap gradient, batch 3, no adjacent duplicates, ties by pool order — check `grow_gn`'s selector, batch, and tie rule.
6. Angle solve: Gauss–Newton/LM least squares on the off-reference vector with analytic Jacobian, angles wrapped to $(-\pi,\pi]$ — the driver's optimizer may be BFGS-type on the scalar fidelity.
7. Frozen versus free routed angles during growth — determine which mode `grow_gn` runs; the growth-ratio law depends on it.
8. Pool: $K$- and $S_z$-conserving rank-≤2 substitutions — in molecules the corresponding rule is the H-connected SD graph with point-group conservation.

### 12.4 Extending the example

The same two scripts run unchanged on any small model whose Hamiltonian can be built on a determinant basis; for a molecule, replace the Hamiltonian block by an integral dump (the `run_psi4_dump.py` route) and the momentum rule by the point-group rule. Keep the two-environment discipline: integrals cross the boundary as a file, never as an import.

---

## Appendix A. Derivations

**A.1 The cubic self-relation and the three-term exponential.** For a single substitution $\mu$, every determinant is either a domain member, a range member, or untouched. On the pair $\{D,D'\}$, $\hat\kappa_\mu=s\begin{pmatrix}0&-1\\1&0\end{pmatrix}$, so $\hat\kappa_\mu^2=-1$ there; on untouched determinants $\hat\kappa_\mu=0$. Hence $\hat\kappa_\mu^2=-\hat P_\mu$ with $\hat P_\mu$ the projector onto the union of the pairs, and $\hat\kappa_\mu^3=-\hat\kappa_\mu$. Then $\hat\kappa_\mu^{2m+1}=(-1)^m\hat\kappa_\mu$ and $\hat\kappa_\mu^{2m}=(-1)^{m+1}\hat\kappa_\mu^2$ for $m\ge1$, and

$$e^{\theta\hat\kappa_\mu}=1+\hat\kappa_\mu\sum_{m\ge0}\frac{(-1)^m\theta^{2m+1}}{(2m+1)!}+\hat\kappa_\mu^2\sum_{m\ge1}\frac{(-1)^{m+1}\theta^{2m}}{(2m)!}=1+\sin\theta\,\hat\kappa_\mu+(1-\cos\theta)\,\hat\kappa_\mu^2 .$$

**A.2 The pair rotation and the zeroing angle.** With $\hat\kappa_\mu^2=-1$ on the pair, $e^{\theta\hat\kappa_\mu}=\cos\theta+\sin\theta\,\hat\kappa_\mu$ there, giving the matrix of Section 3.1. Setting the rotated coefficient of $D'$ to zero, $s\sin\theta\,c_D+\cos\theta\,c_{D'}=0$, gives $\tan\theta=-c_{D'}/(s\,c_D)$; setting that of $D$ to zero, $\cos\theta\,c_D-s\sin\theta\,c_{D'}=0$, gives $\tan\theta=c_D/(s\,c_{D'})$. The survivor is $\pm\sqrt{c_D^2+c_{D'}^2}$ by norm conservation within the pair.

**A.3 The gradient identity and its pair decomposition.** $F(\theta)=(w\cdot e^{\theta\hat\kappa}\Psi)^2$ gives $F'(\theta)=2\,(w\cdot e^{\theta\hat\kappa}\Psi)\,(w\cdot\hat\kappa e^{\theta\hat\kappa}\Psi)$, so $F'(0)=2\,(w\cdot\Psi)(w\cdot\hat\kappa\Psi)$. Antisymmetry gives $\Psi\cdot\hat\kappa\Psi=-\hat\kappa\Psi\cdot\Psi=0$, hence $w\cdot\hat\kappa\Psi=(w-\Psi)\cdot\hat\kappa\Psi$. Writing $\hat\kappa=\sum_p s_p(|D'_p\rangle\langle D_p|-|D_p\rangle\langle D'_p|)$, $(\hat\kappa\Psi)_{D'_p}=s_p\Psi_{D_p}$ and $(\hat\kappa\Psi)_{D_p}=-s_p\Psi_{D'_p}$, so $w\cdot\hat\kappa\Psi=\sum_p s_p(w_{D'_p}\Psi_{D_p}-w_{D_p}\Psi_{D'_p})$.

**A.4 The Jacobian column.** With $v=R_n\cdots R_1\Psi$ and $\partial_\theta e^{\theta\hat\kappa}=\hat\kappa e^{\theta\hat\kappa}$, $\partial v/\partial\theta_k=R_n\cdots R_{k+1}\,\hat\kappa_{\mu_k}\,(R_k\cdots R_1\Psi)$: apply the letters up to $k$, hit with $\hat\kappa_{\mu_k}$, apply the rest. Restricting to off-reference components gives column $k$ of $J$. All columns cost $O(n^2)$ letter applications per Jacobian; the forward partials are shared.

**A.5 The reversal rule.** $(R_n\cdots R_1)^\dagger=R_1^\dagger\cdots R_n^\dagger$ and $R^\dagger=e^{-\theta\hat\kappa}$ (real antisymmetric generator). Therefore the preparation chain lists the compile letters in reverse order with negated angles, and applying it to $\Phi_0$ returns $W^\dagger\Phi_0$; when the compile is exact this equals $\Psi$.

**A.6 Currency identity.** For a unit vector $v$, $1-v_{\Phi_0}^2=\sum_{D\ne\Phi_0}v_D^2$. Writing $v=\Phi_0+\delta$ with $\delta\perp\Phi_0$ to first order, $R\approx\|\delta\|^2$; the gate $10^{-12}$ is a vector error of $10^{-6}$.

**A.7 Parameter counting.** A real unit vector on $d$ determinants lives on $S^{d-1}$, dimension $d-1$; the routed chain has support $-1=d-1$ angles (minus symmetry-locked skips). A chain with $p$ free angles sweeps a manifold of dimension at most $p$; hitting an arbitrary nearby point requires $p\ge d-1$ *and* a Jacobian of rank $d-1$ at the solution. Frozen routing therefore needs at least $d-1$ grown angles (nine in the example); free routing needs enough grown letters to complete the rank (two in the example).

---

## Appendix B. Glossary

- **letter** — one primitive factor $e^{\theta\hat\kappa_\mu}$; **chain** — an ordered product of letters; the chain "spells" the state.
- **substitution** $\mu=(I,A)$ — annihilate the spin-orbitals in $I$, create those in $A$; **rank** $r=|I|=|A|$; a general substitution need not start from the reference's occupied set.
- **pool** — admissible letters: rank ≤ 2, conserving the Hamiltonian's symmetries; the SD edges of the H-connected graph.
- **domain / range / pair / sibling** — determinants a letter can act on, their partners, the two-element sets they form, and the other pairs of the same letter.
- **collateral** — motion of sibling pairs when a letter is applied to zero one coefficient; **fill-in** — collateral that populates determinants outside the support.
- **support** — determinants with $|c_D|$ above the amplitude floor; **level** — excitation level relative to the reference; **block** — H-connected component of the reference.
- **compile direction** — letters applied to $\Psi$ toward $\Phi_0$; **preparation direction** — the reversed, negated chain applied to $\Phi_0$; **prepared state** $w=W^\dagger\Phi_0$ of a partial chain.
- **routing sweep** — Stage 1a: closed-form Givens zeroing along SD edges, outermost first; **routed** — its letters.
- **growth** — Stage 1b: rounds of gradient-scored letter insertion and least-squares angle re-solve; **grown** — its letters; **round**, **batch**, **plateau** (variational floor of a fixed letter set), **gate** ($R<10^{-12}$).
- **torque** — a pair's contribution $s_p(w_{D'}\Psi_D-w_D\Psi_{D'})$ to the selection score; the misalignment of $w$ and $\Psi$ inside that pair's plane.
- **residual currency** — fidelity deficit versus off-reference sum (Section 10.7).
- **direct mode** — one straight-shot letter per support determinant of whatever rank; control arm and instrument, never the route.
- **symmetry gift** — a sibling pair locked to the target pair so one angle zeroes both; lowers the routed count below support $-1$.
- **certificate** — per-instance numerical evidence of exactness: compile residual, preparation check, energy check, count identities, translation acceptance.

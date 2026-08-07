# tucc-chain-compile

Compile an exact eigenstate of a small model Hamiltonian into an **ordered
product of factorized-UCC rotations** ("a chain"), truncate it factor by
factor with an exact bookkeeping ledger, and **translate** the resulting
state into CC cluster amplitudes with the distortion reported honestly.

The package is the worked-validation companion to the TUCC project's
chain-selection work. It implements, end to end and in plain NumPy:

- the Givens-rotation content of the factorized UCC ansatz of
  Xu, Lee and Freericks (MPLB 2020, "P2"), whose Eq. (6) block rotation is
  the primitive move here;
- the per-factor UCC <-> CC disentangling of Freericks (Symmetry 2022,
  "P1"), `exp(theta(A - Adag)) = exp(tan(theta) A) * exp(-ln cos(theta)
  (A Adag - Adag A)) * exp(-tan(theta) Adag)`, which is why every compiled
  angle is kept strictly inside `|theta| < pi/2`;
- an "exact chain solver" in the spirit of the Evangelista-Chan-Scuseria
  ordered-product analysis: ordering is part of the ansatz, and the
  compiler treats it that way.

Momentum-space Hubbard rings (L = 4, 6 at half filling) are the testbed:
small enough to check everything against exact diagonalization, rich
enough to exhibit degenerate Fermi seas, excited roots in nonzero-K
sectors, and genuine rank-6 correlations.

## What it produces

Two compile modes, one ledger format:

- `mode="direct"`: sequential Givens elimination, highest rank first.
  Factor ranks follow the target's excitation content (quadruples,
  hextuples where the state demands them). The truncation curve is
  **monotone by theorem**: after K elimination steps the K-prefix
  fidelity equals the pivot amplitude recorded in the ledger, exactly.
- `mode="sd_paired"`: the spin-graded variant -- same rank<=2 primitive
  letters, applied as spin-flip-tied pairs after overlap-ablated
  routing, so truncated prefixes stay graded by (-1)^S (triplet
  admixture suppressed 5-13x, endpoint exactly spin-pure). Costs
  3.4-5.6x chain length; see docs/METHOD.md section 14.
- `mode="sd_routed"`: every factor is a generalized single or double.
  Higher-rank structure is reached by routing through synthetic
  intermediates; angles are solved jointly (greedy anytime
  initialization + bounded Gauss-Newton + tangent-completion growth).
  Chains are much shorter than the direct ones and every factor is
  CC-translatable, at the cost of a non-monotone prefix curve
  (documented, measured, and explained in `docs/METHOD.md`).

Every compile emits: the factor list `(substitution, theta)` in
preparation order, a per-step ledger (`fid_after`, touched amplitudes,
angle flags), K-truncation tables (fidelity, variational dE, angle and
rank profile), roots tables with <S^2> and K labels, and -- for the
translation demo -- exact cluster analysis `|psi> = exp(T)|pivot>` plus
the SD-rank-capped rebuild `exp(T1+T2)|pivot>` with its fidelity and
energy distortion stated next to the exact numbers.

## Install and run

Plain `pip`; NumPy is the only runtime dependency (pytest for tests).
Works in a bare venv -- no conda/Psi4 required for anything in this repo.

PowerShell (Windows):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[test]"
python -u examples\run_hubbard.py
pytest -q
```

bash (Linux/macOS):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
python -u examples/run_hubbard.py
pytest -q
```

`examples/run_hubbard.py` regenerates everything under `results/`
(~20 s on a laptop): L=6 U=2 and U=6 ground states in both modes, K-grid
truncation tables for each, the U=6 translation demo with amplitude
export, an excited-root compile (root 2, S^2 ~ 0, K = 3), and the L=4 U=8
lattice of P2 with its degenerate Fermi sea (the direct compile uses 5
quadruple factors -- Table 1's quad rotation -- which the SD router
replaces with a 13-doubles chain).

## Results snapshot (committed under `results/`)

| system | mode | length | ranks | max abs theta | fidelity |
|---|---|---|---|---|---|
| L6 U2 GS | sd_routed | 84 | all doubles | 0.611 | 1.0 (exact) |
| L6 U2 GS | direct | 220 | 2:25 3:16 4:97 6:82 | 0.109 | 1.0 (exact) |
| L6 U6 GS | sd_routed | 76 | all doubles | 1.549* | 1.0 (exact) |
| L6 U6 GS | direct | 220 | 2:25 3:16 4:97 6:82 | 0.363 | 1.0 (exact) |
| L6 U6 root 2 (K=3) | sd_routed | 84 | all doubles | 1.526* | 1.0 (exact) |
| L4 U8 GS | sd_routed | 13 | all doubles | 0.787 | 1.0 (exact) |
| L4 U8 GS | direct | 13 | 2:8 4:5 | 0.748 | 1.0 (exact) |

`*` one letter saturates the solver's angle bound (pi/2 - 0.02,
tan theta ~ 45-50); it is flagged in the ledger, and still strictly
inside the disentangling window. All choices among symmetry-tied
amplitudes are canonically tie-broken, so these chains regenerate
identically on any platform (docs/METHOD.md section 13). Translation demo (L6 U6 GS): cluster-analysis
rebuild error 0.0; SD-capped `exp(T1+T2)|pivot>` fidelity **0.986730**,
dE **+197.5 mt** -- the honest cost of throwing away T3/T4/T6.

## Scope and non-goals

- **State-level translation.** `translate.py` does exact cluster analysis
  of the compiled chain state and rank-capped rebuilds. Operator-level
  normal-ordered translation of the factor product itself (P1's algebra
  carried out factor-by-factor into a single normal-ordered exp(T)) is a
  roadmap item, not implemented here.
- **Standalone sign bookkeeping.** This repo carries its own
  fermionic-parity code (`dets.py`) as a scoped exception to the
  project-wide "never re-implement sign bookkeeping" rule, so that the
  validation is self-contained and pip-only. A parity adapter that
  delegates to the `upgradation` (Psi4) environment's machinery is the
  planned reconciliation; the module boundary (`Substitution`,
  `substitution_between`, `parity`) was drawn to make that swap local.
- Model spaces: momentum-space Hubbard rings and hydrogen systems
  (H2, H4, H6) with the self-contained s-only Gaussian bases in
  `molecular.py` (STO-3G and 6-31G), RHF references, no-momentum
  routing. p functions and non-hydrogen atoms are exactly the Psi4
  integration hand-off (roadmap); symmetry beyond (N_up, N_dn[, K])
  and complex orbitals remain out of scope.

## Integration notes (prototype translation suite)

`results/amps_*.json` follows schema `chaincompile.amps.v0`: per-rank
amplitude lists keyed by hole/part spin-orbital tuples, with the pivot
determinant, ordering note, and the chain's angle list included. These
files are meant to be fed to the prototype suite's `amps:<file.json>`
subjects. Angles map to per-factor CC amplitudes via `t = tan(theta)`
(P1); the exporter stores theta, so the bridge is one `math.tan` away and
stays finite because every angle is bounded away from pi/2.

Stage-1 wiring: `disentangle.py` consumes the chain JSONs with an
independent determinant kernel (ported from the upgradation symbolic
engine) and certifies them -- kernel-vs-vector agreement <= 2.2e-16,
eigenstate round-trip infidelity 0.0 -- then scores the first-order
operator-valued (secant) dressing law against exact cluster amplitudes.
Measured result: exact on two-factor probes, dominated by folded terms
on deep chains; see docs/METHOD.md section 11.

Multi-root outputs follow the ADR-003 convention: roots tables label each
state with energy, <S^2>, total momentum K, and dominant determinant, so
downstream ingestion can select roots by symmetry label rather than
index.

## Repository layout

```
src/chaincompile/   dets, sector, hubbard, factors, compile, translate,
                    diagnostics, disentangle (Stage-1 kernel + dressing law),
                    normalorder (constructive composer, stage i)
Optional speed: `pip install -e ".[test,fast]"` adds numba, which
compiles the H-application kernel behind the Davidson iterative
eigensolver (`fastpath.py`); everything runs without it, slower. The
compiled and pure paths are held equal by tests. Check which path
is active with:
`python -c "from chaincompile.fastpath import status; status()"`
(the fallback is correct but ~40x slower on kernel-bound work).

Psi4 workflow (two environments, one file): in the conda env run
`python examples/psi4_export.py --system h4_rect --basis 6-31g --out
dump.npz`; in this env run `python -u examples/run_psi4_dump.py
dump.npz`. The certification identity gates every dump.

examples/           run_hubbard.py  (regenerates results/)
                    run_stage1.py   (certification: kernel, JSON round trip,
                                     dressing law; run after run_hubbard)
                    run_noc_i.py, run_noc_ii.py  (constructive translation
                                     reports, stages i-ii)
                    run_h4.py       (H4 molecular validation)
                    run_hn_scaling.py (H2/H4/H6, 6-31G, measured laws)
                    run_hn_sd.py    (molecular SD chains + translation,
                                     minutes-tier)
                    psi4_export.py  (conda-side exporter; standalone)
                    run_psi4_dump.py (ingest a dump: identity, roots,
                                     compile, translation)
                    run_big_sd.py   (resumable chain compiler for
                                     large supports; rerun until DONE)
results/            committed outputs of the worked validation
docs/METHOD.md      conventions, theorems, counterexamples, solver design
tests/              pytest suite (17 tests, all exact-value checks)
```

License: choose before publishing (nothing in-tree presumes one).

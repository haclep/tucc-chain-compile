# data/

Frozen artifacts. Nothing here is live state — live checkpoints stay
untracked (see .gitignore).

## c2_2348_bigsd_frozen_v0.1.0.pkl

Resumable-compiler checkpoint, C2 dimer frozen-core (8e, 8o) active
space, R = 2.348 bohr. Snapshot taken at v0.1.0. First dense-impossible
exact ground state carried through big-SD chain compilation.

- c2_2348_chain.npz -- equilibrium C2 singlet ground chain (3202 letters,
  ranks {2:3147, 1:55}, residual 6.4e-15, acceptance 2.6e-16): the
  flagship sd chain. From examples/run_big_sd.py on c2_2348.npz,
  frozen-core (8e,8o).
- c2_2348_triplet_pair_chain.npz -- the wrong-root night's chain (2767
  letters): arbitrary mixture of the degenerate triplet Pi pair at
  -74.63998153, +49.77 mHa. First compiled excited-state chain;
  comparison point for the chain-length-vs-correlation law (METHOD 22e).

WARNING: this is a Python pickle. Loading it executes arbitrary code.
Do not open pickles from sources you do not trust — including this one,
unless you trust this repo.


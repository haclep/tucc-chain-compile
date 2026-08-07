"""Translation stage (ii) report: the committed chains constructively
translated, with the measured complexity law."""
import os
import time

import numpy as np

from chaincompile.compile import compile_chain
from chaincompile.dets import Substitution
from chaincompile.diagnostics import write_text
from chaincompile.hubbard import hamiltonian
from chaincompile.sector import SectorBasis
from chaincompile import disentangle as dz
from chaincompile import normalorder as NO

RES = os.path.join(os.path.dirname(__file__), "..", "results")


def pstr(p):
    out = []
    for e, w in sorted(p.terms.items()):
        parts = []
        for k in range(p.n):
            if e[k]:
                parts.append(f"s{k+1}" + (f"^{e[k]}" if e[k] > 1 else ""))
            if e[p.n + k]:
                parts.append(f"c{k+1}" + (f"^{e[p.n+k]}" if e[p.n+k] > 1
                                          else ""))
        out.append(("+" if w > 0 else "-")
                   + ("" if abs(w) == 1 and parts else str(abs(w)))
                   + " ".join(parts))
    return " ".join(out) or "0"


def chain(L, U_):
    basis = SectorBasis(L, L // 2, L // 2)
    evals, evecs = np.linalg.eigh(hamiltonian(basis, U=U_))
    res = compile_chain(evecs[:, 0], basis, mode="sd_routed")
    word = [s for s, _ in res.selected()]
    th = [t for _, t in res.selected()]
    occ = frozenset(p for p in range(2 * L) if (res.pivot_mask >> p) & 1)
    return word, th, occ


def acceptance(c0, amps, word, th, occ):
    state = {tuple(sorted(occ)): 1.0}
    for sub, t in zip(word, th):
        state = dz.apply_factor(sub, float(t), state, tol=0.0)
    ref = tuple(sorted(occ))
    dev = abs(c0 - state.get(ref, 0.0))
    for (h, p), w in amps.items():
        det, sg = dz.apply_A(Substitution(h, p), ref)
        dev = max(dev, abs(w - sg * state.get(det, 0.0)))
    return dev, sum(1 for v in state.values() if abs(v) > 1e-12)


lines = ["# Translation stage (ii) -- the committed chains, constructively\n"]

# L4: symbolic, full curves, closed forms
word, th, occ = chain(4, 8.0)
thv = np.array(th)
Up, sp = NO.compose(word, occ, prune_ann=True)
t0 = time.time()
Uf, sf = NO.compose(word, occ, prune_ann=False)
tf = time.time() - t0
c0, amps = NO.ref_amplitudes(Up, occ)
dev, n_state = acceptance(c0.eval(thv),
                          {k: p.eval(thv) for k, p in amps.items()},
                          word, th, occ)
quad = amps[((0, 1, 2, 3), (4, 5, 6, 7))]
psz = sorted((len(p.terms) for p in amps.values()), reverse=True)
lines += [
    f"## L4 U8 chain (13 letters), symbolic\n",
    f"Acceptance: max |engine - chain state| = {dev:.2e} over all "
    f"{n_state} amplitudes. Creator-projected term curve {sp} "
    f"(saturates at the state support, 10). Full-operator curve {sf} "
    f"(saturates at 898 of the 65536 bound; {tf:.1f} s).\n",
    f"Coefficient-polynomial sizes (exact pathway terms per amplitude): "
    f"{psz}; c0 has {len(c0.terms)} terms.\n",
    f"The quad amplitude's complete closed form through all 13 letters "
    f"(9 pathway terms):\n\n    t(0123 -> 4567) * c0 = {pstr(quad)}\n",
]

# L6: numeric-coefficient constructive evaluation
word, th, occ = chain(6, 6.0)
t0 = time.time()
U6, s6 = NO.compose_numeric(word, th, occ)
t6 = time.time() - t0
c0n, ampsn = NO.numeric_ref_amplitudes(U6, occ)
dev6, n6 = acceptance(c0n, ampsn, word, th, occ)
lines += [
    f"## L6 U6 chain (76 letters), numeric coefficients\n",
    f"Acceptance: max |engine - chain state| = {dev6:.2e} over all "
    f"{n6} amplitudes; {len(ampsn) + 1} creator monomials "
    f"(= state support), composed in {t6:.1f} s. Term-curve tail "
    f"{s6[-6:]} -- saturated.\n",
    "## The complexity law (stage-iii verdict)\n",
    "Operator-monomial count saturates at the reachable state support "
    "in BOTH the creator projection and the full operator -- the "
    "collapsing regime, not tensor growth. The true growth axis is "
    "symbolic pathway counting inside the coefficient polynomials "
    "(88-term amplitudes already at L4; prohibitive by mid-word at "
    "L6). Production representation therefore: symbolic closed forms "
    "where pathway counts stay small (few-factor identities, L4-scale "
    "chains), and the numeric-coefficient constructive evaluation -- "
    "same exact Wick algebra over a float field -- for real chains.\n",
]
write_text(os.path.join(RES, "noc_stage_ii.md"), "\n".join(lines))
print("-> results/noc_stage_ii.md")

"""Molecular SD chains + constructive translation (minutes-tier).

Runs sd_routed on the H6/STO-3G ring (support 160) and H4/6-31G
rectangle (support 208), then constructively translates both chains
and verifies every amplitude -> results/hn_sd.md. ~3 minutes; the fast
overview lives in run_hn_scaling.py. Report contains deterministic
content only (timings are console-side)."""
import os
import time

import numpy as np

from chaincompile.compile import compile_chain
from chaincompile.dets import Substitution
from chaincompile.diagnostics import write_text
from chaincompile.molecular import (build_h_sector, hydrogen_integrals,
                                    mo_integrals, rhf)
from chaincompile.sector import SectorBasis
from chaincompile import disentangle as dz
from chaincompile import normalorder as NO

RES = os.path.join(os.path.dirname(__file__), "..", "results")


def ground_state(cent, basis_name, ndocc, nmo, damp):
    S, T, V, ERI, enuc = hydrogen_integrals(cent, basis_name)
    C, eps, e_el, conv = rhf(S, T + V, ERI, ndocc, damp=damp)
    h, e = mo_integrals(C, T + V, ERI)
    sb = SectorBasis(nmo, ndocc, ndocc)
    H = build_h_sector(h, e, sb)
    w, Vv = np.linalg.eigh(H)
    return sb, Vv[:, 0]


def sd_and_translate(tag, sb, v0, nso, lines):
    t0 = time.time()
    res = compile_chain(v0, sb, mode="sd_routed")
    t_sd = time.time() - t0
    word = [s for s, _ in res.selected()]
    th = [t for _, t in res.selected()]
    occ = frozenset(p for p in range(nso) if (res.pivot_mask >> p) & 1)
    t0 = time.time()
    U, sizes = NO.compose_numeric(word, th, occ)
    c0, amps = NO.numeric_ref_amplitudes(U, occ)
    ref = tuple(sorted(occ))
    state = {ref: 1.0}
    for sub, t in zip(word, th):
        state = dz.apply_factor(sub, float(t), state, tol=0.0)
    dev = abs(c0 - state.get(ref, 0.0))
    for (h, p), w_ in amps.items():
        det, sg = dz.apply_A(Substitution(h, p), ref)
        dev = max(dev, abs(w_ - sg * state.get(det, 0.0)))
    t_noc = time.time() - t0
    sup = int(np.sum(np.abs(v0) > np.sqrt(1e-12) / sb.dim))
    lines.append(
        f"## {tag}\n\n"
        f"sd_routed: length {res.length}, ranks {res.rank_counts()}, "
        f"max|theta| {res.max_abs_theta():.6f}, residual "
        f"{res.final_residual:.1e}, support {sup}, grown "
        f"{res.solver_info['grown']}. Constructive translation: "
        f"{len(amps) + 1} creator monomials, acceptance {dev:.1e}, "
        f"term-curve tail {sizes[-3:]}.\n")
    print(f"{tag}: sd {t_sd:.1f}s (len {res.length}), NOC {t_noc:.1f}s "
          f"(dev {dev:.1e})", flush=True)


def main():
    lines = [
        "# Molecular SD chains, constructively translated\n",
        "The guiding principle end to end at molecular scale: find the "
        "chain of primitive (rank <= 2) UCC factors, then translate that "
        "chain exactly. Enabled by the batched Jacobian (bitwise-"
        "equivalent to the scalar build; tests/test_normalorder.py) and "
        "the raised growth-round cap (a no-op for every previously "
        "converging system -- Hubbard canonicals verified unchanged).\n"]
    R = 1.9
    cent6 = np.array([[np.cos(2*np.pi*k/6), np.sin(2*np.pi*k/6), 0.0]
                      for k in range(6)]) * (R / (2*np.sin(np.pi/6)))
    sb, v0 = ground_state(cent6, "sto-3g", 3, 6, 0.3)
    sd_and_translate("H6 / STO-3G ring (side 1.9 bohr)", sb, v0, 12, lines)
    cent4 = np.array([[0, 0, 0], [2.0, 0, 0], [0, 2.5, 0], [2.0, 2.5, 0]],
                     float)
    sb, v0 = ground_state(cent4, "6-31g", 2, 8, 0.2)
    sd_and_translate("H4 / 6-31G rectangle 2.0 x 2.5 bohr", sb, v0, 16,
                     lines)
    lines.append(
        "Observations: the full physical states compile SHORTER and "
        "faster than their own hard truncations (smooth amplitude tails "
        "are easier targets than sharp cutoffs); molecular sd chains "
        "carry rank-1 letters (singles content absent on the "
        "half-filled lattice); creator-monomial counts land at the "
        "state support, extending the section-16 complexity law "
        "off-lattice at 4-5x the previously validated support.\n")
    write_text(os.path.join(RES, "hn_sd.md"), "\n".join(lines))
    print("-> results/hn_sd.md")


if __name__ == "__main__":
    main()

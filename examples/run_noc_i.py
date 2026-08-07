"""Translation stage (i) report: the constructive composer's verified
identities and the first points of the complexity curve."""
import os
import numpy as np
from chaincompile.dets import Substitution
from chaincompile import normalorder as NO
from chaincompile.diagnostics import write_text

RES = os.path.join(os.path.dirname(__file__), "..", "results")

def pstr(p):
    out = []
    for e, w in sorted(p.terms.items()):
        parts = []
        for k in range(p.n):
            if e[k]: parts.append(f"s{k+1}" + (f"^{e[k]}" if e[k] > 1 else ""))
            if e[p.n+k]: parts.append(f"c{k+1}" + (f"^{e[p.n+k]}" if e[p.n+k] > 1 else ""))
        out.append(("+" if w > 0 else "-") + ("" if abs(w) == 1 and parts else str(abs(w))) + " ".join(parts))
    return " ".join(out) or "0"

cases = [
    ("shared-occupied singles", [Substitution((0,), (2,)), Substitution((0,), (3,))], (0, 1)),
    ("shared-virtual doubles", [Substitution((0, 1), (4, 5)), Substitution((2, 3), (4, 5))], (0, 1, 2, 3)),
    ("disjoint doubles", [Substitution((0, 1), (4, 5)), Substitution((2, 3), (6, 7))], (0, 1, 2, 3)),
    ("routed cascade", [Substitution((0,), (2,)), Substitution((2,), (4,))], (0, 1)),
    ("three singles", [Substitution((0,), (2,)), Substitution((0,), (3,)), Substitution((1,), (2,))], (0, 1)),
]
lines = ["# Translation stage (i) -- constructive normal-ordered composer\n",
         "Each factor is EXACTLY the degree-2 polynomial I + s kappa + "
         "(c-1)(A Adag + Adag A); a word is a finite product, normal-"
         "ordered by exact Wick algebra with integer coefficients in "
         "{s_k, c_k}. No BCH series anywhere. Operator-level equality "
         "with the independent tuple kernel holds to 1e-12 on every "
         "tested shape (tests/test_normalorder.py).\n"]
for label, word, occ in cases:
    U, sizes = NO.compose(word, frozenset(occ))
    c0, amps = NO.ref_amplitudes(U, frozenset(occ))
    lines.append(f"## {label}\n\nterm counts per multiplication: {sizes}; "
                 f"c0 = {pstr(c0)}\n")
    for (h, p), poly in sorted(amps.items()):
        lines.append(f"- {h} -> {p}: {pstr(poly)}")
    lines.append("")
lines.append(
    "Readings: the secant dressing is the ABSENCE of the partner cosine "
    "(disjoint partners contribute s1 c2; sharing deletes c2, and "
    "s1/(c1 c2) = tan sec). Routed composites obey t(0->4) = "
    "tan(t1) sin(t2) -- a new exact mini-law. Disconnected quads carry "
    "s1 s2 exactly (connected T4 = 0 for disjoint doubles). Stage (ii): "
    "the full L4 13-letter chain vs cluster-analysis T; the sizes column "
    "above seeds the stage-(iii) complexity curve.")
write_text(os.path.join(RES, "noc_stage_i.md"), "\n".join(lines) + "\n")
print("-> results/noc_stage_i.md")

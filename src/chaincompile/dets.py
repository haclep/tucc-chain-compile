"""Bitmask determinants + second-quantized operator application with signs.

Scope note (see repo CLAUDE.md): the Procopius prototype defers sign
bookkeeping to the solver's `upgradation` package. This repo is a
*standalone* validation prototype, so it carries its own minimal,
machine-precision-tested sign machinery. A parity adapter against
`upgradation` is a roadmap item, not done here.

Conventions
-----------
- Spin-orbital index:  so = 2*m + sigma  with orbital m in [0, L),
  sigma = 0 (up) / 1 (down).
- A determinant is an int bitmask over spin-orbitals:
      |mask> = prod_{p in mask, ascending p} cdag_p |vac>
- Elementary actions (0 result if Pauli-forbidden):
      c_p    |mask> = (-1)^{#occupied below p} |mask without p>
      cdag_p |mask> = (-1)^{#occupied below p} |mask with p>
- A substitution ("primitive" excitation pattern) is an ordered pair of
  disjoint sorted tuples (holes, parts). Its excitation operator A is
  applied as the op sequence  [c_{i1}, c_{i2}, ..., cdag_{a1}, cdag_{a2}, ...]
  (first listed = first applied to the ket). Adag is the exact adjoint:
  the reversed sequence with c <-> cdag. Adjointness is verified in tests
  by comparing dense matrices.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def popcount(x: int) -> int:
    return bin(x).count("1")


def _parity_below(mask: int, p: int) -> int:
    return -1 if (popcount(mask & ((1 << p) - 1)) & 1) else 1


def annihilate(mask: int, p: int):
    """Apply c_p. Returns (new_mask, sign) or (None, 0)."""
    if not (mask >> p) & 1:
        return None, 0
    return mask & ~(1 << p), _parity_below(mask, p)


def create(mask: int, p: int):
    """Apply cdag_p. Returns (new_mask, sign) or (None, 0)."""
    if (mask >> p) & 1:
        return None, 0
    return mask | (1 << p), _parity_below(mask, p)


def apply_ops(mask: int, ops):
    """Apply a sequence of ('c'|'cd', p), first element applied first."""
    s = 1
    for kind, p in ops:
        mask, sg = (annihilate if kind == "c" else create)(mask, p)
        if mask is None:
            return None, 0
        s *= sg
    return mask, s


@dataclass(frozen=True, order=True)
class Substitution:
    """Primitive substitution: move electrons out of `holes` into `parts`.

    holes and parts are sorted tuples of spin-orbital indices, disjoint.
    rank = len(holes) = len(parts).
    """

    holes: tuple = field(default=())
    parts: tuple = field(default=())

    def __post_init__(self):
        h, p = tuple(self.holes), tuple(self.parts)
        if len(h) != len(p):
            raise ValueError("holes and parts must have equal length")
        if tuple(sorted(h)) != h or tuple(sorted(p)) != p:
            raise ValueError("holes and parts must be sorted tuples")
        if set(h) & set(p):
            raise ValueError("holes and parts must be disjoint")
        object.__setattr__(self, "holes", h)
        object.__setattr__(self, "parts", p)

    # ------------------------------------------------------------------
    @property
    def rank(self) -> int:
        return len(self.holes)

    def a_ops(self):
        return [("c", i) for i in self.holes] + [("cd", a) for a in self.parts]

    def adag_ops(self):
        swap = {"c": "cd", "cd": "c"}
        return [(swap[k], p) for k, p in reversed(self.a_ops())]

    def apply_a(self, mask: int):
        return apply_ops(mask, self.a_ops())

    def apply_adag(self, mask: int):
        return apply_ops(mask, self.adag_ops())

    # pattern tests --------------------------------------------------------
    def hole_mask(self) -> int:
        m = 0
        for i in self.holes:
            m |= 1 << i
        return m

    def part_mask(self) -> int:
        m = 0
        for a in self.parts:
            m |= 1 << a
        return m

    def is_lower(self, mask: int) -> bool:
        """True if `mask` has all holes occupied and all parts empty
        (i.e. A can act; `mask` is the lower member of its block)."""
        return (mask & self.hole_mask()) == self.hole_mask() and (
            mask & self.part_mask()
        ) == 0

    def is_upper(self, mask: int) -> bool:
        return (mask & self.part_mask()) == self.part_mask() and (
            mask & self.hole_mask()
        ) == 0

    # pretty ---------------------------------------------------------------
    def label(self, L: int | None = None) -> str:
        def so_lab(p):
            if L is None:
                return str(p)
            return f"{p // 2}{'u' if p % 2 == 0 else 'd'}"

        h = ",".join(so_lab(i) for i in self.holes)
        a = ",".join(so_lab(i) for i in self.parts)
        return f"({h})->({a})"


def substitution_between(lower_mask: int, upper_mask: int) -> Substitution:
    """The unique primitive substitution whose A maps lower_mask -> upper_mask
    (up to sign). holes = bits in lower not in upper; parts = bits in upper
    not in lower."""
    holes = tuple(sorted(_bits(lower_mask & ~upper_mask)))
    parts = tuple(sorted(_bits(upper_mask & ~lower_mask)))
    return Substitution(holes, parts)


def _bits(mask: int):
    out = []
    p = 0
    while mask:
        if mask & 1:
            out.append(p)
        mask >>= 1
        p += 1
    return out


def bits(mask: int):
    """Sorted list of set bit positions (occupied spin-orbitals)."""
    return _bits(mask)

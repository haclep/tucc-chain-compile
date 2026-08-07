# Molecular SD chains, constructively translated

The guiding principle end to end at molecular scale: find the chain of primitive (rank <= 2) UCC factors, then translate that chain exactly. Enabled by the batched Jacobian (bitwise-equivalent to the scalar build; tests/test_normalorder.py) and the raised growth-round cap (a no-op for every previously converging system -- Hubbard canonicals verified unchanged).

## H6 / STO-3G ring (side 1.9 bohr)

sd_routed: length 298, ranks {2: 290, 1: 8}, max|theta| 1.550641, residual 0.0e+00, support 160, grown 139. Constructive translation: 174 creator monomials, acceptance 1.1e-16, term-curve tail [180, 180, 174].

## H4 / 6-31G rectangle 2.0 x 2.5 bohr

sd_routed: length 293, ranks {2: 283, 1: 10}, max|theta| 0.592462, residual 1.3e-15, support 208, grown 86. Constructive translation: 208 creator monomials, acceptance 9.7e-17, term-curve tail [208, 208, 208].

Observations: the full physical states compile SHORTER and faster than their own hard truncations (smooth amplitude tails are easier targets than sharp cutoffs); molecular sd chains carry rank-1 letters (singles content absent on the half-filled lattice); creator-monomial counts land at the state support, extending the section-16 complexity law off-lattice at 4-5x the previously validated support.

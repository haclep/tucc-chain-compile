# Translation stage (ii) -- the committed chains, constructively

## L4 U8 chain (13 letters), symbolic

Acceptance: max |engine - chain state| = 1.11e-16 over all 10 amplitudes. Creator-projected term curve [2, 4, 6, 6, 8, 8, 10, 10, 10, 10, 10, 10, 10] (saturates at the state support, 10). Full-operator curve [18, 324, 385, 422, 529, 584, 751, 850, 870, 888, 898, 898, 898] (saturates at 898 of the 65536 bound; 12.7 s).

Coefficient-polynomial sizes (exact pathway terms per amplitude): [88, 88, 88, 88, 9, 8, 8, 4, 4]; c0 has 9 terms.

The quad amplitude's complete closed form through all 13 letters (9 pathway terms):

    t(0123 -> 4567) * c0 = +c1 c2 c3 c4 c5 c6 s7 s8 c9 +c1 c2 c3 c4 s5 s6 c7 c8 c9 +c1 c2 s3 s4 c5 c6 c7 c8 c9 +c1 c2 s3 s4 s5 s6 s7 s8 c9 +s1 c2 s9 +s1 s2 c3 c4 c5 c6 c7 c8 c9 +s1 s2 c3 c4 s5 s6 s7 s8 c9 +s1 s2 s3 s4 c5 c6 s7 s8 c9 +s1 s2 s3 s4 s5 s6 c7 c8 c9

## L6 U6 chain (76 letters), numeric coefficients

Acceptance: max |engine - chain state| = 3.33e-16 over all 68 amplitudes; 68 creator monomials (= state support), composed in 3.8 s. Term-curve tail [68, 68, 68, 68, 68, 68] -- saturated.

## The complexity law (stage-iii verdict)

Operator-monomial count saturates at the reachable state support in BOTH the creator projection and the full operator -- the collapsing regime, not tensor growth. The true growth axis is symbolic pathway counting inside the coefficient polynomials (88-term amplitudes already at L4; prohibitive by mid-word at L6). Production representation therefore: symbolic closed forms where pathway counts stay small (few-factor identities, L4-scale chains), and the numeric-coefficient constructive evaluation -- same exact Wick algebra over a float field -- for real chains.

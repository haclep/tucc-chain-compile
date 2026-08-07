# Translation stage (i) -- constructive normal-ordered composer

Each factor is EXACTLY the degree-2 polynomial I + s kappa + (c-1)(A Adag + Adag A); a word is a finite product, normal-ordered by exact Wick algebra with integer coefficients in {s_k, c_k}. No BCH series anywhere. Operator-level equality with the independent tuple kernel holds to 1e-12 on every tested shape (tests/test_normalorder.py).

## shared-occupied singles

term counts per multiplication: [6, 18]; c0 = +c1 c2

- (0,) -> (2,): +s1
- (0,) -> (3,): +c1 s2

## shared-virtual doubles

term counts per multiplication: [18, 81]; c0 = +c1 c2

- (0, 1) -> (4, 5): +s1
- (2, 3) -> (4, 5): +c1 s2

## disjoint doubles

term counts per multiplication: [18, 324]; c0 = +c1 c2

- (0, 1) -> (4, 5): +s1 c2
- (0, 1, 2, 3) -> (4, 5, 6, 7): +s1 s2
- (2, 3) -> (6, 7): +c1 s2

## routed cascade

term counts per multiplication: [6, 18]; c0 = +c1

- (0,) -> (2,): +s1 c2
- (0,) -> (4,): +s1 s2

## three singles

term counts per multiplication: [6, 18, 61]; c0 = +c1 c2 c3

- (0,) -> (2,): +s1
- (0,) -> (3,): +c1 s2 c3
- (0, 1) -> (2, 3): +c1 s2 s3
- (1,) -> (2,): +c1 c2 s3

Readings: the secant dressing is the ABSENCE of the partner cosine (disjoint partners contribute s1 c2; sharing deletes c2, and s1/(c1 c2) = tan sec). Routed composites obey t(0->4) = tan(t1) sin(t2) -- a new exact mini-law. Disconnected quads carry s1 s2 exactly (connected T4 = 0 for disjoint doubles). Stage (ii): the full L4 13-letter chain vs cluster-analysis T; the sizes column above seeds the stage-(iii) complexity curve.

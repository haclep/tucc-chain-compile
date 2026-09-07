# Addendum B to the K1 Learnability Pre-Registration Protocol

**Project:** tucc-chain-compile | Seneca Labs
**Date:** 7 September 2026
**Amends:** `k1_learnability_preregistration.md` (drafted 2026-08-25); Addendum A (2026-08-30)
**Trigger:** Product Strategy Addendum B; the K1b-T4 pred arm result (18.9%, banked 5 Sept); external review of the harness code.

---

## 0. Scope — read first

**K1b-T4 is frozen and in flight (b2 arm running). Nothing in this addendum applies to it.** Sections 1 and 2 amend the umbrella K1 document's outcome interpretation (§9). Section 3 is a set of **[LOG NOW]** recording obligations against the K1b-T4 §8 deviation ledger, not amendments to it.

---

## 1. [K1 §9] D3's fate decoupled from the K1 verdict

§9 currently reads, under FAIL: "D3 dies." **Superseded.**

K1's object (§1) is the map F: system → certified chain. Its verdict states whether F is learnable by a small model. Whether the chains improve a model that trains on them is a different object, tested by DV-PS (`dv_downstream_value_preregistration.md`). Amended reading of §9:

    On PASS / WEAK PASS: D1–D4 as written.
    On FAIL: D2 and D4 unchanged; D1 survives as verification/provenance
             data; D3's status is DETERMINED BY DV-PS, not by K1.

Rationale. The process-supervision literature is the case where a learner benefits from studying traces it cannot itself produce. Coupling D3 to K1 assumed the opposite.

---

## 2. [K1 §9] D2 and certified labels underwritten by DV-LC

§9 lists D2 (exact amplitude sets with certificates) as sellable on any outcome. The technical claim a buyer will test — that certified labels improve a downstream model at measured sample efficiency — is tested by DV-LC. Record the dependency; D2's *sellability* is unaffected, its *evidence* is DV-LC.

---

## 3. [LOG NOW — K1b-T4 §8 ledger] Recordings from the pred and b2 arms and the harness review

Skip any line already carried by the 5 September ledger entry.

**3.1 Seed-line generality.** B2's 360 proposed letters degraded the routed residual from 2.165e-02 to 2.242e-01 (10.4x); pred's 383 degraded it 16.6x. The angle-harm finding is a property of appended proposals at nonzero angles from any source, not of the learned model. The joint solve recovers in ~12 cheap iterations either way. Strengthens the K1c θ = 0 design conclusion.

**3.2 Comparative clause under non-positive B2.** P1's second clause is multiplicative on B2's saving. If B2's saving is ≤ 0, 1.3 × B2 is vacuous and any positive pred saving would "clear" it trivially. Decided before B2 banks: in that case the comparative clause is reported as **UNTESTED**, not passed. (On current trajectory B2 is positive; moot in practice.)

**3.3 Single seed.** The K1b-T4 protocol froze pred at seed 0 (commit 6957f89). The umbrella K1 §6 specifies 5 seeds with mean and 95% CI. Both are true; the T4 verdict is a **single-seed measurement** and is to be stated as such in every write-up. The vocabulary cap (milestone §8.2(a), recorded 30 August before any arm banked) is seed-independent, so additional seeds are not expected to change the verdict's direction. That is an inference to record, not a substitute for the runs; the runs are a K1c-era decision.

**3.4 Wording reconciliation.** Protocol §5 says B2 orders "by the routing heuristic"; the harness orders B2's proposal round-robin by |t| after the shared routed prefix, which every arm orders identically. Consistent; recorded.

**3.5 Four-way chain comparison, scope.** The comparison of the campaign, cold, pred, and b2 chains for the H8 state is restricted to the grown portion, `word[n_routed:]`, since all arms share the 2,467 routed letters by construction (the oracle arms assert it). The four chains vary by proposal and, for cold versus campaign, by stopping rule — not by controlled rule perturbation. The result previews milestone §8.4 gauge averaging; it does not replace it. Six pairwise values give a distribution with wide error bars; the intersection is an estimate of the invariant core, not the core itself.

**3.6 Vocabulary cap, timing cross-reference.** The 48% recall ceiling was recorded in milestone §8.2(a) on 30 August, before any H8 arm banked. Cross-referenced here so that a reader of the ledger finds it predates the verdict.

---

## 4. Summary of changes

| item | applies to | status |
|---|---|---|
| D3 decoupled from K1 outcome | K1 §9 | amendment; in force |
| D2 evidence dependency on DV-LC | K1 §9 | recorded |
| Seed-line generality | K1b (ledger) | log now |
| Non-positive-B2 rule | K1b (ledger) | log now, before B2 banks |
| Single-seed statement | K1b (ledger) | log now |
| Wording reconciliation | K1b (ledger) | log now |
| Four-way comparison scope | K1b (ledger) | log now |
| Vocabulary-cap cross-reference | K1b (ledger) | log now |
| **K1b-T4 protocol itself** | — | **UNCHANGED** |

---

*Analysis in this addendum is Claude's. Sign-off is Logan's.*

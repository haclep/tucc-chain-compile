# Addendum B to the Product Strategy Memo

**Project:** tucc-chain-compile | Seneca Labs
**Date:** 7 September 2026
**Amends:** `senecae_product_strategy_2026-08-30.md` and Addendum A (2026-08-30)
**Trigger:** Planning the buyer-facing evidence for the data product while the K1b-T4 b2 arm runs.

---

## 0. Scope — read first

Per Addendum A §A8 the memo is not versioned before the K1b-T4 verdict. This addendum registers two experiments and one correction. It changes no product decision, no pricing, and nothing about the K1b-T4 race, which is frozen and in flight.

---

## 1. The gap

The memo's data-first decision rests on a claim the plan does not test: that training on certified data improves a downstream model.

K1 tests whether chains are predictable (the map system → chain). K2-VAR tests where variational construction fails. Neither asks the buyer's question: *if I train my model on your data, does it get better, and cheaper to train?* A buyer with an ML background asks that first. Today the honest answer is: the value of the information is measured (oracle arms); the value of training on it is not.

---

## 2. Two experiments, registered

Specification: `dv_downstream_value_preregistration.md` (draft; freeze by commit after the K1b-T4 verdict, before any training).

**DV-LC — Label quality as learning curves.** Same architecture, two training sets, paired on the same systems: certified-exact labels versus approximate labels (MP2 in the model space; DFT where the model space is the full basis). Evaluated on held-out certified labels, with the strong-correlation regime as the decisive split. Reports accuracy against training-set size and the sample-efficiency ratio. Underwrites D2 and the certified energies as labels: the "trusted ground truth" product.

**DV-PS — Process supervision.** A model trained with an auxiliary chain-content target versus the same model without it, versus a shuffled-chain control, on held-out hard systems. Underwrites D3 and the "learnable sequences for foundation models" framing.

---

## 3. Correction: D3's fate is decoupled from K1

K1 §9 states that on FAIL "D3 dies." That coupling is wrong. K1 determines whether chains are *predictable* (the learned-compiler product). DV-PS determines whether they are *useful as training data* (the D3 product). A chain can be unpredictable by a small model and still improve a model that studies it; the process-supervision literature is precisely that case. D3's fate moves to DV-PS. Recorded as K1 Addendum B §1.

---

## 4. What each result unlocks in the pitch

| claim | status today | unlocked by |
|---|---|---|
| Every label exact to 1e-12, replayed on an independent machine; zero label noise by construction | banked | — |
| Perfect knowledge of a chain is worth 660x on H8; content alone 10x on N2 | banked | — |
| A first-generation model with sub-48% vocabulary captured 19%, matching published perturbation theory | banked 5 Sept | — |
| Sequences are deterministic under a documented convention; the invariant fraction across conventions is X | in progress | four-way H8 chain comparison (grown portion) |
| Training on certified labels improves a downstream model by Y at Z samples | **withheld** | DV-LC |
| Training on the derivations improves generalization beyond any auxiliary target | **withheld** | DV-PS |

The two withheld sentences are the ones an ML buyer will test. They are not to be spoken, in any material, until DV banks.

---

## 5. Sequencing (Claude's proposal; Logan decides)

    K1b-T4 verdict (≈10–11 Sept) → DV-LC → DV-PS → K2-VAR → K1c

Rationale. The strategy is data-first, so the experiment that validates the data product precedes the experiment that improves the compiler. DV needs no compilation (the corpus is on disk), small models, and CPU-hours of compute; it costs days of attention. K1c is the larger commitment, and its priority depends on DV's answer: if DV passes, K1c is efficiency work on a validated product; if DV fails, the learned compiler becomes the product and K1c's priority rises. K2-VAR is registered for after 30 September and is unaffected either way.

One experiment at a time still holds. DV-LC and DV-PS run sequentially, each banked before the next starts.

---

## 6. Scale honesty

At 116 certified systems, mostly small, the corpus is an evaluation set and a proof of direction, not a training corpus. DV results at this scale establish sign and slope with error bars, not magnitude at foundation-model scale. The scale story remains the selected-CI front end (Addendum A §7-bis) and K1c corpus growth. This is to be said to buyers, not omitted; the distinction is respected more than the omission would be.

---

## 7. Pitch materials

DOE pitch (due 10 Sept): unchanged. "Each sequence is a worked solution an AI can study" states a property, not an outcome, and remains true.

Activate Technical Reality work-plan slide and the investor memo: list DV-LC and DV-PS as the next pre-registered experiments, with the K1b-T4 verdict and the four-way comparison as banked context. Do not state DV outcomes.

---

## 8. Summary of changes

| item | applies to | status |
|---|---|---|
| DV-LC registered | new experiment | draft; freeze after K1b-T4 verdict |
| DV-PS registered | new experiment | draft; freeze after K1b-T4 verdict |
| D3 decoupled from K1 outcome | K1 §9, this memo's data-product ladder | recorded; K1 Addendum B §1 |
| Withheld pitch sentences named | all external materials | in force now |
| Sequencing DV before K1c | plan | proposal; Logan decides |
| Product strategy memo body | — | **UNCHANGED** (per A8) |

---

*Analysis and recommendations in this addendum are Claude's. The sequencing decision, the DV thresholds, and sign-off are Logan's.*

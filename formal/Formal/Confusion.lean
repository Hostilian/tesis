import Formal.Count

/-!
# Agreement with the COS land-use map (confusion counts)

Python (`pipeline/src/robustness.py`, `confusion`):

```python
p = pred & domain;  r = ref & domain
tp = (p & r).sum();  fp = (p & ~r).sum()
fn = (~p & r & domain).sum();  tn = (domain & ~p & ~r).sum()
precision = tp / (tp + fp);  recall = tp / (tp + fn)      # NaN if denominator is 0
f1 = 2 * precision * recall / (precision + recall)
```

`reference_cos.binary_agreement` is the same with every pixel in the domain.
The code does not compute Cohen's kappa, so kappa is not modelled.

Model: each pixel has three yes/no values: flagged (`pred`), positive in the
reference map (`ref`), and inside the evaluation domain (`dom`).
-/

namespace Formal.Confusion

open Formal

/-- One evaluated pixel. -/
structure Px where
  pred : Bool
  ref : Bool
  dom : Bool

def tp (ps : List Px) : Nat := countWhere (fun p => p.dom && p.pred && p.ref) ps
def fp (ps : List Px) : Nat := countWhere (fun p => p.dom && p.pred && !p.ref) ps
def fn (ps : List Px) : Nat := countWhere (fun p => p.dom && !p.pred && p.ref) ps
def tn (ps : List Px) : Nat := countWhere (fun p => p.dom && !p.pred && !p.ref) ps

/-- Number of pixels in the evaluation domain. -/
def evaluated (ps : List Px) : Nat := countWhere (fun p => p.dom) ps

/-- Every evaluated pixel falls in exactly one of the four cells:
`tp + fp + fn + tn` = number of evaluated pixels. -/
theorem confusion_total (ps : List Px) : tp ps + fp ps + fn ps + tn ps = evaluated ps := by
  induction ps with
  | nil => simp [tp, fp, fn, tn, evaluated]
  | cons x xs ih =>
    simp only [tp, fp, fn, tn, evaluated, countWhere_cons] at *
    cases x with
    | mk pr rf dm => cases pr <;> cases rf <;> cases dm <;> simp <;> omega

/-- Pixels outside the domain never count in any cell. -/
theorem outside_domain_ignored (ps : List Px) (p : Px) (h : p.dom = false) :
    tp (p :: ps) = tp ps ∧ fp (p :: ps) = fp ps ∧ fn (p :: ps) = fn ps ∧ tn (p :: ps) = tn ps := by
  simp [tp, fp, fn, tn, countWhere_cons, h]

/-- Precision denominator `tp + fp` = number of flagged pixels in the domain. -/
theorem tp_add_fp (ps : List Px) : tp ps + fp ps = countWhere (fun p => p.dom && p.pred) ps := by
  unfold tp fp
  exact countWhere_split (fun p : Px => p.dom && p.pred) (fun p : Px => p.ref) ps

/-- Recall denominator `tp + fn` = number of reference-positive pixels in the domain. -/
theorem tp_add_fn (ps : List Px) : tp ps + fn ps = countWhere (fun p => p.dom && p.ref) ps := by
  induction ps with
  | nil => simp [tp, fn]
  | cons x xs ih =>
    simp only [tp, fn, countWhere_cons] at *
    cases x with
    | mk pr rf dm => cases pr <;> cases rf <;> cases dm <;> simp <;> omega

/-- Precision is at most 1: numerator ≤ denominator. -/
theorem precision_le_one (ps : List Px) : tp ps ≤ tp ps + fp ps := Nat.le_add_right _ _

/-- Recall is at most 1: numerator ≤ denominator. -/
theorem recall_le_one (ps : List Px) : tp ps ≤ tp ps + fn ps := Nat.le_add_right _ _

/-- F1 = 2tp / (2tp + fp + fn) is at most 1. -/
theorem f1_le_one (ps : List Px) : 2 * tp ps ≤ 2 * tp ps + fp ps + fn ps := by omega

/-- Accuracy-style share of agreeing pixels is at most 1. -/
theorem agreement_le_one (ps : List Px) : tp ps + tn ps ≤ evaluated ps := by
  have := confusion_total ps
  omega

/-- When precision is undefined (no flagged pixels), there are no true positives either. -/
theorem precision_undefined_tp_zero (ps : List Px) (h : tp ps + fp ps = 0) : tp ps = 0 := by
  omega

/-- Swapping the roles of "flagged" and "reference" swaps false positives and false
negatives (so precision and recall swap) and keeps tp and tn. -/
theorem swap_pred_ref (ps : List Px) :
    let sw := ps.map (fun p => { p with pred := p.ref, ref := p.pred })
    tp sw = tp ps ∧ fp sw = fn ps ∧ fn sw = fp ps ∧ tn sw = tn ps := by
  induction ps with
  | nil => simp [tp, fp, fn, tn]
  | cons x xs ih =>
    simp only [List.map_cons, tp, fp, fn, tn, countWhere_cons] at *
    obtain ⟨h1, h2, h3, h4⟩ := ih
    cases x with
    | mk pr rf dm =>
      cases pr <;> cases rf <;> cases dm <;> simp <;> omega

end Formal.Confusion

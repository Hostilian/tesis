import Formal.Count
import Formal.Threshold

/-!
# Change flags (increase / decrease)

Python (`pipeline/run_case_study.py` lines 468-469 and
`pipeline/src/robustness.py`, `change_mask`):

```python
inc = np.nan_to_num(delta, nan=0) > threshold      # strictly greater
dec = np.nan_to_num(delta, nan=0) < -threshold     # strictly less
```

and for the control pair (`case_study.threshold_table`):
`np.abs(control) > t`.

Note: the code uses a *strict* comparison (`>`), so a pixel whose change is
exactly equal to the threshold is not flagged. The model below copies that.

Model: a pixel difference is a whole number (difference times 10000). A pixel
without a valid difference (NaN in Python) is `none`; `nan_to_num` turns it
into `0`.
-/

namespace Formal.Flags

open Formal

/-- `|d|`. -/
def absI (d : Int) : Int := max d (-d)

/-- Increase flag: `d > t`. -/
def isIncrease (t d : Int) : Bool := decide (t < d)

/-- Decrease flag: `d < -t`. -/
def isDecrease (t d : Int) : Bool := decide (d < -t)

/-- Any change flag: `|d| > t` (the control-pair test in `threshold_table`). -/
def isFlagged (t d : Int) : Bool := decide (t < absI d)

/-- `np.nan_to_num(delta, nan=0)`: a missing difference becomes 0. -/
def nanToZero (d : Option Int) : Int := d.getD 0

/-- Number of increase flags. -/
def countIncrease (t : Int) (ds : List Int) : Nat := countWhere (isIncrease t) ds

/-- Number of decrease flags. -/
def countDecrease (t : Int) (ds : List Int) : Nat := countWhere (isDecrease t) ds

/-- Number of pixels with `|d| > t`. -/
def countFlagged (t : Int) (ds : List Int) : Nat := countWhere (isFlagged t) ds

/-- "Changed by more than `t` in either direction" is exactly "increase or decrease". -/
theorem flagged_iff_inc_or_dec (t d : Int) :
    isFlagged t d = (isIncrease t d || isDecrease t d) := by
  unfold isFlagged isIncrease isDecrease absI
  rw [Bool.eq_iff_iff]
  simp only [Bool.or_eq_true, decide_eq_true_eq]
  constructor <;> intro h <;> omega

/-- With a non-negative threshold a pixel can never be flagged as both an
increase and a decrease. -/
theorem inc_dec_disjoint {t : Int} (ht : 0 ≤ t) (d : Int) :
    ¬ (isIncrease t d = true ∧ isDecrease t d = true) := by
  unfold isIncrease isDecrease
  simp only [decide_eq_true_eq]
  omega

/-- With a non-negative threshold, increase count + decrease count = count of `|d| > t`. -/
theorem count_inc_add_dec {t : Int} (ht : 0 ≤ t) (ds : List Int) :
    countIncrease t ds + countDecrease t ds = countFlagged t ds := by
  unfold countIncrease countDecrease countFlagged
  rw [countWhere_or_of_disjoint _ _ (inc_dec_disjoint ht)]
  exact countWhere_congr _ _ (fun d => (flagged_iff_inc_or_dec t d).symm) ds

/-- Raising the threshold never flags more pixels (`|d| > t`). -/
theorem countFlagged_antitone {t1 t2 : Int} (h : t1 ≤ t2) (ds : List Int) :
    countFlagged t2 ds ≤ countFlagged t1 ds := by
  apply countWhere_mono
  intro d hd
  unfold isFlagged at *
  simp only [decide_eq_true_eq] at *
  omega

/-- Raising the threshold never flags more increase pixels. -/
theorem countIncrease_antitone {t1 t2 : Int} (h : t1 ≤ t2) (ds : List Int) :
    countIncrease t2 ds ≤ countIncrease t1 ds := by
  apply countWhere_mono
  intro d hd
  unfold isIncrease at *
  simp only [decide_eq_true_eq] at *
  omega

/-- Raising the threshold never flags more decrease pixels. -/
theorem countDecrease_antitone {t1 t2 : Int} (h : t1 ≤ t2) (ds : List Int) :
    countDecrease t2 ds ≤ countDecrease t1 ds := by
  apply countWhere_mono
  intro d hd
  unfold isDecrease at *
  simp only [decide_eq_true_eq] at *
  omega

/-- A pixel with no valid difference (NaN, turned into 0) is never flagged
when the threshold is non-negative. -/
theorem missing_never_flagged {t : Int} (ht : 0 ≤ t) :
    isIncrease t (nanToZero none) = false ∧ isDecrease t (nanToZero none) = false
      ∧ isFlagged t (nanToZero none) = false := by
  unfold isIncrease isDecrease isFlagged nanToZero absI
  simp only [Option.getD_none, decide_eq_false_iff_not]
  omega

/-- Flags are symmetric: a decrease of `d` is an increase of `-d`. -/
theorem decrease_is_negated_increase (t d : Int) : isDecrease t d = isIncrease t (-d) := by
  unfold isDecrease isIncrease
  rw [Bool.eq_iff_iff]
  simp only [decide_eq_true_eq]
  constructor <;> intro h <;> omega

/-- Why thresholds must be positive (the config loader rejects `t ≤ 0`):
with a negative threshold the same pixel could be both increase and decrease. -/
theorem negative_threshold_breaks_disjointness :
    ∃ t d : Int, t < 0 ∧ isIncrease t d = true ∧ isDecrease t d = true :=
  ⟨-1, 0, by decide, by decide, by decide⟩

/-- Control-pair false alarms: the threshold chosen by the `control_p99` rule
never flags more control pixels than the 99th-percentile level `q` itself would. -/
theorem control_flags_at_selected_le {grid : List Int} {q t : Int}
    (h : Threshold.selectThreshold grid q = some t) (control : List Int) :
    countFlagged t control ≤ countFlagged q control :=
  countFlagged_antitone (Threshold.select_ge h) control

/-- No control pixel whose `|delta|` is at most `q` is flagged at the chosen threshold. -/
theorem control_below_q_not_flagged {grid : List Int} {q t : Int}
    (h : Threshold.selectThreshold grid q = some t) (c : Int) (hc : absI c ≤ q) :
    isFlagged t c = false := by
  have := Threshold.select_ge h
  unfold isFlagged
  simp only [decide_eq_false_iff_not]
  omega

end Formal.Flags

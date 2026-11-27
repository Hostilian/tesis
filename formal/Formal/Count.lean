/-!
# Counting helper

`countWhere p xs` is the number of elements of `xs` for which `p` is true.
It plays the role of `int(mask.sum())` in the Python code. All other files
count pixels with it, so the lemmas below are reused everywhere.
-/

namespace Formal

/-- Number of elements of a list that satisfy a yes/no test. -/
def countWhere {α : Type} (p : α → Bool) : List α → Nat
  | [] => 0
  | x :: xs => (if p x then 1 else 0) + countWhere p xs

@[simp] theorem countWhere_nil {α : Type} (p : α → Bool) :
    countWhere p [] = 0 := rfl

@[simp] theorem countWhere_cons {α : Type} (p : α → Bool) (x : α) (xs : List α) :
    countWhere p (x :: xs) = (if p x then 1 else 0) + countWhere p xs := rfl

/-- A count never exceeds the number of elements. -/
theorem countWhere_le_length {α : Type} (p : α → Bool) (xs : List α) :
    countWhere p xs ≤ xs.length := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    simp only [countWhere_cons, List.length_cons]
    split <;> omega

/-- A weaker test (true whenever the stronger one is) counts at least as many elements. -/
theorem countWhere_mono {α : Type} (p q : α → Bool)
    (h : ∀ x, p x = true → q x = true) (xs : List α) :
    countWhere p xs ≤ countWhere q xs := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    simp only [countWhere_cons]
    have hx := h x
    cases hp : p x <;> cases hq : q x <;> simp_all <;> omega

/-- Two tests that are never true together: their counts add up to the count of "either". -/
theorem countWhere_or_of_disjoint {α : Type} (p q : α → Bool)
    (h : ∀ x, ¬ (p x = true ∧ q x = true)) (xs : List α) :
    countWhere p xs + countWhere q xs = countWhere (fun x => p x || q x) xs := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    simp only [countWhere_cons]
    have hx := h x
    cases hp : p x <;> cases hq : q x <;> simp_all <;> omega

/-- Splitting a count by a second test: (p and q) plus (p and not q) is p. -/
theorem countWhere_split {α : Type} (p q : α → Bool) (xs : List α) :
    countWhere (fun x => p x && q x) xs + countWhere (fun x => p x && !q x) xs
      = countWhere p xs := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    simp only [countWhere_cons]
    cases hp : p x <;> cases hq : q x <;> simp_all <;> omega

/-- Two tests that agree on every element give the same count. -/
theorem countWhere_congr {α : Type} (p q : α → Bool)
    (h : ∀ x, p x = q x) (xs : List α) :
    countWhere p xs = countWhere q xs := by
  induction xs with
  | nil => simp
  | cons x xs ih => simp only [countWhere_cons, h x, ih]

end Formal

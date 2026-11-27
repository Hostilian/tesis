/-!
# Threshold rule `control_p99`

Python (`pipeline/src/case_study.py`, `resolve_threshold`):

```python
p99 = float(np.percentile(np.abs(control), 99))
for t in sorted(thresholds):
    if t >= p99:
        return t
raise ValueError(...)          # no grid value is large enough
```

Model: threshold values and the 99th percentile `q` are whole numbers (for
example index difference times 10000). Computing `q` itself (NumPy's
percentile) is *not* modelled; the proofs are about what happens after `q`
is known.

* `selectThreshold grid q` is the mathematical rule: the smallest grid value
  that is `≥ q`, or `none` if there is none.
* `firstAtLeast grid q` is a line-by-line copy of the Python loop.

We prove that the rule does what its description says, that the Python loop
computes exactly the rule when the grid is sorted (Python sorts it first),
and that the order in which the grid is written in a config file does not
matter.
-/

namespace Formal.Threshold

/-- Smallest element of `grid` that is `≥ q` (`none` if no element is). -/
def selectThreshold : List Int → Int → Option Int
  | [], _ => none
  | g :: gs, q =>
    match selectThreshold gs q with
    | none => if q ≤ g then some g else none
    | some t => if q ≤ g then some (min g t) else some t

/-- Literal transcription of the Python loop: first element `≥ q`. -/
def firstAtLeast : List Int → Int → Option Int
  | [], _ => none
  | g :: gs, q => if q ≤ g then some g else firstAtLeast gs q

/-- The chosen threshold is one of the grid values. -/
theorem select_mem {grid : List Int} {q t : Int}
    (h : selectThreshold grid q = some t) : t ∈ grid := by
  induction grid generalizing t with
  | nil => simp [selectThreshold] at h
  | cons g gs ih =>
    simp only [selectThreshold] at h
    split at h
    · split at h
      · simp at h; simp [h]
      · simp at h
    · rename_i t' ht'
      split at h
      · simp at h
        have := ih ht'
        rcases Int.le_total g t' with hle | hle
        · rw [Int.min_eq_left hle] at h; simp [h]
        · rw [Int.min_eq_right hle] at h; subst h; exact List.mem_cons_of_mem g this
      · simp at h
        subst h
        simp [ih ht']

/-- The chosen threshold is at least `q` (the control 99th percentile). -/
theorem select_ge {grid : List Int} {q t : Int}
    (h : selectThreshold grid q = some t) : q ≤ t := by
  induction grid generalizing t with
  | nil => simp [selectThreshold] at h
  | cons g gs ih =>
    simp only [selectThreshold] at h
    split at h
    · split at h
      · simp at h; omega
      · simp at h
    · rename_i t' ht'
      have := ih ht'
      split at h
      · simp at h; omega
      · simp at h; omega

/-- The rule returns nothing exactly when every grid value is below `q`
(Python then raises `ValueError` instead of silently picking a value). -/
theorem select_none_iff (grid : List Int) (q : Int) :
    selectThreshold grid q = none ↔ ∀ g ∈ grid, g < q := by
  induction grid with
  | nil => simp [selectThreshold]
  | cons g gs ih =>
    simp only [selectThreshold, List.mem_cons, forall_eq_or_imp]
    split
    · rename_i hn
      have := ih.mp hn
      constructor
      · intro h
        split at h
        · simp at h
        · exact ⟨by omega, this⟩
      · intro ⟨hg, _⟩
        have : ¬ q ≤ g := by omega
        simp [this]
    · rename_i t ht
      constructor
      · intro h
        split at h <;> simp at h
      · intro ⟨_, hall⟩
        have := ih.mpr hall
        rw [this] at ht
        simp at ht

/-- The chosen threshold is the smallest: no grid value `≥ q` is below it. -/
theorem select_le {grid : List Int} {q t : Int}
    (h : selectThreshold grid q = some t) : ∀ g ∈ grid, q ≤ g → t ≤ g := by
  induction grid generalizing t with
  | nil => simp
  | cons g gs ih =>
    intro x hx hqx
    simp only [selectThreshold] at h
    simp only [List.mem_cons] at hx
    split at h
    · rename_i hnone
      have hall := (select_none_iff gs q).mp hnone
      split at h
      · simp at h
        subst h
        rcases hx with hx | hx
        · omega
        · have := hall x hx; omega
      · simp at h
    · rename_i t' ht'
      have ih' := ih ht'
      split at h
      · simp at h
        subst h
        rcases hx with hx | hx
        · omega
        · have := ih' x hx hqx; omega
      · simp at h
        subst h
        rcases hx with hx | hx
        · omega
        · exact ih' x hx hqx

/-- If some grid value is `≥ q`, the rule always returns a threshold. -/
theorem select_isSome {grid : List Int} {q : Int} (h : ∃ g ∈ grid, q ≤ g) :
    ∃ t, selectThreshold grid q = some t := by
  cases hs : selectThreshold grid q with
  | some t => exact ⟨t, rfl⟩
  | none =>
    obtain ⟨g, hg, hqg⟩ := h
    have := (select_none_iff grid q).mp hs g hg
    omega

/-- Monotone: a larger control percentile never gives a smaller threshold. -/
theorem select_mono {grid : List Int} {q1 q2 t1 t2 : Int} (hq : q1 ≤ q2)
    (h1 : selectThreshold grid q1 = some t1) (h2 : selectThreshold grid q2 = some t2) :
    t1 ≤ t2 :=
  select_le h1 t2 (select_mem h2) (Int.le_trans hq (select_ge h2))

/-- The three properties pin down the answer: any grid value that is `≥ q` and
no larger than every other grid value `≥ q` is exactly what the rule returns. -/
theorem select_unique {grid : List Int} {q t : Int}
    (hmem : t ∈ grid) (hge : q ≤ t) (hmin : ∀ g ∈ grid, q ≤ g → t ≤ g) :
    selectThreshold grid q = some t := by
  obtain ⟨t', ht'⟩ := select_isSome ⟨t, hmem, hge⟩
  have h1 := select_le ht' t hmem hge
  have h2 := hmin t' (select_mem ht') (select_ge ht')
  rw [ht']
  congr 1
  omega

/-- The order of values in the config grid does not matter. -/
theorem select_perm {g1 g2 : List Int} (hp : g1.Perm g2) (q : Int) :
    selectThreshold g1 q = selectThreshold g2 q := by
  cases h1 : selectThreshold g1 q with
  | none =>
    have hall := (select_none_iff g1 q).mp h1
    exact ((select_none_iff g2 q).mpr (fun g hg => hall g (hp.mem_iff.mpr hg))).symm
  | some t =>
    refine (select_unique (hp.mem_iff.mp (select_mem h1)) (select_ge h1) ?_).symm
    intro g hg hqg
    exact select_le h1 g (hp.mem_iff.mpr hg) hqg

/-- On a sorted grid the Python loop (`for t in sorted(grid): if t >= p99: return t`)
returns exactly the rule's answer. -/
theorem firstAtLeast_eq_select {grid : List Int} (hs : grid.Pairwise (· ≤ ·)) (q : Int) :
    firstAtLeast grid q = selectThreshold grid q := by
  induction grid with
  | nil => rfl
  | cons g gs ih =>
    rw [List.pairwise_cons] at hs
    obtain ⟨hg, hgs⟩ := hs
    simp only [firstAtLeast, selectThreshold]
    split
    · rename_i hqg
      split
      · simp
      · rename_i t ht
        have : g ≤ t := hg t (select_mem ht)
        simp [Int.min_eq_left this]
    · rename_i hqg
      rw [ih hgs]
      split <;> simp_all

/-- Any thresholds the rule could ever return form a subset of the grid, so
every value it reports was fixed in the config before looking at the main pair. -/
theorem select_in_grid_or_error (grid : List Int) (q : Int) :
    (∃ t, selectThreshold grid q = some t ∧ t ∈ grid ∧ q ≤ t)
    ∨ (selectThreshold grid q = none ∧ ∀ g ∈ grid, g < q) := by
  cases h : selectThreshold grid q with
  | none => exact Or.inr ⟨rfl, (select_none_iff grid q).mp h⟩
  | some t => exact Or.inl ⟨t, rfl, select_mem h, select_ge h⟩

end Formal.Threshold

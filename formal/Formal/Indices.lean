/-!
# Spectral indices stay between -1 and +1

Python (`pipeline/src/case_study.py`):

* `normalized_difference(a, b)` = `(a - b) / (a + b)`, NaN where `|a + b| <= 1e-6`,
  then clipped to `[-1, 1]`.
* `compute_index("ndvi")` = `normalized_difference(nir, red)`.
* `compute_index("bsi")`  = `normalized_difference(swir16 + red, nir + blue)`.

Model: reflectances are non-negative whole numbers (for example reflectance
times 10000, which is how Sentinel-2 digital numbers are stored). An index
value scaled by `S` (for example `S = 10000`) is the integer quotient
`S * (a - b) / (a + b)`.

What is proved: for non-negative inputs the index can never leave `[-1, 1]`
(scaled: `[-S, S]`), so the final `clip` in the Python code never changes a
value computed from non-negative reflectances. It only matters for negative
reflectances, which can occur after the processing-baseline offset is applied.
-/

namespace Formal.Indices

/-- Numerator `a - b` of the normalized difference. -/
def ndNum (a b : Nat) : Int := (a : Int) - (b : Int)

/-- Denominator `a + b` of the normalized difference. -/
def ndDen (a b : Nat) : Int := (a : Int) + (b : Int)

/-- Normalized difference `(a - b) / (a + b)` scaled by `S` and rounded down. -/
def ndScaled (S a b : Nat) : Int := ((S : Int) * ndNum a b) / ndDen a b

/-- NDVI = (nir - red) / (nir + red), scaled by `S`. -/
def ndviScaled (S nir red : Nat) : Int := ndScaled S nir red

/-- Bare Soil Index = ((swir + red) - (nir + blue)) / ((swir + red) + (nir + blue)), scaled by `S`. -/
def bsiScaled (S blue red nir swir : Nat) : Int := ndScaled S (swir + red) (nir + blue)

/-- `np.clip(x, lo, hi)`. -/
def clip (lo hi x : Int) : Int := max lo (min hi x)

/-- The numerator lies between minus the denominator and the denominator,
i.e. the unscaled ratio is in `[-1, 1]`. -/
theorem nd_num_bounds (a b : Nat) :
    -(ndDen a b) ≤ ndNum a b ∧ ndNum a b ≤ ndDen a b := by
  unfold ndNum ndDen
  omega

/-- NDVI numerator bound: `-(nir + red) ≤ nir - red ≤ nir + red`. -/
theorem ndvi_num_bounds (nir red : Nat) :
    -((nir : Int) + red) ≤ (nir : Int) - red ∧ (nir : Int) - red ≤ (nir : Int) + red := by
  omega

/-- BSI numerator bound, with the band sums used in `compute_index("bsi")`. -/
theorem bsi_num_bounds (blue red nir swir : Nat) :
    -(((swir : Int) + red) + ((nir : Int) + blue)) ≤ ((swir : Int) + red) - ((nir : Int) + blue)
    ∧ ((swir : Int) + red) - ((nir : Int) + blue) ≤ ((swir : Int) + red) + ((nir : Int) + blue) := by
  omega

/-- Swapping the two inputs flips the sign of the numerator (antisymmetry). -/
theorem nd_num_antisymm (a b : Nat) : ndNum a b = -(ndNum b a) := by
  unfold ndNum
  omega

/-- Upper bound of the scaled index: never above `S` (that is, never above +1). -/
theorem ndScaled_le (S a b : Nat) (h : 0 < a + b) : ndScaled S a b ≤ S := by
  unfold ndScaled
  have hden : 0 < ndDen a b := by unfold ndDen; omega
  have hnum : ndNum a b ≤ ndDen a b := (nd_num_bounds a b).2
  have hS : (0 : Int) ≤ S := Int.natCast_nonneg S
  have hmul : (S : Int) * ndNum a b ≤ (S : Int) * ndDen a b := Int.mul_le_mul_of_nonneg_left hnum hS
  have hq : (S : Int) * ndNum a b / ndDen a b ≤ (S : Int) * ndDen a b / ndDen a b :=
    Int.ediv_le_ediv hden hmul
  rw [Int.mul_ediv_cancel _ (Int.ne_of_gt hden)] at hq
  exact hq

/-- Lower bound of the scaled index: never below `-S` (that is, never below -1). -/
theorem le_ndScaled (S a b : Nat) (h : 0 < a + b) : -(S : Int) ≤ ndScaled S a b := by
  unfold ndScaled
  have hden : 0 < ndDen a b := by unfold ndDen; omega
  have hnum : -(ndDen a b) ≤ ndNum a b := (nd_num_bounds a b).1
  have hS : (0 : Int) ≤ S := Int.natCast_nonneg S
  have hmul : (S : Int) * (-(ndDen a b)) ≤ (S : Int) * ndNum a b :=
    Int.mul_le_mul_of_nonneg_left hnum hS
  have hq : (S : Int) * (-(ndDen a b)) / ndDen a b ≤ (S : Int) * ndNum a b / ndDen a b :=
    Int.ediv_le_ediv hden hmul
  have hc : (S : Int) * (-(ndDen a b)) / ndDen a b = -(S : Int) := by
    rw [Int.mul_neg, ← Int.neg_mul, Int.mul_ediv_cancel _ (Int.ne_of_gt hden)]
  rw [hc] at hq
  exact hq

/-- The scaled normalized difference is always in `[-S, S]` when `a + b > 0`. -/
theorem ndScaled_bounds (S a b : Nat) (h : 0 < a + b) :
    -(S : Int) ≤ ndScaled S a b ∧ ndScaled S a b ≤ S :=
  ⟨le_ndScaled S a b h, ndScaled_le S a b h⟩

/-- NDVI × S is in `[-S, S]` for non-negative reflectances with `nir + red > 0`. -/
theorem ndvi_bounds (S nir red : Nat) (h : 0 < nir + red) :
    -(S : Int) ≤ ndviScaled S nir red ∧ ndviScaled S nir red ≤ S :=
  ndScaled_bounds S nir red h

/-- BSI × S is in `[-S, S]` for non-negative reflectances with a positive denominator. -/
theorem bsi_bounds (S blue red nir swir : Nat) (h : 0 < (swir + red) + (nir + blue)) :
    -(S : Int) ≤ bsiScaled S blue red nir swir ∧ bsiScaled S blue red nir swir ≤ S :=
  ndScaled_bounds S (swir + red) (nir + blue) h

/-- `clip` always returns a value inside `[lo, hi]` when `lo ≤ hi`. -/
theorem clip_bounds (lo hi x : Int) (h : lo ≤ hi) : lo ≤ clip lo hi x ∧ clip lo hi x ≤ hi := by
  unfold clip
  omega

/-- `clip` leaves values already inside `[lo, hi]` unchanged. -/
theorem clip_of_mem (lo hi x : Int) (h1 : lo ≤ x) (h2 : x ≤ hi) : clip lo hi x = x := by
  unfold clip
  omega

/-- For non-negative reflectances the final `np.clip(..., -1, 1)` never changes NDVI. -/
theorem ndvi_clip_noop (S nir red : Nat) (h : 0 < nir + red) :
    clip (-(S : Int)) S (ndviScaled S nir red) = ndviScaled S nir red :=
  clip_of_mem _ _ _ (ndvi_bounds S nir red h).1 (ndvi_bounds S nir red h).2

/-- For non-negative reflectances the final `np.clip(..., -1, 1)` never changes BSI. -/
theorem bsi_clip_noop (S blue red nir swir : Nat) (h : 0 < (swir + red) + (nir + blue)) :
    clip (-(S : Int)) S (bsiScaled S blue red nir swir) = bsiScaled S blue red nir swir :=
  clip_of_mem _ _ _ (bsi_bounds S blue red nir swir h).1 (bsi_bounds S blue red nir swir h).2

/-- Why the clip exists: with a negative reflectance (possible after the -0.1 offset)
the raw ratio can leave `[-1, 1]`. Here nir = 3, red = -1 gives (3 - (-1)) / (3 + (-1)) = 2. -/
theorem negative_reflectance_can_exceed_one :
    ∃ nir red : Int, 0 < nir + red ∧ nir + red < nir - red := ⟨3, -1, by decide, by decide⟩

end Formal.Indices

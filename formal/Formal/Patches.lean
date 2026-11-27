/-!
# Minimum-patch filter

Python (`pipeline/src/case_study.py`, `keep_patches_ge`, and the minimum size
in `patch_statistics` / `run_case_study.py`):

```python
min_px = max(1, ceil(min_patch_ha * 10_000 / pixel_area_m2))
labels, n = ndimage.label(mask, structure=np.ones((3, 3)))   # 8-connected patches
sizes = np.bincount(labels.ravel())
keep = sizes >= min_pixels;  keep[0] = False
return keep[labels]
```

Model: a flag mask is described by the list of its connected patches, each
given by its size in pixels. Finding the patches (`ndimage.label`) is *not*
modelled; the proofs are about what the size filter does with them. The
number of flagged pixels is the sum of the patch sizes.
-/

namespace Formal.Patches

/-- Patches that survive the filter: size `≥ m`. -/
def kept (m : Nat) (sizes : List Nat) : List Nat := sizes.filter (fun s => decide (m ≤ s))

/-- Number of flagged pixels = sum of patch sizes. -/
def pixels : List Nat → Nat
  | [] => 0
  | s :: ss => s + pixels ss

/-- `max(1, ceil(area_needed / pixel_area))` with areas in whole square metres. -/
def minPatchPixels (neededM2 pixelM2 : Nat) : Nat := max 1 ((neededM2 + pixelM2 - 1) / pixelM2)

/-- The filter never adds flagged pixels. -/
theorem kept_pixels_le (m : Nat) (sizes : List Nat) : pixels (kept m sizes) ≤ pixels sizes := by
  induction sizes with
  | nil => simp [kept, pixels]
  | cons s ss ih =>
    unfold kept at *
    rw [List.filter_cons]
    split <;> simp only [pixels] <;> omega

/-- Applying the filter twice is the same as applying it once. -/
theorem kept_idem (m : Nat) (sizes : List Nat) : kept m (kept m sizes) = kept m sizes := by
  unfold kept
  rw [List.filter_filter]
  congr 1
  funext s
  simp

/-- Every surviving patch has at least `m` pixels. -/
theorem kept_all_ge (m : Nat) (sizes : List Nat) : ∀ s ∈ kept m sizes, m ≤ s := by
  intro s hs
  unfold kept at hs
  simpa using (List.mem_filter.mp hs).2

/-- Surviving patches are a selection of the original patches (nothing is invented or resized). -/
theorem kept_sublist (m : Nat) (sizes : List Nat) : (kept m sizes).Sublist sizes :=
  List.filter_sublist

/-- A larger minimum size never keeps more pixels. -/
theorem kept_antitone {m1 m2 : Nat} (h : m1 ≤ m2) (sizes : List Nat) :
    pixels (kept m2 sizes) ≤ pixels (kept m1 sizes) := by
  induction sizes with
  | nil => simp [kept, pixels]
  | cons s ss ih =>
    unfold kept at *
    rw [List.filter_cons, List.filter_cons]
    by_cases h2 : m2 ≤ s
    · have h1 : m1 ≤ s := Nat.le_trans h h2
      simp [h1, h2, pixels]
      omega
    · by_cases h1 : m1 ≤ s
      · simp [h1, h2, pixels]
        omega
      · simp [h1, h2]
        exact ih

/-- Surviving pixels are at least (number of surviving patches) × `m`. -/
theorem kept_pixels_ge_count_mul (m : Nat) (sizes : List Nat) :
    (kept m sizes).length * m ≤ pixels (kept m sizes) := by
  induction sizes with
  | nil => simp [kept, pixels]
  | cons s ss ih =>
    unfold kept at *
    rw [List.filter_cons]
    split
    · rename_i hs
      simp only [List.length_cons, pixels, Nat.succ_mul]
      simp at hs
      omega
    · exact ih

/-- With a minimum of 1 pixel, every real (non-empty) patch is kept. -/
theorem kept_one (sizes : List Nat) (h : ∀ s ∈ sizes, 0 < s) : kept 1 sizes = sizes := by
  unfold kept
  rw [List.filter_eq_self]
  intro s hs
  have := h s hs
  simp
  omega

/-- The minimum patch size is always at least one pixel. -/
theorem minPatchPixels_pos (neededM2 pixelM2 : Nat) : 1 ≤ minPatchPixels neededM2 pixelM2 := by
  unfold minPatchPixels
  omega

/-- A patch of `minPatchPixels` pixels really covers the requested area (rounding up, not down). -/
theorem minPatchPixels_covers_area (neededM2 pixelM2 : Nat) (hp : 0 < pixelM2) :
    neededM2 ≤ minPatchPixels neededM2 pixelM2 * pixelM2 := by
  unfold minPatchPixels
  have hdm := Nat.div_add_mod (neededM2 + pixelM2 - 1) pixelM2
  have hlt := Nat.mod_lt (neededM2 + pixelM2 - 1) hp
  have hmax : (neededM2 + pixelM2 - 1) / pixelM2 ≤ max 1 ((neededM2 + pixelM2 - 1) / pixelM2) :=
    Nat.le_max_right _ _
  have hmul := Nat.mul_le_mul_right pixelM2 hmax
  rw [Nat.mul_comm pixelM2] at hdm
  omega

end Formal.Patches

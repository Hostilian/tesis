# Machine-checked proofs of the change-detection rules

This folder holds mathematical proofs, written in the Lean 4 proof assistant, that the decision rules of the Sentinel-2 change method do what the thesis says they do. A computer checks every step. If a single step were wrong or missing, `lake build` would fail.

## What this shows, and what it does not

**Shown:** the *logic* of five rules is correct for every possible input, not just for the inputs we tested. The rules are modelled with whole numbers. For example, an index difference of 0.1234 is written as 1234.

**Not shown:**

- Anything about satellite physics, atmospheric correction or sensor calibration.
- That the method finds real land-use change. Agreement with the COS map is measured separately (`docs/case-study/data/`), and is not ground truth.
- NumPy's 99th-percentile calculation and SciPy's patch labelling. The proofs start from their outputs.
- Floating-point rounding. Python works with decimals; the proofs use whole numbers.

The link between the proofs and the real code is `pipeline/tests/test_formal_spec.py`. It runs the real Python functions on more than 2,500 seeded random cases and checks that they behave like the Lean models. That is strong testing, not proof.

## The rules and what is proved

| Rule (Python) | Lean file | Proved for every input |
|---|---|---|
| NDVI and Bare Soil Index (`case_study.normalized_difference`, `compute_index`) | `Formal/Indices.lean` | With non-negative reflectances, both indices stay between -1 and +1. So the final `clip` in the code never changes such a value. It only matters for negative reflectances, which the proofs show can push the raw ratio past 1. |
| Threshold rule `control_p99` (`case_study.resolve_threshold`) | `Formal/Threshold.lean` | The chosen threshold is a grid value, is at least the control 99th percentile, and is the smallest such value. If no grid value is large enough, the rule returns nothing (Python raises an error). A noisier control pair never gives a smaller threshold. The order of the grid in the config does not matter. The Python loop gives exactly this answer. |
| Change flags (`run_case_study.py`, `robustness.change_mask`, `case_study.threshold_table`) | `Formal/Flags.lean` | With a positive threshold no pixel is both an increase and a decrease. Increase count plus decrease count equals the count of pixels with \|change\| above the threshold. Raising the threshold never flags more pixels. Missing pixels (NaN) are never flagged. The chosen threshold never flags more control pixels than the 99th-percentile level would. |
| Minimum-patch filter (`case_study.keep_patches_ge`, `patch_statistics`) | `Formal/Patches.lean` | The filter never adds pixels. Running it twice gives the same result as once. Every surviving patch has at least the minimum size. A larger minimum never keeps more pixels. The minimum patch size rounds up, so a kept patch always covers the requested area. |
| Agreement counts (`robustness.confusion`, `reference_cos.binary_agreement`) | `Formal/Confusion.lean` | Every evaluated pixel falls in exactly one of true positive, false positive, false negative and true negative. Pixels outside the evaluation domain never count. Precision, recall and F1 are never above 1. Swapping "flagged" and "reference" swaps precision and recall. The code does not compute Cohen's kappa, so kappa is not covered. |

One detail the proofs make explicit: the threshold rule picks a value **at least** the control percentile (`>=`). A pixel is then flagged only if its change is **strictly above** the threshold (`>`). A change exactly equal to the threshold is not flagged.

`Formal/Audit.lean` makes the build fail if any theorem depends on an unfinished step or on an extra assumption. Only Lean's three standard logical axioms are allowed (`propext`, `Quot.sound`, `Classical.choice`). The last build audited 76 theorems, including small helper lemmas that Lean generates itself.

## How to check it yourself

1. Install Lean with the official installer, elan: <https://github.com/leanprover/elan>. The exact Lean version is pinned in `lean-toolchain` (Lean 4.36.0); elan downloads it on first use.
2. In this folder, run `lake build`. A successful run ends with `axiom audit passed: ... theorems` and `Build completed successfully`.
3. From the repository root, run `python -m pytest pipeline/tests/test_formal_spec.py -q`. The `lake build` test inside it is skipped when Lean is not installed.

The proofs use only Lean's built-in library (no Mathlib), so the build takes well under a minute after the toolchain is downloaded. GitHub Actions runs the same build in `.github/workflows/formal.yml`.

# Soil laboratory results ↔ Sentinel-2: plan and safeguards

**Status:** exploratory pilot, not part of the registered thesis aims. The supervisor decides whether it becomes a chapter, an appendix or future work. No real soil result exists yet; every number from it so far is a **synthetic demonstration**.

## The question

Do laboratory soil results correlate with what Sentinel-2 sees on bare fields, beyond what location alone explains? If yes, satellite images could later give a first indication of soil conditions in places without a laboratory. They would not replace the laboratory.

## What can and cannot work

Sentinel-2 sees only the top millimetres of the soil, and only when the field is bare, dry and free of straw.

| Property | Plausible from optical surface reflectance? |
|---|---|
| Soil organic carbon | Sometimes (darker soils); depends on moisture and region |
| Clay content | Sometimes (SWIR absorption around 2.2 µm) |
| Iron oxides | Sometimes (visible bands) |
| Carbonates | Weak |
| Total nitrogen | Only as a stand-in for organic carbon |
| pH | Weak and regional |
| Plant-available P and K | No spectral basis; used as **negative controls** (a "signal" here means something is wrong) |

**Bare soil is rare.** In a real test at 3 public points near Beja and Castro Verde (27 Nov 2026, 24 dates each), only 1 point had bare soil, on 3 dates. Summer stubble has NBR2 0.22–0.27 and is correctly rejected. Plan for many samples to have no usable image.

## How the code avoids false correlations

`pipeline/src/soil_link.py`, `pipeline/run_soil_link.py`.

1. **Bare-soil mask:**
   - SCL 4/5 only, with a 20 m buffer around clouds and shadows.
   - All bands non-negative.
   - NDVI ≤ 0.25 and NBR2 ≤ 0.125; both are parameters, so report their sensitivity.
   - At least 3 distinct 20 m SWIR pixels.
2. **One image per overpass.** Duplicate catalogue copies (original vs reprocessed) are removed, and dates are spread over the year (at most 2 per month).
3. **Spatial block cross-validation.** The block size comes from the data's own spatial range (empirical variogram), at least 5 km.
4. **Five model families** (ridge, PLS, random forest, gradient boosting) against a mean baseline.
5. **Trend removal.** A smooth north–south / east–west surface is removed from soil values and features first, so a shared regional trend cannot pass as a signal.
6. **Spatial null model.** Moran spectral randomization (Wagner & Dray 2015). Copies of the soil map keep its smoothness at every scale but no longer line up with the features. The real result must beat 95 % of them. Each copy repeats the whole model choice, so picking the best model cannot flatter the result.
7. **Too-few-independent-areas guard.** When soil values and features both stay similar over distances close to the size of the study area, no test can decide. The answer is then "inconclusive", not yes or no.
   - The threshold is at least 2.5 independent areas per feature.
   - It was calibrated on synthetic data: the randomization test alone gave 0/10 false signals with about 38–67 independent areas, 4/10 with 19–38 and 10/10 with 14–27.

**Approaches that were tried and rejected (27 Nov).** Each failed on the "unrelated smooth maps" test, which is why the final design is the one above.

| Approach | False signals on unrelated smooth maps |
|---|---|
| Plain shuffling | 3/3 (independent review) |
| Shuffling within local areas | 2/5 |
| Location-only model first, then spectra on the residuals | 5/6 |
| Sliding the map with wrap-around | 8/8 |
8. **Multiple-testing correction** across properties (Benjamini–Hochberg).
9. **Area of applicability.** A prediction for a new place is used only if that place looks like the training data.
10. **Strict input checks:**
   - decimal commas are read correctly;
   - "<5" style values are kept as censored and counted;
   - duplicate sample IDs and unreadable cells stop the run;
   - depth, method and unit columns stay metadata.

**Self-test** (`python pipeline/run_soil_link.py demo`). Five synthetic scenarios.

Measured on 27 Nov with the two linear models, 10 seeds each:

| Scenario | Correct | Verdict |
|---|---|---|
| Planted signal | 10/10 | found |
| Planted signal with patchy, field-scale features | 10/10 | found |
| Pure noise | 10/10 | no signal |
| Two unrelated smooth maps (the review's trap) | 10/10 | inconclusive |
| Shared regional trend | 10/10 | no signal |

That is 0 false signals in 30 runs where none was planted. All 5 scenarios also pass with all four model families (1 seed each).

## Data you could use

| Source | Access | Notes |
|---|---|---|
| Farm laboratory reports | Written agreement with the farm | Personal/business data: GDPR, no coordinates in public files, agree where the data may be processed |
| LUCAS 2018 topsoil (EU) | Free on request from ESDAC | No redistribution; cite as required |
| ISRIC WoSIS | Open download | Check the licence of the snapshot used |
| SoilGrids 250 m | Open | A baseline to beat, not training data |

Lab CSV columns: `sample_id, lat, lon, date, depth_cm, method, unit, <property columns>`. Keep the file outside this repository and pass its path to the CLI.

## How many samples

`python pipeline/run_soil_link.py power --r 0.3 --n-tests 3 --bare-share 0.33`
- For r = 0.3 with 3 properties tested, and if 1 in 3 samples has bare-soil imagery: **341 lab samples**.
- Clustered sampling needs more; set `--design-effect`.
- With fewer than about 100 usable samples, only strong relationships can be detected.

## Compute

Measured on the laptop:
- **Feature extraction:** about 20–35 s per sample per date. It is limited by download speed, not processing power, so many parallel workers help. Grouping reads by tile and date is the next optimisation.
- **Evaluation:** CPU-bound. With 199 permutations, the main and residual tests and four models, expect minutes for 100–500 samples and hours for 20,000.
- **GPU:** only needed if image foundation models (e.g. Prithvi, Clay) are tried later, after the simple models.

## Next steps (in order)

1. Supervisor decision on scope (email 1, question 4).
2. Bare-soil availability on 30 public points across Alentejo (backlog J4).
3. Sensitivity of the bare-soil rule (J5) and a 2–3 year window (J6).
4. Obtain lab data (J2, J3) with written permission.
5. Run `features` and `evaluate` on the teacher's Linux machine; report every verdict, including "no evidence".

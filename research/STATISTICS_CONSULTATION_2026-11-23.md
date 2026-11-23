# Research questions and statistics consultation

**Research planning note — 23 November 2026**  
**Project:** Space-Based Economic Intelligence (SBEI)  
**Status:** Questions for statistical advice, **not** approved thesis changes or empirical findings.

> **Evidence boundary:** The existing public dashboard contains **10 synthetic anomaly examples and zero independently validated anomaly detections**. A separately documented Planetary Computer preview acquired **21,253 usable Sentinel-2 pixels** across three public study regions on 19 November 2026; this demonstrates bounded real raster access, **not** detection accuracy. The historical F1 = 0.907, Pearson r = 0.724 (p = 0.0002), Moran's I = 0.648 and runtime claims remain unverified. See [validation gaps](../THESIS_VALIDATION_GAPS.md), [evidence](../docs/evidence.html) and [real observation guide](../PLANETARY_PIXEL_PREVIEW.md).

## A. Existing supervisor-approved thesis direction

Preserve the current thesis topic. The project's three documented research questions are:

1. **RQ1 — Spatial anomalies:** *How reliably can open satellite spectral APIs identify localized industrial and mining resource anomalies compared to ground truth records?*
2. **RQ2 — VIIRS and economics:** *What is the correlation between VIIRS night-time light fluctuations and macro/microeconomic indicators in the target regions?*
3. **RQ3 — Pipeline performance:** *What pipeline latency and processing constraints limit the scalability of free satellite APIs for real-time economic monitoring?*

**Status:** RQ1 and RQ2 are not yet empirically answered. RQ3 is partially addressed as a software-engineering demonstrator but lacks controlled end-to-end production measurements. The originally stated F1 and correlation thresholds are *hypotheses*, not confirmed results. See [Chapter 1](../thesis/chapters/01_introduction.md) and [Chapter 7](../thesis/chapters/07_conclusion.md).

## B. Eight questions for the statistics professor

### 1. Ground-truth validation

**Ask:** How should I validate an unsupervised anomaly-detection model when independently verified real anomalies are scarce?

**Why / decision needed:** Compare independent field records, licensed reference datasets and blinded/manual labels. Agree on what counts as a true positive.

### 2. Sample size & independence

**Ask:** How many independent satellite observations, scenes, dates or field samples would support a defensible statistical claim?

**Why / decision needed:** Pixels in the same scene are spatially correlated; count independent sampling units and uncertainty.

### 3. Leakage-safe evaluation

**Ask:** How should I divide nearby pixels and consecutive dates into training, tuning and held-out testing sets?

**Why / decision needed:** Consider spatial block cross-validation, temporal holdout and leakage checks.

### 4. Simple baselines

**Ask:** Which simpler methods should Isolation Forest be compared with: seasonal Z-scores, change-point detection or threshold rules?

**Why / decision needed:** Specify baselines, parameters and selection criteria before inspecting test results.

### 5. VIIRS and economic trends

**Ask:** Is Pearson correlation appropriate for VIIRS night-time lights versus regional GDP, or should I adjust for trend, seasonality, autocorrelation and lag?

**Why / decision needed:** Define compatible temporal units, missing-data rules, lag selection and meaningful uncertainty.

### 6. Measurement artefacts

**Ask:** How can I distinguish genuine land-condition changes from clouds, seasonal vegetation, irrigation patterns, sensor calibration and measurement noise?

**Why / decision needed:** Request quality-control rules, sensitivity analyses and uncertainty representation.

### 7. Cross-resolution Portugal study

**Ask:** How should I compare Sentinel-1/2 observations with drone or aircraft imagery and field measurements when spatial resolutions and acquisition dates differ?

**Why / decision needed:** Select unit of analysis, aggregation, time windows and permissible cross-source comparison.

### 8. Minimum viable experiment

**Ask:** Given limited time and real ground truth, what is the smallest statistically credible empirical study for an Informatics bachelor's thesis?

**Why / decision needed:** Choose one region, one outcome, an independent benchmark, a simple baseline and reproducible holdout evaluation.

## C. Optional Portugal / Alentejo case study — scope decision

**Candidate question, not yet supervisor-approved:** *Can freely available Sentinel-1 and Sentinel-2 time-series data detect meaningful changes in agricultural land conditions in Alentejo, and does combining them with independently measured field observations improve detection reliability?*

This would be an **additional or revised case study only with explicit thesis-supervisor approval**. Do not claim it is feasible at individual-tree or sensor level before checking pixel size, spatial support, cloud coverage, sample timing, reliable labels and field/sector mappings.

Potential independent comparisons: authorized Sentinel-2 time series; Sentinel-1 backscatter with appropriate processing; licensed and georeferenced drone/aircraft orthomosaics; independently recorded irrigation/weather/probe data, and farm or agronomic field records **only where access and academic research use are authorized**. Do not publish private farm boundaries, supplier data, identifiable operational locations or raw sensor records in this repository.

## D. Decisions to request before implementing a new experiment

- [ ] Pick **one primary research question** and **one estimand/outcome** (what quantity will be estimated).
- [ ] Identify the **independent validation label source** and who can verify it.
- [ ] Define sampling unit, study area, observation dates and inclusion/exclusion rules.
- [ ] Decide a leakage-safe spatial/temporal split and one or two **simple baselines**.
- [ ] Specify metrics appropriate to rare events (confusion matrix; precision/recall/F1 if genuinely labeled; precision-recall curves where useful); avoid reporting accuracy from unlabeled data.
- [ ] Select appropriate uncertainty method (e.g. spatial/block bootstrap) rather than naive per-pixel confidence intervals.
- [ ] For economic time series, predefine lag handling, units, sample size, seasonal adjustment and autocorrelation treatment.
- [ ] Document missingness, cloud masks, measurement error and sensitivity analyses.
- [ ] Agree on minimum defensible study if no independent labels can be secured; **reframe as feasibility/engineering** rather than invented validation.
- [ ] Record the professor's advice as **meeting notes** and obtain supervisor agreement before changing formal thesis questions.

## E. Meeting notes and decision log

**Not yet recorded.** No meeting outcome or advice is asserted here. Add dated notes *after* the consultation, distinguishing professor suggestions from supervisor-approved thesis changes. Do not include private farm or identity records.

**Public webpage:** [Research questions & statistical validation](../docs/research-questions.html)  
**Related methodology:** [THESIS_VALIDATION_GAPS.md](../THESIS_VALIDATION_GAPS.md)

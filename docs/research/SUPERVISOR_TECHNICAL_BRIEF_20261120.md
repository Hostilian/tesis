# Bachelor's thesis — technical supervisor briefing
**20 November 2026 · Review draft / not submitted or sent**  
**Student:** Eren Öztürk | **Supervisor:** Dr. Jiří Brožek  
**Registered direction in current repository:** *Space-Based Economic Intelligence: Detecting Hidden Resource Anomalies Using Open Satellite APIs*. **Official CZU thesis-system assignment not independently retrieved in this pass; no renaming requested.**

### Working question (Candidate A)
**How can an open-source, API-first satellite intelligence system identify and transparently display reproducible resource-condition changes in real Earth-observation data while preserving source provenance and scientifically honest validation limits?** Economic interpretation remains the formal-title motivation, but no economic effect is inferred from spectral change alone.

### Working implementation and evidence
Public code: [tesis](https://github.com/Hostilian/tesis) · preserved main baseline [feed5e6](https://github.com/Hostilian/tesis/commit/feed5e6fb17c4149c9c64b396b091776c2e32641).  
[Isolated source branch](https://github.com/Hostilian/tesis/tree/operation/thesis-convergence-20261120) and [experimental map implementation](https://github.com/Hostilian/tesis/tree/operation/thesis-convergence-20261120/docs/experimental/geo-intelligence) (not on production Pages).

- **Existing public three-region acquisition evidence:** 21,253 observed Sentinel-2 L2A pixels across Chile, Peru and Czechia. [Source record](https://github.com/Hostilian/tesis/blob/main/docs/data/observed_three_region_proof_20261119.json); no event validation.
- **New two-scene public Chile comparison:** 4 Oct 2024 vs 14 Oct 2025, Sentinel-2 PB 05.11; **6,512 paired clear pixels**, 116 GeoJSON cells. Correct ESA reflectance `(DN-1000)/10000`. Median `ΔNDVI=-0.0101746`; 0 pixels below illustrative `-0.15` threshold. **No labeled events, detection scores or economic correlation.**
- **Upstream components already reused:** Planetary Computer STAC, PySTAC Client, rasterio WarpedVRT, NumPy, existing `GeospatialPreprocessor`, Leaflet. No new paid service, model router, or geospatial engine.
- **Tests:** 28 selected integration/scientific-guard regression tests passed locally on Windows after restoring correct test-output location. Exact command: `python -m pytest pipeline/tests/test_planetary_observation.py pipeline/tests/test_observed_change.py pipeline/tests/test_evidence_integrity.py -q --basetemp=<external-writable-dir>`. Browser-local HTML and GeoJSON returned HTTP 200 and headless Chrome populated actual metrics. Not an independent scientific replication.

### Method / validation proposal
1. Verify scene-level radiometric offset, optical calibration, CRS, resolution, SCL cloud/shadow QA, observed footprint and reproducibility.
2. Add seasonally comparable real acquisitions, a simple threshold/robust temporal baseline, and sensitivity/uncertainty analysis.
3. Seek **independent labels** and geographic/temporal holdout before precision/recall/F1; otherwise report an exploratory methodological system and numerical QA only.
4. Reconcile revised Markdown Chapters 5–7 with existing LaTeX/PDF and remove any unsupported previous quantitative claims before submission.
5. Optional restricted agricultural case study only after owner permission, authentic measurements, and separation from public thesis records.

### Proposed milestones (subject to graduation/exam workload)
**Nov–Dec:** validate upstream calibration and temporal evidence; repair manuscript provenance, preserve public default. **January:** independently reproduce one defensible experiment and consolidate chapters. **2027 thesis submission:** dependent on CZU schedule and supervisor review, not presumed.

**Supervisor decisions requested:** Does Candidate A remain within the registered resource/economic-intelligence assignment? Is a rigorous *real-data, non-ground-truth exploratory* evaluation acceptable pending labeled events? What level of independently observed economic/resource evidence is necessary to meet bachelor thesis expectations?

**Scientific caveat:** real scene pixels and software tests do not establish successful event detection, causality, model accuracy or thesis approval.

# SOIL-5 — Coordinated five-track programme

Date: 23 November 2026. Status: active research and prototyping, **not** an approved thesis-scope change, certified soil chemistry service, or commercially validated product. Resources: one laptop, free/open EO data, no GPU cluster, no guaranteed sponsor or lab dataset. **ABSOLUTE NO-SEND**: drafts only, no external communication, purchase or submission without individual user authorization.

## Single platform, five independently tested hypotheses

All tracks share one pipeline: public satellite imagery → scene provenance and SCL QA → reviewable surface-condition change candidates → independent field or lab reference where available → evidence dossier, confidence limits and optional human sampling priority. An unsuccessful chemistry hypothesis **must not block** a functioning optical change audit.

| ID | Workstream | Pilot output | Scientific/commercial stop condition | Current state |
|---|---|---|---|---|
| SOIL-01 | EU Soil Evidence Pack (previous rank 1) | Source-linked case dossier, scenes, date, resolution, source licence, independent verification status, uncertainty, simple exports | Existing free CLMS/QGIS workflow makes equivalent deliverable easily; no budgeted buyer | Specification; not yet bought or independently reviewed |
| SOIL-02 | Soil sealing / removal change audit (rank 2) | Paired Sentinel / Copernicus change candidates reviewed against independent imagery or site observations | Incorrect sealing assertions, no reliable reference, insufficient improvement over CLMS | Public imagery pipeline exists; no independent classification |
| SOIL-03 | Soil sampling priority map (rank 3) | Proposed lab sample sites prioritized by spatial variation, coverage and uncertainty, with fixed-budget baseline | No improvement over random/grid/soil expert site selection with independently measured soil samples | Experimental protocol only; lab labels unavailable |
| SOIL-04 | Bare-soil / erosion exposure alert (rank 4) | Vegetation/bare-soil exposure change and review flag; not measured soil loss | Phenology/burn/construction cause unacceptable false alarms, or free baseline suffices | NDVI/NDRE observed on public Alentejo pixels; no erosion truth |
| SOIL-05 | Satellite-to-laboratory pH / N / P / K replacement challenge (rank 13) | Analyte-by-analyte attempted prediction and *abstention* rules, independent chemical comparison | No lawful lab data, unacceptable external error, mandatory lab testing, or inadequate target specificity | **Not laboratory equivalent; hypothesis only** |

**Critical truth boundary for SOIL-05:** common Sentinel-2 multispectral sensors observe surface spectral reflectance. They do not directly assay subsurface pH, bioavailable P/K, nitrate, pollutants, organisms, DNA or chemistry. Soil organic carbon and some soil properties may correlate with EO plus terrain/climate context when field-calibrated, but published site-specific R² is *not* a percentage of correct lab predictions. The proposed 90% metric must be defined per analyte as a pre-registered proportion of independent held-out lab measurements within an analytically meaningful allowable error, with confidence intervals, spatial leave-region-out tests and OOD abstention. No such evidence is currently available.

## Shared public technology and strict data provenance

- Reuse existing thesis live-source reader (pipeline/planetary_observation.py), public Alentejo red-edge script (research/prototypes/rededge_real_pixel_preview.py), rasterio, PySTAC Client, Planetary Computer and QGIS/openEO. Prefer adapting these over creating another ingestion framework.
- Existing bounded sample: public Sentinel-2B scene acquired 27 June 2025, 9,216 *analysis-grid* pixels, median NDRE 0.213 and NDVI 0.262. These are not 9,216 independent ground-truth samples, lab chlorophyll values or chemistry measurements. Source proof: docs/data/observed_alentejo_rededge_20261123.json.
- Each future record must contain: workstream_id, source_scene_id, acquisition_time, native_resolution_m, source_licence, bbox/site key, processing_version, cloud_mask, data_hash, claim_level (observed/candidate/field_verified), reference_type, independent_reference_date, uncertainty, review_status, and relevant missing fields as null.
- Rota Única soil/leaf records, farm geometry, supplier API keys, drone/aircraft imagery and customer details remain private; do not publish to open repos. LUCAS laboratory data require license compliance. SoilGrids is a predictive baseline, NOT independent laboratory truth.
- Free direct competitors and substitutes include Copernicus CLMS Imperviousness, SoilGrids, FAO Trends.Earth, QGIS, ESA NAVISP sampling and ESA SOCBIO-MAP. Don't sell a generic free map as a proprietary invention.

## Work packages

**A. Paired optical pilot (SOIL-01/02/04):** Use two public real Sentinel-2 scenes in the same bounded test region. Retrieve with reproducible source IDs; align grid, mask shadows/cloud and calculate NDVI/visible-bare-surface change candidates. Clearly label output *observed spectral difference*, not verified soil sealing/removal or erosion. Export JSON/CSV candidate packet with checksums. No private field boundary needed.

**B. Evidence packet (SOIL-01):** Produce a self-contained static case packet with quality flags, scene lineage, exclusions, uncertainty, and human verification instructions. Benchmark against a human repeating the task using free CLMS/QGIS.

**C. Sampling priority (SOIL-03):** Compare stratified, grid and random site selection under the *same sample budget*. No measured accuracy or sample savings without lawfully acquired independent laboratory samples.

**D. Analyte falsification (SOIL-05):** Start with SOC as the most plausible correlational property, then separately investigate pH, total N, available P, available K and contaminants. Never reuse one target metric for another. Pre-register depth, tolerance, lab error, site-year splits, MAE/RMSE, residual bias, 90% within-tolerance hypothesis and abstention outside training support. Training on predicted SoilGrids as if lab truth is prohibited.

**E. Market entry:** Identify real government and corporate buyer workflows, procurement routes and signed/paid evidence; maintain buyer budgets and cost estimates as UNKNOWN until proven. Category revenues and policy directives do not establish purchases.

## Hard gates and current receipts

| Gate | Required | Current |
|---|---|---|
| Public scene ingestion | Real COG with source IDs, pixel checksum | Passed for one red-edge Alentejo scene |
| Paired surface comparison | Two real dates, common QA/CRS and source hashes | Pending |
| Independently verified surface labels | Site-independent reference, false-alarm rate, confidence | Missing |
| Independent soil laboratory values | Actual analyte, depth, sampling date, permitted coordinates | Missing |
| 90% lab-equivalence | Predefined chemical tolerance and cross-region held-out proof | **Not established** |
| Buyer evidence | Named budget owner, problem, authorized paid pilot | None |
| Thesis approval | Explicit Brožek confirmation of scope change | Not established |

**Rule for deliverables:** a successful scripted retrieval is not a verified environmental event; a model agreement score is not a lab replacement; regulatory monitoring needs are not commercial demand.

## All earlier ideas preserved in active long-term parking lot

The **other eight** ranked options remain intact and potentially reusable later: (1) water pigment/bloom QA, (2) habitat/phenology change, (3) stand-alone lab-sample provenance, (4) orchard pigment/foliar N calibration, (5) surface moisture triage, (6) surface salinity risk, (7) carbon maps for unsampled sites, and (8) biochemical/economic forecasting. Each retains separate scientific and commercial gaps in research/RANKED_SOIL_VENTURE_REVIEW_2026-11-23.md, research/BIOCHEM_EO_MARKET_AND_VALIDATION_2026-11-23.md, and research/RESEARCH_QUERY_BACKLOG_2026-11-23.md. Nothing deleted or misrepresented as rejected forever.

The 3 formal thesis RQs and 8 professor-consultation questions remain in research/STATISTICS_CONSULTATION_2026-11-23.md. Five Évora courses, Czech/PT visa, wallet/CCTV, hardship, SOL4R and Rota Única device/API goals are **separate ongoing workstreams**; do not expose them in this public repository.

**Prompts and reviews:** research/SOIL_FIVE_EXECUTION_PROMPTS_2026-11-23.md. Review prior VenturaAtlas/OMEGA evidence rules, but do not claim a completed 12-round commercial study.

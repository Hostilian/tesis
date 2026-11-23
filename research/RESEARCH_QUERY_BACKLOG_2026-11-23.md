# Research query backlog — satellites × plant biochemistry × soil chemistry × economics

**Created:** 23 November 2026  
**Status:** Open research questions, **not** automatic executions, scheduled monitors, thesis amendments, validated outcomes or commercial ideas.  
**Owner approval:** No third-party messages, purchases, submissions, research-data releases or external bookings. All proposed requests remain **unsent**.

## Evidence discipline

A real STAC item and accessible TIFF asset prove **source availability only**. An NDRE or soil-prediction output proves computation, **not** leaf chlorophyll, nitrogen content, soil carbon or physical change. A statistically defendable result requires paired independent laboratory observations, spatial/temporal holdouts, uncertainty estimates, reproducible scripts, and provenance. Values calculated from another model, such as SoilGrids, are **not laboratory ground truth**.

## Verified test inputs and limits

- **Sentinel-2 bands:** B05/B06/B07 red-edge are 20 m; B08 near-IR is 10 m; B8A is 20 m; native resolution controls the effective detail. Official Copernicus band documentation: https://s2.pages.eopf.copernicus.eu/msi/s2msi/main/context.html.
- **Live access probe:** Planetary Computer STAC item `S2B_MSIL2A_20241004T143749_R096_T19KEQ_20241004T183052` returned B05/B06/B07 COG assets. The signed assets each returned HTTP 206 and TIFF header `49492a00` for a 4-KiB range request (23 Nov 2026, authorized computer, metadata-only probe). Signed URLs were not persisted. This **does not** mean a full spectral image has been read or matched to biology.
- **Existing thesis:** `pipeline/planetary_observation.py` ingests B02/B03/B04/B08/B11/SCL and verified earlier public real-pixel samples; still lacks B05/B06/B07 and any site-matched biochemical laboratory labels.
- **Almond field precedent:** https://ishs.org/ishs-article/1395_20/ — reported r² values 0.79/0.72 in respective years, **study-specific**, not an external guarantee.
- **Chlorophyll caution:** https://www.nature.com/articles/s41597-025-05831-x — global chlorophyll product independent validation R² 0.37; not an upper bound, but real transfer-risk evidence.
- **Soil Portugal precedent:** https://novaresearch.unl.pt/en/publications/a-comparative-study-of-eo-data-fusion-and-satellite-embeddings-fo/ — independent 43-sample evaluation R² 0.44; spatial CV R² 0.34. **A modest model, not lab replacement.**
- **LUCAS 2018:** https://esdac.jrc.ec.europa.eu/content/lucas-2018-topsoil-data — 18,984 point laboratory samples; registration and **licensee-only/need-to-know usage**; no public raw redistributions and not field-level definitive.
- **LUCAS 2022:** https://esdac.jrc.ec.europa.eu/content/lucas-2022-topsoil-data — current landing page inconsistent about public release and registration; verify before claiming downloadability.

## Track A — plant pigments, nitrogen, orchard condition (priority)

| ID | Exact future research query / validation task | Test or decision | Failure criterion | Status |
|---|---|---|---|---|
| PLANT-01 | What public Sentinel-2 L2A **B05 B06 B07 B8A** real assets are readable near a *generic* non-private agricultural benchmark in Alentejo, and what fraction survives SCL masking? | B05/B06/B07/B8A raster-read, georegistration, QA; preserve public scene IDs | No aligned cloud-free pixels; expected red-edge assets absent | OPEN; asset access probed |
| PLANT-02 | Can NDRE or chlorophyll red-edge index track leaf chlorophyll across field measurements **better than NDVI and seasonal baseline** on held-out orchard blocks? | Independent SPAD or chemical chlorophyll samples; block CV | Leakage, mixed pixels, no improvement or no labels | OPEN |
| PLANT-03 | Can Sentinel-2 predict **lab-measured almond foliar nitrogen** out-of-year/out-of-farm in Portugal? | Permissioned foliar N (%) observations, sampling protocol, temporal matchup, spatial block CV | No true lab reference, out-of-domain failure | OPEN |
| PLANT-04 | Which biochemical signals in almond trees are confounded by water stress, soil background, canopy density and phenology? | Sensitivity / confounder matrix, independent covariates | Candidate index is nonspecific | OPEN |
| PLANT-05 | At 20m, what is the minimal tree spacing / orchard block area with acceptable pure-crop pixels, compared to commercial drone orthomosaics? | Mixed-pixel test using approved plot masks | Insufficient homogeneous area | OPEN |
| PLANT-06 | Does Sentinel-1 SAR add any independent measurable predictive value to a Sentinel-2 red-edge vegetation index in cloudy periods? | Test combined model against optical-only holdout; radar calibration | No incremental value, acquisition mismatch | OPEN |
| PLANT-07 | Could NASA PACE / Sentinel-3 plant-pigment products support a separate water chlorophyll / phytoplankton study in larger Portuguese water bodies? | In-situ pigment matchups and footprint test | Too-small water body or no water lab samples | OPEN |

## Track B — soil laboratory chemistry → prediction at unsampled locations (priority)

| ID | Exact future research query / validation task | Test or decision | Failure criterion | Status |
|---|---|---|---|---|
| SOIL-01 | Can a licensed **LUCAS 2018** topsoil CSV with SOC, pH, N, P, K and sample metadata be used for **private supervised training**? | Registration, license acceptance, POINT_ID and spatial joins; no public raw data | No lawful accessible sample | OPEN |
| SOIL-02 | Can Sentinel-2 **bare-soil optical reflectance**, texture/land cover, climate and topography improve held-out **SOC concentration** prediction over climate/topography alone? | RF/Ridge baselines; spatial blocks, true independent samples | No improvement vs nonsatellite baseline | OPEN |
| SOIL-03 | How much does model performance deteriorate when predicting **unsampled Portuguese regions**, especially Alentejo with different soil moisture, crop cover and parent material? | Leave-region-out, leave-year-out testing, OOD flag and uncertainty | Predictions unjustifiably confident outside training support | OPEN |
| SOIL-04 | What are the minimum data/coverage conditions under which a model may provide **conditional estimates rather than lab replacements**? | Error calibration, prediction intervals, abstention zones | Undercoverage / unreliably narrow intervals | OPEN |
| SOIL-05 | Can satellite imagery independently predict **pH, phosphorus, potassium, pesticide residues or microbial eDNA**? Which are unidentifiable by optical bands alone? | Target-by-target evidence + independent lab splits; prioritize SOC | No direct observability / poor external predictive power | OPEN; null hypotheses default |
| SOIL-06 | How do official **SoilGrids** or ESA/JRC products compare as **baselines**, not ground-truth labels? | Compare map predictions to *independent observed lab measurements* | Circular validation against other modeled products | OPEN |
| SOIL-07 | Can repeated, harmonized lab sampling plus satellite covariates detect credible **change in soil carbon**, not merely spatial differences? | Longitudinal matched measurements and error budget | Measurement noise exceeds expected change | OPEN |

## Track C — research-to-product and original economics (deferred)

| ID | Exact future research query / validation task | Test or decision | Status |
|---|---|---|---|
| ECON-01 | Does independent biochemistry/soil proxy signal add forecasting value for officially recorded agricultural outcomes beyond weather, phenology, price and baseline covariates? | Holdout and release-date-safe econometric benchmark | DEFER |
| ECON-02 | Could a point-in-time, spatially validated proxy add anything to economic/commodity forecasting **after costs and information lags**? | Leakage-safe, nontrading research; no alpha claim | DEFER |
| MARKET-01 | Which grower, lab, advisor, insurer, water utility or environmental researcher **already pays** for an orchard-to-lab satellite integration or SOC reporting workflow? | Named buyer + current workflow and budget evidence, verified externally | OPEN, no outreach |
| MARKET-02 | Do free alternatives (Copernicus, QGIS, SoilGrids, NASA/PACE, existing farm suites) already solve the user's problem? | Benchmark exact workflows and substitutes | OPEN |
| MARKET-03 | Can one consented buyer articulate a specific avoided lab/field cost and accept a paid independent-quality pilot? | Payment-first test only with explicit approval; no synthetic receipts | OPEN, no outreach |

## Minimum viable scientific experiment — proposed gate

1. Verify one public real satellite scene and relevant COG pixels (no private farm geometry).
2. Define units: real sample site × date × target lab analyte; capture sampling method/depth and permitted coordinates.
3. Build **nonsatellite baseline** and simple satellite baseline before ensemble/ML models.
4. Spatial leave-region-out and/or leave-farm-out tests, with time-based holdout; avoid randomly splitting correlated pixels.
5. Evaluate MAE/RMSE/R² against **actual laboratory measurements** and report calibration, bias and coverage.
6. Reject unsupported chemical labels; present uncertainty and abstention when outside calibration domain.
7. Protect source licenses and private Rota Única data; document which results are public.
8. Obtain thesis-supervisor approval for scope change and scientific evaluator review; do not turn a software demo into a chemistry claim.

## Project continuity / related goals

- [Existing thesis research questions & professor consultation](STATISTICS_CONSULTATION_2026-11-23.md)
- [Independent science / industry / OSS / VenturaAtlas OMEGA screen](BIOCHEM_EO_MARKET_AND_VALIDATION_2026-11-23.md)
- [Thesis verification gaps and real-vs-mock gate](../THESIS_VALIDATION_GAPS.md)
- [Current public research page](../docs/research-questions.html)
- **Other workstreams remain active**: five Évora courses, wallet report/CCTV and related hardship outreach, Czech biometrics, Portuguese visa-sticker verification, Rota Única equipment/API tasks. This file is not a substitute for those separate ledgers.

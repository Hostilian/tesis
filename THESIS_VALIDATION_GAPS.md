# Thesis Validation Gaps & Implementation Crosswalk

**Status:** Research-integrity remediation | 19 November 2026  
**Project:** Space-Based Economic Intelligence (SBEI) | CZU bachelor's thesis  
**Topic:** Retain the supervisor-approved thesis topic. This note does **not** certify results or propose a topic change.

## 1. Confirmed implementation facts

1. The published `docs/api/v1/status/index.json` records a historical pipeline run with `mock_mode: true` and `providers_used: ["mock"]`.
2. `pipeline/src/ingestion.py` currently builds the Sentinel-2 multispectral feature arrays from `MockDataClient.sentinel2_bands()` even when a GEE summary query is authenticated. Its monthly VIIRS series is mock-generated.
3. `docs/data/anomalies.json` contains ten synthetic demonstration records. No verified satellite-scene IDs or independent validation labels are attached to them.
4. `docs/data/anomalies.provenance.json` contains deterministic input hashes; those hashes help track a run but **do not** establish real-world provenance, ground-truth correctness, or model accuracy.
5. Software CI verifies tests, code quality, dependency/security scanning and deployment. Software CI success **does not** constitute empirical research validation.

**Observed-pixel milestone (19 Nov 2026):** A follow-up Planetary Computer test successfully read 21,253 usable Sentinel-2 L2A pixels in total: 9,216 Chile, 2,821 Peru and 9,216 Czechia after SCL masking. See `docs/data/observed_three_region_proof_20261119.json` and the successful three-region GitHub Actions run. This proves a bounded source-pixel ingestion path, **not** any specific economic/environmental anomaly or model accuracy. The ten dashboard cases remain synthetic.

## 2. Claims in the current thesis draft requiring evidence or revision

| Draft location | Claim requiring verification | Evidence/decision needed |
|---|---|---|
| Chapter 5, §5.1 | 184 satellite tiles / observed imagery | List of actual product IDs, tiles, acquisition timestamps, pixel assets, spatial bounds and checksums |
| Chapter 5, §5.3.1 | 200 PlanetScope-labeled validation pixels; F1 0.907 | Authorised labels, sampling protocol, independence from tuning, confusion matrix and reproducible evaluation script |
| Chapter 5, §5.3.2 | VIIRS–GDP Pearson r 0.724 and p 0.0002 | Real VIIRS observations and GDP series, temporal alignment, complete pairs, model assumptions and calculation notebook |
| Chapters 5–7 | Moran's I 0.648, bootstrap CI, runtime benchmarks | Saved input vectors, code, seed, hardware, evaluation scripts and repeated-run reports |
| Chapters 6–7 | Validated results and fully reproducible empirical conclusions | Rewrite as provisional until the evidence above passes independent review |
| Precompiled `thesis/thesis.pdf` | Existing unverified claims are also present in the current manuscript lineage | Do not submit as validated research; regenerate PDF only after manuscript and evidence reconciliation |

**No result should be upgraded to "verified" based solely on visually plausible maps, GitHub Actions success, provider authentication, OpenStreetMap proximity, artificial confidence intervals, or unlinked references to external reports.**

## 3. Real-data migration plan (open-source first)

### A. Satellite catalogue and real raster inputs

- Query the **current CDSE STAC API**: `https://stac.dataspace.copernicus.eu/v1/`; the earlier `catalogue.dataspace.copernicus.eu/stac/v1` endpoint was deprecated.
- Search a documented `sentinel-2-l2a` collection by bbox/time/cloud cover. Preserve returned STAC Item IDs and asset URLs. A catalogue item is **metadata only**, not pixel data.
- For each accepted acquisition, retrieve or access the **actual reflectance raster assets**, record raster CRS/geotransform and band scales, apply correct QA/cloud masks, then compute NDVI/NDWI/BSI from those real arrays.
- Reuse PySTAC Client + rasterio + xarray/stackstac or openEO rather than reimplementing catalogue navigation, cloud retrieval or raster reprojection.
- Reject empty/failed download, mismatched CRS, absent bands or invalid cloud mask rather than silently substituting mock arrays in a scientific run.

### B. VIIRS and statistical validation

- Retrieve genuine VIIRS night-light radiance for the study polygons, retaining product/version, temporal aggregation, mask and quality flags.
- Independently obtain official GDP series with source vintage and units; align dates before computing correlations. Missing IMF data must be missing, **not zero GDP growth**.
- Split training/tuning and held-out evaluation geographically and temporally. Publish signed-off label provenance and confusion matrix, not just a final score.

### C. Agritech case study with Rota Única — privacy-by-design

Potential private inputs include authorised **Sentinel-1/2 imagery**, periodic **drone flights**, less frequent **manned-aircraft imagery**, soil/leaf results, field operations, weather stations and water/soil probes. These provide a strong multi-resolution test case only **after written permission, lawful processing and a documented data-sharing boundary**.

- Keep farm boundaries, commercial imagery, raw probe measurements, API tokens and supplier files in the authorised private R&D environment.
- Use synthetic, publicly licensed or irreversibly aggregated examples on GitHub Pages. Never publish operational farm coordinates or supplier credentials.
- Require field/sector/device crosswalk, timestamps, calibration status, sensor quality and source checksums before any comparison.
- Treat cross-source validation (optical vs SAR vs drone/plane vs probes) as a hypothesis to evaluate, not a completed accomplishment.

### Open-source integration choices and current implementation status

This is a **candidate architecture**, not evidence that private integrations have been completed.

| Source | Prefer reuse of | Current observable status |
|---|---|---|
| Public Sentinel-2 pixels | Microsoft Planetary Computer + PySTAC Client + rasterio; CDSE STAC for catalogue discovery | **Working** in a three-region public preview (21,253 usable pixels); no validated anomaly model |
| Sentinel-1 radar | Established Sentinel-1 GRD sources and existing geospatial raster readers | Provider interface exists; no independently validated fused SAR raster observations in public evidence |
| Drone and crewed-aircraft photographs | **OpenDroneMap / WebODM** for photogrammetry, orthomosaics, DSM/DTM and georeferencing; GDAL for reprojection | Not processed against Rota Única data; source access and permission required |
| Weather sensors and irrigation/water probes | **OGC SensorThings API 2.0** observation/datastream model or read-only supplier adapters with clear timestamps, calibration and units | No private water-probe API has been proven end-to-end in this public thesis repository |
| Soil/leaf laboratories and farm operations | Schema-normalized private tables with source CSV/JSON hashes and pseudonymous field keys | No authorised private rows exported or validated in the public research pipeline |

**Separation of concerns:** Align sensors, flights and satellite scenes by dates, CRS and authorised pseudonymous field/sector identifiers **inside the private environment**. Public outputs should contain only approved, non-reidentifiable statistics and independently cleared samples. Do not copy Rota Única files to the public repo, or create synthetic "actual supplier" results for missing APIs.

**Recommended data contracts:** adopt STAC Items for imagery asset metadata, OGC SensorThings Observation/Datastream concepts for probes, and GeoTIFF/COG for georeferenced orthomosaics. Test field-to-sensor identity, sensor QA, units, clock drift, scene-footprint overlaps, resolution and acquisition-window alignment before attempting supervised or unsupervised fusion.

**Implementation blockers:** authorisation to use and publish any farm-level evidence; supplier API base URLs/credentials and subscription scopes; complete device-to-sector mappings; checked sensor-calibration records; approved drone/aircraft imagery and processing consent; independent agronomic ground truth.

Official references: [STAC (OGC)](https://www.ogc.org/standards/stac/), [OGC SensorThings API 2.0](https://docs.ogc.org/is/23-019/23-019.html), [OpenDroneMap](https://github.com/OpenDroneMap/ODM), [WebODM](https://webodm.org/).

### Course-to-thesis completion gates

| Course | What is already usable in the thesis | What still needs completion before claiming its contribution validated |
|---|---|---|
| INF13207L — Tecnologias Web | Three hosted dashboards, static JSON API, PWA and security checks | Independent browser/accessibility and end-user functional verification |
| INF13204L — Metodologias e Desenvolvimento de Software | Git branches, protected evidence contracts, reproducible tests and CI workflows | Formal requirements traceability and reviewable release criteria |
| MAT02354L — Probabilidade e Estatística | Hypothesis definitions, model interfaces and proposed metrics | Real-label/real-series inferential analysis and uncertainty |
| INF14387L — Transformação e Análise de Dados | Actual public raster sampling, quality masking, lineage/checksums and missing-data policy | Full multi-temporal ETL and observation-to-outcome joins |
| INF13186L — Interação Humano-Computador | V2/V3/V4 map-oriented interfaces | Documented user evaluation, usability measures and accessible design revisions |

These are thesis-level connections, **not evidence of passing or submitting the five course assignments**.

## 4. Five Évora course connections to the thesis

| Course | Reusable thesis capability | Evidence to generate |
|---|---|---|
| INF13207L — Tecnologias Web | Static REST contract, secure GitHub Pages, PWA and dashboard | Browser tests, API contract and accessibility checks |
| INF13204L — Metodologias e Desenvolvimento de Software | Requirements, issues, tests, CI, reproducibility and release governance | Traceability matrix, test coverage, tagged reproducible releases |
| MAT02354L — Probabilidade e Estatística | Descriptive statistics, sampling, correlation, significance, uncertainty | Labeled-data analysis notebook, assumptions, CIs and hypothesis checks |
| INF14387L — Transformação e Análise de Dados | Real ingestion, joins, schema/quality rules, outlier and missing-data handling | Source-to-product lineage, ETL validation and transformations |
| INF13186L — Interação Humano-Computador | Dashboard information hierarchy, map interactions, accessibility and user evaluation | Personas, scenario tasks, usability measurements and interface revisions |

Course assignments and the thesis are distinct academic submissions. Reuse methods and independently authored components **only where course rules permit**, with attribution and no duplicate-submission misrepresentation.

## 5. Definition of done

A genuinely validated result requires all of the following: observed source assets and identifiers, auditable geospatial preprocessing, independent ground truth, an appropriate held-out evaluation, reproducible statistics, clear limits, and an explicit reviewer decision. Until then, publish only the clearly marked demonstration layer.

**Reference documentation:** [CDSE STAC](https://documentation.dataspace.copernicus.eu/APIs/STAC.html), [PySTAC Client](https://pystac-client.readthedocs.io/), [stackstac](https://stackstac.readthedocs.io/), [CDSE APIs](https://dataspace.copernicus.eu/analyse/apis).  

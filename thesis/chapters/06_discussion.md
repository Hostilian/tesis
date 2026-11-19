# Chapter 6: Discussion

> **Research status — 19 November 2026.** This chapter discusses observed software capabilities, research limitations and open validation questions. Historical numerical benchmark claims are archived under `shelf/manuscript-pre-validation-20261119` pending verification; they are not adopted as confirmed empirical findings.

## 6.1 Answers to the Research Questions

### 6.1.1 Research Question 1 — Spatial Anomaly Detection

**Question:** How reliably can satellite spectral APIs identify industrial and mining changes compared with independent ground-truth records?

The current implementation demonstrates spectral feature computation over arrays, an Isolation Forest anomaly detector, and structured export of example event records. However, its published detection inputs are deterministic synthetic arrays and its public "ground truth" references were not independently matched to source image assets. It therefore **does not yet quantify real-world spatial detection reliability**. Evaluation of RQ1 requires genuine source pixels, independent annotated events and geographically/temporally held-out tests.

The software architecture shows where optical indices and future Sentinel-1 radar features may be combined. The current detection model does not, by itself, establish a verified optical/SAR fusion result.

### 6.1.2 Research Question 2 — VIIRS Radiance and Economic Activity

**Question:** What relationship exists between independently observed VIIRS night-time light changes and official economic indicators?

The temporal-analysis interface can process a numeric radiance series and explain deviations, but the published monthly VIIRS sequence is synthetic. Public IMF and World Bank endpoint availability demonstrates connection capability, not the correct socioeconomic alignment or a validated Pearson correlation. RQ2 is **not yet empirically answered**. Future work must establish comparable time windows, region definitions, official data vintages, uncertainty, seasonal effects, trend and possible confounding.

### 6.1.3 Research Question 3 — System Performance and Constraints

**Question:** Which API, compute and processing constraints affect reproducible geospatial data workflows?

The public site and static API can be deployed at low infrastructure cost, and the code contains provider clients, retries and explicit missing-data handling. GitHub Actions can test and deploy the application. However, production-scale imagery ingestion latency, third-party API quota behavior, storage cost, geographic scalability and model quality **remain unmeasured under a documented real-observation workload**.

Three bounded Sentinel-2 L2A raster previews were successfully acquired via Microsoft Planetary Computer on 19 November 2026 (21,253 valid masked pixels in Chile, Peru and Czechia combined). This supports the narrow claim that real source pixels can be loaded and processed. It does not provide independently validated anomalies, a representative production benchmark or a completed fusion experiment. The synthetic dashboard records remain unchanged.

## 6.2 Relationship to Existing Research

Unsupervised outlier detection may help prioritize candidate areas for further inspection, but detecting an outlier in reflectance space is not the same as determining whether mining or industrial expansion occurred. Physical interpretation requires sensor-specific quality control, contextual data and independent verification.

VIIRS night-time radiance can be considered as a potential proxy for activity, but observed correlations may be affected by seasonal illumination, weather, economic geography, policies, outages and data revision. Any claim of predictive utility needs separate out-of-sample evaluation.

The project should not report performance comparisons against published supervised models without matched benchmarks, equivalent labeling standards and clearly cited source results.

## 6.3 Practical Contribution and Limitations

### Software contribution

The demonstrated contribution is an inspectable information-engineering pipeline and accessible web interface linking satellite provider clients, spectral transformations, anomaly-scoring logic, provenance metadata and a versioned static API. Three distinct dashboard experiences support map exploration, temporal displays and scenario presentation.

The evidence safeguards are also a contribution: explicit synthetic status, separate run records, unverified labels, read-only scheduled rehearsals, no automatic scientific publication, and a fail-closed experimental real-pixel path.

### Scientific limitations

1. **Construct validity.** An unsupervised anomaly score is not a calibrated probability of an economic event. The study does not yet establish event-class correctness.
2. **Source validity.** The published imagery-derived feature arrays and monthly radiance values are synthetic. Provider reachability does not verify source pixels.
3. **Ground-truth validity.** The current repository does not provide a linked and independently audited label set for all public anomaly examples.
4. **Statistical validity.** Spatial and temporal dependence, data leakage, denominator choices, missing data, multiple comparisons and geographic transferability remain to be addressed.
5. **Reproducibility limits.** Unit tests and deterministic mock inputs are reproducible software evidence; empirical reproducibility requires the original observational assets and analysis notebooks.
6. **Operational performance.** Production data volumes, latency, error handling, and integration costs have not been demonstrated at a representative workload.

## 6.4 Privacy, Ethics and Rota Única Case-Study Potential

A possible agritech case study could compare Sentinel optical/radar observations with authorized drone imagery, periodic manned-aircraft surveys, weather measurements, irrigation/water probes and soil/leaf assessments. This is a **planned validation design**, not a completed multisensor fusion experiment.

Farm boundaries, private imagery, device mappings, sensor streams and supplier credentials must remain in an authorized private environment. Public demonstrations should rely on open data, synthetic scenarios, and aggregated non-sensitive evidence that has undergone review. Written authorization, data minimization, traceability and source-licensing checks precede any use of operational records in a thesis.

## 6.5 Integration With the Five Universidade de Évora Courses

The project offers cross-disciplinary opportunities without conflating separate coursework with thesis evidence:

| Course | Connection | Demonstrable artifact |
|---|---|---|
| INF13207L — Tecnologias Web | API contracts, PWA behavior, accessibility and geospatial UI | Static endpoint checks, browser tests and secure deployment |
| INF13204L — Metodologias e Desenvolvimento de Software | Requirements, CI, tests, architecture and version control | Test traceability and repeatable releases |
| MAT02354L — Probabilidade e Estatística | Sampling, inference, correlation and uncertainty | Held-out evaluation and documented statistical assumptions |
| INF14387L — Transformação e Análise de Dados | Real-data acquisition, missingness, quality and lineage | Source ID inventory, QA rules and reproducible transformations |
| INF13186L — Interação Humano-Computador | Visual hierarchy, personas, accessible maps and evaluation | Usability study with recorded tasks and outcomes |

Any reused source code or project material must comply with the requirements of each course and academic integrity policy.

## 6.6 A Structured Validation Roadmap

The most effective next sequence is: (1) authenticate and retrieve one bounded real Sentinel-2 scene collection, (2) store private source identifiers and checksums, (3) verify spectral and quality masks, (4) build an independent validation set, (5) evaluate the spatial hypothesis, (6) retrieve and align a real VIIRS/economic time series, and (7) test the temporal hypothesis with transparent uncertainty.

Only then can the manuscript make results-level conclusions about specific extraction sites, model accuracy or economic relationships.

**Discussion conclusion:** Software engineering feasibility has been demonstrated. The scientific hypotheses and operational value remain open questions requiring observed data and independent evaluation.

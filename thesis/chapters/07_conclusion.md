# Chapter 7: Conclusion and Future Research

> **Research status — 19 November 2026.** This is a provisional conclusion for an actively developed thesis. Earlier draft performance claims and final-validation statements are retained in the preserved manuscript branch but are not represented here as substantiated results.

## 7.1 Scope of the Implemented Contribution

This project has implemented a working thesis demonstrator for space-based economic intelligence. The repository includes provider interfaces, structured spectral preprocessing, Isolation Forest and temporal-anomaly components, reproducible synthetic examples, versioned static JSON endpoints and three interactive browser dashboards. The published map defaults to satellite imagery, and the public site explicitly identifies synthetic event records rather than presenting them as field-verified discoveries.

Automated GitHub workflows cover Python tests on multiple runtimes, strict type and style checks, security review, API-health checks and deployment. These results are useful software verification, but they do not establish the accuracy of any specific geographical or economic inference.

The system also contains a separate, fail-closed experimental path for acquiring bounded real Sentinel-2 pixel samples and writing private source/checksum records. The separate Planetary Computer route has now **successfully acquired three bounded real Sentinel-2 source previews** (21,253 usable pixels across Chile, Peru and Czechia on 19 November 2026), confirming a bounded real-imagery input path without GEE credentials. This is **not** proof of an independently verified mining anomaly, scientific model accuracy or a completed production dataset.

## 7.2 Research Questions and Hypotheses

| Question | What has been implemented | Empirical conclusion |
|---|---|---|
| RQ1: Can unsupervised models identify industrial/mining anomalies? | Spectral array processing, Isolation Forest and synthetic spatial examples | **Open** — independent real-scene evaluation required |
| RQ2: Do VIIRS radiance variations correlate with economic indicators? | Time-series detector, economic API adapters and synthetic VIIRS example | **Open** — observed paired series and statistical evaluation required |
| RQ3: Which performance and API constraints affect the pipeline? | Software orchestration, CI, static deployment and bounded acquisition design | **Partially addressed** — production workload measurements required |

The earlier manuscript draft's figures (including F1 = 0.907, Pearson r = 0.724, Moran's I = 0.648 and a 9-second runtime) must **not** be cited as independently measured thesis outcomes until the source data and calculations are reconstructed and reviewed.

## 7.3 Methodological and Practical Significance

The project demonstrates the usefulness of separating input acquisition, transformation, anomaly modeling, evidence status and web presentation. Keeping mock inputs distinct from real observations prevents a visually convincing map from being mistaken for confirmed environmental or economic intelligence.

A reproducible detection claim requires traceable source assets, appropriate cloud/quality controls, source-versus-output lineage, external ground-truth evidence, held-out evaluation and scientifically defensible uncertainty estimates. A software artifact may remain useful and presentable while its scientific hypotheses are still under investigation.

## 7.4 Priorities for Completion

1. Acquire documented observed Sentinel-2 raster values in a bounded region using an authorized account, then test transformations and record source IDs.
2. Develop an independent, licensed spatial reference dataset; compare models with simple baselines and held-out evaluation.
3. Obtain genuine VIIRS radiance time series and official regional economic indicators, align dates and missingness, and perform transparent statistical inference.
4. Add reproducible measurements for runtime, network usage and API quota limitations.
5. Explore Sentinel-1 radar and drone/aircraft imagery only with suitable geospatial quality controls and authorization, and avoid public exposure of Rota Única operational data.
6. Complete an academic validation review and synchronize Markdown, LaTeX and the final thesis PDF before submission.

These priorities connect to the five Universidade de Évora courses through software development, web engineering, statistical inference, data transformation and human-computer interaction. They do not imply that independent course submissions are complete.

## 7.5 Current Limits and Responsible Use

The interactive map is a **research demonstrator**, not an operational surveillance, environmental enforcement, insurance-pricing or investment-decision system. Its public example scenarios are synthetic. All direct connections to production sensor systems or restricted geospatial imagery must be implemented privately under explicit permissions.

The key unresolved requirement is empirical evidence: authenticated provider access and passing code-quality checks are prerequisites for some workflows, not substitutes for real-data validation.

## 7.6 Project Artifacts

- Main repository: https://github.com/Hostilian/tesis
- V2 dashboard: https://hostilian.github.io/tesis/
- V3 dashboard: https://hostilian.github.io/tesis/index3.html
- V4 dashboard: https://hostilian.github.io/tesis/index4.html
- Public evidence statement: https://hostilian.github.io/tesis/evidence.html
- Real-observation acquisition guide: `REAL_OBSERVATION.md` (repository)
- Thesis validation gap register: `THESIS_VALIDATION_GAPS.md` (repository)

**Submission note:** The compiled PDF and LaTeX sources must be regenerated from these revised and subsequently verified sections. Existing precompiled artifacts may still contain obsolete draft claims and are not declared submission-ready.

**Conclusion:** The implemented pipeline and visualization provide a verifiable software basis for a thesis; scientific validation of real satellite and economic observations remains the principal outstanding research milestone.

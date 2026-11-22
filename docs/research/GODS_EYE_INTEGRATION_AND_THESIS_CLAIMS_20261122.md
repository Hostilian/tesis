# Thesis integration and God's Eye View deep-source research — 22 November 2026

**Status:** evidence-backed research notebook and implementation audit; **NOT** approved CZU thesis scope, completion certificate, production deployment or university submission. Public production `main` / `docs/index.html` / `index3.html` / `index4.html` are deliberately untouched.

## Research question retained

Working formulation from [20 Nov ADR](ADR-THESIS-CONVERGENCE-20261120.md):

> How can an API-first, open-source Earth-observation pipeline acquire, compare and explain reproducible satellite-derived resource-condition changes with traceable provenance and explicit uncertainty, while avoiding unsupported economic or anomaly claims?

Supervisor Jiří Brožek must review that formulation against the formal CZU assignment. **No thesis topic change has been authorized.**

## Exact findings from independently inspected upstream sources

1. **God's Eye View's key contribution is geospatial integration and operator navigation, not extraction detection.** The original code by Bilawal Sidhu (MIT source; data separately licensed) combines live/refreshable public feeds into Cesium-based 3D navigation. Its *Recent Imagery* layer supports bounded-area HLS/Sentinel/Landsat selections and A/B visual comparisons. Some traffic and positions are simulations or estimates, not ground truth. Source: [original project](https://github.com/bilawalsidhu/gods-eye-view), [README](https://github.com/bilawalsidhu/gods-eye-view/blob/main/README.md), [Recent Imagery implementation](https://github.com/bilawalsidhu/gods-eye-view/blob/main/src/layers/recentImagery/index.js).
2. **There is a real upstream extension point, avoiding a new globe.** God’s Eye Director accepts `gev-scene-bundle` version 1, scene-document version 7, `geojson` packs, SHA-256/byte-length checks, and a review-before-apply import. Its renderer accepts bounded Polygon features with unique string IDs in WGS84, but ignores arbitrary GeoJSON properties for map styling. Source: [data-pack specification](https://github.com/bilawalsidhu/gods-eye-view/blob/main/docs/DIRECTOR-DATA-PACKS.md), [sharing specification](https://github.com/bilawalsidhu/gods-eye-view/blob/main/docs/DIRECTOR-SHARING.md), source `src/director/packs/geojson.js`.
3. **Upstream license caveat is material.** MIT grants permission for *source code* reuse, not the data bundled with or fetched by the app. Notably, TeleGeography submarine-cable data are CC BY-NC-SA and Bhote Koshi assets are CC BY-NC, while Google basemaps and other providers have own licensing/quotas. A compliant thesis export must not inherit an upstream claim of broad data reuse. Sources: [LICENSE](https://github.com/bilawalsidhu/gods-eye-view/blob/main/LICENSE), [DATA_SOURCES.md](https://github.com/bilawalsidhu/gods-eye-view/blob/main/DATA_SOURCES.md).
4. **Copernicus L2A radiometry requires processing-baseline-aware offset.** The ESA Sentinel-2 Level-2A equation is `(DN + BOA_ADD_OFFSET)/QUANTIFICATION_VALUE` (for the observed PB 05.xx scenes `(DN-1000)/10000`). STAC metadata documents the acquisition and asset lineage; it is not a substitute for independent scientific validation. Sources: [ESA Sentinel-2 products](https://sentiwiki.copernicus.eu/web/s2-products), [STAC specification](https://stacspec.org/en/about/stac-spec/), [MPC docs](https://planetarycomputer.microsoft.com/docs/).
5. **The same denominator is essential when comparing dates.** Earlier 2024→2025 and 2025→2026 experiments had different valid-overlap masks (6,512 vs 3,702). On 22 Nov, a third actual STAC/COG acquisition and a fixed **three-way finite NDVI mask** produced a shared denominator of 3,702/9,216. Experimental source IDs/dates, SHA and detailed values are recorded in the private output and summary below.
6. **Upstream drone software should not be conflated.** ODM is a separate AGPL photogrammetry engine; current WebODM states it is no longer affiliated with OpenDroneMap and uses ODX. Neither installs automatically, and both are restricted to data approved for private processing. Sources: [ODM](https://github.com/OpenDroneMap/ODM), [WebODM](https://github.com/WebODM/WebODM).
7. **New Grafana deployments must not depend on abandoned agents.** Grafana Agent EOL was 2025-11-01, Promtail EOL 2026-03-02; Grafana Alloy is the evaluated collector for any future private pipeline. No current live production telemetry verified. Sources: [Agent docs](https://grafana.com/docs/agent/latest/about/), [Promtail docs](https://grafana.com/docs/loki/latest/send-data/promtail/).
8. **Ponytail's minimal-code process is useful but its marketing metrics are not thesis experiments.** No global hooks were installed; this implementation reused official God’s Eye parsing rather than creating a custom JS 3D engine. Source: [canonical Ponytail](https://github.com/DietrichGebert/ponytail), not third-party forks.
9. **An OpenRouter-powered inference layer is optional and currently unjustified.** No model call, API key or paid inference is part of the measured reproducibility result. If adopted later, a deterministic source/evidence contract should precede generative narration; no private sensor data may be sent to a remote model without explicit authorization. Source: [OpenRouter Skills](https://github.com/OpenRouterTeam/skills).

## What is implemented — verified vs blocked

| Application / integration | Confirmed implementation / evidence | Remaining blocking gate |
| --- | --- | --- |
| **Thesis public/production multi-model website** | Historical `docs/index.html`, `index3.html`, `index4.html` untouched; satellite remains original default | User approval for any future feature promotion |
| **Satellite STAC/COG (MPC, PySTAC, rasterio)** | Two validated source-acquisition periods + new three-date shared-mask pipeline, signed real public Sentinel-2 scene IDs, processing-baseline checks | Cross-sensor calibration / clouds, multiple sites, uncertainty |
| **God's Eye View** | **Functional interoperable Director JSON scene bundle** with 116 reviewed public summary polygons; officially parsed using upstream source and decoded as valid geometry; linked only from experimental viewer | Full God’s Eye app browser rendering, user acceptance, deployment choice |
| **Leaflet evidence viewer / Web Technologies / HCI pattern** | Existing separately isolated experimental 2D viewer, now with 3D export link; mobile-aware markup inherited | Browser user testing / actual course grading criteria; not course submission proof |
| **Data Transformation / Statistics** | New reproducible common-mask and descriptive quantile calculation, pytest fixtures; native NumPy with no extra framework | Larger real-data validation; examiner-specific deliverables; independent labels |
| **Software Methods** | Typed metadata contracts, deterministic tests and external interchange tests; no new monolith | Academic project is distinct and must be submitted separately; native Wiki/permissions outstanding |
| **Rota Única sensor and orchard case study** | Existing private catalogs, provenance and catalog CI were previously repaired; public thesis consumes **ZERO company records** | Written data-use authorization, verified farm-device mapping, supplier endpoints, read-only live authentication, device health |
| **OpenDroneMap / WebODM / aerial imagery** | Maintained upstream and license analysis only | Authorized images, privacy/legal clearance, calibrated orthomosaic workflow, sufficient local compute |
| **Grafana Alloy / dashboards** | Integration boundary reviewed; prior project's tests/catalog distinct | Real usable telemetry and an authorized private runtime; no invented metrics |
| **Ponytail / autonomous coding review** | Source-first reuse applied in implementation; upstream MIT reviewed | Decide on per-repo controlled instructions only; no forced global plugin/hook |
| **OpenRouter / model routing / AI narration** | No inference, costs, credentials or synthetic narration used | Actual research benefit, privacy assessment and cost guardrails |
| **CZU manuscript** | Candidate evidence and thesis-ready *draft* sentences below | Supervisor scope approval, bibliography, full reproducibility/figure audit, LaTeX/PDF final QA |

## New source-confirmed three-scene result (22 Nov 2026)

**Private** `research_private/observations/three_scene_latest/` stores the primary authentic run, rather than a GitHub Pages data feed. Public metadata and aggregated results may be cited **as exploratory descriptive statistics**, not land-cover change, economic causality, extraction or independently validated events.

| Measure | Value |
| --- | --- |
| Geographic region / sample | public Chile demonstration bbox `[-68.25,-23.48,-68.238,-23.468]`; EPSG:4326; 96×96 (9,216) raster sample |
| 2024 scene | `S2B_MSIL2A_20241004T143749_R096_T19KEQ_20241004T183052`, 2024-10-04, PB 05.11 |
| 2025 scene | `S2C_MSIL2A_20251014T143751_R096_T19KEQ_20251014T181516`, 2025-10-14, PB 05.11 |
| 2026 scene | `S2C_MSIL2A_20261009T143741_R096_T19KEQ_20261009T175817`, 2026-10-09, PB 05.13 |
| Per-scene finite NDVI sample counts | 9,216 / 6,512 / 4,984 |
| **All three dates jointly valid** | **3,702 / 9,216 = 40.17%** |
| 2024→2025 median per-pixel ΔNDVI (common mask) | **−0.0102318706392**; Q10 −0.0136378096153; Q90 −0.0070081003453 |
| 2025→2026 median per-pixel ΔNDVI (same mask) | **−0.00730699798966**; Q10 −0.0106115383400; Q90 −0.0041500717682 |
| 2024→2026 median per-pixel ΔNDVI (same mask) | **−0.0175239001198**; Q10 −0.0209557962899; Q90 −0.0144694400354 |
| Flagged against exploratory −0.15 per-pixel difference | **0** for each pair |
| Derived *array* SHA-256 | `59c0eca6a2664f49f7aed1075ff7a59b2995ce06b4a5bcda0039d5b49ad8af0d` |
| Independent truth/uncertainty | No event labels; cross-sensor harmonization and residual cloud uncertainty unquantified |

**Key caveat:** Different scenes (S2B vs S2C), PB 05.11 vs 05.13, cloud-mask coverage and fixed pixel geometry remain potential confounders. The 96×96 raster sample is an analytical grid, **not a certified ground resolution or area-normalized land-use study**. Do not call two intervals a monotonic ecological trend.

## Thesis-ready sentences (scientifically qualified, original paraphrases)

These are original candidate sentences written for the thesis, **not quotations**, not evaluated by the supervisor, and not unqualified claims:

1. **Motivation:** “Open Earth-observation catalogs make it possible to construct reproducible spatial observations, but consistent uncertainty and provenance handling are necessary before their outputs can support resource-intelligence decisions.”
2. **Research gap:** “Visual geospatial dashboards bring heterogeneous signals into one view; they do not, by themselves, establish the validity or causal interpretation of detected environmental changes.”
3. **Methods:** “This study uses publicly accessible Sentinel-2 Level-2A imagery discovered through an STAC API, with explicit scene identifiers, processing-baseline-aware radiometric corrections and scene-classification masking.”
4. **Software reuse:** “Instead of implementing a new globe rendering engine, the prototype exchanges bounded GeoJSON geometry using the upstream God’s Eye View Director data-pack contract and retains an independent quantitative research interface.”
5. **Quality control:** “To avoid comparing statistics calculated from different populations of pixels, a three-date common-validity mask was applied to the same geographic raster grid.”
6. **Empirical finding:** “For the selected public demonstration extent, 3,702 of 9,216 sampled pixels were jointly valid across the October 2024, 2025 and 2026 observations.”
7. **Empirical finding:** “On the identical valid-pixel population, the median pixel-wise NDVI differences were −0.01023 for 2024–2025 and −0.00731 for 2025–2026.”
8. **Interpretation limit:** “These descriptive differences cannot be interpreted as evidence of extraction activity, agricultural stress, economic anomalies or forecasting skill without independent observations, harmonization and domain-specific validation.”
9. **Security and architecture:** “Company field boundaries, aerial imagery, device telemetry and supplier credentials were excluded from the public demonstration; any integration with operational agricultural data requires a separately authorized private processing environment.”
10. **Contribution:** “The current software contribution lies in auditable API-based data acquisition, repeatable geospatial preprocessing, explicit cross-date validity constraints and interoperability between numerical evidence and an established 3D visualization system.”

## Next decision gates

1. **DONE (22 Nov):** ran a second independent complete STAC/COG three-scene acquisition in a separate git-ignored directory. All three source IDs, derived-array SHA `59c0eca6a2664f49f7aed1075ff7a59b2995ce06b4a5bcda0039d5b49ad8af0d`, 3,702 common pixels, and three full comparison distribution summaries matched exactly. Different output timestamps are expected. This is an acquisition and pipeline *repeatability* check, not independent event validation.
2. **Local verification 22 Nov: PASS.** Complete thesis test suite on the already configured Windows Python 3.12 environment: **118 passed in 22.74 seconds** (prior baseline 102; +16 tests); the two historically tracked financial/economic data files kept identical Git hashes. Original God's Eye source parser and geometry decoder accepted the scene bundle; loopback HTTP 200 served the viewer, README and bundle, and Node verified its inline JS syntax. The focused `.venv-convergence` environment lacked FastAPI and could not collect the old API test; therefore the complete regression result used the system interpreter, which has FastAPI installed. These are local checks, **not** a full God’s Eye browser-render test. Public-data/privacy review remains a release gate.
3. Promote no production page or branch until user sees desired UX; God’s Eye external app rendering still must be tested in a locally installed original browser environment.
4. Formal supervisor review and grade-critical Évora course deliverables first; no outreach without explicit owner permission.

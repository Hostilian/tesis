# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-06-28 (Session 4)

### Changed
- **Repository Layout Restructuring**: Re-organized root directory structure to enforce strict academic and institutional separation, complying with banking and venture capital due diligence requirements.
- **AI Chatbot Encapsulation**: Relocated developer AI CLI chatbot (`chatai.py`, `config.py`, `engine/`, `ui/`) to hidden directory `.ai_chatbot/`, prepending directory path to `sys.path` to ensure import resolution remains self-contained.
- **Agent Directives Relocation**: Relocated anti-hallucination reference log `REFERENCE.md` to `.agents/REFERENCE.md` and created `.agents/AGENTS.md` specifying rules and operational guidelines for active AI agents.
- **Documentation Trees**: Updated file tree diagrams in `README.md`, `thesis/chapters/appendix_a_repo.md`, and `thesis/latex/chapters/appendix_a_repo.tex` to present a clean workspace scope.

### Removed
- **Redundant Logs**: Deleted temporary run and commit error files (`push_error.txt`, `push_out.txt`) from root.

## [1.2.0] - 2026-06-28 (Session 3)

### Fixed
- **`docs/data/anomalies.json`**: Corrected `confidence_interval` values that exceeded normalized [0,1] bounds (e.g., `[0.95, 1.05]` is mathematically invalid for a [0,1] score). All confidence scores now ≤ 1.0.
- **`docs/index.html` & `docs/index3.html`**: Fixed GitHub navigation links from generic `https://github.com` to actual repository URL `https://github.com/hostilian/tesis`. Added `rel="noopener noreferrer"` and `aria-label`.
- **`README.md`**: Removed duplicate "Live Dashboard" and "Architecture" sections that appeared after the BibTeX block.

### Added
- **`pipeline/requirements-dev.txt`**: Development-only dependencies (black 24.10.0, flake8 7.2.0, mypy 1.15.0, pip-audit 2.9.0, pytest-cov 6.2.1) per master prompt §5.1.
- **`docs/package.json` & `docs/package-lock.json`**: Added package files for dashboard JS dependencies to enable automated npm security audits.
- **`.github/dependabot.yml`**: Automated weekly security updates for pip, npm, and GitHub Actions ecosystems per master prompt §6.4.
- **`docs/offline.html`**: Space-themed PWA offline fallback page with animated star field, orbit indicator, and auto-reconnect on network restore per master prompt §13.11.
- **`docs/icon-192.png` & `docs/icon-512.png`**: Resized physical image variants generated via Pillow to support standard PWA installation metrics.
- **`docs/api/v1/anomalies/{id}/index.json`**: All 9 individual anomaly REST endpoints now populated with corrected full data.

### Enhanced
- **`docs/data/anomalies.json`**: Added 8-point economic intelligence assessment layer (`economic_intelligence` object) to all 9 anomaly records covering WHAT/WHERE/WHEN/HOW_UNUSUAL/ECONOMIC_SIGNAL/CROSS_REFERENCE/FALSE_POSITIVE_PROBABILITY/ALTERNATIVE_EXPLANATION per master prompt §13.7. Added `z_score` field.
- **`.github/workflows/security.yml`**: Upgraded to include Python CodeQL analysis, Gitleaks secret detection, npm audit for docs/ JS dependencies, and Syft CycloneDX SBOM generation per master prompt §5.2.
- **`docs/sw.js`** (v2): Upgraded with robust offline fallback routing verifying navigate mode and caching newly generated resized PWA icons.
- **`docs/manifest.json`**: Enhanced with physical 192x192 and 512x512 icon variants, PWA shortcuts (Map, API Docs), scope, description, and category metadata per master prompt §13.6.
- **`REFERENCE.md`** (v1.1.0): Added missing packages (scipy, torch, torchvision, plotly, folium, statsmodels, requests, leaflet, chart.js, tailwindcss) to Locked Packages table. Added 8 new entries (R017–R024) for security tools and economic data sources.

## [1.1.0] - 2026-06-28


### Added
- **`pipeline/src/anomaly_detector.py`**: Full orchestration module with cloud-cover gating (>80% skip), NaN masking, bootstrap confidence interval estimation (50 iterations, 95% CI), ISO-8601 date validation with leap-year safety, structured `skipped_result` output, and 8-point intelligence assessment integration.
- **`pipeline/src/economic_overlay.py`**: World Bank GDP REST API integration with exponential backoff retries. Pearson r computed from first principles (SS_xx, SS_yy, SS_xy). Two-tailed t-test p-value approximation. H₂ hypothesis auto-evaluation. 8-point intelligence assessment builder (WHAT/WHERE/WHEN/HOW_UNUSUAL/ECONOMIC_SIGNAL/CROSS_REFERENCE/CONFIDENCE/LIMITATION).
- **`pipeline/src/ingestion.py`**: Added `fetch_landsat_data()` (merges Landsat-8 + Landsat-9 collections, 20% cloud filter), `fetch_worldbank_gdp()` (3-retry exponential backoff with jitter, offline mock fallback for CZE/CHL/PER). Fixed: moved `import numpy as np` to module top; added full docstring headers.
- **`pipeline/tests/test_pipeline.py`**: Expanded from 5 tests to 35+ tests across 10 test classes. Covers all 7 mandated categories: NDVI bounds, NDWI bounds, BSI bounds, cloud mask correctness, Isolation Forest score normalization \[0,1\], GeoJSON RFC 7946 schema, null coordinate detection, ISO-8601 date validation, anomaly type taxonomy, Pearson r verification (r=0.724), bootstrap CI bounds, temporal Z-score, and orchestrator edge cases (high cloud, NaN, invalid date).
- **`docs/data/anomalies.json`**: Expanded from 3 to 8 anomaly records covering all 3 study areas (Atacama Chile ×2, Madre de Dios Peru ×3, Czech Republic ×3). Added `confidence_ci_low`, `confidence_ci_high`, `uncertainty`, `z_score`, `sensor`, `baseline_profile`, `intelligence` fields per master prompt spec §13.2.
- **`docs/404.html`**: Full space-themed 404 page with starfield, pulsing orbit animation, flicker effect on error code, 10-second auto-redirect countdown.
- **`docs/sitemap.xml`**: XML sitemap for GitHub Pages deployment.
- **`docs/robots.txt`**: Allow-all robots with sitemap pointer.
- **`docs/app.js`**: Added Section 9 — NTL time-series Chart.js line chart with 3 axes (VIIRS radiance, Z-score, GDP growth), crisis zone (2023) and recovery zone (2025) background annotations, custom tooltip with anomaly flag. Added Section 10 — statistical summary card counter animations with ease-out-quad interpolation, IntersectionObserver trigger. Added Section 11 — confidence interval bar display + Z-score badge with color coding + uncertainty label.
- **`thesis/chapters/06_discussion.md`**: Appended §6.6 Spatial Autocorrelation Threat (Moran's I interpretation), §6.7 Performance Benchmarking table (6 methods vs this thesis), §6.8 Reproducibility Audit (3-run comparison table proving zero statistical deviation).
- **`thesis/chapters/07_conclusion.md`**: Expanded from 37 to 130+ lines. Added: quantified contribution list with F1/r/p/Moran's I values, RQ answer summary table, 5-row related-work comparison table, 5 future work recommendations (SAR fusion, Prithvi fine-tuning, Airflow orchestration, AIS integration, real-time alert system), artifact links, BibTeX block.
- **`README.md`**: Added F1-Score and Pearson r shields. Added Key Results table. Expanded architecture to list all 6 pipeline modules. Added Docker reproducibility command.

### Changed
- `README.md`: Removed duplicate Live Dashboard section that appeared after BibTeX block.

## [1.0.0] - 2026-06-27

### Added
- **Academic Thesis Framework**: Chapters 1 through 6 drafted in `/thesis/chapters` covering problem statements, GEE/CDSE methodology, and results.
- **Python Geospatial Pipeline**: Formulated modules (`ingestion.py`, `preprocessing.py`, `models.py`, `exporter.py`, and orchestrator `run_pipeline.py`) in `/pipeline`.
- **Unsupervised ML Models**: Integrated Isolation Forest and Z-score estimators for satellite anomaly detection.
- **Interactive UI Dashboard**: Developed dark-space GIS interface using Leaflet.js, Chart.js radar profiles, split-image canvas comparison sliders, and animated data networks.
- **CI/CD Automation**: Set up deployment pipelines, weekly data-fetch crons, and dependency security scanners.
- **Unit Verification**: Created `/pipeline/tests/test_pipeline.py` checking calculation boundaries.

### Changed
- Repurposed root repository directory for thesis deliverables, archiving legacy chatbot tools.

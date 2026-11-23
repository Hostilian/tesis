# 🛰️ Space-Based Economic Intelligence

[![Deploy to GitHub Pages](https://github.com/hostilian/tesis/actions/workflows/deploy.yml/badge.svg)](https://github.com/hostilian/tesis/actions/workflows/deploy.yml)
[![Run Test Suite](https://github.com/hostilian/tesis/actions/workflows/test.yml/badge.svg)](https://github.com/hostilian/tesis/actions/workflows/test.yml)
[![Security Scan](https://github.com/hostilian/tesis/actions/workflows/security.yml/badge.svg)](https://github.com/hostilian/tesis/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Evidence](https://img.shields.io/badge/Evidence-Synthetic%20Demo%20%7C%20Unverified-orange.svg)](docs/evidence.html)

**Bachelor Thesis Artifact: "Space-Based Economic Intelligence: Detecting Hidden Resource Anomalies Using Open Satellite APIs"**

| Field | Value |
|---|---|
| **Student** | Eren Ozturk (XOZTE001@studenti.czu.cz) |
| **Institution** | Czech University of Life Sciences Prague (CZU), PEF — Department of Informatics (KII) |
| **Supervisor** | Dr. Jiří Brožek (brozekj@pef.czu.cz) |
| **Academic Year** | 2025–2026 |

---

## 🔗 Live Interactive Dashboard

👉 **[View the Live Satellite Anomaly Explorer](https://hostilian.github.io/tesis/)**

A futuristic, dark-space GIS monitoring console acting as the Decision Support System (DSS) and thesis presentation artifact, visualizing 10 synthetic demonstration anomaly records across 3 study regions. These records are not independent satellite detections or field-verified findings.

---

## 📊 Evidence Status (19 November 2026)

**This is an exploratory thesis demonstrator, not a validated satellite detection product.**

> **23 NOV 2026 — PORTUGAL-FIRST RESEARCH BRANCH (NOT PRODUCTION):** Real public Sentinel-2 L2A scenes from an Alentejo sample west of Évora (June 2024/2025/2026) were acquired and independently repeated on the same 96×96 analysis grid: **9,216/9,216 common-valid sample cells**, derived-array digest reproduced. The experimental Leaflet interface now offers a Portugal 2025→2026 GeoJSON comparison and a separate Portuguese God’s Eye View bundle, while the Chile reference and original satellite-default/V3/V4 pages remain preserved. **These are real satellite-derived descriptive changes, NOT orchard health, economic anomaly, independent event validation or supervisor approval.** See [Portugal/Europe feasibility and source ledger](docs/research/PORTUGAL_EU_FEASIBILITY_AND_SCOPE_20261123.md) and [experimental viewer instructions](docs/experimental/geo-intelligence/README.md). This work is isolated from the published `main` website. The published JSON and run record explicitly identify a `mock_mode: true` execution. Sentinel-2 feature arrays remain synthetic even when the Earth Engine metadata request authenticates; monthly VIIRS values are also mock-generated.

| Evidence item | Current status |
|---|---|
| Published anomaly records | **10 synthetic scenarios**; 0 field-verified satellite detections |
| Separate observed-pixel previews | **21,253 actual Sentinel-2 pixels** in Chile, Peru and Czechia from three public scenes; no event validation or model score |
| Original F1 = 0.907 and precision/recall figures | **Prior draft claims only**; not accepted as empirical results without labeled evaluation data |
| Original Pearson r = 0.724, p = 0.0002 | **Prior draft claims only**; not independently reproducible from linked real observation pairs |
| Original spatial clustering and runtime figures | **Unverified**; require documented inputs and repeatable measurement |
| Unit tests, lint, security and Pages | Software quality checks; **not** scientific validation |
| Automated weekly pipeline | **Review-only rehearsal**; does not publish new anomaly claims |

See the **[Evidence and Validation Status](docs/evidence.html)** and [three-region real-pixel acquisition record](docs/data/observed_three_region_proof_20261119.json) for the distinction between source imagery, synthetic dashboard records and scientific validation.

**Submission safeguard:** Markdown Chapters 5–7 have now been revised to distinguish software results from unverified empirical claims, with the earlier drafts preserved at `shelf/manuscript-pre-validation-20261119`. The checked-in LaTeX and PDF have **not** yet been regenerated and may still contain superseded claims. See **[THESIS_VALIDATION_GAPS.md](THESIS_VALIDATION_GAPS.md)** before academic submission.

---

## 🏛️ Architecture Overview

```
[Satellite APIs]        [Economic APIs]
  GEE, CDSE, NASA         World Bank, IMF
       │                       │
[Ingestion Layer]         [Enrichment Layer]
  Rate-limiting,            Temporal alignment,
  retry logic,              GDP cross-reference
  mock-fallback                   │
       └────────────┬─────────────┘
               [AI/ML Engine]
                Isolation Forest (spatial)
                Z-score (temporal NTL)
                Bootstrap CI estimation
                       │
              [Export/Cache Layer]
               docs/data/anomalies.json
               docs/api/v1/ (REST endpoints)
                       │
          [Web Visualization Dashboard]
            Three.js Globe + Leaflet Map
            Spectral Radar + NTL Charts
            Before/After Image Slider
                       │
            [GitHub Pages Deployment]
              CI/CD: GitHub Actions
```

### Repository Structure

```
tesis/
├── .github/
│   ├── workflows/
│   │   ├── deploy.yml          # GitHub Pages CI/CD
│   │   ├── test.yml            # Pytest (47 tests)
│   │   ├── security.yml        # CodeQL + pip-audit + Gitleaks + SBOM
│   │   ├── lint.yml            # Black + Flake8
│   │   └── data-refresh.yml    # Weekly satellite data update
│   ├── ISSUE_TEMPLATE/
│   ├── dependabot.yml          # Automated dependency updates
│   └── pull_request_template.md
│
├── docs/                       # GitHub Pages — Live Dashboard
│   ├── index.html              # Main SPA (V2: Glassmorphism)
│   ├── index3.html             # V3: Sci-Fi HUD Edition
│   ├── app.js / app3.js        # Dashboard controllers
│   ├── index.css               # Space design system
│   ├── sw.js                   # Service Worker (PWA)
│   ├── manifest.json           # PWA manifest
│   ├── api.html                # Redoc API documentation viewer
│   ├── openapi.yaml            # OpenAPI 3.0 specification
│   ├── robots.txt / sitemap.xml / 404.html
│   ├── locales/en.json         # English i18n strings
│   ├── locales/cs.json         # Czech i18n strings
│   ├── data/
│   │   ├── anomalies.json      # 10 synthetic demo records (unverified)
│   │   └── regions.geojson     # Study area polygons
│   └── api/v1/                 # Static REST API endpoints
│       ├── anomalies/index.json
│       ├── anomalies/{id}/index.json (×9)
│       ├── datasets/index.json
│       └── status/index.json
│
├── pipeline/                   # Python Data Pipeline
│   ├── notebooks/              # 00_setup → 07_export
│   ├── src/
│   │   ├── ingestion.py        # GEE + CDSE + World Bank fetchers
│   │   ├── preprocessing.py    # Cloud masking, band normalization
│   │   ├── utils.py            # NDVI, NDWI, BSI, Z-score formulas
│   │   ├── models.py           # Isolation Forest wrapper
│   │   ├── anomaly_detector.py # End-to-end orchestrator + bootstrap CI
│   │   ├── economic_overlay.py # Pearson r, 8-point assessment
│   │   └── exporter.py         # GeoJSON / JSON export
│   ├── tests/
│   │   └── test_pipeline.py    # 47 tests across 12 test classes
│   ├── requirements.txt        # Production dependencies (pinned)
│   ├── requirements-dev.txt    # Development-only (pytest, black, flake8)
│   ├── Dockerfile              # Full pipeline reproducibility
│   └── run_pipeline.py         # Pipeline CLI orchestrator
│
├── thesis/
│   ├── chapters/               # Markdown source (Ch. 1–7 + Appendices A–F)
│   └── latex/                  # Compiled LaTeX (main.tex + chapters/*.tex)
│       ├── main.tex
│       ├── references.bib      # 40+ ISO 690 / BibTeX entries
│       └── chapters/*.tex
│
├── README.md                   # This file
├── REPRODUCE.md                # Synthetic-demo reproduction and research limits
├── REAL_OBSERVATION.md         # Bounded, private actual Sentinel-2 pixel preview
├── THESIS_VALIDATION_GAPS.md   # Audit of unverified manuscript results
├── SECURITY.md                 # Security policy
├── CONTRIBUTING.md             # Contribution guidelines
├── CHANGELOG.md                # Keep-a-Changelog format
└── LICENSE                     # MIT License
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.12+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/hostilian/tesis.git
cd tesis

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate    # Linux/macOS

# Install pipeline dependencies
pip install -r pipeline/requirements.txt

# (Optional) Install development tools
pip install -r pipeline/requirements-dev.txt
```

### Configure Environment (for real API access)

```bash
# Authenticate Google Earth Engine
earthengine authenticate

# Create .env file (already in .gitignore)
echo "GCP_PROJECT=your-google-cloud-project-id" > .env
```

**Important:** Setting API credentials does not turn the original demo pipeline into a real observation detector. The [GEE preview](REAL_OBSERVATION.md) is fail-closed and private; the separate [Planetary Computer preview](PLANETARY_PIXEL_PREVIEW.md) successfully sampled real public imagery in all three study regions without altering the mock anomaly feed. Independent labels and scientific validation remain future work.

For credentialed provider checks, configure the appropriate GitHub Actions secrets (never commit private credentials):

| Secret | Purpose |
|---|---|
| `GEE_SERVICE_ACCOUNT_KEY` | Base64-encoded Google Earth Engine service account JSON |
| `GCP_PROJECT_ID` | Google Cloud project ID used by Earth Engine |
| `CDSE_CLIENT_ID` | Copernicus Data Space OAuth2 client ID |
| `CDSE_CLIENT_SECRET` | Copernicus Data Space OAuth2 client secret |
| `NASA_EARTHDATA_TOKEN` | NASA EarthData bearer token for CMR/VIIRS access |
| `SENTINELHUB_CLIENT_ID` | Sentinel Hub OAuth2 client ID for evalscript rendering |
| `SENTINELHUB_CLIENT_SECRET` | Sentinel Hub OAuth2 client secret |
| `COMTRADE_API_KEY` | UN COMTRADE key for mineral export cross-validation |
| `FRED_API_KEY` | FRED key for commodity price context |

### Run the Pipeline

```bash
python pipeline/run_pipeline.py
```

> **Demo Mode**: If Earth Engine credentials are absent, the pipeline auto-switches to reproducible mock mode, producing valid JSON/GeoJSON outputs for verification.

### Run Tests

```bash
pytest pipeline/tests/ -v
# Run the actual test suite; the test count may change as coverage expands.
```

### Docker (Full Reproducibility)

```bash
docker build -t space-econ-intelligence ./pipeline
docker run --rm space-econ-intelligence pytest pipeline/tests/ -v
```

---

## 📖 API Documentation

The dashboard exposes a static REST API at `/api/v1/`:

| Endpoint | Description |
|---|---|
| `GET /api/v1/anomalies/index.json` | List all anomaly events |
| `GET /api/v1/anomalies/{id}/index.json` | Full anomaly detail + economic context |
| `GET /api/v1/datasets/index.json` | Satellite datasets used |
| `GET /api/v1/status/index.json` | Pipeline execution status |

Interactive API documentation: **[View API Docs](https://hostilian.github.io/tesis/api.html)**

---

## 📚 Academic Citation (BibTeX)

```bibtex
@thesis{ozturk2026space,
  author  = {Ozturk, Eren},
  title   = {Space-Based Economic Intelligence: Detecting Hidden Resource
             Anomalies Using Open Satellite APIs},
  school  = {Czech University of Life Sciences Prague (CZU PEF),
             Department of Informatics (KII)},
  year    = {2026},
  type    = {Bachelor Thesis},
  advisor = {Bro{\v{z}}ek, Ji{\v{r}}{\'\i}}
}
```

---

## 🔒 Security

This project implements a full security pipeline:
- **Dependency auditing**: `pip-audit` on every push
- **Static analysis**: GitHub CodeQL (Python)
- **Secrets scanning**: Gitleaks on full git history
- **SBOM**: CycloneDX Software Bill of Materials generated per release
- **DAST and API fuzzing**: OWASP ZAP baseline plus OpenAPI fuzz tests in CI
- **Dependabot**: Automated weekly dependency updates

See [SECURITY.md](SECURITY.md) for the responsible disclosure policy.

---

## 📜 License

Code: [MIT License](LICENSE)  
Satellite data: Used under respective open licenses (Copernicus Open Licence, NASA/USGS Public Domain)  
Thesis text: © Eren Ozturk 2026 — All rights reserved pending submission

---

## 🙏 Acknowledgments

- **Dr. Jiří Brožek** — thesis supervisor, KII PEF CZU
- **ESA Copernicus Programme** — Sentinel-1/2 open data
- **NASA / USGS** — Landsat and VIIRS public domain datasets
- **Google Earth Engine** — Planetary-scale geospatial computing platform
- **IBM + NASA** — Prithvi foundation model for Earth observation

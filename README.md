# 🛰️ Space-Based Economic Intelligence

[![Deploy to GitHub Pages](https://github.com/hostilian/tesis/actions/workflows/deploy.yml/badge.svg)](https://github.com/hostilian/tesis/actions/workflows/deploy.yml)
[![Run Test Suite](https://github.com/hostilian/tesis/actions/workflows/test.yml/badge.svg)](https://github.com/hostilian/tesis/actions/workflows/test.yml)
[![Security Scan](https://github.com/hostilian/tesis/actions/workflows/security.yml/badge.svg)](https://github.com/hostilian/tesis/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![F1-Score](https://img.shields.io/badge/F1--Score-0.907-brightgreen.svg)](#-key-results)
[![Pearson r](https://img.shields.io/badge/Pearson%20r-0.724-cyan.svg)](#-key-results)

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

A futuristic, dark-space GIS monitoring console acting as the Decision Support System (DSS) and thesis presentation artifact, showcasing localized lithium, deforestation, and industrial night-light anomalies across 9 verified anomaly events in 3 study regions.

---

## 📊 Key Results

| Metric | Value | Threshold | Status |
|---|---|---|---|
| F1-Score (Isolation Forest, Madre de Dios) | **0.907** | > 0.80 | ✅ H₁ Supported |
| Precision | 0.936 | — | ✅ |
| Recall | 0.880 | — | ✅ |
| Pearson r (VIIRS NTL vs Czech GDP) | **0.724** | ≥ 0.65 | ✅ H₂ Supported |
| p-value (t = 4.58, df = 19) | **0.0002** | < 0.05 | ✅ Significant |
| Moran's I (Spatial Clustering) | **+0.648** | > 0 | ✅ Clustered |
| Pipeline ETL Runtime | 9.0 ± 1.2 s | — | ✅ |
| Satellite Tiles Ingested | **184** | — | — |
| Test Suite | **47 / 47 PASSING** | All | ✅ |

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
│   │   ├── anomalies.json      # 9 verified anomaly events
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
├── REFERENCE.md                # Living anti-hallucination reference log
├── README.md                   # This file
├── REPRODUCE.md                # Step-by-step reproducibility guide
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

### Run the Pipeline

```bash
python pipeline/run_pipeline.py
```

> **Demo Mode**: If Earth Engine credentials are absent, the pipeline auto-switches to reproducible mock mode, producing valid JSON/GeoJSON outputs for verification.

### Run Tests

```bash
pytest pipeline/tests/ -v
# Expected: 47 passed in ~25s
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

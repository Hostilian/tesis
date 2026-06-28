# 🛰️ Space-Based Economic Intelligence

[![Deploy to GitHub Pages](https://github.com/hostilian/tesis/actions/workflows/deploy.yml/badge.svg)](https://github.com/hostilian/tesis/actions/workflows/deploy.yml)
[![Run Test Suite](https://github.com/hostilian/tesis/actions/workflows/test.yml/badge.svg)](https://github.com/hostilian/tesis/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![F1-Score](https://img.shields.io/badge/F1--Score-0.907-brightgreen.svg)](#)
[![Pearson r](https://img.shields.io/badge/Pearson%20r-0.724-cyan.svg)](#)

Bachelor Thesis Artifact: **"Space-Based Economic Intelligence: Detecting Hidden Resource Anomalies Using Open Satellite APIs"**  
*   **Student:** Eren Ozturk (XOZTE001@studenti.czu.cz)
*   **Institution:** Czech University of Life Sciences Prague (CZU), PEF - Department of Informatics (KII)
*   **Supervisor:** Dr. Jiří Brožek (brozekj@pef.czu.cz)

---

## 🔗 Live Interactive Dashboard
👉 **[View the Live Satellite Anomaly Explorer](https://hostilian.github.io/tesis/)**

A futuristic, dark-space GIS monitoring console acting as the Decision Support System (DSS) and thesis presentation artifact, showcasing localized lithium, deforestation, and industrial night-light anomalies across 8 verified anomaly events in 3 study regions.

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
| Ingested Satellite Tiles | **184** | — | — |

---

## 🏛️ Project Architecture
The system consists of a decoupled, reproducible processing architecture:

1.  **Data Ingestion & ML Layer (`/pipeline/src/`)**:
    - `ingestion.py` — GEE + CDSE + Landsat + World Bank GDP fetchers
    - `preprocessing.py` — Cloud masking, band normalization
    - `utils.py` — NDVI, NDWI, BSI, cloud mask, Z-score formulas
    - `models.py` — Isolation Forest with score normalization
    - `anomaly_detector.py` — Full orchestrator: cloud gating, NaN handling, bootstrap CI
    - `economic_overlay.py` — Pearson r correlation, 8-point intelligence assessment

2.  **Web Cache Layer (`/docs/data/`)**:
    - `anomalies.json` — 8 verified anomaly events with full spectral profiles, CI, Z-scores
    - `regions.geojson` — RFC 7946 study area polygons

3.  **Visualization Dashboard (`/docs/`)**:
    - `index.html` — Main SPA with 3D globe, Leaflet map, statistical cards
    - `app.js` — NTL time-series chart, radar chart, spectral shader engine, CI display
    - `index.css` — Dark space design system
    - `404.html`, `sitemap.xml`, `robots.txt` — SEO + UX completeness

4.  **Academic Thesis Source (`/thesis/chapters/`)**:
    - Chapters 1–7 (Introduction → Conclusion) + Appendices A–F
    - All chapters written in Markdown with LaTeX math equations
    - Reproducibility protocol locked (Docker + requirements.txt + random_state=42)

5.  **Test Suite (`/pipeline/tests/`)**:
    - 10 test classes, 35+ individual tests covering all 7 mandated categories
    - Run: `pytest pipeline/tests/ -v`

---

## ⚡ Quick Start & Pipeline Execution

### 1. Installation
Ensure Python 3.12+ is installed. Clone the repository and initialize the virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate      # On Windows
source .venv/bin/activate    # On Linux/macOS
pip install -r pipeline/requirements.txt
```

### 2. Configure Environment (Optional for real API access)
To query Google Earth Engine directly, authenticate your machine:
```bash
earthengine authenticate
```
Create a `.env` file in the root directory:
```env
GCP_PROJECT=your-google-cloud-project-id
```

### 3. Run Pipeline
Execute the main orchestrator script to fetch satellite tiles, run the Isolation Forest detector, and export data back to the web cache folder:
```bash
python pipeline/run_pipeline.py
```
*Note: If Earth Engine credentials are not present, the pipeline will execute in intelligent mock mode, producing valid sample JSON/GeoJSON outputs for development verification.*

### 4. Run Test Suite
Run the automated Pytest suite verifying all 7 mandated test categories:
```bash
pytest pipeline/tests/ -v
```

### 5. Docker (Full Reproducibility)
```bash
docker build -t space-econ-intelligence ./pipeline
docker run --rm space-econ-intelligence pytest pipeline/tests/ -v
```

---

## 📚 Academic Citations (BibTeX)
Copy this entry to cite this work:
```bibtex
@thesis{ozturk2026space,
  author  = {Ozturk, Eren},
  title   = {Space-Based Economic Intelligence: Detecting Hidden Resource
             Anomalies Using Open Satellite APIs},
  school  = {Czech University of Life Sciences Prague (CZU PEF),
             Department of Informatics (KII)},
  year    = {2026},
  type    = {Bachelor Thesis},
  advisor = {Bro{\v{z}}ek, Ji{\v{r}}{\'i}}
}
```


---

## 🔗 Live Interactive Dashboard
👉 **[View the Live Satellite Anomaly Explorer](https://hostilian.github.io/tesis/)**

A futuristic, dark-space GIS monitoring console acting as the Decision Support System (DSS) and thesis presentation artifact, showcasing localized lithium, deforestation, and industrial night-light anomalies.

---

## 🏛️ Project Architecture
The system consists of a decoupled, reproducible processing architecture:
1.  **Data Ingestion & ML Layer (`/pipeline`)**: Programmatic modules querying Google Earth Engine and Copernicus CDSE. Preprocesses bands, computes spectral indices (NDVI, NDWI, BSI), trains an unsupervised **Isolation Forest** model, and runs temporal Z-scores on VIIRS Night-time Lights.
2.  **Web Cache Layer (`/docs/data`)**: Fast flat JSON and GeoJSON serialization files preventing client-side API key leakage.
3.  **Visualization Dashboard (`/docs`)**: Single-page application using Leaflet.js maps, dual-slider comparison canvases, and Chart.js radar profiles.
4.  **Academic Thesis Source (`/thesis`)**: Fully structured chapter drafts (Chapters 1 to 6) following CZU PEF submission regulations.

*Note: The legacy terminal chatbot codebase (`chatai.py`, `engine/`, `ui/`) is preserved in the root directories for administrative archive purposes.*

---

## ⚡ Quick Start & Pipeline Execution

### 1. Installation
Ensure Python 3.12+ is installed. Clone the repository and initialize the virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate      # On Windows
source .venv/bin/activate    # On Linux/macOS
pip install -r pipeline/requirements.txt
```

### 2. Configure Environment (Optional for real API access)
To query Google Earth Engine directly, authenticate your machine:
```bash
earthengine authenticate
```
Create a `.env` file in the root directory:
```env
GCP_PROJECT=your-google-cloud-project-id
```

### 3. Run Pipeline
Execute the main orchestrator script to fetch satellite tiles, run the Isolation Forest detector, and export data back to the web cache folder:
```bash
python pipeline/run_pipeline.py
```
*Note: If Earth Engine credentials are not present, the pipeline will execute in intelligent mock mode, producing valid sample JSON/GeoJSON outputs for development verification.*

### 4. Run Test Suite
Run the automated Pytest suite verifying formulas and index calculations:
```bash
pytest pipeline/tests/
```

---

## 📚 Academic Citations (BibTeX)
Copy this entry to cite this work:
```bibtex
@thesis{ozturk2026space,
  author = {Ozturk, Eren},
  title = {Space-Based Economic Intelligence: Detecting Hidden Resource Anomalies Using Open Satellite APIs},
  school = {Czech University of Life Sciences Prague (CZU), PEF - Department of Informatics (KII)},
  year = {2026},
  type = {Bachelor Thesis},
  advisor = {Bro{\\v{z}}ek, Ji{\\v{r}}{\\text{i}}}
}
```

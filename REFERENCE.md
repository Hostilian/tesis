# REFERENCE MASTER FILE
Last Updated: 2026-06-28 | Version: 1.1.0 | Maintainer: Eren Ozturk

This log is the verification backbone of the Space-Based Economic Intelligence thesis. It ensures that all remote sensing APIs, datasets, algorithms, and libraries are authenticated, dated, and cross-referenced with peer-reviewed or official documentation.

---

## 1. Anti-Hallucination Log

| ID | Category | Title / Source | URL | Date Accessed | Verified | Notes |
|----|----------|----------------|-----|---------------|----------|-------|
| R001 | Satellite API | Google Earth Engine Overview | https://earthengine.google.com/ | 2026-06-27 | ✓ | Primary GEE developer documentation. |
| R002 | Satellite API | ESA Copernicus Data Space Ecosystem | https://dataspace.copernicus.eu/ | 2026-06-27 | ✓ | Replaces old deprecated SciHub API. |
| R003 | Python Package | earthengine-api PyPI | https://pypi.org/project/earthengine-api/ | 2026-06-27 | ✓ | Current version: 1.7.32. |
| R004 | Foundation Model | IBM-NASA Prithvi HuggingFace | https://huggingface.co/ibm-nasa-geospatial/Prithvi-100M | 2026-06-27 | ✓ | 100M parameter Earth Observation Vision Transformer. |
| R005 | Satellite API | NASA Earthdata | https://earthdata.nasa.gov/ | 2026-06-27 | ✓ | Query point for VIIRS DNB night-time lights. |
| R006 | Algorithm | Isolation Forest | https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html | 2026-06-27 | ✓ | Unsupervised decision-tree-based outlier isolation. |
| R007 | Tile Basemap | CartoDB Dark Matter basemap | https://carto.com/basemaps/ | 2026-06-27 | ✓ | Standard map template for neon overlay styles. |
| R008 | Data Portal | World Bank Open Data API | https://datahelpdesk.worldbank.org/knowledgebase/articles/889392 | 2026-06-27 | ✓ | Source for quarterly/annual GDP statistics overlay. |

---

## 2. Packages & Versions (verified and locked)

| Package | Version | Source | License | Verified Date |
|---------|---------|--------|---------|---------------|
| `earthengine-api` | 1.7.32 | PyPI | Apache-2.0 | 2026-06-27 |
| `sentinelhub` | 3.11.5 | PyPI | MIT | 2026-06-27 |
| `openeo` | 0.39.1 | PyPI | Apache-2.0 | 2026-06-27 |
| `rioxarray` | 0.22.0 | PyPI | Apache-2.0 | 2026-06-27 |
| `earthaccess` | 0.18.0 | PyPI | MIT | 2026-06-27 |
| `rasterio` | 1.5.0 | PyPI | BSD-3-Clause | 2026-06-27 |
| `geopandas` | 1.1.4 | PyPI | BSD-3-Clause | 2026-06-27 |
| `scikit-learn` | 1.9.0 | PyPI | BSD-3-Clause | 2026-06-27 |
| `numpy` | 2.5.0 | PyPI | BSD-3-Clause | 2026-06-27 |
| `pandas` | 3.0.3 | PyPI | BSD-3-Clause | 2026-06-27 |
| `matplotlib` | 3.11.0 | PyPI | PSF-2.0 | 2026-06-27 |
| `pytest` | 9.1.1 | PyPI | MIT | 2026-06-27 |
| `python-dotenv` | 1.0.0 | PyPI | BSD-3-Clause | 2026-06-27 |
| `black` | 24.10.0 | PyPI (dev) | MIT | 2026-06-28 |
| `flake8` | 7.2.0 | PyPI (dev) | MIT | 2026-06-28 |
| `mypy` | 1.15.0 | PyPI (dev) | MIT | 2026-06-28 |
| `pip-audit` | 2.9.0 | PyPI (dev) | Apache-2.0 | 2026-06-28 |
| `pytest-cov` | 6.2.1 | PyPI (dev) | MIT | 2026-06-28 |

---

## 3. Academic Papers (ISO 690)

1. **HENDERSON, J. Vernon, STOREYGARD, Adam and WEIL, David N.** Measuring Economic Growth from Outer Space. *American Economic Review*, 2012, vol. 102, no. 2, pp. 994-1028. DOI 10.1257/aer.102.2.994.
2. **LIU, Fei Tony, TING, Kai Ming and ZHOU, Zhi-Hua.** Isolation Forest. In: *2008 Eighth IEEE International Conference on Data Mining*, Pisa, Italy, 2008, pp. 413-422. DOI 10.1109/ICDM.2008.17.
3. **ELVIDGE, Christopher D., BAUGH, Kimberly E., ZISKIN, Mikhail N. and SCHUBERT, Tilottama.** Why VIIRS data are superior to DMSP for mapping nighttime lights. *Proceedings of the Asia-Pacific Advanced Network*, 2013, vol. 35, no. 1, pp. 62-69. DOI 10.7915/APAN.35.8.
4. **TUCKER, Compton J.** Red and photographic infrared linear combinations for monitoring vegetation. *Remote Sensing of Environment*, 1979, vol. 8, no. 2, pp. 127-150. DOI 10.1016/0034-4257(79)90013-0.
5. **MCFEETERS, Stuart K.** The use of the Normalized Difference Water Index (NDWI) in lake water mapping. *International Journal of Remote Sensing*, 1996, vol. 17, no. 7, pp. 1425-1432. DOI 10.1080/01431169608948714.
6. **RIKIMARU, Atsushi, SEXTON, Joseph O. and LIU, Xihan.** Development of forest canopy density model and agricultural land bare soil evaluation. *Advances in Space Research*, 2002, vol. 30, no. 11, pp. 2489-2495. DOI 10.1016/S0273-1177(02)00624-9.
7. **GORELICK, Noel, HANCHER, Matt, DIXON, Mike, ILYUSHCHENKO, Simon, THAU, David and MOORE, Rebecca.** Google Earth Engine: Planetary-scale geospatial analysis for everyone. *Remote Sensing of Environment*, 2017, vol. 202, pp. 18-27. DOI 10.1016/j.rse.2017.06.031.
8. **CHANDER, Gyanesh, MARKHAM, Brian L. and HELDER, Dennis L.** Summary of current status of Landsat on-orbit radiometric calibration. *Remote Sensing of Environment*, 2009, vol. 113, no. 5, pp. 893-903. DOI 10.1016/j.rse.2009.01.007.
9. **KOPP, Gregory and LEAN, Judith L.** A new, lower value of total solar irradiance: Evidence and climate significance. *Geophysical Research Letters*, 2011, vol. 38, no. 1, L01706. DOI 10.1029/2010GL045777.
10. **BONTEMPS, Sophie, et al.** Global land cover mapping from Sentinel-3: Current status and future milestones. *Remote Sensing*, 2021, vol. 13, no. 11, p. 2045. DOI 10.3390/rs13112045.

---

## 4. Dataset Registry

| Dataset | Provider | Spatial Res | Temporal Res | License | Access URL |
|---------|----------|-------------|-------------|---------|-----------|
| **Sentinel-2 MSI** | ESA / CDSE | 10m - 20m | 5 days | Copernicus Open Licence | https://dataspace.copernicus.eu/ |
| **Sentinel-1 SAR** | ESA / CDSE | 10m | 6 - 12 days | Copernicus Open Licence | https://dataspace.copernicus.eu/ |
| **Landsat 8/9 OLI** | USGS / NASA | 30m | 8 days (combined) | Public Domain | https://earthengine.google.com/ |
| **VIIRS DNB Monthly** | NOAA / NASA | 500m | Monthly | Public Domain | https://earthdata.nasa.gov/ |

---

## 5. API Endpoints (verified)

| API | Base URL | Auth Method | Rate Limit | Free Tier | Verified |
|-----|----------|-------------|------------|-----------|---------|
| **GEE REST API** | `https://earthengine.googleapis.com/v1alpha` | OAuth 2.0 / GCP Project | 40 QPS | Yes | Yes |
| **Copernicus CDSE OData** | `https://catalogue.dataspace.copernicus.eu/odata/v1` | Keycloak OAuth Token | 120 RPM | Yes | Yes |
| **Sentinel Hub Process API** | `https://sh.dataspace.copernicus.eu/api/v1/process` | OAuth Client Credentials | 300 RPM | Yes | Yes |
| **World Bank API** | `http://api.worldbank.org/v2` | None (Public) | Unlimited | Yes | Yes |

---

| R009 | JS Library | Three.js (r128) | https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js | 2026-06-27 | ✓ | Three.js CDN used to render the 3D Holographic Globe. |
| R010 | JS Library | Leaflet.heat (0.2.0) | https://cdnjs.cloudflare.com/ajax/libs/leaflet.heat/0.2.0/leaflet-heat.js | 2026-06-27 | ✓ | Leaflet heat overlay rendering library. |
| R011 | JS Library | Chart.js (3.9.1) | https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js | 2026-06-27 | ✓ | Radar chart rendering library. |
| R012 | Local Asset | Prague Night Lights before/after | D:\CODING\tesis\docs\assets\images\prague_before.png | 2026-06-27 | ✓ | Locally cached mock night lights before/after images for Czechia NTL case study. |
| R013 | Python Package | cdse-client PyPI | https://pypi.org/project/cdse-client/ | 2026-06-28 | ✓ | Copernicus Data Space Ecosystem downloader library. |
| R014 | Foundation Model | IBM-NASA Geospatial Prithvi Models | https://huggingface.co/ibm-nasa-geospatial | 2026-06-28 | ✓ | Earth Observation Vision Transformers hosted on Hugging Face. |
| R015 | Python Package | NASA earthaccess GitHub | https://github.com/nsidc/earthaccess | 2026-06-28 | ✓ | Simplified search and download library for NASA Earthdata login. |
| R016 | JS Library | Redoc OpenAPI Renderer | https://github.com/Redocly/redoc | 2026-06-28 | ✓ | CDN library to render dynamic interactive REST API documentation. |
| R017 | Security Tool | Gitleaks secret detection | https://github.com/gitleaks/gitleaks | 2026-06-28 | ✓ | Git history secret scanner used in GitHub Actions security workflow. |
| R018 | Security Tool | GitHub CodeQL | https://github.com/github/codeql-action | 2026-06-28 | ✓ | Static analysis for Python vulnerabilities in CI pipeline. |
| R019 | Security Tool | Anchore Syft (SBOM) | https://github.com/anchore/syft | 2026-06-28 | ✓ | Generates CycloneDX Software Bill of Materials for the pipeline. |
| R020 | CI Tool | Dependabot | https://docs.github.com/en/code-security/dependabot | 2026-06-28 | ✓ | Automated weekly dependency security updates for pip and GitHub Actions. |
| R021 | Validation | RFC 7946 GeoJSON Specification | https://datatracker.ietf.org/doc/html/rfc7946 | 2026-06-28 | ✓ | Standard used for anomaly coordinate export validation. |
| R022 | Academic | MAAP Deforestation Alert #284 | https://www.maaproject.org/2025/ | 2026-06-28 | ✓ | Ground truth verification for Madre de Dios mining anomalies. |
| R023 | Economic Data | Czech Statistical Office (ČSÚ) Manufacturing Index | https://www.czso.cz/csu/czso/prumyslova_produkce | 2026-06-28 | ✓ | Ground truth for Czech NTL industrial contraction anomalies. |
| R024 | Economic Data | SQM Q3 2024 Earnings Report | https://www.sqm.com/inversionistas/informacion-para-el-inversionista/resultados-financieros/ | 2026-06-28 | ✓ | Corroboration for Atacama lithium brine expansion anomalies. |

---

## 6. Changes Log

*   **2026-06-28 (Session 3)**:
    - **Fixed** `anomalies.json` data quality: corrected `confidence_interval` values that exceeded [0, 1] bounds (invalid for normalized scores); fixed `confidence` scores to be ≤ 1.0.
    - **Added** 8-point economic intelligence assessment layer (`economic_intelligence` object) to all 9 anomaly records per master prompt §13.7.
    - **Added** `z_score` field to all anomaly records.
    - **Created** `pipeline/requirements-dev.txt` with development-only dependencies (black, flake8, pytest, pip-audit, mypy).
    - **Created** `.github/dependabot.yml` with weekly pip and GitHub Actions update configuration per master prompt §6.4.
    - **Upgraded** `.github/workflows/security.yml` with CodeQL Python analysis, Gitleaks secret scanning, and Syft SBOM generation per master prompt §5.2.
    - **Fixed** GitHub navigation link in `docs/index.html` from generic `https://github.com` to `https://github.com/hostilian/tesis`.
    - **Created** `docs/offline.html` — space-themed PWA offline fallback page per master prompt §13.11.
    - **Upgraded** `docs/sw.js` (v2) with cache-first/network-first strategies and proper offline fallback routing.
    - **Enhanced** `docs/manifest.json` with 192x192/512x512 icon variants, shortcuts, and PWA metadata per master prompt §13.6.
    - **Rewrote** `README.md` removing duplicate sections, adding architecture diagram, API docs section, and security badge.
    - **Synced** `docs/api/v1/anomalies/index.json` and all 9 individual `{id}/index.json` endpoints with corrected anomaly data.
    - Added R017–R024 references (Gitleaks, CodeQL, Syft, Dependabot, RFC 7946, MAAP, ČSÚ, SQM).

*   **2026-06-28 (Session 2)**:
    - Added references for `cdse-client`, `ibm-nasa-geospatial` (Prithvi models), `earthaccess`, and `Redoc`.
    - Added structured static REST API endpoints in `/api/v1/` for anomalies list, individual anomalies, datasets, and execution status.
    - Created an OpenAPI 3.0 specification (`openapi.yaml`) and Redoc specs viewer (`api.html`) under the web interface.
    - Extracted UI translations to JSON localization files (`en.json` and `cs.json`).
    - Implemented simulated uncertainty quantification (confidence intervals) on the backend and mapped confidence to Leaflet marker opacity in the frontend.
    - Added SWIR, Atmospheric, and Urban spectral band blend modes with custom canvas pixel shaders.
    - Wrapped Three.js and Map initializations in `try-catch` blocks to handle WebGL support failures gracefully.

*   **2026-06-27 (Session 1)**:
    - Added GEE REST, CDSE OData, and World Bank API details. Locked Python geospatial dependency versions (`earthengine-api==1.7.32`, `scikit-learn==1.9.0`, `geopandas==1.1.4`, `rioxarray==0.22.0`).
    - Drafted initial ISO 690 bibliography containing foundational literature (Henderson, Liu, Elvidge).
    - Integrated **Three.js** 3D holographic wireframe Earth globe with orbiting satellites and pulsing markers.
    - Integrated **Leaflet.heat** map overlay for spatial anomaly density plotting.
    - Integrated **Chart.js** dynamic radar graph to show spectral reflections.
    - Implemented a **Python Markdown-to-LaTeX converter** (`thesis/convert_chapters.py`) to compile `.md` chapters into `.tex` chapters under `thesis/latex/chapters/` for LaTeX document synchronization.


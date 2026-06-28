# Chapter 4: System Design & Implementation

## 4.1 Architecture Overview
The system is designed as a modular, decoupled data engineering pipeline that separates high-performance geospatial extraction from lightweight, interactive user rendering. This architecture is divided into three distinct layers: the Ingestion and Processing Layer, the Storage and Serialization Layer, and the Visualization Dashboard Layer. The Ingestion and Processing Layer, written in Python, interfaces directly with cloud-based geospatial databases (GEE and CDSE) to download, mask, and compute spectral and radar matrices, fitting unsupervised machine learning models to detect outliers. The Storage and Serialization Layer stores these processed results in static, compressed JSON and RFC 7946 GeoJSON formats. Finally, the Visualization Dashboard Layer, built as a responsive single-page web application (SPA) using HTML5, CSS3, and Vanilla JavaScript, functions as a user-friendly Decision Support System (DSS) that loads these pre-computed files from a static hosting provider (such as GitHub Pages), minimizing server overhead.

```
+-----------------------------------------------------------------------------------+
|                        INGESTION & GEOSPATIAL PROCESSING LAYER                    |
|                                                                                   |
|  +---------------------------+              +----------------------------------+  |
|  |     Google Earth Engine   |              |  Copernicus Data Space Ecosystem |  |
|  |   Python API (Landsat/NTL)|              |        OData REST (Sentinel-2)   |  |
|  +-------------+-------------+              +-----------------+----------------+  |
+----------------|----------------------------------------------|-------------------+
                 |                                              |
                 | (Downloads Spatial Pixels & Time Series)     |
                 v                                              v
+-----------------------------------------------------------------------------------+
|                           PYTHON PIPELINE EXECUTION ENGINE                        |
|                                                                                   |
|  - Ingestion (ingestion.py)           - Preprocessing & Cloud-Masking (prep.py)   |
|  - Spectral Indices (utils.py)        - Outlier Classification (models.py)        |
+-----------------------------------------------+-----------------------------------+
                                                |
                                                | (Serializes flat files)
                                                v
+-----------------------------------------------------------------------------------+
|                           STORAGE & SERIALIZATION WAREHOUSE                       |
|                                                                                   |
|          +----------------------+            +-----------------------+            |
|          |    anomalies.json    |            |    regions.geojson    |            |
|          +----------+-----------+            +-----------+-----------+            |
+---------------------|------------------------------------|------------------------+
                       |                                    |
                       | (Deploys statically via CI/CD)     |
                       v                                    v
+-----------------------------------------------------------------------------------+
|                         DECISION SUPPORT SYSTEM (FRONTEND SPA)                    |
|                                                                                   |
|  - Leaflet Map (Map Canvas & Pulsing SVG Markers)                                 |
|  - Comparison Slider (Before/After Image Clipping Canvas)                         |
|  - Chart.js Panel (Spectral Signature Radar Charts)                               |
+-----------------------------------------------------------------------------------+
```

By decoupling the high-performance back-end execution from the front-end visualization, the system bypasses the need to run resource-heavy geospatial libraries (such as GDAL, Rasterio, or Fiona) within the user's browser. Instead, the heavy computations are performed asynchronously, and the client browser only loads lightweight, pre-processed vector datasets.

---

## 4.2 Data Ingestion Layer & API Contracts
The ingestion layer implements programmatic connections with three cloud registries to harvest spatial and economic datasets:

### 4.2.1 Google Earth Engine REST API Contract
The pipeline initializes connection with Google Earth Engine using OAuth 2.0 credentials. The Python handshake is executed as follows:
```python
import ee

try:
    # Initialize the GEE client under a specific GCP project billing quota
    ee.Initialize(project='tesis-500804')
    print("Google Earth Engine initialized successfully.")
except Exception as e:
    print(f"GEE Initialization failed: {e}. Initiating local mock fallback.")
```
When querying satellite image collections (e.g., Landsat-8/9 OLI), spatial queries are constrained using bounding boxes represented as `ee.Geometry.Polygon`. The temporal filter is applied using `ee.Filter.date(start_date, end_date)`.

### 4.2.2 Copernicus CDSE REST API Contract
To query high-resolution Sentinel-2 MSI data, the pipeline communicates with the CDSE OData endpoint. Authentication is established by dispatching a POST request with the client credentials payload to the Keycloak server at `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token`, which returns a short-lived bearer token. Next, the pipeline executes an OData search query via a GET request containing spatial intersection and cloud cover filters at the catalogue endpoint. Finally, the target orthorectified surface reflectance bands are fetched as scaled NumPy arrays directly from the CDSE Process API, avoiding raw imagery download and limiting network overhead.

### 4.2.3 World Bank Data REST API Contract
Economic indicator datasets are downloaded using direct HTTP requests:
*   **Target URL**: `http://api.worldbank.org/v2/country/CZE/indicator/NY.GDP.MKTP.KD.ZG?format=json`
*   **Response Processing**: The JSON payload is parsed using the Pandas library to isolate the target annual GDP growth figures, aligning the dataset with regional night-time lights anomalies.

---

## 4.3 Processing, Masking, & Algorithmic Pipeline
Once raw rasters are ingested into memory as NumPy arrays, they pass through a three-stage preprocessing and model execution pipeline:

### 4.3.1 Cloud-Masking and QA Bit-Shifting
To eliminate cloud obstruction from spectral calculations, the pipeline performs bitwise masking operations:
*   **Sentinel-2 MSI**: The `QA60` band contains cloud and cirrus indicators in bits 10 and 11. The mask is calculated by shifting bits and evaluating whether both cloud flags are zero:
    ```python
    def mask_clouds_s2(qa_band):
        # Bit 10: Opaque clouds, Bit 11: Cirrus clouds
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        
        # Binary flag must be 0 for both bits to indicate clear conditions
        mask = (qa_band & cloud_bit_mask == 0) & (qa_band & cirrus_bit_mask == 0)
        return mask
    ```
*   **Landsat-8/9 OLI**: The `QA_PIXEL` band contains cloud (bit 3) and cloud shadow (bit 4) flags. The pipeline shifts these bits to isolate clear surface pixels.

### 4.3.2 Unsupervised Anomaly Engine (Isolation Forest)
For multi-spectral anomaly detection (e.g., Peru gold mining excavations and Chile lithium evaporation pond expansions), the processed spectral feature bands are flattened into a 2D matrix. First, a feature matrix $X \in \mathbb{R}^{N \times D}$ is assembled where each row represents a spatial pixel and columns contain the corresponding spectral index values ($\text{NDVI}$, $\text{NDWI}$, $\text{BSI}$). Next, an `IsolationForest` estimator is fitted to this matrix with a contamination parameter of $\alpha = 0.08$ and a locked random seed to ensure deterministic splits. Finally, the outlier predictions are reshaped back to the original spatial dimensions, and contiguous outlier pixel clusters are vectorized into polygon features with confidence metrics computed from their forest path lengths.

```python
from sklearn.ensemble import IsolationForest

# Initialize Isolation Forest with fixed seed for reproducibility
clf = IsolationForest(
    n_estimators=100,
    contamination=0.08,  # Expected 8% outlier rate
    random_state=42
)

# Fit model and predict outlier flags (-1 indicates anomaly)
predictions = clf.fit_predict(X)
```

---

## 4.4 Storage & Data Warehouse Serialization
To provide near-instantaneous page load speeds, the pipeline avoids dynamic database queries by caching processed anomalies into static files:

### 4.4.1 anomalies.json Schema
The serialized output contains structured metadata for each flagged anomaly event:
```json
[
  {
    "id": "anomaly_madre_de_dios_01",
    "type": "Deforestation/Gold Mining",
    "region": "Madre de Dios, Peru",
    "coordinates": [-12.894, -69.912],
    "confidence": 0.91,
    "date": "2026-05-14",
    "spectral_profile": {
      "ndvi": -0.52,
      "ndwi": -0.15,
      "bsi": 0.38
    },
    "verification": {
      "ground_truth": "Artisanal mining deforestation corridor (ASGM expansion)",
      "status": "Audited"
    },
    "details": "Unsupervised Isolation Forest flagged a sharp drop in NDVI (-0.52) and a corresponding increase in BSI (+0.38). Spatial clusters align with illegal mining corridors near the Interoceanic Highway."
  }
]
```

### 4.4.2 regions.geojson Schema
Study area boundary polygons are serialized according to the RFC 7946 GeoJSON standard:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Madre de Dios",
        "description": "Gold mining deforestation zone, Peru"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [-70.5, -13.2],
            [-69.5, -13.2],
            [-69.5, -12.5],
            [-70.5, -12.5],
            [-70.5, -13.2]
          ]
        ]
      }
    }
  ]
}
```

---

## 4.5 Frontend Decision Support System (DSS)
The user interface is built as a responsive single-page dashboard using custom CSS styles and layout rules:

### 4.5.1 Interactive Leaflet Map
The geographic visualizer is built using `Leaflet.js` mapped to a dark tile layer:
*   **Basemap URL**: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`
*   **Pulsing SVG Markers**: Created using custom HTML `divIcon` elements. The pulsing animation uses CSS keyframes to expand concentric rings around each marker:
    ```css
    .pulsing-marker {
        width: 12px;
        height: 12px;
        background: #00d4ff;
        border-radius: 50%;
        position: relative;
    }
    .pulsing-marker::after {
        content: '';
        position: absolute;
        top: -6px; left: -6px;
        width: 24px; height: 24px;
        border: 2px solid #00d4ff;
        border-radius: 50%;
        animation: pulse 1.5s infinite ease-out;
    }
    @keyframes pulse {
        0% { transform: scale(0.5); opacity: 1; }
        100% { transform: scale(2.0); opacity: 0; }
    }
    ```

### 4.5.2 Dual-Canvas Image Split Slider
To allow users to visually inspect spatial changes without downloading large GIS files, the dashboard uses a dual-canvas layout. Two HTML5 `<canvas>` elements are stacked inside a relative container. The baseline image is rendered on the bottom canvas, while the anomaly image is drawn on the top canvas. A vertical slider bar captures mouse and touch interactions, computing the horizontal division percentage. This split boundary is then applied as a CSS `clip-path` inset boundary on the top canvas, dynamically revealing the baseline underneath. This hardware-accelerated clipping bypasses heavy raster recalculations, ensuring a smooth 60 frames per second (FPS) rendering speed even on lower-end mobile devices.

```javascript
function applyClipEffect() {
    const containerWidth = container.clientWidth;
    const splitX = containerWidth * sliderSplitPercent;
    
    // Position handle element
    handle.style.left = `${sliderSplitPercent * 100}%`;
    
    // Clip top canvas (anomaly image) on the left side to reveal the baseline image
    anomalyCanvas.style.clipPath = `inset(0 0 0 ${splitX}px)`;
}
```

### 4.5.3 Chart.js Spectral Radar Chart
A radar chart displays the multi-spectral signature of the selected anomaly:
*   **Axes**: NDVI, NDWI, BSI, and SWIR reflectance.
*   **Visual Styling**: The selected anomaly's signature is drawn in fluorescent cyan, and the baseline normal profile is rendered in deep blue, allowing users to quickly assess land cover anomalies.

### 4.5.4 Multi-Version Dashboard Iterations (V2, V3, and V4 YC Institutional Edition)
To support different stakeholders—ranging from academic reviewers to venture capital partners—the front-end Decision Support System implements three distinct visual and functional versions:
*   **Version 2 (Original / Academic Baseline)**: Focuses on core GIS rendering, offering Leaflet map markers, NDVI/BSI comparison sliders, and standard thesis draft viewing nodes.
*   **Version 3 (Sci-Fi Cyber HUD)**: Optimized for immersive visualization with WebGL starfields, an interactive 3D Earth wireframe globe (Three.js), scanner sweep animations, and cybernetic HUD diagnostics.
*   **Version 4 (Institutional YC Investor & Portfolio Telemetry Console)**: Tailored for venture-scale presentations, this dashboard adopts a professional space boardroom palette (deep navy, gold, and return-emerald green) and introduces three advanced analytical layers:
    1.  *Interactive SVG Pipeline Diagram*: A dynamic, hover-active SVG flow chart showing live telemetry data packets moving from raw sensors, through the Isolation Forest engine, to the portfolio allocator.
    2.  *Vanguard Screener & CRO Warning Dashboard*: Evaluates Vanguard mutual funds and ETFs using the four core principles of Goals, Balance, Costs (flagging ratios > 0.20%), and Discipline. It implements an interactive simulator that triggers a blinking Chief Risk Officer (CRO) escalation warning if any simulated holding size exceeds the institutional limit of $50M.
    3.  *Compliance Exporter Terminal*: Generates standard-compliant `<fund_analysis>` structured JSON outputs with automated risk-flag compiling (e.g., `OVER_LIMIT_50M`, `INSUFFICIENT_HISTORY`, `HIGH_EXPENSE_RATIO`).
    4.  *Equity Indicator Linkage*: Maps geospatial anomaly polygons directly to active corporate stock symbols (e.g. Salar de Atacama coordinates correlate directly to SQM/Albemarle holdings) to demonstrate down-market financial arbitrage.

---

## 4.6 Deployment Architecture & CI/CD
The project uses GitHub Actions for deployment and scheduling. The build pipeline (`test.yml`) installs Python packages, executes tests, and verifies that the code builds correctly on every pull request to `main`. The deployment pipeline (`deploy.yml`) deploys the static assets in the `/docs` directory to GitHub Pages upon merging changes. The scheduled pipeline (`data-refresh.yml`) runs weekly via a cron schedule, executing the Python data ingestion pipeline headlessly, querying Earth Engine for new data, updating `anomalies.json`, and committing the updated cache files back to the repository.

---

## 4.7 Security & Vulnerability Auditing
To secure the serverless system, the following protocols are implemented. API credentials and private keys are completely isolated from version control by employing local `.env` files matching the `.gitignore` specification, while production credentials are provided dynamically through encrypted GitHub Action Secrets. A strict Content Security Policy (CSP) is configured via meta tags to restrict stylesheet and script sources to the local domain and verified content delivery networks (CDNs), preventing cross-site scripting (XSS) attacks. Additionally, security audits are automated in the CI/CD pipeline, invoking `pip-audit` to inspect Python packages and running CodeQL scans alongside secret scanners to prevent vulnerability leaks.

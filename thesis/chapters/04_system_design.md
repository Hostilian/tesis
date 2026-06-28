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
The ingestion layer implements programmatic connections with three cloud registries to harvest spatial and economic datasets, backed by a hardened transport layer to guarantee resilience.

### 4.2.1 Google Earth Engine REST API Contract & SDK Resilience
The pipeline initializes connection with Google Earth Engine using OAuth 2.0 credentials. To safeguard the pipeline against rate limits and transient connection drops (e.g., during intensive spatial operations), all Earth Engine calls (such as `.getInfo()` and `.reduceRegion()`) are wrapped in a resilient execution handler (`execute_resilient_call`) that enforces exponential backoff and jitter. The Python initialization and call wrapping are executed as follows:

```python
import ee
from pipeline.src.http_resilience import execute_resilient_call

# Resilient GEE initialization wrapper
def init_gee_resilient():
    try:
        ee.Initialize(project='tesis-500804')
        return True
    except Exception as e:
        return False

success = execute_resilient_call(init_gee_resilient, service_name="GEE Init")
```
When querying satellite image collections (e.g., Landsat-8/9 OLI), spatial queries are constrained using bounding boxes represented as `ee.Geometry.Polygon`. The temporal filter is applied using `ee.Filter.date(start_date, end_date)`. If GEE is unreachable, the client falls back to deterministic mock datasets.

### 4.2.2 Copernicus CDSE REST API Contract & Token-Bucket Throttling
To query high-resolution Sentinel-2 MSI data, the pipeline communicates with the CDSE OData endpoint. Authentication is established by dispatching a POST request with the client credentials payload to the Keycloak server at `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token`, which returns a short-lived bearer token. To prevent rate-limit failures, a Token-Bucket `RateLimiter` enforces a rate limits policy (burst capacity of 10 tokens refilling at 2 requests per second). Next, the pipeline executes an OData search query via a GET request containing spatial intersection and cloud cover filters at the catalogue endpoint. Finally, the target orthorectified surface reflectance bands are fetched as scaled NumPy arrays directly from the CDSE Process API, avoiding raw imagery download and limiting network overhead.

### 4.2.3 World Bank Data REST API Contract & Circuit Breaker
Economic indicator datasets are downloaded using direct HTTP requests:
*   **Target URL**: `http://api.worldbank.org/v2/country/CZE/indicator/NY.GDP.MKTP.KD.ZG?format=json`
*   **Response Processing**: The JSON payload is parsed using the Pandas library to isolate the target annual GDP growth figures, aligning the dataset with regional night-time lights anomalies.
*   **Resilience**: Request dispatching is guarded by a lightweight `CircuitBreaker`. If 3 consecutive failures occur, the circuit opens for a 30-second cooldown period, routing calls directly to locally cached World Bank values.

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

### 4.3.2 Decoupled Proprietary Engine & Spatial-Temporal Models
To support enterprise deployment, SBEI's mathematical models are isolated inside a proprietary module `SpatialTemporalEconomicEngine`. This decouples calculations from ingestion facades:

1. **Spatial Isolation Forest**: Sentinel-2 bands are mapped to spectral indices $\mathbf{x} = [\text{NDVI}, \text{NDWI}, \text{BSI}]$. An ensemble of 100 Isolation Trees (iTrees) is fitted on feature matrix $X \in \mathbb{R}^{N \times D}$ to isolate anomalies. The outlier score $s(x, n)$ is calculated as:
   $$s(x, n) = 2^{-\frac{\mathbb{E}(h(x))}{c(n)}}$$
   where $h(x)$ is the path length of sample $x$, $\mathbb{E}(h(x))$ is the average path length across all trees, and $c(n)$ is the average path length of unsuccessful search in a Binary Search Tree (BST) built with $n$ nodes:
   $$c(n) = 2 \ln(n - 1) + 0.5772156649 - \frac{2(n - 1)}{n}$$
2. **Empirical Variance via Bootstrap Resampling**: To quantify score reliability and filter out false positives caused by transient weather effects or sensor aberrations, the engine executes $B = 50$ bootstrap iterations. By drawing random samples with replacement from the pixel matrix, the engine computes $95\%$ confidence bounds around the mean anomaly score:
   $$\text{CI}_{95\%} = \left[ \bar{s} - 1.96 \cdot \frac{\sigma_s}{\sqrt{B}}, \, \bar{s} + 1.96 \cdot \frac{\sigma_s}{\sqrt{B}} \right]$$
3. **Temporal Night-Time Lights Deseasonalization**: For macroeconomic time-series (VIIRS DNB lights), deviations are computed via rolling Z-score:
   $$Z_t = \frac{Y_t - \mu_w}{\sigma_w}$$
   where $\mu_w$ and $\sigma_w$ represent the rolling mean and standard deviation over window $w=12$ months, and the denominator is bounded by a variance floor $\sigma_w = \max(\sigma_w, 10^{-5})$ to guarantee numeric stability.

```python
from pipeline.src.engine.spatial_temporal_engine import SpatialTemporalEconomicEngine

# Initialize the proprietary mathematical engine
engine = SpatialTemporalEconomicEngine(contamination=0.08, random_state=42)

# Fit spatial features and compute mean anomaly scores and confidence bounds
scores, ci_low, ci_high = engine.compute_spatial_anomalies_bootstrap(X, n_bootstrap=50)
```

---

## 4.4 Storage & Data Warehouse Serialization
To provide near-instantaneous page load speeds, the pipeline avoids dynamic database queries by caching processed anomalies into static files, while binding them to cryptographic proofs to assure data integrity:

### 4.4.1 anomalies.json Schema
The serialized output contains structured metadata for each flagged anomaly event, including the audit-ready provenance ledger hash:
```json
[
  {
    "id": "anomaly_madre_de_dios_01",
    "type": "Deforestation/Gold Mining",
    "region": "Madre de Dios, Peru",
    "coordinates": [-12.894, -69.912],
    "confidence": 0.91,
    "uncertainty": 0.007,
    "confidence_interval": [0.903, 0.917],
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
    "details": "Unsupervised Isolation Forest flagged a sharp drop in NDVI (-0.52) and a corresponding increase in BSI (+0.38). Spatial clusters align with illegal mining corridors near the Interoceanic Highway.",
    "provenance_hash": "c71fa7a88bcde119f0deae99b8219abf55b9e0f6c2419efde09c8d19bc2e1180"
  }
]
```

### 4.4.2 Cryptographic Provenance, Audit Ledger & PipelineRunRecord
To ensure that all economic insights are legally defensible and auditable by investment banks and audit entities, SBEI implements a provenance hashing mechanism and signed execution audit trails. 

For every anomaly, the pipeline computes:
1. **Raw Tile Hash**: A SHA-256 digest of the raw satellite image arrays, incorporating the data type, shape, and raw contiguous bytes:
   $$\text{Tile\_Hash} = \text{SHA256}(\text{dtype} \parallel \text{shape} \parallel \text{bytes})$$
2. **Parameters Hash**: A SHA-256 digest of model hyperparameters (contamination fraction, random seeds, number of trees).
3. **Combined Hash**: The final verification hash computed by concatenating and hashing the tile and parameters digests:
   $$\text{Provenance\_Hash} = \text{SHA256}(\text{Tile\_Hash} \parallel \text{Parameters\_Hash})$$

This combined fingerprint is saved as `provenance_hash` within each anomaly record, while a detailed record of the inputs is preserved in a sidecar file (`anomalies.provenance.json`) to allow downstream validation.

Additionally, the pipeline produces a signed execution log:
- **PipelineRunRecord**: Contains the run ID, timestamp, record count, execution status, and a SHA-256 signature calculated over these properties using a secure system-wide secret key. This record is appended to the system status registry at `/api/v1/status/index.json`, providing a tamper-evident audit history of all pipeline runs.
- **Data Lineage Tracking**: Every serialized anomaly record includes a `data_lineage` object detailing its data source provenance (e.g. `Sentinel-2 MSI`, `Landsat-8/9 OLI`, `Suomi-NPP VIIRS`), API endpoints queried, and the cryptographic hash of the execution run that generated it, enabling full reproducibility from the raw satellite sensors to the final dashboard.

### 4.4.3 regions.geojson Schema
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

### 4.5.5 REST Ingestion Webhooks & Distributed Task Queues
SBEI implements a real-time REST API web server using FastAPI to handle incoming financial feeds and satellite processing requests:
- **Webhook Ingestion**: Exposes `POST /api/v1/webhooks/financial` receiving commodity spot prices, returning a signed receipt transaction hash.
- **Distributed Queues**: Exposes `POST /api/v1/ingest/satellite` which delegates long-running remote sensing ingestion tasks to Celery asynchronous workers backed by a Redis message broker, enabling concurrent horizontal scaling.

---

## 4.6 Deployment Architecture & CI/CD
The project uses GitHub Actions for deployment, scheduling, and validation. The build pipeline (`test.yml`) installs Python packages, spins up a transient **Redis container service** for Celery backend tests, executes tests, and verifies that the code builds correctly on every pull request to `main`. The deployment pipeline (`deploy.yml`) deploys the static assets in the `/docs` directory to GitHub Pages upon merging changes. The scheduled pipeline (`data-refresh.yml`) runs weekly via a cron schedule, executing the Python data ingestion pipeline headlessly, querying Earth Engine for new data, updating `anomalies.json`, and committing the updated cache files back to the repository.

---

## 4.7 Security & Vulnerability Auditing
To secure the serverless system, the following protocols are implemented. API credentials and private keys are completely isolated from version control by employing local `.env` files matching the `.gitignore` specification, while production credentials are provided dynamically through encrypted GitHub Action Secrets. A strict Content Security Policy (CSP) is configured via meta tags to restrict stylesheet and script sources to the local domain and verified content delivery networks (CDNs), preventing cross-site scripting (XSS) attacks. 

Additionally, security audits are automated in the CI/CD pipeline. Static application security testing (SAST) is handled by CodeQL and `pip-audit` to inspect Python packages. Dynamic application security testing (DAST) is handled by a custom fuzzer (`fuzz_api.py`) executed in the `security.yml` workflow, sending SQL injection and cross-site scripting payloads to the API endpoints to verify resilience against crash vectors.

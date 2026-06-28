# Chapter 4: System Design & Implementation

## 4.1 Architecture Overview
The system is designed as a modular, decoupled data engineering pipeline that separates high-performance geospatial extraction from lightweight, interactive user rendering. This architecture is divided into three distinct layers:
1.  **Ingestion & Processing Layer (Python/GEE/CDSE)**: Fetches and clean-masks raw multi-spectral and radar rasters. Computes spectral indices and fits unsupervised machine learning anomaly models.
2.  **Storage & Serialization Layer (JSON/GeoJSON)**: Serializes processed anomaly data, spatial polygon boundaries, and temporal statistics into standard flat file formats.
3.  **Visualization Dashboard Layer (HTML5/CSS3/Vanilla JS)**: A futuristic single-page application (SPA) that acts as the user interface (UI) and Decision Support System (DSS), loading static serialized feeds from GitHub Pages.

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

By decoupling the high-performance back-end from the front-end visualization, the system bypasses the need to run resource-heavy geospatial libraries (such as GDAL, Rasterio, or Fiona) within the user's browser. Instead, the heavy computations are performed asynchronously, and the client browser only loads lightweight, pre-processed vector datasets.

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
To query high-resolution Sentinel-2 MSI data, the pipeline communicates with the CDSE OData endpoint.
1.  **Authentication**: The pipeline sends a POST request with the client credentials payload to:
    `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token`
2.  **OData Search Request**: A GET request queries available granules using filter strings:
    `https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/Value lt 20.0) and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON((...))')`
3.  **Process API**: Fetches orthorectified surface reflectance bands directly as NumPy arrays, limiting network overhead.

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
For multi-spectral anomaly detection (e.g., Peru gold mining excavations and Chile lithium evaporation pond expansions), the processed spectral feature bands are flattened into a 2D matrix:
1.  **Feature Assembly**: A matrix $X \in \mathbb{R}^{N \times D}$ is constructed, where each row represents a pixel, and the columns contain computed index values ($\text{NDVI}, \text{NDWI}, \text{BSI}$).
2.  **Model Training**: An `IsolationForest` model (from `scikit-learn`) is trained with a locked random seed and configured contamination threshold:
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
3.  **Spatial Projection**: Outliers are reshaped back to the original raster grid. Spatial clusters (groups of contiguous outlier pixels) are vectorized into centroid coordinates and assigned a confidence score based on their isolation path lengths.

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
To allow users to visually inspect spatial changes without downloading large GIS files, the dashboard uses a dual-canvas layout:
1.  **Structure**: Two HTML5 `<canvas>` elements are layered on top of each other inside a relative-positioned container. The baseline image is drawn on the bottom canvas, and the anomaly image is drawn on the top canvas.
2.  **Clipping Event Loop**: A vertical separator bar tracks dragging inputs (`mousedown` / `touchstart`). The horizontal split percentage is calculated, and the top canvas is cropped using the CSS `clip-path` property:
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
3.  **Performance Optimization**: By using hardware-accelerated CSS clipping instead of redrawing pixel blocks on every frame, the interface achieves a smooth rendering rate of 60 frames per second (FPS), even on mobile web browsers.

### 4.5.3 Chart.js Spectral Radar Chart
A radar chart displays the multi-spectral signature of the selected anomaly:
*   **Axes**: NDVI, NDWI, BSI, and SWIR reflectance.
*   **Visual Styling**: The selected anomaly's signature is drawn in fluorescent cyan, and the baseline normal profile is rendered in deep blue, allowing users to quickly assess land cover anomalies.

---

## 4.6 Deployment Architecture & CI/CD
The project uses GitHub Actions for deployment and scheduling:
*   **Build Pipeline (`test.yml`)**: Installs Python dependencies, executes tests, and verifies that the code builds correctly on every pull request to `main`.
*   **Deployment Pipeline (`deploy.yml`)**: Deploys the static assets in the `/docs` directory to GitHub Pages upon merging changes.
*   **Scheduled Pipeline (`data-refresh.yml`)**: Runs weekly via a cron schedule. It executes the Python data ingestion pipeline headlessly, queries Earth Engine for new data, updates `anomalies.json`, and commits the updated cache files back to the repository.

---

## 4.7 Security & Vulnerability Auditing
To secure the serverless system, the following protocols are implemented:
*   **API Credential Isolation**: No credentials or private keys are stored in the repository. Local testing relies on `.env` files (excluded from version control via `.gitignore`), while automated scripts access secrets configured in the GitHub Actions environment.
*   **Content Security Policy (CSP)**: To protect against cross-site scripting (XSS) and code injection, a meta tag restricts scripts and stylesheet sources to the local domain and verified CDN hosts.
*   **Dependency Auditing**: The CI/CD pipeline runs `pip-audit` to scan Python packages for vulnerabilities and executes `npm audit` to check frontend dependencies, ensuring the code remains secure and up to date.

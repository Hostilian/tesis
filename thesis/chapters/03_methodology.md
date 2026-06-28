# Chapter 3: Methodology

## 3.1 Research Design & Paradigm
This study is structured under a **positivist, quantitative-dominant research design**, employing empirical geospatial observations, multi-spectral band math, and unsupervised machine learning algorithms to evaluate orbital data as a proxy for real-world economic activity. The research paradigm is grounded in the physical sciences: satellite sensors measure raw solar reflectance and microwave backscatter, which are objective physical properties of the Earth's surface. 

These physical observations are processed through a structured Information Engineering pipeline, transforming unstructured raster bands into structured anomaly events. While the core processing and modeling are quantitative, a qualitative ground-truthing layer is integrated to cross-reference detected anomalies with news reports, corporate press releases, and official mining registries, establishing a robust mixed-method validation framework.

---

## 3.2 Data Ingestion & API Architectures
The automated ingestion pipeline queries three primary geospatial data portals and one socioeconomic database, operating under rate-limited, decoupled connection parameters:

### 3.2.1 Google Earth Engine (GEE) Ingestion
The pipeline interfaces with GEE utilizing the Python `earthengine-api` library. GEE serves as the primary engine for processing large-scale spatial collections. Ingestion parameters are configured dynamically:
*   **Coordinate Bounds**: Bounding boxes are defined in WGS 84 (EPSG:4326) coordinates.
*   **Cloud Filtering**: Collections are filtered to keep only scenes with cloud cover below 20% using the `CLOUDY_PIXEL_PERCENTAGE` attribute for Sentinel-2, or `CLOUD_COVER` for Landsat-8/9.
*   **Temporal Filtering**: Image collections are filtered using start and end date boundaries to establish distinct baseline and anomaly comparison epochs.

### 3.2.2 Copernicus Data Space Ecosystem (CDSE) Ingestion
CDSE OData and Sentinel Hub APIs are queried programmatically to ingest high-resolution Sentinel-1 SAR and Sentinel-2 optical bands.
1.  **OAuth Authentication**: The system requests a short-lived bearer token using client credentials.
2.  **Process API Payload**: A POST request containing the bounding box, output resolution (10m), target bands, and custom Evalscript (which computes indices and cloud masks on the server side) is transmitted.
3.  **Raster Acquisition**: The CDSE backend returns a single multi-band GeoTIFF or scaled NumPy array, minimizing local bandwidth.

### 3.2.3 Socioeconomic API Integration
The World Bank API is queried to fetch regional annual GDP metrics. The REST query is structured as:
`http://api.worldbank.org/v2/country/{country}/indicator/NY.GDP.MKTP.KD.ZG?format=json`
The system extracts the tabular data and matches the temporal records with satellite night-time lights anomalies.

---

## 3.3 Spectral Index Formulations
To convert raw digital numbers (DN) or top-of-atmosphere (TOA) reflectance values into indicators of land-use change, the pipeline implements four mathematical index formulations:

### 3.3.1 Normalized Difference Vegetation Index (NDVI)
NDVI quantifies vegetation density and health by contrasting the high absorption of chlorophyll in the red visible band with the high reflectance of leaf mesophyll in the near-infrared (NIR) band:
$$\text{NDVI} = \frac{\rho_{\text{NIR}} - \rho_{\text{Red}}}{\rho_{\text{NIR}} + \rho_{\text{Red}}}$$
*   **Sentinel-2 Band Map**: $\frac{B8 - B4}{B8 + B4}$
*   **Landsat-8/9 Band Map**: $\frac{B5 - B4}{B5 + B4}$
*   **Reflectance Range**: $[-1.0, 1.0]$. Dense forest canopies exhibit values between $0.6$ and $0.9$. Land clearing, open-pit mining, or infrastructure construction drops NDVI values close to $0.0$ or into negative ranges.

### 3.3.2 Normalized Difference Water Index (NDWI)
NDWI, originally formulated by McFeeters (1996), maps open water surfaces and monitors changes in moisture levels by utilizing the green band and the NIR band:
$$\text{NDWI} = \frac{\rho_{\text{Green}} - \rho_{\text{NIR}}}{\rho_{\text{Green}} + \rho_{\text{NIR}}}$$
*   **Sentinel-2 Band Map**: $\frac{B3 - B8}{B3 + B8}$
*   **Landsat-8/9 Band Map**: $\frac{B3 - B5}{B3 + B5}$
*   **Reflectance Range**: $[-1.0, 1.0]$. Open water features (such as tailing dams and lithium brine evaporation ponds) display positive NDWI values ($>0.1$), whereas soil and vegetation show negative values.

### 3.3.3 Bare Soil Index (BSI)
BSI integrates SWIR, red, NIR, and blue bands to isolate exposed soil and rock surfaces, providing an indicator for deforestation, mining activity, and soil disturbance:
$$\text{BSI} = \frac{(\rho_{\text{SWIR1}} + \rho_{\text{Red}}) - (\rho_{\text{NIR}} + \rho_{\text{Blue}})}{(\rho_{\text{SWIR1}} + \rho_{\text{Red}}) + (\rho_{\text{NIR}} + \rho_{\text{Blue}})}$$
*   **Sentinel-2 Band Map**: $\frac{(B11 + B4) - (B8 + B2)}{(B11 + B4) + (B8 + B2)}$
*   **Landsat-8/9 Band Map**: $\frac{(B6 + B4) - (B5 + B2)}{(B6 + B4) + (B5 + B2)}$
*   **Reflectance Range**: $[-1.0, 1.0]$. Exposed mining soils, quarries, and agricultural fields show high positive BSI values ($>0.15$), contrasting with healthy vegetation ($<0.0$).

### 3.3.4 VIIRS Night-time Lights (NTL) Radiance Calibration
The Suomi-NPP VIIRS Day/Night Band (DNB) captures nocturnal light emissions. Unlike legacy sensors, the VIIRS DNB undergoes absolute radiometric calibration, reporting radiance in units of nanowatts per square centimeter per steradian:
$$\text{Radiance} = \text{Pixel Value} \times 10^{-9} \text{ W}\cdot\text{cm}^{-2}\cdot\text{sr}^{-1}$$
Nocturnal radiance values correlate directly with economic factors such as electricity consumption, traffic volume, and industrial output.

---

## 3.4 Unsupervised Anomaly Detection Mathematics

### 3.4.1 Spatial Anomaly Detection (Isolation Forest)
For multi-spectral pixels in mining and industrial Regions of Interest (ROIs), an unsupervised **Isolation Forest** is trained. The core premise is that anomalies are few and spectrally distinct, making them easier to isolate than normal pixels.

Let $X = \{x_1, x_2, \dots, x_N\}$ be a dataset of $N$ spatial observations in a $D$-dimensional space, where $D = [\text{NDVI}, \text{NDWI}, \text{BSI}, \rho_{\text{SWIR1}}]$. The algorithm recursively splits the dataset by randomly selecting a feature and a random split value between the minimum and maximum values of that feature, constructing an ensemble of Isolation Trees ($iTrees$).

The anomaly score $s(x, n)$ for an observation $x$ is defined as:
$$s(x, n) = 2^{-\frac{\mathbb{E}(h(x))}{c(n)}}$$
Where:
*   $h(x)$ is the path length (number of edges traversed from the root node to a terminating leaf node) of sample $x$ in an individual tree.
*   $\mathbb{E}(h(x))$ is the expected (average) path length of $x$ across the forest of $T$ trees.
*   $c(n)$ is the average path length of an unsuccessful search in a Binary Search Tree (BST) built from $n$ nodes, serving as a normalization factor:
$$c(n) = 2\ln(n - 1) + 2\gamma - \frac{2(n - 1)}{n}$$
Here, $\gamma \approx 0.5772156649$ is the **Euler-Mascheroni constant**.

**Anomaly Thresholding**:
*   If $s(x, n) \approx 1.0$: The sample exhibits short path lengths across the forest, indicating that it is easily isolated and flagged as an anomaly.
*   If $s(x, n) < 0.5$: The sample has long path lengths, indicating it falls within the normal land cover profile.
*   The contamination parameter is set to $\alpha = 0.08$, defining the proportion of expected outliers.

### 3.4.2 Temporal Anomaly Detection (Z-Score)
To detect economic and industrial shocks in night-time light radiance time series, a rolling statistical Z-score is calculated:
$$Z_t = \frac{Y_t - \mu_{(t-W, t-1)}}{\sigma_{(t-W, t-1)}}$$
Where:
*   $Y_t$ is the night-time lights radiance at month $t$.
*   $\mu_{(t-W, t-1)}$ is the historical mean calculated over a rolling window $W$ (configured as $W = 12$ months to account for annual cycles).
*   $\sigma_{(t-W, t-1)}$ is the standard deviation over the same rolling window $W$.

**Threshold Rules**:
*   $Z_t > 2.5$: Represents a significant positive anomaly, suggesting rapid industrial expansion or infrastructure development.
*   $Z_t < -2.5$: Indicates a significant negative anomaly, suggesting factory closures, power outages, or economic contractions.

---

## 3.5 Statistical Rigor & Validation Matrix
To validate the reliability of detected satellite anomalies, three statistical metrics are calculated:

### 3.5.1 Spatial Classification Performance
Using verified ground-truth shapes (e.g., official mining registry maps), the spatial anomalies are evaluated using a confusion matrix:
$$\text{Precision} = \frac{\text{True Positives (TP)}}{\text{True Positives (TP)} + \text{False Positives (FP)}}$$
$$\text{Recall} = \frac{\text{True Positives (TP)}}{\text{True Positives (TP)} + \text{False Negatives (FN)}}$$
$$\text{F1-Score} = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

### 3.5.2 Temporal Economic Correlation
To evaluate the correlation between night-time lights radiance anomalies ($Z_t$) and official quarterly GDP growth, the pipeline computes Pearson's product-moment correlation coefficient ($r$):
$$r = \frac{\sum_{i=1}^n (X_i - \bar{X})(Y_i - \bar{Y})}{\sqrt{\sum_{i=1}^n (X_i - \bar{X})^2 \sum_{i=1}^n (Y_i - \bar{Y})^2}}$$
Where $X_i$ is the satellite radiance anomaly score, $Y_i$ is the GDP growth rate, and $n$ is the number of observation quarters. 

A two-tailed Student's t-test is used to calculate the $p$-value, ensuring the correlation is statistically significant ($p < 0.05$).

### 3.5.3 Spatial Autocorrelation (Moran's I)
To account for spatial dependency—the principle that neighboring pixels are more likely to exhibit similar anomaly scores—we compute Moran's $I$ coefficient to verify spatial clustering:
$$I = \frac{N}{S_0} \frac{\sum_{i=1}^N \sum_{j=1}^N w_{ij}(x_i - \bar{x})(x_j - \bar{x})}{\sum_{i=1}^N (x_i - \bar{x})^2}$$
Where $N$ is the number of spatial units indexed by $i$ and $j$, $x$ is the anomaly score, $\bar{x}$ is the mean, $w_{ij}$ is the spatial weight matrix, and $S_0$ is the sum of all weights:
$$S_0 = \sum_{i=1}^N \sum_{j=1}^N w_{ij}$$
Moran's $I > 0$ indicates spatial clustering, while $I < 0$ indicates spatial dispersion, helping validate the structural consistency of detected mining footprints.

---

## 3.6 Reproducibility Protocol
To guarantee that third-party researchers can replicate all findings, the methodology implements:
1.  **Software Environment Locks**: All Python packages and system libraries are locked in a Docker configuration file ([Dockerfile](file:///d:/CODING/tesis/pipeline/Dockerfile)) and [requirements.txt](file:///d:/CODING/tesis/pipeline/requirements.txt).
2.  **Algorithmic Seeds**: Random number generation seeds in scikit-learn's Isolation Forest are locked (`random_state=42`), ensuring deterministic decision-tree splits.
3.  **Data Archives**: Raw coordinates, sensor metadata, and processing parameters are saved in a static [regions.geojson](file:///d:/CODING/tesis/docs/data/regions.geojson) file, allowing identical geographic bounding boxes to be queried in future runs.

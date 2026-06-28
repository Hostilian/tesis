# PATENT DISCLOSURE: SPATIAL-TEMPORAL OVERLAY FOR SATELLITE-BASED ECONOMIC ANOMALY DETECTION

**Inventors:** Eren Ozturk et al.  
**Assignee:** Space-Based Economic Intelligence Inc. (YC SaaS platform)  
**Status:** Confidential Draft for Patent Attorney Review  

---

## 1. Field of the Invention
This invention relates to remote sensing, satellite image processing, and machine learning applied to automated econometric forecasting. Specifically, it relates to a computer-implemented system that fuses multi-spectral spatial anomalies and temporal nocturnal illumination time series to detect and verify localized economic shocks (e.g., lithium extraction footprint, gold mining expansion, factory shutdowns).

---

## 2. Mathematical Novelty & System Architecture

The core of the proprietary system lies in a dual-phase, decoupled spatial-temporal overlay engine.

```
       +---------------------------------------------+
       |             Raw Satellite Data              |
       |  (Sentinel-2, Sentinel-1, NOAA/VIIRS DNB)   |
       +----------------------+----------------------+
                              |
              +---------------+---------------+
              |                               |
              v                               v
    [Spatial Processing]            [Temporal Processing]
    - QA60 Cloud Masking            - Monthly NTL Averaging
    - Spectral Indices (NDVI,       - Rolling Window Baseline
      NDWI, BSI)                    - Rolling Z-Score
    - Isolation Forest Outliers
              |                               |
              +---------------+---------------+
                              |
                              v
                +---------------------------+
                |  Spatial-Temporal Fusion  |
                |     & H2 Correlation      |
                +-------------+-------------+
                              |
                              v
                +---------------------------+
                |  Cryptographic Provenance |
                |      Hashing Ledger       |
                +---------------------------+
```

### Phase A: Spatial Feature Extraction and Isolation Forest
We map high-dimensional surface reflectance values into standardized indices designed to extract specific economic indicator proxies.

1. **Normalized Difference Vegetation Index (NDVI)**:
   $$\text{NDVI} = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}} = \frac{B_8 - B_4}{B_8 + B_4}$$
   Indicates biomass presence. Severe deforestation or land-clearing for open-pit mining causes $\text{NDVI}$ to plunge.

2. **Normalized Difference Water Index (NDWI)**:
   $$\text{NDWI} = \frac{\text{Green} - \text{NIR}}{\text{Green} + \text{NIR}} = \frac{B_3 - B_8}{B_3 + B_8}$$
   Identifies surface water. Brine evaporation pools (critical for Lithium extraction) exhibit highly elevated $\text{NDWI}$.

3. **Bare Soil Index (BSI)**:
   $$\text{BSI} = \frac{(B_{11} + B_4) - (B_8 + B_2)}{(B_{11} + B_4) + (B_8 + B_2)}$$
   Detects bare earth exposure (open pits, quarries, tailing pond margins).

The feature vector $\mathbf{x} = [\text{NDVI}, \text{NDWI}, \text{BSI}]$ is passed to an ensemble of Isolation Trees (iTrees). The anomaly score $s(x, n)$ is defined as:
$$s(x, n) = 2^{-\frac{\mathbb{E}(h(x))}{c(n)}}$$
where $h(x)$ is the path length of observation $x$ in an iTree, $\mathbb{E}(h(x))$ is the average path length across all trees, and $c(n)$ is the average path length of unsuccessful searches in a Binary Search Tree (BST) with $n$ nodes:
$$c(n) = 2 \ln(n - 1) + 0.5772156649 - \frac{2(n - 1)}{n}$$

Outlier predictions are filtered where $s(x, n) \ge \tau$ (where $\tau$ is set by the contamination rate, e.g., $\tau \ge 0.65$ representing high anomaly certainty).

### Phase B: Temporal Night-Time Lights Deseasonalization
For monthly radiance $Y_t$ from VIIRS DNB, we compute a rolling Z-score:
$$Z_t = \frac{Y_t - \mu_w}{\sigma_w}$$
where $\mu_w$ and $\sigma_w$ are the mean and standard deviation over a rolling historical baseline of $w$ months (default $w=12$ to capture seasonal cycles):
$$\mu_w = \frac{1}{w} \sum_{i=1}^{w} Y_{t-i}$$
$$\sigma_w = \sqrt{\frac{1}{w} \sum_{i=1}^{w} (Y_{t-i} - \mu_w)^2 + \epsilon}$$
where $\epsilon = 10^{-5}$ is the standard deviation floor to prevent division-by-zero on completely unlit regions.

Anomalies are flagged when $|Z_t| > 2.5$, mapping to positive economic surges or negative contractions/shutdowns.

### Phase C: Joint Spatial-Temporal Pearson Correlation
To validate the hypothesis that these satellite anomalies correlate with macroeconomic activity, we run a Pearson correlation check:
$$r = \frac{\sum (Z_t - \bar{Z})(G_t - \bar{G})}{\sqrt{\sum (Z_t - \bar{Z})^2 \sum (G_t - \bar{G})^2}}$$
where $G_t$ is the GDP growth rate (from World Bank / IMF data). Hypothesis $H_2$ is supported when:
$$r \ge 0.65 \quad \text{and} \quad p < 0.05$$

---

## 3. Cryptographic Provenance Ledger
To ensure legally defensible evidence for institutional banking compliance, each anomaly is associated with a SHA-256 combined hash:
$$\text{combined\_hash} = \text{SHA256}(\text{raw\_tile\_hash} \parallel \text{processing\_parameters\_hash})$$
This guarantees the data flow's integrity and reproducibility.

# Thesis direction 2027 — proposed only

**Official topic remains Space-Based Intelligence & APIs until supervisor confirmation.** The existing economic/resource-anomaly prototype should not be erased. Proposed supplementary research question: *Can multi-source Earth-observation and permitted agricultural observations identify or explain orchard vegetation changes more reliably or interpretably than a satellite-only baseline?*

## Defensible minimum research contribution
One or two approved study polygons, authentic Sentinel-2 Level-2A observations with acquisition IDs and cloud masks, seasonal NDVI/NDMI time series, robust median/MAD anomaly baseline, independently reviewed changes and an auditable dashboard. The prototype should preserve geographic, temporal and processing provenance. Explicitly distinguish observations, model flags, human interpretations and confirmed field events.

**H0:** Added context does not improve pre-registered evaluation performance/interpretability relative to the satellite-only baseline. **H1 (optional):** Approved aerial evidence improves spatial interpretation for independently reviewed event windows. Without enough ground truth, report **coverage, consistency and reproducibility**, not predictive F1.

## Research boundaries
NDVI = (NIR - red)/(NIR + red); NDMI = (NIR - SWIR1)/(NIR + SWIR1). McFeeters NDWI = (green - NIR)/(green + NIR) approximates open-water signal and is **not** interchangeable with NDMI. EVI and BSI require band-specific scaling. Sentinel-2 L2A uses scene classification (SCL); exclude clouds, cirrus, cloud shadow, snow and no-data, and document pixel coverage. Simple RGB orthophotos do not provide NIR, thermal, or NDVI. Almond phenology, bare-soil fractions, pruning, seasonal irrigation and shadows confound canopy interpretation. No water-stress diagnosis or yield prediction without adequate labels.

## Observation and review unit
Use orchard block × acquisition date, not randomly shuffled pixels. Preserve original sensor imagery, product ID, spatial resolution, georeferencing, quality mask, licence, processing version, aggregation method, field/block ID and reviewer adjudication. Hold out blocks or dates to prevent spatial/temporal leakage.

## Conditional data architecture
Public catalogue (STAC) -> authenticated raster acquisition -> validated WGS84 study area -> quality/cloud masking -> block-level features -> seasonal baseline -> anomaly candidates -> independent verification -> non-confidential visual/export. Private imagery/sensor/operations records can be joined only in an authorized, controlled workspace; publish public or synthetic artefacts separately.

## Current code
`python -m pipeline.run_agriculture_pilot` produces clearly marked synthetic reflectances and an **offline request template only**. It does not download imagery or classify crops. `pipeline/src/agriculture_pilot.py` validates Polygon geometry, creates the latest CDSE STAC query payload and computes transparent NDVI/robust MAD deviation.

## Official source
Copernicus announced its new STAC API on 16 Oct 2026: https://dataspace.copernicus.eu/news/2026-10-16-new-sfeos-stac-catalogue-endpoint . Current search: https://stac.opensearch.dataspace.copernicus.eu/v1/search ; endpoint migration deadline **12 January 2027**. Scene classification: https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html . STAC standard: https://stacspec.org/ . Live asset download and provider authentication remain **untested** in this pilot.

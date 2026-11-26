# Credential-free observed Sentinel-2 pixel preview (Planetary Computer)

This is an **experimental open-data research path**. It is isolated from the synthetic public anomaly feed and does not publish results or claim that a scene proves a mining, environmental or economic event.

## Why this path?

Microsoft Planetary Computer provides a STAC catalogue, raster asset keys and temporary signed links for public Sentinel-2 L2A Cloud-Optimized GeoTIFFs. The existing project dependencies already include `planetary-computer`, `pystac-client` and `rasterio`. This supports a bounded observed-pixel preview without requiring Google Earth Engine credentials.

## One small public research area

```bash
pip install -r pipeline/requirements.txt
python -m pipeline.planetary_observation \
  --bbox -68.250 -23.480 -68.238 -23.468 \
  --start 2024-10-01 --end 2024-10-15 \
  --output-dir research_private/observations
```

The program uses the actual STAC product identifier, filters a bounded collection by date and reported cloud cover, signs **asset URLs only in memory**, and reads B02/B03/B04/B08/B11 and SCL raster assets on a shared geodetic 96×96 preview grid. It excludes cloudy/shadow/saturated pixels from the scene classification band before calculating NDVI, NDWI and BSI.

The output is a compressed pixel dataset (`*.npz`) and a private JSON manifest containing the source scene ID, acquisition time, cloud metadata, band names, grid CRS, checksum and unverified status. It never writes into `docs/`, sends messages, or reads private farms. In-repository output is restricted to git-ignored `research_private/`.

**Limits:** This is a controlled public-data preview, not multi-scene operational mosaicking. Signed URLs can expire; availability and licensing may change. The preview is not yet an audited atmospheric correction, a full multi-resolution geospatial validation, or a measured ecological/economic change.

## Evidence status

Use a successful source-pixel preview to document:
1. Which STAC item and asset keys were read
2. Whether all spectral bands and scene-classification quality masks align
3. How many pixels remain after masking
4. The saved raster-array checksum

That evidence supports the narrow claim **“observed satellite pixels were retrieved from the identified STAC item.”** It does not support **“we discovered verified extraction anomalies”** until independent labels and held-out evaluation are completed.

Run offline unit tests with:

```bash
pytest pipeline/tests/test_planetary_observation.py -q
```

Reference: [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/) and [PySTAC Client](https://pystac-client.readthedocs.io/).

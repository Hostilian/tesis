# Real Sentinel-2 Pixel Preview — Controlled Acquisition

**Status:** Experimental acquisition path, **NOT an independently validated anomaly-detection result**.  
**Default behavior:** Fail closed. Requires GEE account access, an authenticated session, and `GCP_PROJECT`. No synthetic fallback, publication or farm-data upload.

## Why a separate workflow?

The existing publicly deployed study map uses deterministic synthetic Sentinel-2 and VIIRS inputs. The real-imagery preview is intentionally isolated until a validated raster-to-detection pipeline exists. A successful observed pixel download is **only the first evidence gate**, not verification of an anomaly or a claim of model accuracy.

## Run a small real-pixel preview

```bash
pip install -r pipeline/requirements.txt
earthengine authenticate
export GCP_PROJECT="your-authorized-cloud-project"

python -m pipeline.real_observation \
  --bbox -68.250 -23.480 -68.238 -23.468 \
  --start 2024-10-01 --end 2024-10-15 \
  --output-dir research_private/observations
```

The coordinates here are **public demonstration geography in Chile**, not any private farm. Avoid entering Rota Única boundaries or operational sensor positions into public code, issues, logs or screenshots.

The tool limits the preview to at most 2 km along either side, a 45-day acquisition interval, 60 input scenes and 25,000 sampled pixels. It checks the source collection is non-empty and that scene identifiers, array shapes and usable pixels exist. The code masks Sentinel-2 scene-classification cloud/cloud-shadow categories, aligns the preview on an EPSG:4326/30-m grid and computes NDVI, NDWI and BSI. The outputs are:

- Local compressed `*.npz` band/index arrays, excluded by `.gitignore`.
- Local `*.json` manifest with scene IDs, dates, bounds, checksum, sampling grid, and explicit `real_pixel_inputs_unvalidated` status.

**Credentials are never stored in outputs.** Output remains private; the tool does not modify `docs/` and does not publish to GitHub Pages.

## Evidence gates still missing

1. Inspect actual pixel values, cloud/shadow validity and the acquisition scene footprints at finer resolution; verify SCL QA, CRS, reprojected pixel sizes, temporal compositing and calibration.
2. Maintain an immutable asset inventory including provider version, signed URL expiry handling, original scene footprints and scene-level checksums.
3. Join independently labeled change events with consistent time/space alignment.
4. Evaluate Isolation Forest on held-out labeled regions and dates, report confusion matrix, precision/recall/F1 with uncertainty.
5. Obtain full reproducibility with published scripts and non-sensitive test inputs; log validation reviewer and limitations.
6. Only after all gates pass, consider publishing a separate real-observation dataset with clear licensing and authorization, preserving the demo as a distinct dataset.

The official Google Earth Engine [`ee.Image.sampleRectangle` documentation](https://developers.google.com/earth-engine/apidocs/ee-image-samplerectangle) describes the pixel-array sampling method. The [CDSE STAC catalogue](https://documentation.dataspace.copernicus.eu/APIs/STAC.html) helps discover scene metadata, but catalogue matches are **not** raster pixels.

## Testing

```bash
pytest pipeline/tests/test_real_observation.py -q
```

These tests use controlled **fabricated test arrays**. Passing them does not certify successful authentication, real imagery acquisition, geographic alignment or scientific model performance.

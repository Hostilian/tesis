# Reproducing the Portugal case study

This page covers the two Sentinel-2 change case studies served at `case-study/`:

- `alqueva_olive`: the Alqueva irrigation area, Beja – Ferreira do Alentejo.
- `neves_corvo_mine`: the Neves-Corvo mine area, Castro Verde / Almodôvar.

Every number on the page comes from `data/<case_id>/results.json` and `reference_cos.json`. The run that produced them is described in `data/<case_id>/manifest.json`: input scene IDs, retrieval time, code commit, package versions, command and SHA-256 of each output.

## 1. Setup

You need Python 3.12 and internet access. No account, API key or token is used.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # macOS / Linux
pip install numpy==2.2.2 scipy==1.15.3 rasterio==1.5.0 pystac-client==0.8.6 pyproj shapely matplotlib pillow requests
```

These packages are a subset of `pipeline/requirements.txt`. Installing that whole file also works but pulls in Earth Engine, torch and other packages this case study does not use.

## 2. Commands

Run these from the repository root:

```bash
# optional: re-create the study-area screening (coarse, whole tile 29SNC)
python pipeline/run_case_study.py screen --item S2A_29SNC_20180818_1_L2A --item S2B_29SNC_20240821_0_L2A

# list candidate scenes (documents the date-selection rule)
python pipeline/run_case_study.py discover --bbox -8.042 37.907 -7.928 37.997 --start 2025-07-15 --end 2025-09-10 --max-cloud 1

# run each case (about 2 minutes each on a home connection)
python pipeline/run_case_study.py run pipeline/case_studies/alqueva_olive.json
python pipeline/run_case_study.py run pipeline/case_studies/neves_corvo_mine.json

# compare with the independent land-use map (DGT COS 2018v4 -> 2025v1)
python pipeline/run_case_study.py evaluate-cos pipeline/case_studies/alqueva_olive.json
python pipeline/run_case_study.py evaluate-cos pipeline/case_studies/neves_corvo_mine.json

# offline tests (method arithmetic + public artifacts match their manifests)
python -m pytest pipeline/tests/test_case_study.py -q
```

## 3. Inputs

| Input | Source | Access | Licence |
|---|---|---|---|
| Sentinel-2 L2A scenes, pinned by STAC item ID in `pipeline/case_studies/*.json` | Earth Search v1 (Element 84), collection `sentinel-2-l2a`, public COGs on AWS | Live HTTPS range reads of the study-area window only | Copernicus Sentinel data legal notice (free, full and open; attribution required) |
| Land-use reference COS2018v4-S2 and COS2025v1-S2 | Direção-Geral do Território OGC API – Features, `ogcapi.dgterritorio.gov.pt` | Live, bounding-box query | CC-BY (dados.gov.pt) |

Date rule, applied the same way to both cases:
- peak-summer window, the same relative orbit (R037), scene cloud under 1 %;
- processing baseline 05.xx on both dates, so the reflectance offset is handled identically;
- the scene closest to mid-August.

The control pair is two scenes from the same sensor (S2C), 20 days apart in August 2025.

## 4. Outputs

| Path | In Git | Content |
|---|---|---|
| `docs/case-study/data/<case>/manifest.json` | yes | Run record: inputs, environment, command, hashes |
| `docs/case-study/data/<case>/results.json` | yes | Coverage, index statistics, threshold, sensitivity, change areas, patch statistics, resolution table |
| `docs/case-study/data/<case>/reference_cos.json` | yes | Agreement with the COS reference |
| `docs/case-study/data/<case>/*.png, *.jpg, *.geojson, *.csv` | yes | Figures, web-map overlays (EPSG:4326), change patches, sensitivity table, clipped COS polygons |
| `pipeline/data/case_studies/<case>/<run_id>/*.tif` | no (git-ignored) | Full-resolution 10 m GeoTIFFs: index difference, change classes, stability split |

## 5. Method in one paragraph

1. Read the red, NIR and SCL bands for NDVI (blue, red, NIR, SWIR-1 and SCL for BSI) on the 10 m grid of one MGRS tile.
2. Convert to reflectance with the scale and offset from the STAC metadata. When `earthsearch:boa_offset_applied` is true, the pixels are already harmonised, so no second offset is applied (see `effective_offset()` in `pipeline/src/case_study.py`).
3. Mask everything except SCL classes 4 (vegetation), 5 (not vegetated) and 6 (water), and compute the index difference on pixels valid on both dates.
4. Set the threshold before looking at the change map: the smallest value in the grid that is at least the 99th percentile of |difference| in the 20-day control pair.
5. Keep connected patches of at least 1 ha (8-connectivity).

Case-specific steps:
- **Alqueva:** water pixels are excluded from the change classes, and increase pixels are split by within-year stability (May versus August 2025).
- **Neves-Corvo:** the difference is centred on the study-area median, because the whole scene showed a BSI shift between years that a 20-day control cannot capture.

## 6. Known constraints

- **Earth Search metadata.** `raster:bands.offset = -0.1` is published even where the offset is already applied to the pixels. Applying it twice saturated NDVI at 1 in a first run that was discarded. The check is documented in the code.
- **DGT OGC API availability.** The service returned HTTP 503 at about 11:20 UTC on 2026-11-26 and worked shortly after. `evaluate-cos` fails loudly instead of silently skipping.
- **Stale artifacts.** `evaluate-cos` reads the local GeoTIFFs of the run named in the public manifest. If they are missing, re-run the case first.
- **What it is and isn't.** A screening method. It shows where the surface signal changed, not why. COS agreement is agreement with another map, not field truth.

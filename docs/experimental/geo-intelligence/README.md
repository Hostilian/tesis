# Experimental observed satellite-change viewer

**Branch-only prototype; NOT the production thesis landing page.** Existing satellite dashboard, `index3.html`, `index4.html`, shelf branches and historic demo API remain intact. **Do not automatically promote this experimental route to GitHub Pages.**

This folder uses the **existing Leaflet** library and normal GeoJSON. It intentionally does **not** install Cesium, God’s Eye View, MapLibre, deck.gl, Grafana, OpenRouter, a new app framework or backend. The simple map shows actual **two-scene Sentinel-2 NDVI differences**, not classified economic/environmental events.

## Reproduce current observed input (only public geography)

From repository root, install in a fresh virtual environment (Python 3.12); existing dependencies are pinned in `pipeline/requirements.txt`. If resource-constrained, only `numpy`, `planetary-computer`, `pystac-client`, `rasterio` and the existing preprocessor's dependencies are used for this new path.

```powershell
python -m pipeline.observed_change --bbox -68.250 -23.480 -68.238 -23.468 --before-start 2024-10-01 --before-end 2024-10-15 --after-start 2025-10-01 --after-end 2025-10-15 --output-dir research_private/observations
```

The command queries a documented public STAC catalog and reads actual signed COG pixels in memory. The source product IDs are recorded in the output. Both scenes are Sentinel-2 L2A **processing baseline 05.11**, requiring `(raw DN - 1000)/10000` BOA reflectance; this is checked from actual STAC properties rather than guessed from date. No mock mode or synthetic fallback is used. The output is kept under git-ignored `research_private/`; only a public synthetic-free **derived GeoJSON aggregate** has been reviewed and committed in this isolated branch.

Artifact: `data/observed_ndvi_change_20261120.geojson` includes paired clear count **6,512**, median ΔNDVI **-0.0101745748**, 116 8×8-pixel summaries, and **0** pixels falling below the illustrative ΔNDVI ≤ -0.15 threshold. Corrected radiometry supersedes earlier same-day computed output in branch history. **This is not ground-truth anomaly validation**.

### Run browser preview, without deployment
```powershell
python -m http.server 8765 --bind 127.0.0.1 --directory docs
```
Visit `http://127.0.0.1:8765/experimental/geo-intelligence/`. The page fails closed with an honest message if its research JSON cannot load; it never fabricates values. Tiles require access to the external OpenStreetMap tile service, subject to its provider terms; the source evidence is independent of tile-loading success.

### Tests
```powershell
python -m pytest pipeline/tests --basetemp="C:/a-writable-temp-folder" -q
```

A full test run on the authorized Windows laptop reported **102 passed** (20 Nov 2026). A pre-existing test mutated `docs/data/financial_feed.json` by adding duplicate fixture rows; its diff was saved privately before restoring the test-induced mutation. This is a **suite side-effect warning** pending proper test isolation, not a source observation. Headless Chrome desktop/mobile smoke runs loaded real numbers and Leaflet tiles at localhost; no independent user testing was conducted.

### Boundaries
- No Rota Única private field geometry, drone imagery, sensors, maps or supplier credentials.
- No independent event ground truth, precision, recall, F1, economic effect or causality claim.
- The current masked geographic 96×96 raster is a preview grid, not certified physical surface-area delineation.
- No adaptive threshold tuning on event labels; fixed -0.15 heuristic is **illustrative only**.
- Check SCL mask classifications, radiometric calibration, geography, seasonality and atmospheric differences before scientific interpretation.
- Official provider and asset terms apply. Leaflet uses BSD-2-Clause, OSM tiles require attribution.

Read [ADR](../../research/ADR-THESIS-CONVERGENCE-20261120.md), [license-aware catalog](../../research/OPEN_SOURCE_REUSE_CATALOG_20261120.md) and [ESA processing-baseline documentation](https://sentiwiki.copernicus.eu/web/s2-processing).

Rollback: no production deploy has occurred. The baseline `main@feed5e6` and `preserve/main-20261120-feed5e6` remain untouched; new commits are only on the isolated operation branch.

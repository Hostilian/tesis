# Direct reuse license and provenance evidence — 22 November 2026

**Review target:** `operation/thesis-convergence-integrated-20261122`. This is a **source-file license check** for components actually reused by the observed Sentinel-2 preview. It does not assert a complete supply-chain audit, paid-service authorization, dataset redistribution rights, or legal advice.

| Used component | Pinned version / role | Original upstream evidence read | Findings and remaining conditions |
|---|---|---|---|
| [PySTAC Client](https://github.com/stac-utils/pystac-client) | `pystac-client==0.8.6`; search STAC items | [Upstream LICENSE](https://github.com/stac-utils/pystac-client/blob/main/LICENSE) | **Apache-2.0** in source LICENSE; retain any required notices when redistributing binaries or source. Installed distribution verification pending |
| [rasterio](https://github.com/rasterio/rasterio) | `rasterio==1.5.0`; WarpedVRT aligned COG access | [Upstream LICENSE.txt](https://github.com/rasterio/rasterio/blob/main/LICENSE.txt) | **BSD-3-Clause**; attribution and no-endorsement terms. Check native GDAL bundle and version |
| [NumPy](https://github.com/numpy/numpy) | `numpy==2.2.2`; masked NDVI and aggregation | [Upstream LICENSE.txt](https://github.com/numpy/numpy/blob/main/LICENSE.txt) | **BSD-3-Clause**, with third-party notices in release distribution. Exact wheel/license bundle audit pending |
| [Planetary Computer Python SDK](https://github.com/microsoft/planetary-computer-sdk-for-python) | `planetary-computer==1.0.0`; signed public raster asset links | [Upstream LICENSE](https://github.com/microsoft/planetary-computer-sdk-for-python/blob/main/LICENSE) | **MIT source-code license**. Not a license for Microsoft hosting, ESA imagery, COG products or all underlying catalogs |
| [Leaflet](https://github.com/Leaflet/Leaflet) | 1.9.4; existing site map and experimental GeoJSON viewer | [Upstream LICENSE](https://github.com/Leaflet/Leaflet/blob/main/LICENSE) and [official CDN instructions](https://leafletjs.com/download.html) | **BSD-2-Clause**. Experimental CSS/JS assets now use official 1.9.4 jsDelivr URLs and upstream documented SRI digests; do not copy entire library or run installers |
| [GDAL](https://github.com/OSGeo/gdal) | Native dependency of rasterio, not separately installed for this feature | [Upstream LICENSE.TXT](https://github.com/OSGeo/gdal/blob/master/LICENSE.TXT) | General **MIT-style** licensing, with **per-file and third-party exception notices** explicitly included. Do not reduce entire dependency graph to one MIT label |
| [Sentinel-2 MSI L2A](https://sentiwiki.copernicus.eu/web/s2-products) | 2024 & 2025 public source scenes | [ESA processing conventions](https://sentiwiki.copernicus.eu/web/s2-processing) | Source imagery and ESA product terms are distinct from software licenses. Preserve attribution, source scene IDs, processing baseline, SCL mask, dataset dates and only approved derived public artifacts |
| [OpenStreetMap tiles](https://operations.osmfoundation.org/policies/tiles/) | Geo-reference basemap, small demo | [OSM copyright](https://www.openstreetmap.org/copyright), [tile usage policy](https://operations.osmfoundation.org/policies/tiles/) | Attribution is shown in the map and footer. Public tile server access requires compliance with usage policy, browser cache and no high-volume scraping |

## Concrete code/config evidence

The original thesis `pipeline/requirements.txt` already includes `planetary-computer`, `pystac-client`, `rasterio` and `numpy`. The new experiment **did not add another geospatial dependency** and imports these pre-existing packages. Browser `docs/experimental/geo-intelligence/index.html` reuses the existing Leaflet 1.9.4 architecture with verified CDN integrity:

- CSS: `sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=`
- JS: `sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=`

Only **glue code for the research question**, not a replacement map or raster engine, was written: two-source temporal comparison, chronology/CRS/scene QA, aggregation to GeoJSON, and a read-only experimental UI.

## Approval gates still open

1. Confirm **installed release** dependency notices, transitive licenses, pinned hashes/SBOM, vulnerability results, and compatibility with Python/runtime.
2. Verify Copernicus/Planetary Computer attribution and public redistribution terms for the **derived 93 KB GeoJSON**, not the privately retained source NPZ.
3. Check OSM tile service and third-party CDN network policies; run a real accessible-browser/mobile test after the latest SRI change.
4. If God’s Eye View, ODM/WebODM or any other candidate is ever vendored/forked, inspect their **bundled datasets**, copyright and copyleft/NC restrictions again. Current decision is **no vendoring**.

**Result:** Direct upstream source licenses reviewed. Full quality Gate A is **PARTIAL** until release/transitive/dataset review. No external messages, paid API calls, installs or farm-source transfers occurred.

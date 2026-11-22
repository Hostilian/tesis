# Open-source reuse catalog — 20 November 2026

**Status:** **Initial primary-source triage, not installation approval.** This catalog prioritizes the current user goal. Repository existence, recent activity (GitHub metadata), and several explicit license files were checked. `NOASSERTION` means GitHub's license classifier did NOT resolve the license; inspect the actual LICENSE/NOTICE and included assets before copying. No code or third-party bundled dataset was copied from these projects.

Scoring: **Fit** (H high / M medium / L low for *this thesis vertical slice*); **Integration** (E easy / M moderate / H high effort). Security audits, exact release/commit pinning, benchmark performance, mobile scores and transitive dependency reviews remain **not performed** except where noted. All proposed public components must be reviewed for accessibility and third-party attribution before promotion. **Free** refers to no required paid runtime for the stated local use case, not a guarantee that third-party imagery or hosted APIs cost nothing.

| # | Upstream official/repository | License status (source or GitHub API) | Fit | Integration | Decision / why | Risks, costs and validation gate |
|---|---|---|---|---|---|---|
| 1 | [Existing thesis Leaflet integration](https://github.com/Leaflet/Leaflet) | BSD-2-Clause via API | H | E | **REUSE NOW**; current site already uses Leaflet and loads GeoJSON | Tile-provider terms, network, accessibility; browser verify |
| 2 | [Planetary Computer STAC](https://planetarycomputer.microsoft.com/docs/) | Public service/data terms distinct from code | H | E | **REUSE NOW**; already retrieved signed authentic COG pixels | Availability, links expire, data terms, radiometric correction |
| 3 | [PySTAC Client](https://github.com/stac-utils/pystac-client) | GitHub API NOASSERTION; inspect file | H | E | **REUSE NOW** already pinned in existing requirements | STAC search schema/API behavior, dependency license check |
| 4 | [rasterio](https://github.com/rasterio/rasterio) | GitHub API NOASSERTION; inspect file | H | E | **REUSE NOW**; existing WarpedVRT handles geospatial reprojection | GDAL runtime, actual grid/scale verification |
| 5 | [NumPy](https://github.com/numpy/numpy) | Review installed package license for release | H | E | **REUSE NOW** for NDVI, NaN masks and pixel summaries | Numerical tolerances and domain-specific semantic tests |
| 6 | [GDAL](https://github.com/OSGeo/gdal) | GitHub API NOASSERTION; inspect file | M | M | Use as existing rasterio dependency / CLI only when needed | Large native dependencies; unnecessary install now |
| 7 | [GeoPandas](https://github.com/geopandas/geopandas) | BSD-3-Clause via API | M | E | Deferred: useful for joined vector layers, not needed for 96×96 grid | CRS and shapely stack, larger assets |
| 8 | [xarray](https://github.com/pydata/xarray) | Apache-2.0 via API | M | M | Deferred until real temporal cubes are needed | Memory, Dask interoperability and sample alignment |
| 9 | [stackstac](https://github.com/gjoseph92/stackstac) | License review pending | M | M | Future multi-date STAC→xarray integration candidate | Reprojection, lazy reads, memory and provider authentication |
| 10 | [openEO](https://openeo.org/) | Service/client-specific terms pending | M | H | Evaluate as alternative platform; not needed for two-scene preview | Provider backend limits, authorization and API portability |
| 11 | [CDSE STAC official](https://documentation.dataspace.copernicus.eu/APIs/STAC.html) | Public dataset/API terms | H | M | Documented alternate discovery source; no custom crawler | Endpoint migration, credentials for downstream assets |
| 12 | [MapLibre GL JS](https://github.com/maplibre/maplibre-gl-js) | GitHub API NOASSERTION; manual LICENSE pending | H | M | Candidate for next *genuinely needed* vector/terrain layers | WebGL/mobile fallback; licensing map/terrain styles |
| 13 | [deck.gl](https://github.com/visgl/deck.gl) | MIT via API | M | M | Defer; meaningful when thousands of geospatial objects | GPU costs, complexity vs existing Leaflet |
| 14 | [CesiumJS](https://github.com/CesiumGS/cesium) | Apache-2.0 via API | M | H | Only adopt for scientifically useful 3D terrain/globe | 3D/tiles dependencies, memory, device compatibility |
| 15 | [OpenLayers](https://github.com/openlayers/openlayers) | BSD-2-Clause via API | M | M | Alternative, not alongside Leaflet absent a concrete need | Avoid dual map frameworks |
| 16 | [kepler.gl](https://github.com/keplergl/kepler.gl) | MIT via API | M | H | Rapid exploratory analyst tool; not thesis production UI now | Heavy frontend/dependency and saved-state complexity |
| 17 | [GeoLibre](https://github.com/opengeos/GeoLibre) | MIT via API | M | M | Review for useful patterns; no extra deployed runtime | Scope/compatibility check |
| 18 | [God's Eye View](https://github.com/bilawalsidhu/gods-eye-view) | **MIT code** verified in LICENSE; **separate NC/ODbL/other data** | M | H | **DO NOT CLONE FULL APP.** Review navigation/layer concepts only | Bundled TeleGeography CC BY-NC-SA, Bhote Koshi CC BY-NC; branded/military-centric UX and third-party APIs |
| 19 | [rio-tiler](https://github.com/cogeotiff/rio-tiler) | Verify current LICENSE | M | M | Defer unless larger COG tile streams require server tiles | GitHub Pages cannot serve arbitrary Python tile backend |
| 20 | [TiTiler](https://github.com/developmentseed/titiler) | Verify current LICENSE | M | H | Reuse only if tile server is justified | Hosting, bandwidth, security; static Pages has no backend |
| 21 | [OpenDroneMap](https://github.com/OpenDroneMap/ODM) | **AGPL-3.0** via API | L for public thesis / H optional private | H | Best-known photogrammetry candidate; **private only** | GPL obligations, processing costs, photogrammetric calibration, authorization |
| 22 | [WebODM](https://github.com/OpenDroneMap/WebODM) | **AGPL-3.0** via API | L public / H optional private | H | UI/workflow candidate for approved drone inputs | Runtime resources, licensing, no farm publication |
| 23 | [Grafana Skills](https://github.com/grafana/skills) | **Apache-2.0** via API | L now / M operations | E instructions | Review vetted skills only; **no server install yet** | No live telemetry; avoid fabricated graphs |
| 24 | [Grafana GCX](https://github.com/grafana/gcx) | **Apache-2.0** via API | L now / M operations | H | Defer until actual runtime diagnostics | Do not replace Grafana's normal provisioned dashboards |
| 25 | [Grafana Alloy](https://grafana.com/docs/alloy/latest/introduction/) | Check installed release/NOTICE | L now / M operations | M | Current collector choice if backend added | Agent and Promtail deprecated; no need for static GitHub Pages |
| 26 | [Grafana](https://github.com/grafana/grafana) | Verify current licensing/edition | L now / M private ops | H | No operational metrics or private server currently demonstrated | Hosting/credentials, false status widgets |
| 27 | [Ponytail canonical](https://github.com/DietrichGebert/ponytail) | **MIT** via API; inspect hooks | H as review methodology | E instructions | **Apply reuse ladder; do not globally install hooks blindly** | Performance marketing claims not independently replicated |
| 28 | [StarQuant/ponytail-skill](https://github.com/StarQuant/ponytail-skill) | MIT via API | M | E | Mirror/instructions reviewed; **canonical is DietrichGebert** | Pin verified maintained upstream instead |
| 29 | [OpenRouter Skills](https://github.com/OpenRouterTeam/skills) | License not yet verified | L now / M optional review | E | **No runtime / no API calls; optional instruction-only** | Paid inference, private-data egress, secrets, models move |
| 30 | [stac-fastapi](https://github.com/stac-utils/stac-fastapi) | Release/LICENSE verification pending | L | H | Do not build a STAC backend while public catalog already exists | Maintenance / backend hosting unnecessary |
| 31 | [QGIS](https://github.com/qgis/QGIS) | GPL-family; exact current obligations verify | M as desktop auditor | E local | Use as an independent analyst tool for validating CRS/masks | No need to bundle desktop code in website |

## Ranked implementation decision

1. **Keep existing** Planetary Computer + PySTAC Client + rasterio + NumPy + `GeospatialPreprocessor`. Reuse scientifically proven ESA baseline conversion; avoid proprietary calibration.
2. **Keep existing Leaflet**, using plain GeoJSON in a separate experiment; no new globe framework until the user interaction requires 3D.
3. **Use QGIS/GDAL as external QA tools**, not new application dependencies.
4. When real data volume justifies it: **xarray/stackstac**, then potentially **MapLibre**; isolate prototypes.
5. **Keep ODM/WebODM private and optional** pending permission and actual image data.
6. **Hold Grafana/OpenRouter/God's Eye View integration** until runtime, security, or research value justifies them.

## Upstream activity and security limits

GitHub metadata on 20 Nov 2026 reports recent commits for the principal candidates (Leaflet, MapLibre, Cesium, deck.gl, GDAL, GeoPandas, xarray, Grafana skills/GCX, God's Eye View, Ponytail, ODM/WebODM), not proof of release quality. No transitive CVE audit or production load test was completed in this catalog. Before **copying source or assets**: lock release/commit, inspect each LICENSE/NOTICE and bundled dataset license, assess security, and retain attribution. Third-party tiles, fonts, imagery, compiled models, and packages may have licenses unrelated to the app's code license.

**Official confirmations:** [CDSE 2026 STAC changes](https://dataspace.copernicus.eu/news/2026-10-16-new-sfeos-stac-catalogue-endpoint) (current endpoint may change in 2027), [Grafana Agent EOL](https://grafana.com/docs/agent/latest/about/), [Promtail EOL](https://grafana.com/docs/loki/latest/send-data/promtail/), [OpenRouter Skills](https://openrouter.ai/skills/).

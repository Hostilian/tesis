# Sentinel-2 seasonal replication — 22 November 2026

**Evidence class:** real public EO observations; **interpretation unvalidated**. This note records an exploratory repeat of an existing pipeline, not new algorithm development or a validated resource anomaly. No private Rota Única geometry, API or agronomic measurements used.

## Why replicate

The [20 November exploratory pair](ADR-THESIS-CONVERGENCE-20261120.md) used October 2024 Sentinel-2B and October 2025 Sentinel-2C. This follow-up compares October **2025 and 2026**, both **Sentinel-2C**, to improve temporal/sensor comparability while preserving the previously fixed geography and radiometric calibration.

## Existing upstream integration reused

The execution called **unchanged** `python -m pipeline.observed_change` from this thesis checkout, using the previously integrated **Microsoft Planetary Computer STAC, PySTAC Client, rasterio/WarpedVRT and NumPy**; the only local action was choosing new date windows.

```powershell
.\.venv-convergence\Scripts\python.exe -m pipeline.observed_change `
  --bbox -68.25 -23.48 -68.238 -23.468 `
  --before-start 2025-10-01 --before-end 2025-10-18 `
  --after-start 2026-10-01 --after-end 2026-10-18 `
  --output-dir research_private/observations/seasonal_2025_2026
```

Execution on the authorized Windows remote laptop wrote a **git-ignored private** GeoJSON observation record; it did not modify public site assets. The same command was independently rerun into a different output directory.

## Observations and source IDs

| Field | 2025 comparison scene | 2026 comparison scene |
| --- | --- | --- |
| Scene | `S2C_MSIL2A_20251014T143751_R096_T19KEQ_20251014T181516` | `S2C_MSIL2A_20261009T143741_R096_T19KEQ_20261009T175817` |
| Acquisition | 2025-10-14T14:37:51.025Z | 2026-10-09T14:37:41.025Z |
| Processing baseline | 05.11 | 05.13 |
| BOA `ADD_OFFSET` in source DN | −1000 | −1000 |
| Provider/collection | Microsoft Planetary Computer / Sentinel-2 L2A | Microsoft Planetary Computer / Sentinel-2 L2A |

Results for bounding box `[-68.25, -23.48, -68.238, -23.468]` (lon/lat), same 96×96 sample grid:

| Derived measurement | 2024→2025 earlier pair | **2025→2026 new pair** |
| --- | ---: | ---: |
| Paired clear/valid pixels | 6,512 | **3,702** |
| Total sampled pixels | 9,216 | **9,216** |
| Spatial aggregate features | 116 | **82** |
| Median per-pixel NDVI difference (after−before) | −0.010174574771930473 | **−0.007306997989659468** |
| Pixels with difference ≤ −0.15 (exploratory threshold) | 0 | **0** |
| Independently validated anomaly labels | **none** | **none** |

**Repeatability check:** second complete live STAC/COG run selected the **identical two source scene IDs** and produced exactly matching **derived-array SHA-256** `bd05797838bc886ded80f3e0a458def125ebfb09f37219a79f938c0d1e4d47b5`, valid pixel count and median NDVI difference. The two GeoJSON *file* hashes differ because their recording timestamps differ; the derived arrays match. This is a source-and-pixel repeatability observation, **not independent model-performance validation**.

## Limitations that control thesis claims

1. These are **two different pairwise valid-pixel intersections**, not the same common pixel mask across all three acquisition dates. Do not compare the medians as a continuous three-year trajectory or trend. The 2025→2026 pair has only 3,702/9,216 usable pixels.
2. The first pair crosses **Sentinel-2B → Sentinel-2C**; the second uses two S2C scenes but processing baselines **05.11 → 05.13**. Calibration records support the −1000 offset, not a full cross-baseline/harmonization uncertainty study.
3. October acquisitions are approximately seasonal but differ in day and cloud/shadow conditions. SCL masking excludes classes 0,1,3,8,9,10,11; residual contamination, BRDF, terrain, atmosphere and pixel-grid resampling may affect differences.
4. NDVI change, especially near zero, is **not evidence** of resource extraction, agricultural stress, economic causality, extraction rates, yield or intervention impacts. The −0.15 threshold is an uncalibrated example and **zero flags is not a negative ground-truth event result**.
5. A derived-array checksum is not an ESA/COG source-archive checksum. Reproduction also depends on public asset availability and signed URLs. Source metadata and fixed processing settings must accompany any final manuscript evidence.
6. No student/teacher report, sensor readings, company data, academic marks or third-party communications were created or modified.

## Next scientific gate

Align **three real scenes** onto one grid and the **same three-way valid-pixel intersection**, then report paired raw distributions, uncertainty/sensitivity to cloud and radiometry settings, and repeat across independent regions/seasons. Prefer existing rasterio/xarray/stats and verified upstream implementations; create only essential glue. Add independent labels before any detector accuracy, and actual aligned economic data before any correlation/causal claim. Obtain CZU supervisor scope validation before revising the registered topic.

**Data policy:** both full private derived GeoJSON runs are under `research_private/observations/seasonal_2025_2026*`, excluded by `.gitignore`. This public note includes only shareable ESA/public-scene metadata and aggregate results.

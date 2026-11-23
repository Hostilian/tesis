# Portugal-first and European validation scope — 23 November 2026

**Status:** working geography decision and authentic public-data experiment, **not** a CZU-approved thesis scope change or a validated agricultural event. The existing thesis title and the exact 20 November Candidate A remain unchanged. No Rota Única polygons, device locations, imagery or company telemetry are present.

## Research alignment

**Selected central question (unchanged):** “How can an API-first, open-source Earth-observation pipeline acquire, compare and explain reproducible satellite-derived resource-condition changes with traceable provenance and explicit uncertainty, while avoiding unsupported economic or anomaly claims?”

**Proposed geographical specification, for supervisor review:** “How can an open-source, API-first Earth-observation system reproducibly compare and communicate satellite-derived resource-condition changes in Portugal and selected European regions, with explicit quality control, provenance and uncertainty appropriate to the available spatial resolution?”

**Candidate B / constrained agricultural case study:** “At what field- or orchard-block scale can freely available Sentinel-2 observations describe vegetation-condition change in Alentejo, and when are independently authorized high-resolution imagery and ground observations required?” This is **conditional**, not an assertion of individual-tree phenology, almond yield, irrigation stress, disease or causal attribution.

**Candidate C / engineering-method question:** “How can STAC/COG acquisition, validated transformations, GeoJSON exchange and reusable geospatial interfaces deliver a reproducible, provenance-preserving Portugal-first decision-support prototype?” This can be evaluated **without fine individual-tree imagery**. It is a method/contribution, not a competing thesis title.

**Geographic priority:** primary public study near Évora/Alentejo, secondary open public comparison elsewhere in Portugal, tertiary independent European comparator (e.g. Czechia or Spain) **only after a verified source and scientific sampling design**. The historic Chile evidence is preserved as a separate methodological baseline, not deleted or rebranded as Portugal.

## What the imagery can and cannot resolve

| Source | Nominal scale / cadence | Suitable study use | Unacceptable interpretation without independent validation |
| --- | --- | --- | --- |
| Sentinel-2 MSI L2A | 10 m visible/NIR; 20 m red-edge/SWIR; 60 m atmospheric bands | Field-scale temporal vegetation-index and surface-condition changes, when fields contain sufficient uncontaminated pixels | Single almond-tree vigor, bloom dates, fruit maturity, yield, exact water stress or diseases |
| Sentinel-1 radar | Instrument-dependent; frequently distributed at 10 m pixel spacing, but spacing is not effective spatial resolution | Complement cloudy optical scenes; test moisture/structure-sensitive backscatter with calibrated interpretation | Direct soil moisture or crop-stage ground truth from one backscatter layer |
| Portugal DGT orthoimagery / OrtoSat | Selected DGT orthophotos 25 cm to 1 m; OrtoSat2023 30 cm | Historic geometric context, object/row delineation and possible reference-image interpretation subject to access, dates and reuse terms | Daily high-resolution time series, guaranteed current tree condition, or unrestricted reuse |
| DGT SMOS MIAEV/MACAT and EU CLMS HR-VPP | Many products at 10 m; product-specific temporal resolution | Independent product comparison and vegetation/land-cover context with source/validation checks | Unquestioned event labels, supervised truth, or plantation management advice |

**Resolution rule:** A 96×96 sampling grid reprojected to EPSG:4326 is an analytical **resampled preview**, not a measured native 10 m pixel or confirmed parcel boundary. An ordinary NDVI difference mixes canopy, soil, atmosphere, seasonal phenology and acquisition geometry. Do not train or label a farm-level detector from these example AOIs.

## Live run 1 — near-Évora boundary-sensitivity pilot (diagnostic, NOT chosen)

- Public sample rectangle EPSG:4326: `[-7.86, 38.52, -7.848, 38.532]`.
- Acquisitions 2024-06-12 (tile 29SPC), 2025-06-17 (tile 29SPC), 2026-06-19 (tile 29SNC).
- Three-way finite NDVI common mask **3,684 / 9,216 = 39.97%**; per-scene counts 3,684, 3,684, 9,216.
- Potential tile-edge/scene-footprint and quality-selection problem: only part of the grid survives. **Tile change is an observation; the exact cause of coverage loss remains to be independently diagnosed.**
- This is a *quality finding*, not evidence of environmental change. Retain the full output in git-ignored private research evidence.

## Live run 2 — west-of-Évora public pilot (selected for further QA)

- Public sample rectangle EPSG:4326: `[-8.03, 38.53, -8.018, 38.542]`. Its crop/land-cover classification and ownership are **unknown**; this is **not** an asserted Rota Única farm.
- Three **authentic** Sentinel-2 L2A COG scenes via Microsoft Planetary Computer public STAC:
  - 2024-06-12: `S2B_MSIL2A_20240612T112119_R037_T29SNC_20240612T152007`, processing baseline `05.10`.
  - 2025-06-07: `S2B_MSIL2A_20250607T112109_R037_T29SNC_20250607T133245`, baseline `05.11`.
  - 2026-06-19: `S2A_MSIL2A_20260619T112131_R037_T29SNC_20260619T210258`, baseline `05.12`.
- Reflectance correction in the unchanged existing reader: BOA additive offset **−1000 DN** / quantification 10,000, with SCL exclusion 0,1,3,8,9,10,11.
- All **9,216/9,216** resampled sample cells are finite/valid across all three dates. This is a valid-pixel overlap result, **not** independent scientific quality certification.
- Same-grid **median per-pixel NDVI differences**: 2024→2025 **+0.05386168264**, 2025→2026 **−0.10986893628**, 2024→2026 **−0.05549225234**.
- Derived **array** SHA-256: `af8740772d77d5f24fd6b5f57afa2701498caee81a7d06fb1195753e1aa8b981`; this is **not** an original Copernicus product archive checksum.
- No independent land-cover labels, field boundaries, agronomic inspections, uncertainty intervals, anomaly performance or economic inference exist. S2B→S2A and PB changes still require sensitivity checks.
- The separate public-aggregate **2025→2026 pair** is the derived GeoJSON at `../experimental/geo-intelligence/data/portugal_alentejo_ndvi_change_20261123.geojson`: 9,216 valid paired pixels, 144 summary polygons, median ΔNDVI −0.10986893628, 2,847 pixels meeting **an uncalibrated** ΔNDVI ≤ −0.15 illustrative threshold. No cell/flag means a validated anomaly.

### Reproduce from the existing code (no new satellite reader)

Use Python 3.12 with the **existing** `pipeline/requirements.txt` geospatial packages, and run from repository root:

```powershell
python -m pipeline.three_scene_observation --bbox -8.03 38.53 -8.018 38.542 --first-start 2024-06-01 --first-end 2024-06-25 --middle-start 2025-06-01 --middle-end 2025-06-25 --last-start 2026-06-01 --last-end 2026-06-25 --output-dir research_private/observations/portugal_evora_repeat
python -m pipeline.observed_change --bbox -8.03 38.53 -8.018 38.542 --before-start 2025-06-01 --before-end 2025-06-25 --after-start 2026-06-01 --after-end 2026-06-25 --output-dir research_private/observations/portugal_evora_pair_repeat
```

The private `research_private/` results are git-ignored and must **never** be blindly uploaded. The committed experimental viewer uses a previously inspected, narrowly derived public GeoJSON export. Do not copy data from any company folder. Compare scene IDs, derived digest and metrics for a repeat rather than expecting recording timestamps/file hashes to match.

## Remaining acceptance gates before making Portugal the thesis empirical centerpiece

1. **Independent same-scene reproduction:** rerun, match the derived arrays digest, and preserve an isolated dated receipt.
2. **Acquisition QA:** explain the first AOI's missing scene footprint, compare alternate sources/times; do not choose scenes solely by scene-wide cloud percentage.
3. **Spatial QA:** use an appropriate projected metric CRS, check native resolution, resampling and mixed pixels; use meaningful AOI sizes and parcel boundaries only from authorized, validated sources.
4. **Temporal QA:** seasonally match days or phenological stages; compare multiple acquisitions per season, masks, observation count and cloud/shadow sensitivity.
5. **Scientific QA:** quantify baseline/sensor sensitivity; use independent evaluation labels if making a detector/accuracy claim. Verify DGT/CLMS product licenses, accessibility and reference-date suitability.
6. **Agri feasibility:** treat Sentinel-2 as **block-scale aggregate**; acquire permission and actual ground truth before claiming almond health or comparing any company farm.
7. **Economic scope:** clarify with Dr. Brožek whether a real economic overlay is mandatory for the approved title; do not convert NDVI changes into resource extraction or GDP statements.
8. **Release:** keep public default / V3 / V4 untouched; this experiment remains an isolated branch until owner acceptance and QA.

## Primary official sources

- ESA Sentinel-2 L2A/10–20–60 m: https://sentinels.copernicus.eu/sentinel-data-access/sentinel-products/sentinel-2-data-products/collection-0-level-2a
- CDSE S2 L2A documentation and SCL: https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html
- DGT 2025 orthophoto catalogue: https://www.dgterritorio.gov.pt/novo-catalogo-de-ortofotos-de-portugal-continental-no-centro-de-dados-da-dgt
- DGT 25 cm orthos metadata: https://snig.dgterritorio.gov.pt/rndg/srv/api/records/96d83932-f957-40d6-a2ea-3a25751c4b2d
- DGT OrtoSat2023 coverage/terms: https://www.dgterritorio.gov.pt/Disponibilizacao-da-OrtoSat2023-Completa
- DGT MIAEV/MACAT product guidance: https://smos.dgterritorio.gov.pt/produtos-cartograficos-especificos
- Copernicus vegetation phenology: https://land.copernicus.eu/en/products/vegetation
- Sentinel-1 SAR: https://documentation.dataspace.copernicus.eu/Data/Sentinel1.html
- Existing ADR: [Satellite-first architecture](ADR-THESIS-CONVERGENCE-20261120.md).

**No external messages, submissions, data purchases, company API calls, or deployment were made as part of this research experiment.**

## Executed technical checks and repeatability — 23 November 2026

- A **second independent complete live STAC/COG execution** of the west-of-Évora 2024/2025/2026 experiment returned the **same three exact scene IDs, all 9,216 common-valid pixels, the same median 2025→2026 ΔNDVI, and identical derived array SHA-256** `af8740772d77d5f24fd6b5f57afa2701498caee81a7d06fb1195753e1aa8b981`; timestamps differed as expected. This is source-and-array repeatability only.
- Existing pipeline produced a separate public two-scene 2025→2026 GeoJSON, and the existing God's Eye View bridge exported exactly 144 reviewed geometric cells. Both original upstream God’s Eye parse/decode functions accepted the new Portugal bundle and preserved 116-cell Chile reference.
- **20 focused Python tests passed**, covering the existing Chile bridge, the new Portugal public-data contracts and the shared-grid three-scene workflow. Viewer inline JavaScript syntax parsed successfully with Node. Local HTTP preview returned 200. A complete browser interaction/visual acceptance pass was **not established**; the headless Chrome DOM attempt did not yield usable output. No live Pages release from this branch.
- The first AOI's tile transition and 39.97% common-valid count should remain an explicit data-selection quality issue. High clear-pixel overlap on the second AOI **does not** quantify classification validity, radiometric uncertainty or agronomic accuracy.

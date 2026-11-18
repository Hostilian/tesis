# Open imagery and software options for an agricultural monitoring study

**Review date:** 18 November 2026  
**Status:** Source review and implementation options only. No imagery was acquired, no flight was performed, and no partner or other private data was accessed or published.

## Recommended source mix

| Source | What it can contribute | Strengths | Limits and verification before use |
|---|---|---|---|
| Copernicus Sentinel-2 L2A through CDSE STAC | Repeat satellite surface-reflectance observations for broader field context. | Public catalogue/API; bounded spatial and temporal search; band selection. | Cloud and revisit gaps; mixed pixel scales; exact items and assets must be inspected. Sentinel-2 red and NIR are 10 m, while red-edge and SWIR bands are 20 m. |
| DGT Portugal 2025 orthophotos | Aircraft-acquired, orthorectified RGB+NIR aerial reference over mainland Portugal. | Official DGT page reports 25 cm GSD, RGB+NIR, acquisition between 29 March and 26 July 2025, open download and CC BY 4.0 attribution. | Confirm the correct map tile, full metadata, exact capture date, and whether it is appropriate for the study question. A dated basemap is not field ground truth or a repeated crop-health series. |
| OpenAerialMap | Search for openly licensed aerial/UAV imagery contributed for particular locations. | Open discovery of imagery and metadata; may avoid a new capture. | Coverage is location/date dependent. Inspect each asset’s license, resolution, date, CRS, source and metadata; do not assume imagery exists over a target field. |
| OpenDroneMap (ODM) | Create orthophotos, elevation models or point clouds from authorized overlapping geotagged drone stills. | Open-source photogrammetry tooling with documented output and resource options. | Processing can be CPU/RAM/disk intensive. Reuse an existing orthomosaic first. If ODM is needed, bound image count and concurrency, choose a no-GPU/fast-orthophoto path if suitable, and measure the actual machine. |
| QGIS and GDAL | Inspect, align, reproject, clip, compare and document vector/raster data. | Mature open-source GIS tools support common raster/vector formats and web services. | Correct CRS, pixel alignment, scale, units and nodata treatment still require methodological decisions. |

Primary documentation:

- [DGT: new mainland Portugal orthophoto catalog](https://www.dgterritorio.gov.pt/novo-catalogo-de-ortofotos-de-portugal-continental-no-centro-de-dados-da-dgt)
- [DGT: 2021 orthophotos](https://www.dgterritorio.gov.pt/Ortofotomapas-2021)
- [Copernicus Data Space STAC catalogue](https://documentation.dataspace.copernicus.eu/APIs/STAC.html)
- [Copernicus Sentinel-2 L2A bands and resolutions](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html)
- [OpenAerialMap](https://openaerialmap.org/about/) and [its documentation](https://docs.openaerialmap.org/)
- [OpenDroneMap documentation](https://docs.opendronemap.org/) and [processing options](https://docs.opendronemap.org/arguments/)
- [QGIS supported data documentation](https://docs.qgis.org/3.44/en/docs/user_manual/working_with_vector/supported_data.html)

## Keep the image types distinct

- **Satellite scene:** sensor product with known acquisition time, band definitions, pixel resolution and processing level.
- **Aircraft orthophoto:** already orthorectified aerial raster; DGT’s 2025 release is a public candidate for Portugal mainland.
- **Drone orthomosaic:** processed product from an authorized survey or a photogrammetric reconstruction.
- **Raw drone/aircraft video:** footage, not a validated map layer. Frame extraction and georeferencing require adequate camera, time, position, overlap, and calibration data.
- **Vendor vegetation layer:** an output whose native bands, units, formulas, processing, and rights must be confirmed before comparison.

RGB-only images cannot yield NIR-based NDVI or NDRE. For any multi-sensor comparison, preserve native bands and metadata, inspect radiometric calibration, align the CRS and dates, and state how resampling affects the comparison. Same-named indexes from different products are not automatically comparable.

## Reuse-first architecture

1. A source adapter discovers public satellite products through STAC or reads an authorized existing aerial raster.
2. A metadata gate checks acquisition date, footprint, CRS, bands, pixel scale, nodata, quality mask, license, and provenance before processing.
3. A bounded transform step clips the authorized study extent, applies quality masks, and records every resampling/feature choice.
4. One transparent baseline produces a map or change summary, not a crop diagnosis unless independently validated.
5. A separate evaluation component compares outputs with a dated, independent reference if one exists.
6. An API/map shows data mode and provenance; mock, public, vendor, and field-reference inputs remain visibly distinct.
7. A benchmark record separates API/network waiting, cache, raster processing, and memory use.

The existing thesis repository contains preprocessing, anomaly analysis, API and dashboard modules. These source files establish implementation candidates, not proof that live imagery has been queried or scientifically validated.

## Legal, privacy and data gates

- Prefer public existing imagery before planning a new flight or requesting private footage.
- For any new UAS operation in Portugal, check current ANAC geographic-zone and operating requirements for the exact place, aircraft and flight. EU open-category rules include operational limits such as maintaining visual line of sight; the applicable subcategory and local restrictions must be checked before flight.
- Obtain permission from the image/data owner and landowner for use in university research, storage and thesis publication. Do not put private boundaries, images, supplier tokens or farm records in a public repository.
- Apply source-specific attribution and license terms. DGT describes its 2025 orthophotos as open data under CC BY 4.0.
- Preserve the difference between public basemap coverage, partner imagery, synthetic fixtures, and actual independent field observations.

References: [ANAC Portugal open-category information](https://www.anac.pt/VPT/GENERICO/DRONES/CATEGORIA_ABERTA/Paginas/CategoriaAberta.aspx), [EASA open-category rules](https://www.easa.europa.eu/en/domains/drones-air-mobility/operating-drone/open-category-low-risk-civil-drones), and [EU Implementing Regulation 2019/947](https://eur-lex.europa.eu/eli/reg_impl/2019/947/oj).

## Validation required before a thesis claim

| Claim | Minimum evidence |
|---|---|
| “Imagery was acquired” | Provider, collection/item/flight ID, dates, exact source file, license/permission, checksum and acquisition log. |
| “Images were aligned” | CRS and pixel-grid metadata, reprojection/resampling record, alignment check and documented tolerances. |
| “The output detects a crop condition” | Independently collected dated ground labels, sampling design, label protocol, class balance, error analysis and an appropriate evaluation split. |
| “It is low-compute” | Repeated measurements on a named machine and pinned environment; bounded input size; API time separated from local processing; raw RAM/time records. |
| “The API works” | An authorized live request, response record with sensitive fields redacted, error/rate-limit behavior and a reproducible offline fixture. |

No such imagery acquisition, API request, flight, empirical validation, or benchmark is claimed in this document.


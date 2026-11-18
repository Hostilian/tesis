# Integrated imagery options and thesis-scope decision gate
**Review date:** 18 November 2026  
**Status:** Public-source planning note only. It does not approve a thesis-scope change, assert data acquisition, or report empirical results.

## One integrated software/data pipeline

A bounded geospatial thesis can connect software and data-analysis learning outcomes through one system:

**catalogue/provider adapters → metadata and provenance → quality checks → preprocessing → one justified baseline → evaluation → API/service → map/dashboard**

The research question, study area, and period must come from the approved assignment. Course alignment supports the engineering explanation; it does not approve the subject or validate results. See the public [course-outcome crosswalk](COURSE_OUTCOMES_TO_GEOSPATIAL_PIPELINE_2026-11-18.md) for the six-unit matrix.

## Scope options

| Option | Scope | Decision gate |
|---|---|---|
| A — retain current approved topic | Keep the registered satellite/API research question and narrow it to one defensible use case | Read the current formal assignment; preserve its scope |
| B — request a bounded agricultural case | One study unit and time window, one primary satellite collection, and at most one existing aerial reference product | Supervisor approval, any formal amendment, data rights, exact metadata, coverage, and a suitable validation plan |
| C — combine all modalities | Satellite, drone, crewed aircraft, private supplier layers, sensors, and prediction in one study | Defer unless the formal assignment requires it and rights, data, validation, time, and resources are all established |

Option A is the low-scope-risk default until an academic decision is recorded. Option B is a focused proposal. Option C multiplies owners, licenses, calibration and alignment work, data frequencies, validation needs, and computational load.

## Candidate imagery and open-source workflow

| Source/modality | Candidate role | Required checks before use |
|---|---|---|
| Sentinel-2 L2A via Copernicus Data Space STAC | Broad, repeated satellite observation | Exact collection/item, AOI/date, product level, assets/bands, cloud/quality filters, CRS, resolution, terms, quotas, and processing state |
| DGT 2025 mainland orthophotos | Possible aircraft-derived context or comparison | Confirm exact tile coverage and metadata; verify acquisition date, bands, CRS, resolution, license and attribution |
| Existing drone orthomosaic | Local detail if its use is authorized | Owner/supplier rights, date, sensor bands, GSD, CRS, calibration, NoData, and publication terms |
| Raw authorized drone stills with OpenDroneMap | Orthomosaic reconstruction only if needed | Image rights, overlap/geotags, bounded workload, disk/RAM/runtime and output quality |
| OpenAerialMap | Discover openly licensed imagery | Exact item, footprint/date, source, license and data quality |
| QGIS/GDAL | Inspect metadata/CRS, clip, compare and visualize geospatial data | Installed versions, supported formats, processing parameters and provenance |

DGT’s official catalogue announcement describes the 2025 mainland orthophoto coverage as 25 cm GSD and four RGB+NIR bands, with aerial photographs acquired between 29 March and 26 July 2025 and reuse under CC BY 4.0. The precise tile for a study location still needs checking; this imagery is not ground truth by default.

Copernicus Data Space STAC is a discovery interface; its documentation does not establish that a study-specific item was selected or downloaded. Public data, open-source software, free API/service tiers, and private/commercial access are separate categories.

## Cross-sensor and validation rules

- Treat satellite scenes, orthorectified aircraft mosaics, raw drone frames, provider-derived indices, telemetry, and field observations as distinct data types.
- RGB-only imagery cannot produce NIR-based indices such as NDVI or NDRE. Check the native band set rather than trusting a product label.
- Verify acquisition timing, radiometry, CRS, ground-sampling distance, masks, NoData, licensing, and geometric alignment before comparing sensors.
- Compare or aggregate at a defensible common scale. Higher image resolution does not make an image independent ground truth.
- Use independent, dated reference observations for accuracy claims. Without them, describe the work as a software pipeline or exploratory observation, not validated prediction.
- Distinguish software tests, mock fixtures, live API integration, authentic acquisitions, and scientific validation.
- Any proposed new UAS flight requires current location- and operation-specific review of national geographic zones and applicable rules. Existing licensed imagery is a lower-friction starting point.

## Course integration

The same pipeline can evidence:

- HCI: identified users/tasks and an actual interface-evaluation method.
- Software methods: requirements, models, component interfaces, version control, testing, and validation.
- Web technologies: API contract, client/server behavior, error handling, and documented deployment.
- Data transformation: input-quality checks, missing/NoData handling, outlier and imbalance choices, and transformation records.
- Probability/statistics: sampling, assumptions, uncertainty, and justified tests.
- Component-based software development: reusable adapters, clear boundaries, refactoring, profiling, and tests.

Current course descriptions establish learning outcomes only. Confirm current requirements before claiming any particular implementation or assessment satisfies a course.

## Evidence and academic-integrity boundary

A module, dashboard, mock fixture, screenshot, or successful test is not evidence of authentic imagery or scientific accuracy. For each empirical claim, preserve source/item identifiers, dates, AOI, license, masks, transformations, configuration, code revision, command, run log, outputs, and independent labels where needed.

Follow the applicable university assignment and academic rules. Keep results, discussion, and conclusions based on the student’s own verified work. Do not promote mock examples or unreproduced metrics as empirical findings.

## Public references

- [Copernicus Data Space STAC documentation](https://documentation.dataspace.copernicus.eu/APIs/STAC.html)
- [Copernicus Sentinel-2 collection information](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2)
- [DGT announcement: mainland Portugal orthophoto catalogue and 2025 coverage](https://www.dgterritorio.gov.pt/novo-catalogo-de-ortofotos-de-portugal-continental-no-centro-de-dados-da-dgt)
- [DGT orthophoto catalogue](https://cdd.dgterritorio.gov.pt/dgt-fe/catalogos/colecoes)
- [OpenAerialMap](https://imagery.hotosm.org/)
- [QGIS](https://qgis.org/)
- [OpenDroneMap documentation](https://docs.opendronemap.org/)
- [ANAC UAS geographic zones](https://dnt.anac.pt/?lang=pt)
- [ANAC guidance on restricted/conditional zones](https://www.anac.pt/VPT/GENERICO/DRONES/ZONA_PROIBIDAS_CONDICIONADAS/Paginas/Zonasproibidasoucondicionadas.aspx)
# Integrated imagery options and thesis-scope decision gate
**Review date:** 18 November 2026  
**Status:** Public-source planning note only. It does not approve a thesis-scope change, assert data acquisition, or report empirical results.

## One integrated software/data pipeline

A single coherent thesis can preserve the full breadth of its registered aims while connecting relevant software and data-analysis learning outcomes through one system:

**source/modality adapters → metadata and provenance → modality-specific quality checks → preprocessing and alignment → analyses appropriate to the approved aims → evidence-based evaluation → optional API/service or map/dashboard**

Preserve every connected aim and question in the approved assignment; do not collapse them to one site, period, sensor, phenomenon, or statistic by default. Course outcomes bound concrete work packages inside that thesis. They do not add research aims, approve the topic, or validate results. See the public [course-outcome crosswalk](COURSE_OUTCOMES_TO_GEOSPATIAL_PIPELINE_2026-11-18.md) for direct-fit and conditional units.

## Scope options

| Option | Scope | Decision gate |
|---|---|---|
| A — preserve the registered aims | Retain the formal title, connected objectives/questions, and intended breadth; map each aim to relevant methods, evidence, and course work packages | Retrieve the current UIS assignment and keep its breadth as the baseline |
| B — preferred agricultural application | Assess whether the registered aims can be implemented in an agricultural Earth-observation workflow across satellite, existing authorized drone/orthomosaic, and crewed-aircraft imagery where each source is relevant and supportable | Supervisor/UIS approval, rights, coverage, metadata, comparability, and suitable evidence for each claim |
| C — optional operational inputs | Add supplier APIs, sensors, telemetry, weather/soil data, new flights, or prediction only when directly relevant to an approved aim | Include each input only after its relevance, permission, data quality, time, and evaluation needs are clear |

The user's preferred working direction is B while preserving A's full scope; it is a proposal, not an approval. Keep the intended modalities visible when a source is temporarily unavailable and document that evidence gap. If an element conflicts with the formal assignment, ask the supervisor for the smallest necessary formal adjustment instead of narrowing silently. Course work packages should support the same thesis. Omit any course or source with no direct fit.

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

Possible teacher-bounded work packages within that same pipeline are:

- Component-based software development, software methods, data transformation, and probability/statistics are direct-fit candidates when their outcomes map to a real artifact and evidence task.
- Web technologies is conditional on the API/web deliverable remaining relevant to the approved thesis.
- HCI is conditional on a genuine, permitted user/task and interface evaluation; otherwise omit it from the thesis crosswalk.

These are candidate mappings, not a requirement to include all six units. Ask each teacher whether the proposed artifact demonstrates a current learning outcome; remove any mapping they judge irrelevant. The formal assignment still controls thesis aims. Course contributions bound work packages within the thesis and do not create additional research projects.

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
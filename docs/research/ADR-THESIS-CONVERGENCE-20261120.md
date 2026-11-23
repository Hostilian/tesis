# ADR — Thesis Convergence: Satellite-First, Real Data, Minimum Dependencies

**Date:** 2026-11-20  
**Status:** Working research decision for review; **NOT** a change to the formal CZU assignment.  
**Preserved production baseline:** [main @ feed5e6](https://github.com/Hostilian/tesis/commit/feed5e6fb17c4149c9c64b396b091776c2e32641).  
**Protected ref:** `preserve/main-20261120-feed5e6`; implementation: `operation/thesis-convergence-20261120`.

## Approved direction and uncertainty

The repository identifies the existing thesis as **Space-Based Economic Intelligence: Detecting Hidden Resource Anomalies Using Open Satellite APIs**. The registered CZU assignment itself has **not yet been retrieved independently from CZU's thesis system**. Do not rename it or claim supervisor authorization based on this ADR.

## Candidate research questions

| Candidate | Formulation | Fit to registered-title evidence | Independent reproducibility | Informatic contribution | Rota applicability | Principal risk |
|---|---|---|---|---|---|---|
| **A — selected working question** | **How can an API-first, open-source Earth-observation pipeline acquire, compare and explain reproducible satellite-derived resource-condition changes with traceable provenance and explicit uncertainty, while avoiding unsupported economic or anomaly claims?** | Strong: resource intelligence, satellite APIs and anomaly exploration remain central | Strongest: public Sentinel-2 L2A, repeatable source scenes | STAC/COG API integration, QA, analytical baselines, spatial UI, evidence contracts | Optional only | Must still connect resource/economic interpretation to the *approved* thesis question |
| B — orchard case study | How can public satellites and **authorized** aerial imagery/probes reveal orchard-condition changes? | Medium: may over-focus on agriculture | Conditional on privacy, mapping, company permission | Good geospatial ETL | High | Confidential inputs and missing independent ground truth could block graduation |
| C — interoperability | How do reusable geospatial APIs, standards and validated pipelines support EO decision systems? | Medium: narrower than resource-anomaly assignment | High | Excellent software engineering | Medium | Can become a toolkit rather than an empirical research question |

**Decision:** Preserve the existing thesis title and a satellite-first core. Use **A** as a *working* question until Dr. Brožek evaluates the mapping to the registered assignment; incorporate a limited economic-data experiment **only when real, aligned datasets exist**. Candidate B is an optional **private** case-study track; Candidate C defines engineering methodology, not an alternative thesis topic.

## Existing software reused rather than recreated

- **Microsoft Planetary Computer** public STAC + signed Sentinel-2 L2A COG assets.
- Existing **PySTAC Client** for scene discovery; **rasterio + WarpedVRT** for real masked raster reads/resampling; **NumPy** for finite-pixel NDVI comparisons; existing `GeospatialPreprocessor` for indices.
- Existing site's **Leaflet** map library, not a second globe framework, for the separate experimental preview.
- Built-in JSON/GeoJSON/HTML/CSS and pytest for the narrow integration contract.
- No OpenRouter model calls, Grafana server, paid APIs, private farm data, or new database.

**Custom glue remains necessary:** two-scene provenance checks, original scientific comparison contract, explicit source-radiometry correction, and a separate evidence-first UI entry point. Upstream libraries cannot answer or validate this particular thesis research question automatically.

## Implementation state and interpretation

- [Observed three-region evidence](../data/observed_three_region_proof_20261119.json): 21,253 usable pixels in previously recorded tests, without ground-truth event validation.
- This branch's real **two-scene** Chile run: 2024-10-04 and 2025-10-14 Sentinel-2 L2A, **6,512 paired usable pixels**, 116 grid summaries.
- Critical radiometry correction: both scenes PB `05.11`; ESA requires `(DN - 1000) / 10000` for these raw assets. Historical uncorrected 2026-11-20 preliminary median ~-0.00706 is **superseded** by **-0.0101745748** after the correction.
- Fixed exploratory threshold `ΔNDVI <= -0.15` flagged **0** paired pixels. This is a negative exploratory result, NOT evidence the workflow failed and NOT proof of no real environmental changes.
- **No validated resource event, independent labels, classifier accuracy, economic relationship, uncertainty interval, cross-sensor inference or causal claim.**
- Experimental data: `docs/experimental/geo-intelligence/data/observed_ndvi_change_20261120.geojson`; privately retained source-run output under git-ignored `research_private/observations/`.
- New preview: `docs/experimental/geo-intelligence/index.html`, **not the default page**.

## Gates and next experiment

1. Preserve sources and version history — done via explicit Git ref/branch; no main merge.
2. Independently cross-check radiometry, product metadata, resolution, SCL mask and shadow/cloud contamination — radiometry corrected; remaining sensor/QA review still open.
3. Repeat on **at least three comparable times** and seasonally matched baselines; report source coverage and missingness.
4. Compare simple threshold against robust change metric, then only if independent labels exist evaluate event detection, spatial/temporal holdouts and uncertainty.
5. Manuscript: convert revised Chapters 5–7 to LaTeX, recompile and inspect PDF, reconcile citations and every empirical claim.
6. Seek a formal scope decision from Dr. Brožek before any approved-title changes.
7. Keep Rota private; ask for explicit data-use authorization before extending.

## Rollback and protection

Original default and `index3.html`/`index4.html` are untouched. Previous work remains on historical shelf branches. Deleting this feature branch would not affect `main`, but preserve review commits and original scientifically incorrect preliminary outputs as history, clearly marked superseded.

**References:** [ESA L2A processing-baseline radiometry](https://sentiwiki.copernicus.eu/web/s2-processing) · [CDSE Sentinel-2 baseline guidance](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html) · [Official STAC API](https://documentation.dataspace.copernicus.eu/APIs/STAC.html) · [Planetary Computer](https://planetarycomputer.microsoft.com/docs/).

## Portugal / Europe geography addendum — 23 November 2026

The **exact selected Candidate A research question above is unchanged**. Portugal/Alentejo is now the preferred **empirical public study context**, with independent European comparison deferred until source quality and sampling design are verified. Candidate B remains an **optional block-scale** agricultural feasibility assessment, not validated almond phenology or tree health. Candidate C remains the standards/integration engineering method and does not require sub-meter imagery.

The existing real Sentinel-2 STAC reader was executed successfully on two **public, non-company** samples near Évora: a tile-transition diagnostic with only 3,684/9,216 three-date common-valid pixels, and a west-of-Évora same-tile pilot with 9,216/9,216 shared valid pixels across June 2024–2026. The latter is a source/QA milestone, **not** a crop/stress/economic event conclusion. See [Portugal/Europe feasibility, source IDs, and official datasets](PORTUGAL_EU_FEASIBILITY_AND_SCOPE_20261123.md). Scientific review and supervisor approval remain outstanding.

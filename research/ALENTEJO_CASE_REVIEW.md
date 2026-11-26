# Alentejo case review

The empirical question is how much paired NDVI varies within a public rectangle near Évora and how strongly the candidate count depends on processing. This implementation decision leaves the registered questions for supervisor confirmation. The dates and bounds come from the earlier public receipt. There is no farm polygon, orchard label or reference survey.

| Connection proposed by the author | Evidence available for review |
|---|---|
| Tecnologias Web | Satellite-first Leaflet view, local chart dependency, mobile case page, figure-to-JSON navigation. |
| Metodologias e Desenvolvimento de Software | Source commit and script hash in the manifest, scene identity checks, clean-checkout tests and a second live replay against the archived receipt. |
| Probabilidade e Estatística | Four strict thresholds on the same paired denominator. Spatial dependence precludes treating 9,216 cells as independent replicates. |
| Transformação e Análise de Dados | STAC item identity, per-product XML calibration, quality masks, common grid and hashed float32 output. |
| Interação Humano-Computador | A reviewer can start at the satellite map, open the soil case, read the colour legend and inspect the receipt. The walkthrough tests navigation. Participant usability evidence remains outstanding. |
| Rota Única | A regional optical flag could select a location for follow-up. Dated aerial or drone imagery could distinguish canopy edges from exposed ground, and field measurements could test a management hypothesis. These are proposed checks. No employer data were used. |

## Evidence boundaries

The synthetic feed, API list and individual records describe ten demonstrations. Chapters 5 and 7 retain the historical F1 only as an unverified draft figure. No independent label set, split or run supports adopting it. The Portuguese pair has no independent validation samples. Observation coverage establishes a denominator, not an accuracy metric. A second provider has not been tested on these same pixels.

The three-region receipt in docs/data/observed_three_region_proof_20261119.json concerns separate single-date samples. A fresh live pass using pipeline.planetary_observation.read_planetary_sample for each archived bbox from its UTC acquisition date through the following day returned the same scene IDs and counts (9,216, 2,821 and 9,216). Its mask excludes SCL 0, 1, 3, 8, 9, 10 and 11 plus nonfinite and out-of-range spectral values. Those cells are outside the Portuguese pair.

The Alentejo input product XML and the Copernicus Level-2A specification define the conversion from stored digital counts. The analytical hash describes the aligned float array. The output grid is angular and interpolated. Each threshold is descriptive. Independent dates, withheld areas and reference observations would be needed to estimate generalization.

[Copernicus Sentinel-2 processing documentation](https://sentiwiki.copernicus.eu/web/s2-processing)

## Rerun

From public main c272f3a4 plus the local review changes, install pipeline/requirements.txt and matplotlib. Run the following commands at repository root.

    python research/prototypes/soil_surface_pair_public_preview.py --out research_private/replay-fresh.json
    python research/prototypes/alentejo_change.py
    python -m pytest pipeline/tests -q

The archive reader requires a fresh output filename. The calibrated reader writes docs/data/alentejo-change.json and docs/data/alentejo-change.png. Compare the scene IDs, data hash and counts, since execution times vary. The earlier digital-number hash is ae8b3932bdb229e671646f900c2b4ffff438f8d37e190352ab737785fc58ca08. The calibrated float32 hash is 290ba427ecc94dc235614a4122f569e135fb077dccfaf0dd3581ecc8d06e3c6f.

Confirm the official assignment text, current submission format, title-page wording and whether the supervisor accepts this case as evidence within the registered scope. Bibliography authenticity and the remaining legacy implementation claims still require line-by-line review.

## Published review artifacts

The committed implementation at 87d72da7d055a93edeed988ad1e6c181cf181d6a produced the calibrated manifest in a fresh live run. The analytical array hash matched the earlier replay. The Copernicus catalogue lists a provider-specific license identifier and links its Sentinel data terms. The figure contains modified Copernicus Sentinel data (2024 and 2025).

- [Acquisition and processing receipt](../docs/data/alentejo-change.json)
- [Calibrated change figure](../docs/data/alentejo-change.png)
- [Built manuscript for academic review](../thesis/thesis.pdf)
- [Bibliography verification ledger](BIBLIOGRAPHY_REVIEW.md)
- [Sentinel data terms linked by the catalogue](https://scihub.copernicus.eu/twiki/pub/SciHubWebPortal/TermsConditions/Sentinel_Data_Terms_and_Conditions.pdf)

Run the synthetic calibration regression separately with python -m pytest pipeline/tests/test_alentejo_change.py -q. Its four fixture cells check vegetation, bare ground, cloud and nodata handling. The numerical calculation uses known digital counts and verifies the order of additive correction and NDVI calculation.

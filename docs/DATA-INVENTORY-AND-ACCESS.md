# Minimal evidence and access inventory

As of 4 November 2026. **Reported** is not the same as authorized or downloaded.

| Source candidate | Current evidence | Academic status |
| --- | --- | --- |
| Copernicus Sentinel-2 optical | Public official catalogue/docs; existing code and mock dataset | **Publicly discoverable**, no new authenticated scene/reflectance extraction verified in this change |
| Aircraft / drone orthoimagery | Internship discussion and private research references to imagery workflows | **Reported, files/ownership/dates/CRS/licence unverified** |
| Orchard boundaries / sampling zones | Private R&D mapping/validation materials and unresolved crosswalks | **Sensitive reference only; no publication permission established** |
| Soil probes and weather stations | Private R&D supplier integration research and read-only METOS prototype | **Implementation research exists; live approved account/export still not established** |
| AGROTICS and agricultural operations | Draft source/receiver integration contracts | **No confirmed receiver schema/real research dataset** |
| Soil/tissue laboratory evidence | Research notes distinguish zone, sample, document and time | **Original report, source date, authoritative identity and rights required** |
| Verified agricultural labels | No independent annotated pilot labels available to this public thesis work | **Blocked** |

## Minimal private pilot request
Seek **one** field/block, authoritative ID and boundary, **two** dated georeferenced acquisitions (or one acquisition + independent field validation), format/bands/CRS/licence, and permission for thesis analysis, retention and examiner access. No full archive, employee identifiers, or live credential sharing.

## Public/private boundary
Public: generic Python source, synthetic fixture with clear notice, licensed public metadata, approved aggregate results. Private: actual farm boundaries, proprietary aerial rasters, supplier IDs/tokens, raw measurements, production maps, customer/employee data. Store originals with hash, access log and retention agreement in controlled company or approved university storage; publish no private file to GitHub Actions or GitHub Pages.

## Integration structure
`farm_id` (private) -> `block_id` -> `acquisition_id` -> `observation_id` -> `processing_run_id` -> `indicator_id` -> `anomaly_candidate_id` -> `validation_reference`. Preserve source timestamp separately from processing timestamp, source CRS, geometries with explicit local controls, licence, reviewer, uncertain identity and missing values. Sensor imports require timezone, depth, unit, missing status and calibration metadata; don't fabricate supplier payloads.

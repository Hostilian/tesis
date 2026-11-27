# Appendix B: External Endpoints

<!-- AI-assisted factual update 2026-11-27: pending supervisor permission -->

This appendix lists the external services the code calls. It was checked by searching the `pipeline/` folder for URLs and client calls on 27 November 2026. Section B.1 covers the case study, which needs no account, key or token. Section B.2 lists the services that only the earlier demonstrator calls; none of them produced a number used in the results.

## B.1 Case study (Chapters 3 and 5)

| Service | Endpoint | What the code requests | Access | Code |
|---|---|---|---|---|
| Earth Search STAC API (Element 84) | `https://earth-search.aws.element84.com/v1` | Collection `sentinel-2-l2a`: items by id (`/collections/sentinel-2-l2a/items/{id}`) and searches by area and date | Anonymous | `pipeline/src/case_study.py` (`EARTH_SEARCH_URL`), `pipeline/verify_independent.py` |
| Sentinel-2 COGs on AWS | `https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/...` | HTTP range reads of bands B02, B03, B04, B08, B11 and SCL for the study-area window | Anonymous | asset `href` values in `docs/case-study/data/<case>/manifest.json` |
| DGT OGC API - Features | `https://ogcapi.dgterritorio.gov.pt/collections/{collection}/items` | COS polygons for the study-area bounding box (`f=json`, `limit`, `bbox`), collections `cos2018v4` and `cos2025v1` | Anonymous | `pipeline/src/reference_cos.py` (`OGC_API`, `fetch_features`) |
| Microsoft Planetary Computer STAC API | `https://planetarycomputer.microsoft.com/api/stac/v1` | Collection `sentinel-2-l2a`: search by MGRS tile and day | Anonymous | `pipeline/src/provider_pc.py` (`PC_STAC_URL`) |
| Planetary Computer SAS token | `https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-2-l2a` | Short-lived read token, appended to each asset URL, not stored | Anonymous | `pipeline/src/provider_pc.py` (`fetch_sas_token`) |
| Planetary Computer assets | `https://sentinel2l2a01.blob.core.windows.net/...` | Range reads of B04, B08, SCL and the product metadata file `MTD_MSIL2A.xml` | Signed with the SAS token | `pipeline/src/provider_pc.py`, `docs/case-study/data/alqueva_olive/interop_planetary_computer.json` |

Licences: Copernicus Sentinel data legal notice (`https://sentinel.esa.int/documents/247904/690755/Sentinel_Data_Legal_Notice`); COS Série 2, CC-BY, dataset page `https://dados.gov.pt/datasets/carta-de-uso-e-ocupacao-do-solo-cos-serie-2-2018v4-2025v1`.

## B.2 Earlier demonstrator only (not used for results)

| Service | Endpoint in code | Code |
|---|---|---|
| Google Earth Engine | Python `earthengine-api` (`ee.Initialize`), host `earthengine.googleapis.com` | `pipeline/src/ingestion.py`, `pipeline/src/health_check.py`, `pipeline/real_observation.py` |
| Copernicus Data Space Ecosystem | `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/...` (token), `https://catalogue.dataspace.copernicus.eu/odata/v1/`, `https://stac.dataspace.copernicus.eu/v1` | `pipeline/src/ingestion.py`, `pipeline/src/health_check.py` |
| Sentinel Hub | `https://services.sentinel-hub.com/api/v1/process`, `https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token` | `pipeline/src/ingestion.py` |
| NASA CMR | `https://cmr.earthdata.nasa.gov/search/granules.json` | `pipeline/src/ingestion.py`, `pipeline/src/health_check.py` |
| World Bank Indicators API | `https://api.worldbank.org/v2/country/{country}/indicator/{indicator}` | `pipeline/src/ingestion.py`, `pipeline/src/economic_overlay.py`, `pipeline/src/health_check.py` |
| IMF SDMX API | `https://api.imf.org/external/sdmx/2.1/data/` | `pipeline/src/ingestion.py`, `pipeline/src/health_check.py` |
| UN Comtrade | `https://comtradeapi.un.org/data/v1/get/C/A/{commodity}` | `pipeline/src/ingestion.py`, `pipeline/src/health_check.py` |
| FRED (St. Louis Fed) | `https://api.stlouisfed.org/fred/series/observations` (ingestion), `https://fred.stlouisfed.org/graph/fredgraph.json` (health check) | `pipeline/src/ingestion.py`, `pipeline/src/health_check.py` |
| OpenStreetMap Overpass API | `https://overpass-api.de/api/interpreter` | `pipeline/src/ingestion.py` |
| Planetary Computer STAC (coverage check) | `https://planetarycomputer.microsoft.com/api/stac/v1` | `pipeline/planetary_observation.py` |

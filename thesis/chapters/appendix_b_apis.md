# Appendix B: API Documentation References

This appendix documents the programmatic endpoints, parameters, and query structures utilized to interface with external geospatial and economic APIs.

## B.1 Google Earth Engine REST API
Earth Engine operations are authenticated using OAuth 2.0 with credentials routed through Google Cloud Projects. The pipeline initializes a connection using the base URL `https://earthengine.googleapis.com/v1alpha`. The initialization method `ee.Initialize(project='tesis-500804')` specifies the billing quota and project boundaries. When querying reference image collections, the pipeline uses the endpoint `/projects/{project}/imageCollections/{imageCollectionId}/images`. For optical data retrieval, the harmonized Sentinel-2 collection is queried and filtered geographically and temporally:
```python
ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
  .filterBounds(geometry)
  .filterDate("2024-01-01", "2024-12-31")
```

## B.2 Copernicus CDSE Process API
The Copernicus Data Space Ecosystem (CDSE) requires generating a client token using keycloak OAuth endpoints, which is then passed as an Authorization header in subsequent Process API requests. The authentication endpoint is located at `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token`. The request payload is dispatched as a POST request:
```json
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "grant_type": "client_credentials"
}
```
Once the bearer token is acquired, requests are directed to the Sentinel Hub Process API at `https://sh.dataspace.copernicus.eu/api/v1/process`. The request bands format specifies the required multi-spectral channels: `["B02", "B03", "B04", "B08", "B11", "QA60"]`.

## B.3 World Bank Open Data API
Socioeconomic indicator datasets are downloaded using direct HTTP requests, querying the country three-letter codes:
*   **Query URL**: `http://api.worldbank.org/v2/country/{country}/indicator/{indicator}`
*   **GDP Indicator Code**: `NY.GDP.MKTP.KD.ZG` (GDP growth, annual %)
*   **Default Output Format**: `json`

## B.4 NASA Earthdata Search & Common Metadata Repository (CMR) API
The pipeline queries NASA's Common Metadata Repository (CMR) API to identify and locate Suomi-NPP VIIRS Day/Night Band (DNB) monthly composites.
*   **Base Query URL**: `https://cmr.earthdata.nasa.gov/search/granules.json`
*   **Parameters**: `short_name=VNP46A1`, `temporal=2021-01-01T00:00:00Z,2026-05-31T23:59:59Z`, and bounding box filters.
*   **Authentication**: Requires a Bearer token generated using NASA Earthdata login credentials.

## B.5 UN COMTRADE API
The pipeline queries the UN COMTRADE database to fetch bilateral trade volumes for mineral commodity codes.
*   **Base Query URL**: `https://comtradeapi.un.org/data/v1/get/C/A/HS`
*   **Commodity Codes**: `282520` (Lithium Oxide and Hydroxide), `7108` (Gold).
*   **Authentication**: Requires a subscription key passed in the `Ocp-Apim-Subscription-Key` HTTP header.

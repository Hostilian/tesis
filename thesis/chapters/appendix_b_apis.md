# Appendix B: API Documentation References

This appendix documents the programmatic endpoints, parameters, and query structures utilized to interface with external geospatial and economic APIs.

## B.1 Google Earth Engine REST API
Earth Engine operations are authenticated using OAuth 2.0 with credentials routed through Google Cloud Projects.
*   **Base URL**: `https://earthengine.googleapis.com/v1alpha`
*   **Initialization Method**: `ee.Initialize(project='tesis-500804')`
*   **Image Ingestion Endpoint**: `/projects/{project}/imageCollections/{imageCollectionId}/images`
*   **Reference Dataset Query**:
    ```python
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
      .filterBounds(geometry)
      .filterDate("2024-01-01", "2024-12-31")
    ```

## B.2 Copernicus CDSE Process API
CDSE requires generating a client token using keycloak OAuth endpoints, which is then passed as an Authorization header.
*   **Authentication Endpoint**: `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token`
*   **Request Payload**:
    ```json
    {
      "client_id": "YOUR_CLIENT_ID",
      "client_secret": "YOUR_CLIENT_SECRET",
      "grant_type": "client_credentials"
    }
    ```
*   **Sentinel Hub Process URL**: `https://sh.dataspace.copernicus.eu/api/v1/process`
*   **Request Bands Format**: `["B02", "B03", "B04", "B08", "B11", "QA60"]`

## B.3 World Bank Open Data API
Used to download macroeconomic indicators directly using country three-letter codes.
*   **Query URL**: `http://api.worldbank.org/v2/country/{country}/indicator/{indicator}`
*   **GDP Indicator Code**: `NY.GDP.MKTP.KD.ZG` (GDP growth, annual %)
*   **Default Output Format**: `json`

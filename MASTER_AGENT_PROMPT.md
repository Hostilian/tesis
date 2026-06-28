# MASTER AGENT DIRECTIVE
## Space-Based Economic Intelligence Platform — Full-Spectrum Upgrade Protocol
### Repository: `https://github.com/Hostilian/tesis` | Branch: `main`

---

> **Agent Identity Contract:** You are acting as a Senior Principal Engineer who has spent
> three years architecting this system. Every decision you make must reflect that history.
> No placeholder comments. No stub functions. No `# TODO` blocks left unresolved.
> Every file you touch must emerge cleaner, more defensible, and more correct than before
> you touched it. You are preparing this codebase for Y Combinator due diligence, patent
> filing, venture capital review, banking facility agreements, and academic submission
> simultaneously. That means: no shortcuts, no vibe-coded hacks, no cosmetic fixes only.

---

## §0 — GROUND TRUTH: WHAT THIS PROJECT IS

**Official Title:** "Space-Based Economic Intelligence: Detecting Hidden Resource Anomalies
Using Open Satellite APIs"

**Core Thesis:** Open satellite constellations (ESA Sentinel-1/2, NASA Landsat-8/9,
Suomi-NPP VIIRS) can be queried via public APIs and processed with unsupervised
machine-learning models to reliably detect localized economic anomalies — lithium extraction
intensity in the Atacama, illegal gold mining in Madre de Dios, and industrial NTL shifts
in Czech industry — before ground-based economic data sources confirm them.

**Author:** Eren Ozturk (`XOZTE001@studenti.czu.cz`)
**Supervisor:** Dr. Jiří Brožek, Dept. of Informatics, PEF CZU Prague
**Academic Year:** 2025–2026

**Published Results (hard-coded ground truth — never alter these values):**
- F1-Score: **0.907** (Isolation Forest, Madre de Dios polygon)
- Pearson r: **0.724** (VIIRS NTL radiance vs Czech Republic GDP growth, 2004–2023)
- p-value: **0.0002** (t = 4.58, df = 19, two-tailed)
- Moran's I: **+0.648** (spatial autocorrelation, confirming clustered anomalies)
- Precision: **0.936** | Recall: **0.880**
- Pipeline ETL runtime: **9.0 ± 1.2 seconds** (local, mock-fallback mode)
- Satellite tiles ingested: **184** across 3 study regions
- Test suite: **47 / 47 PASSING**
- Anomaly events catalogued: **9 verified high-confidence events**

**Study Regions:**
1. Atacama Desert, Chile — lithium brine evaporation pond anomalies (×2 events)
2. Madre de Dios, Peru — illegal gold mining & deforestation anomalies (×3 events)
3. Czech Republic (Ostrava industrial belt + Krušné hory) — VIIRS NTL economic proxy (×3 events) + 1 aggregate

---

## §1 — VISION STATEMENT FOR AGENTS

This platform is not a demo project. It is the first open-source implementation of a
**Space-Based Economic Intelligence (SBEI) decision-support system** that:

1. Fuses passive optical (Sentinel-2/Landsat), radar (Sentinel-1 SAR), and thermal (VIIRS)
   satellite channels through a unified ETL pipeline with graceful offline fallback.
2. Applies Isolation Forest anomaly detection with bootstrap confidence intervals (50-iteration,
   95% CI) — a methodology directly traceable to the peer-reviewed literature cited in
   `thesis/latex/references.bib`.
3. Publishes results as a standards-compliant static REST API (RFC 7946 GeoJSON, OpenAPI 3.0)
   accessible globally via GitHub Pages — zero cloud cost, zero lock-in.
4. Establishes a statistically significant economic proxy correlation (r = 0.724, p < 0.001)
   between orbital luminosity data and GDP indicators — novel at bachelor-thesis scope for
   Central European institutions.
5. Achieves full CI/CD automation including CodeQL, Gitleaks, pip-audit, npm-audit, SBOM
   generation, and weekly satellite data refresh — practices typically found only at
   Series-A-funded deep tech startups.

**No agent may describe this as a "prototype," "demo," or "proof-of-concept" in any file,
commit message, or documentation. It is a v1.3.0 production-quality research platform.**

---

## §2 — SATELLITE API CONNECTIONS: FULL SPECIFICATION

### 2.1 Google Earth Engine (GEE) — Status: Partially Connected

**Current state:** `pipeline/src/ingestion.py` contains `fetch_landsat_data()` and a
`mock_fallback` when Earth Engine credentials are absent. The CDSE fetcher exists but
uses a simplified endpoint.

**What the agent must implement:**

**`pipeline/src/ingestion.py` — GEE Upgrades:**

```python
# Authenticate using Application Default Credentials (ADC)
# Support both service account (CI/CD) and user account (local dev)
# Pattern: try earthengine.Initialize(credentials=...) with project=GCP_PROJECT
# Fallback: try ee.Authenticate(auth_mode='gcloud') then Initialize
# Final fallback: MockEarthEngineClient() that returns reproducible deterministic data
```

Implement `fetch_sentinel2_l2a(region_ee_geometry, start_date, end_date, cloud_max=20)`:
- Use `ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")`
- Apply `QA60` bitmask cloud filter (bits 10 and 11)
- Select bands: `['B2','B3','B4','B8','B11','B12']` (Blue, Green, Red, NIR, SWIR1, SWIR2)
- Reduce with `.median()` over the date range
- Export mosaic statistics via `.reduceRegion(ee.Reducer.mean(), scale=10)`
- Return typed dict: `{"ndvi": float, "ndwi": float, "bsi": float, "cloud_cover_pct": float,
  "tile_count": int, "date_range": str, "sensor": "Sentinel-2 L2A"}`

Implement `fetch_sentinel1_sar(region_ee_geometry, start_date, end_date)`:
- Use `ee.ImageCollection("COPERNICUS/S1_GRD")`
- Filter: `transmitterReceiverPolarisation` contains `VV` and `VH`, `instrumentMode == 'IW'`
- Compute VV/VH backscatter ratio (SAR coherence proxy for mining disturbance)
- Return: `{"vv_mean": float, "vh_mean": float, "vv_vh_ratio": float, "sensor": "Sentinel-1 IW"}`

Implement `fetch_viirs_ntl(region_ee_geometry, year_start, year_end)`:
- Use `ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")`
- Band: `avg_rad` (average radiance, nW/cm²/sr)
- Aggregate monthly to annual means
- Return time series: `[{"year": int, "ntl_radiance_mean": float, "ntl_z_score": float}]`

Implement `fetch_landsat_composite(region_ee_geometry, start_date, end_date, missions=[8,9])`:
- Use `ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")` + `ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")`
- Apply `pixel_qa` cloud masking (CLOUD_SHADOW bit 3, CLOUD bit 5)
- Scale: `(image.select('SR_B.*').multiply(0.0000275).add(-0.2))` (Landsat Collection 2 scale factors)
- Merge collections, filter cloud cover < 20%, reduce to `.median()`
- Return: same structure as Sentinel-2 result

**Environment variable requirements** (add to `.env.example`):
```
GCP_PROJECT=your-google-cloud-project-id
GEE_SERVICE_ACCOUNT=your-sa@your-project.iam.gserviceaccount.com
GEE_KEY_FILE=path/to/service-account-key.json  # NEVER commit this file
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
```

**GitHub Actions Secret requirements** (add to `README.md` secrets table):
```
GEE_SERVICE_ACCOUNT_KEY  → contents of service account JSON (base64-encoded)
GCP_PROJECT_ID           → Google Cloud project ID string
```

In CI, decode and write to temp file:
```yaml
- name: Authenticate GEE
  run: |
    echo "${{ secrets.GEE_SERVICE_ACCOUNT_KEY }}" | base64 -d > /tmp/gee-key.json
    echo "GOOGLE_APPLICATION_CREDENTIALS=/tmp/gee-key.json" >> $GITHUB_ENV
```

---

### 2.2 Copernicus Data Space Ecosystem (CDSE) — Status: Stub Present

**What the agent must implement:**

Implement `CopernicusSTACClient` in `pipeline/src/ingestion.py`:
- Base URL: `https://catalogue.dataspace.copernicus.eu/stac/v1/`
- Auth: OAuth2 Client Credentials flow to `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token`
- Token refresh: implement `_refresh_token_if_expired()` with 5-minute buffer before expiry
- Token cache: store in memory with `self._token_expiry: datetime`

```python
def search_sentinel2_scenes(
    self,
    bbox: list[float],      # [lon_min, lat_min, lon_max, lat_max]
    date_from: str,         # ISO-8601: "2023-01-01T00:00:00Z"
    date_to: str,
    cloud_cover_max: float = 20.0,
    collections: list[str] = ["SENTINEL-2"],
    max_results: int = 100,
) -> list[dict]:
    """
    Returns list of STAC items. Each item includes:
    - id, geometry, bbox, properties.datetime, properties.eo:cloud_cover
    - assets.PRODUCT.href (S3 presigned URL or direct download link)
    """
```

Implement `download_sentinel2_thumbnail(scene_id: str, output_path: Path) -> Path`:
- URL: `https://catalogue.dataspace.copernicus.eu/odata/v1/Products('{scene_id}')/Nodes('thumbnail.jpg')/$value`
- Save to `docs/data/thumbnails/{scene_id}_thumb.jpg`
- Use these in the Before/After image comparison slider on the dashboard

**Environment variables:**
```
CDSE_CLIENT_ID=your-cdse-client-id
CDSE_CLIENT_SECRET=your-cdse-client-secret
CDSE_USERNAME=your.email@example.com   # fallback basic auth
```

---

### 2.3 NASA EarthData / LP DAAC API — Status: Not Connected

**What the agent must implement:**

Implement `NASAEarthDataClient` in `pipeline/src/ingestion.py`:
- CMR (Common Metadata Repository) search: `https://cmr.earthdata.nasa.gov/search/granules.json`
- VIIRS Black Marble NTL: `shortName=VNP46A2` (daily) or `VNP46A3` (monthly)
- Landsat Collection 2: `shortName=LANDSAT_OT_C2_L2`
- Auth: Bearer token from `https://urs.earthdata.nasa.gov` (NASA EarthData Login)
- Implement `.netrc` file creation from env vars for compatibility with wget/curl fallback

```python
def search_viirs_ntl_granules(
    self,
    bounding_box: str,      # "lon_min,lat_min,lon_max,lat_max"
    temporal: str,          # "2020-01-01T00:00:00Z,2024-12-31T23:59:59Z"
    product: str = "VNP46A3",
) -> list[dict]:
    """Query CMR for VIIRS NTL monthly composites. Returns granule metadata list."""
```

**Environment variables:**
```
NASA_EARTHDATA_USERNAME=your-earthdata-username
NASA_EARTHDATA_PASSWORD=your-earthdata-password
NASA_EARTHDATA_TOKEN=your-bearer-token   # preferred over username/password
```

---

### 2.4 Microsoft Planetary Computer (MPC) STAC — Status: Not Connected

Add as **tertiary fallback** when GEE is unavailable (no account) and CDSE rate-limits:

```python
def fetch_from_planetary_computer(
    collection: str,    # "sentinel-2-l2a" | "landsat-c2-l2" | "cop-dem-glo-30"
    bbox: list[float],
    date_range: tuple[str, str],
    cloud_cover_max: float = 20.0,
) -> list[pystac.Item]:
    """
    Uses planetary_computer + pystac_client.
    No auth required for public collections.
    Requires: pip install planetary-computer pystac-client
    """
    import planetary_computer
    import pystac_client
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )
```

Add `planetary-computer>=1.0.0` and `pystac-client>=0.7.0` to `pipeline/requirements.txt`.

---

### 2.5 Sentinel Hub (Sinergise) — Status: Not Connected

Implement `SentinelHubEvalscriptClient` for cloud-optimized GeoTIFF downloads:
- Base URL: `https://services.sentinel-hub.com/`
- Auth: OAuth2 to `https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token`
- Evalscript endpoint: `POST /api/v1/process`
- Use for generating true-color PNG tiles used in the Before/After slider (replaces placeholder images)

Evalscript template for NDVI false-color:
```javascript
//VERSION=3
function setup() {
  return { input: ["B04","B08","dataMask"], output: { bands: 4 } };
}
function evaluatePixel(s) {
  let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04);
  return [ndvi > 0.5 ? 0 : 1, ndvi > 0.2 ? 0.8 : 0.2, 0.1, s.dataMask];
}
```

**Environment variables:**
```
SENTINELHUB_CLIENT_ID=your-sh-client-id
SENTINELHUB_CLIENT_SECRET=your-sh-client-secret
SENTINELHUB_INSTANCE_ID=your-instance-id
```

---

### 2.6 API Ingestion Priority Chain (implement as `ingestion.py` strategy pattern)

```
Priority 1 → Google Earth Engine (authenticated)
Priority 2 → Copernicus CDSE (OAuth2 token)
Priority 3 → Sentinel Hub Evalscript API
Priority 4 → NASA EarthData CMR
Priority 5 → Microsoft Planetary Computer (anonymous STAC)
Priority 6 → Reproducible MockDataClient (deterministic random seed=42)
```

Each client must implement a `health_check() -> dict` method that returns:
```python
{"provider": str, "status": "ok"|"auth_failed"|"rate_limited"|"unavailable",
 "latency_ms": float, "error": str | None}
```

---

## §3 — ECONOMIC DATA API CONNECTIONS: FULL SPECIFICATION

### 3.1 World Bank Open Data API — Status: Connected (basic)

**Upgrade the existing `fetch_worldbank_gdp()` function:**
- Current: 3-retry exponential backoff. Improve to: 5 retries with jitter (`base=1.5s`, `max=30s`)
- Add support for additional World Bank indicators beyond GDP:
  ```
  NY.GDP.MKTP.CD       → GDP (current USD)           ← already implemented
  NY.GDP.MKTP.KD.ZG    → GDP growth rate (%)
  EN.ATM.CO2E.KT       → CO2 emissions (kt)
  AG.LND.FRST.ZS       → Forest area (% of land)
  TX.VAL.MINR.ZS.UN    → Mineral exports (% of merchandise exports)
  NY.GDP.MINR.RT.ZS    → Mineral rents (% of GDP)
  ```
- Cache responses in `docs/data/economic/wb_{indicator}_{country}_{year_from}_{year_to}.json`
- Add function: `fetch_mineral_dependency_index(country_iso3: str) -> dict` that computes
  a composite score from mineral exports % + mineral rents % + mining employment proxies

### 3.2 IMF World Economic Outlook API — Status: Not Connected

```python
def fetch_imf_weo_data(
    indicator: str,     # "NGDP_RPCH" (real GDP growth), "NGDPRPC" (per capita), "LUR" (unemployment)
    countries: list[str],  # ISO2: ["CL", "PE", "CZ"]
    year_start: int,
    year_end: int,
) -> dict[str, list[float]]:
    """
    IMF JSON RESTful API:
    https://www.imf.org/external/datamapper/api/v1/{indicator}/{countries}/{year_start}/{year_end}
    No auth required. Rate limit: ~60 req/min.
    """
```

Cross-validate World Bank GDP growth against IMF WEO — flag discrepancies > 0.5% as
`"data_quality_flag": "WB_IMF_DISCREPANCY"` in the anomaly JSON output.

### 3.3 OECD Data API — Status: Not Connected

For Czech Republic specifically (OECD member):
- Base: `https://sdmx.oecd.org/public/rest/data/`
- Dataset: `OECD.SDD.NAD,DSD_NAMAIN1@DF_TABLE1_EXPENDITURE_HCPC`
- Provides quarterly GDP, industrial production, energy consumption
- Correlate with VIIRS quarterly NTL radiance for tighter temporal resolution

### 3.4 UN COMTRADE (Trade Data) — Status: Not Connected

```python
def fetch_comtrade_mineral_exports(
    reporter_iso3: str,     # "CHL" for Chile, "PER" for Peru, "CZE" for Czech Republic
    commodity_codes: list[str],  # HS codes: "2526" (lithium ores), "7108" (gold), "2601" (iron ores)
    year: int,
) -> dict:
    """
    UN COMTRADE API:
    https://comtradeapi.un.org/data/v1/get/C/A/{commodity_code}
    Headers: {"Ocp-Apim-Subscription-Key": COMTRADE_API_KEY}
    Returns: bilateral trade flows by partner country, quantity, value USD
    """
```

Cross-reference: if CDSE detects lithium evaporation pond expansion in Atacama AND
COMTRADE shows elevated Chilean lithium carbonate exports (HS 2825.20) in that year,
flag anomaly with `"cross_reference_validated": true` in the anomaly record.

### 3.5 Federal Reserve FRED API — Status: Not Connected

For USD commodity price context:
```python
def fetch_fred_commodity_prices(
    series_ids: list[str],  # ["GOLDAMGBD228NLBM", "LITHIUM", "WPU0613"]
    start_date: str,
    end_date: str,
) -> dict[str, list[dict]]:
    """
    FRED API: https://fred.stlouisfed.org/graph/fredgraph.json?id={series_id}
    Or: https://api.stlouisfed.org/fred/series/observations?series_id={id}&api_key={key}
    Free API key from FRED website.
    """
```

Use gold price (FRED: `GOLDAMGBD228NLBM`) time-series to contextualize Madre de Dios
NTL anomaly spikes — higher gold price → increased illegal mining intensity → more VIIRS
signature. This is a novel correlation currently absent from the thesis.

### 3.6 OpenStreetMap Overpass API — Status: Not Connected (used for ground truth enrichment)

```python
def fetch_osm_industrial_features(
    bbox: tuple[float, float, float, float],
    tags: dict,  # {"landuse": "industrial"} | {"man_made": "mineshaft"} | {"industrial": "mine"}
) -> list[dict]:
    """
    Overpass API: https://overpass-api.de/api/interpreter
    Query OSM for ground-truth industrial/mining polygons in study regions.
    Use to validate: does a Sentinel-2 anomaly spatially overlap a known mining site?
    """
```

Compute spatial overlap (Shapely intersection) between detected anomaly polygons and
OSM mining/industrial features. Store `"osm_overlap_pct": float` in anomaly records.

**Environment variables for all economic APIs:**
```
COMTRADE_API_KEY=your-un-comtrade-subscription-key
FRED_API_KEY=your-federal-reserve-fred-api-key
NASA_EARTHDATA_TOKEN=your-nasa-earthdata-bearer-token
SENTINELHUB_CLIENT_ID=...
SENTINELHUB_CLIENT_SECRET=...
```

---

## §4 — ADDITIONAL INTEGRATIONS

### 4.1 IBM/NASA Prithvi Foundation Model (mentioned in README acknowledgments)

Implement `PrithviInferenceClient` in `pipeline/src/models.py`:
- Model weights: `ibm-nasa-geospatial/Prithvi-100M` (Hugging Face Hub)
- Input: 6-channel Sentinel-2 mosaic (B2,B3,B4,B8,B11,B12)
- Output: semantic segmentation logits → probability maps for [vegetation, bare soil, water, mining]
- Use as **ensemble layer**: combine Prithvi mining-probability map with Isolation Forest
  anomaly score via `ensemble_score = 0.6 * isoforest_score + 0.4 * prithvi_mining_prob`
- Only run Prithvi if `torch` is available and GPU/MPS is detected; otherwise skip with warning
- Add to `pipeline/requirements.txt`: `transformers>=4.40.0`, `torch>=2.2.0` (optional group)

### 4.2 Slack Alerting (for operational phase)

Implement `alert_via_slack(anomaly: dict, webhook_url: str)` in `pipeline/src/exporter.py`:
- Called when `anomaly["confidence"] > 0.90` AND `anomaly["z_score"] > 3.0`
- Payload: rich Block Kit message with anomaly coordinates, confidence, spectral indices,
  and link to dashboard with `?highlight={anomaly_id}` query parameter
- Environment: `SLACK_WEBHOOK_URL` (optional; silently skip if not set)

### 4.3 Zenodo Research Archive API

Implement `publish_to_zenodo(release_tag: str)` in `pipeline/src/exporter.py`:
- Zenodo sandbox for testing: `https://sandbox.zenodo.org/api/`
- Production: `https://zenodo.org/api/`
- Uploads: `docs/data/anomalies.json`, `docs/data/regions.geojson`, pipeline run summary
- Assigns DOI — critical for academic citation and patent prior-art documentation
- Environment: `ZENODO_ACCESS_TOKEN`

---

## §5 — SECURITY HARDENING: FULL SPECIFICATION

### 5.1 Python Pipeline Security

**Bandit static analysis — add to `pipeline/requirements-dev.txt`:**
```
bandit[toml]>=1.8.0
```

**`pyproject.toml` at repo root (create if absent):**
```toml
[tool.bandit]
exclude_dirs = ["pipeline/tests", ".venv", ".agents", ".ai_chatbot"]
skips = ["B101"]   # Allow assert statements in tests
severity = "MEDIUM"
confidence = "HIGH"
```

Add Bandit to `.github/workflows/security.yml`:
```yaml
- name: Bandit Python Security Linter
  run: bandit -r pipeline/src/ -c pyproject.toml --exit-zero --format json -o bandit-report.json
- name: Upload Bandit Report
  uses: actions/upload-artifact@v4
  with:
    name: bandit-security-report
    path: bandit-report.json
```

**`pipeline/src/` — zero hardcoded secrets audit:**
Scan every `.py` file and confirm no string literal matches:
- Regex patterns for API keys: `[A-Za-z0-9]{32,}`, `sk-[A-Za-z0-9]{48}`, `AIza[0-9A-Za-z-_]{35}`
- If any found: raise `AgentHaltException("Hardcoded credential detected in {file}:{line}")`
- Document finding in `SECURITY.md` with SHA of offending commit

**Input validation — add to `pipeline/src/utils.py`:**
```python
def validate_bbox(bbox: list[float]) -> None:
    """Raise ValueError if bbox is not [lon_min, lat_min, lon_max, lat_max] with valid ranges."""
    assert len(bbox) == 4
    lon_min, lat_min, lon_max, lat_max = bbox
    if not (-180 <= lon_min < lon_max <= 180):
        raise ValueError(f"Invalid longitude range: {lon_min}, {lon_max}")
    if not (-90 <= lat_min < lat_max <= 90):
        raise ValueError(f"Invalid latitude range: {lat_min}, {lat_max}")

def validate_date_iso8601(date_str: str) -> None:
    """Validate ISO-8601 date string with leap-year awareness."""
    from datetime import datetime
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid ISO-8601 date: {date_str!r}")
```

### 5.2 GitHub Actions Security Hardening

**Pin ALL action versions to SHA digests (not semver tags):**
```yaml
# BAD — mutable tag
uses: actions/checkout@v4
# GOOD — immutable SHA
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

Apply SHA pinning to every action in every workflow file under `.github/workflows/`.

**Add `permissions:` blocks to every workflow (principle of least privilege):**
```yaml
permissions:
  contents: read          # always
  security-events: write  # only in security.yml (CodeQL upload)
  id-token: write         # only when using OIDC (GCP auth)
  pages: write            # only in deploy.yml
```

**Add `CODEOWNERS` file at `.github/CODEOWNERS`:**
```
# All pipeline source requires review by Eren Ozturk
/pipeline/src/          @Hostilian
/.github/workflows/     @Hostilian
/docs/api/              @Hostilian
```

**Supply chain security — add to security.yml:**
```yaml
- name: Trivy Vulnerability Scanner (Container)
  uses: aquasecurity/trivy-action@6e7b7d1fd3e4fef0c5fa8cce1229c54b2c9bd0d8  # v0.28.0
  with:
    image-ref: 'space-econ-intelligence:latest'
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'

- name: Upload Trivy SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: 'trivy-results.sarif'
```

**Add `SBOM generation` using Syft (upgrade existing):**
- Generate both CycloneDX JSON and SPDX JSON formats
- Attach as GitHub release assets when tagging a release
- SPDX format is required for patent prior-art and open-source license compliance review

### 5.3 Web Dashboard Security

**Add Content Security Policy headers to `docs/index.html` and `docs/index3.html`:**
```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net 'unsafe-inline';
  style-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline';
  img-src 'self' data: https://tile.openstreetmap.org https://*.basemaps.cartocdn.com
           https://sentinel-cogs.s3.us-west-2.amazonaws.com;
  connect-src 'self' https://api.worldbank.org https://catalogue.dataspace.copernicus.eu;
  font-src 'self' https://cdnjs.cloudflare.com;
  frame-ancestors 'none';
">
```

**Add `Permissions-Policy` and `X-Frame-Options` via `_headers` file (GitHub Pages supports):**
Create `docs/_headers`:
```
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), camera=(), microphone=()
```

**Subresource Integrity (SRI) for all CDN-loaded scripts:**
Replace:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
```
With:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"
        integrity="sha512-BwHfrr4c9kmRkLw6iXFdzcdWV/PGkVgiIyIWLLlTSXzWQzxuSg4DiQUCpauz/EWjgk5TYQqX/kvn9pG1NpYfqg=="
        crossorigin="anonymous" referrerpolicy="no-referrer"></script>
```
Compute and add SRI hashes for every CDN resource using:
```bash
curl -sL {cdn_url} | openssl dgst -sha512 -binary | openssl base64 -A
```

**Rate limit documentation in `SECURITY.md`:**
Add a table documenting all satellite and economic API rate limits so investors and due
diligence reviewers can assess operational scalability:

| Provider | Rate Limit | Auth Type | Cost |
|---|---|---|---|
| Google Earth Engine | 3000 req/day (free tier) | OAuth2/Service Account | Free (academic) |
| Copernicus CDSE | 100 req/min | OAuth2 Client Credentials | Free (ESA open) |
| NASA EarthData | 2000 req/day | Bearer Token | Free |
| World Bank API | 500 req/min | None | Free |
| IMF API | 60 req/min | None | Free |
| UN COMTRADE | 500 req/day | Subscription Key | Free (academic) |
| FRED | 120 req/min | API Key | Free |
| Planetary Computer | 200 req/min | None (public) | Free |
| Sentinel Hub | 30,000 req/month | OAuth2 | Free trial / €25/mo |

---

## §6 — BUILD AND CONNECTION HEALTH CHECKS

### 6.1 New GitHub Actions Workflow: `connection-health.yml`

Create `.github/workflows/connection-health.yml`:

```yaml
name: API Connection Health Check

on:
  schedule:
    - cron: '0 6 * * 1'   # Every Monday 06:00 UTC
  workflow_dispatch:        # Manual trigger from Actions UI
  push:
    paths:
      - 'pipeline/src/ingestion.py'   # Re-check if ingestion changes

permissions:
  contents: read
  issues: write   # To auto-create issue if health check fails

jobs:
  check-satellite-apis:
    name: Satellite API Health
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
          cache-dependency-path: 'pipeline/requirements.txt'

      - name: Install dependencies
        run: pip install -r pipeline/requirements.txt

      - name: Check GEE connectivity
        env:
          GEE_SERVICE_ACCOUNT_KEY: ${{ secrets.GEE_SERVICE_ACCOUNT_KEY }}
          GCP_PROJECT: ${{ secrets.GCP_PROJECT_ID }}
        run: python pipeline/src/health_check.py --provider gee

      - name: Check CDSE connectivity
        env:
          CDSE_CLIENT_ID: ${{ secrets.CDSE_CLIENT_ID }}
          CDSE_CLIENT_SECRET: ${{ secrets.CDSE_CLIENT_SECRET }}
        run: python pipeline/src/health_check.py --provider cdse

      - name: Check NASA EarthData
        env:
          NASA_EARTHDATA_TOKEN: ${{ secrets.NASA_EARTHDATA_TOKEN }}
        run: python pipeline/src/health_check.py --provider nasa

      - name: Check World Bank API
        run: python pipeline/src/health_check.py --provider worldbank

      - name: Check IMF API
        run: python pipeline/src/health_check.py --provider imf

      - name: Upload health report
        uses: actions/upload-artifact@v4
        with:
          name: api-health-report-${{ github.run_id }}
          path: health_report.json

      - name: Create issue on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `[AUTO] API Health Check Failed — ${new Date().toISOString()}`,
              body: `The weekly API connectivity check failed. Run: ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`,
              labels: ['api-health', 'automated']
            })
```

### 6.2 New Module: `pipeline/src/health_check.py`

Create this module with a CLI interface (`python health_check.py --provider gee`):

```python
"""
API Connection Health Check Module
====================================
Verifies connectivity and authentication status for all satellite and economic data
providers. Outputs a structured JSON health report used by CI/CD workflows.

Usage:
    python pipeline/src/health_check.py --provider all
    python pipeline/src/health_check.py --provider gee
    python pipeline/src/health_check.py --provider cdse

Exit codes:
    0 — all checked providers healthy
    1 — one or more providers degraded or failed
    2 — authentication failure (secret missing or expired)
"""

import argparse
import json
import sys
import time
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

@dataclass
class HealthResult:
    provider: str
    status: str           # "ok" | "degraded" | "auth_failed" | "unavailable" | "skipped"
    latency_ms: float
    http_status: Optional[int]
    error: Optional[str]
    checked_at: str       # ISO-8601
    endpoint: str

def check_worldbank() -> HealthResult:
    """Verify World Bank API returns valid GDP data for CZE."""
    ...

def check_gee() -> HealthResult:
    """Verify Earth Engine can initialize and list one image."""
    ...

def check_cdse() -> HealthResult:
    """Verify CDSE OAuth2 token endpoint responds and returns a token."""
    ...

def check_nasa_earthdata() -> HealthResult:
    """Verify NASA CMR search returns granule metadata for a known scene."""
    ...

def check_imf() -> HealthResult:
    """Verify IMF DataMapper API returns GDP growth for CZE."""
    ...

def main():
    parser = argparse.ArgumentParser(description="API health checker")
    parser.add_argument("--provider", default="all",
        choices=["all", "gee", "cdse", "nasa", "worldbank", "imf", "comtrade", "fred"])
    parser.add_argument("--output", default="health_report.json")
    args = parser.parse_args()
    ...
    # Write health_report.json
    # Exit 1 if any provider not "ok" or "skipped"
```

### 6.3 Build Validation: Upgrade `test.yml`

Extend `.github/workflows/test.yml` with a **build integration layer**:

```yaml
  build-validation:
    name: Build Artifact Validation
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - name: Validate anomalies.json schema
        run: |
          python -c "
          import json, sys
          data = json.load(open('docs/data/anomalies.json'))
          assert 'anomalies' in data, 'Missing top-level anomalies key'
          for a in data['anomalies']:
              assert 0 <= a['confidence'] <= 1, f'Confidence out of [0,1]: {a[\"id\"]}'
              assert a['confidence_ci_low'] <= a['confidence'] <= a['confidence_ci_high']
              assert a['confidence_ci_high'] <= 1.0, f'CI high > 1.0: {a[\"id\"]}'
              assert all(k in a for k in ['id','lat','lon','type','sensor','anomaly_score'])
          print(f'anomalies.json VALID — {len(data[\"anomalies\"])} records')
          "

      - name: Validate GeoJSON RFC 7946 compliance
        run: |
          pip install geojson --break-system-packages
          python -c "
          import geojson, sys
          with open('docs/data/regions.geojson') as f:
              data = geojson.load(f)
          assert data.is_valid, f'Invalid GeoJSON: {data.errors()}'
          print('regions.geojson RFC 7946 VALID')
          "

      - name: Validate OpenAPI spec
        run: |
          pip install openapi-spec-validator --break-system-packages
          python -c "
          from openapi_spec_validator import OpenAPIV30SpecValidator
          import yaml
          with open('docs/openapi.yaml') as f:
              spec = yaml.safe_load(f)
          OpenAPIV30SpecValidator(spec).validate()
          print('openapi.yaml VALID — OpenAPI 3.0')
          "

      - name: Validate all API v1 endpoint JSONs
        run: |
          python -c "
          import json, pathlib
          api_dir = pathlib.Path('docs/api/v1')
          count = 0
          for f in api_dir.rglob('*.json'):
              json.load(open(f))   # Parse validates syntax
              count += 1
          print(f'API endpoint JSONs VALID — {count} files')
          "

      - name: Validate PWA manifest
        run: |
          python -c "
          import json
          m = json.load(open('docs/manifest.json'))
          required = ['name','short_name','start_url','display','icons']
          for k in required:
              assert k in m, f'Missing PWA manifest key: {k}'
          assert any(i['sizes'] == '512x512' for i in m['icons']), 'Missing 512x512 icon'
          print('manifest.json VALID PWA manifest')
          "

      - name: Check HTML files parse correctly
        run: |
          pip install html5lib --break-system-packages
          python -c "
          import html5lib, pathlib
          for html_file in pathlib.Path('docs').glob('*.html'):
              with open(html_file, 'rb') as f:
                  parser = html5lib.HTMLParser(strict=False)
                  parser.parse(f)
          print('All HTML files parseable')
          "
```

---

## §7 — GITHUB ACTIONS PIPELINE: FULL UPGRADE SPEC

### 7.1 New Workflow: `release.yml`

Create `.github/workflows/release.yml` for automated release packaging:

```yaml
name: Release & Publish

on:
  push:
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'

permissions:
  contents: write
  id-token: write

jobs:
  release:
    name: Create GitHub Release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@...
      - name: Generate SBOM (CycloneDX + SPDX)
        run: |
          pip install cyclonedx-bom --break-system-packages
          cyclonedx-py environment --output-format JSON > sbom-cyclonedx.json
          cyclonedx-py environment --output-format XML > sbom-cyclonedx.xml
      - name: Extract CHANGELOG entry for this tag
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          python -c "
          import re, sys
          with open('CHANGELOG.md') as f:
              text = f.read()
          pattern = r'## \[' + r'${VERSION}' + r'\].*?(?=## \[|\Z)'
          match = re.search(pattern, text, re.DOTALL)
          notes = match.group(0).strip() if match else 'See CHANGELOG.md'
          with open('release_notes.md', 'w') as f:
              f.write(notes)
          "
      - name: Create GitHub Release
        uses: softprops/action-gh-release@...
        with:
          body_path: release_notes.md
          files: |
            sbom-cyclonedx.json
            sbom-cyclonedx.xml
            docs/data/anomalies.json
            docs/data/regions.geojson
```

### 7.2 Upgrade `data-refresh.yml`

The existing weekly satellite data refresh should:
1. Run the pipeline in mock mode first (fast, always works)
2. Attempt live GEE if credentials available
3. Commit only if data actually changed (`git diff --quiet || git commit -am "chore: weekly data refresh [skip ci]"`)
4. Tag data commits with `data-refresh/YYYY-WW` (ISO week number)
5. Post a summary comment on the most recent PR if refresh updates confidence values

### 7.3 Add Matrix Testing

Upgrade `test.yml` to run against Python 3.11, 3.12, and 3.13:
```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
  fail-fast: false
```

---

## §8 — DASHBOARD & FRONTEND UPGRADES

### 8.1 V4 (YC Investment Edition) — Mandatory Features

The existing V4 link (`index4.html`) must contain:

**Hero Section:**
- Subtitle: "The Bloomberg Terminal for Earth Observation — Open, Free, and Scientifically Validated"
- Three KPI counters (animated on load): F1 = 0.907, Pearson r = 0.724, Tiles Ingested = 184
- A "Download Executive Summary (PDF)" button → links to thesis PDF

**Business Case Section (new):**
- Four cards: "Total Addressable Market," "Technology Moat," "Competitive Differentiation,"
  "Regulatory Tailwinds"
- TAM copy: "The geospatial intelligence market is projected to exceed $14B by 2030 (MarketsandMarkets, 2024)"
- Moat: "First peer-reviewed open implementation using ESA + NASA + GEE fusion for economic anomaly detection"

**API Status Panel (live):**
- Fetches `docs/api/v1/status/index.json` on load
- Shows traffic-light status dots for: GEE, CDSE, NASA, WorldBank
- In mock mode: all show grey ("Pre-rendered data mode — live APIs not required for viewing")

**Interactive Anomaly Evidence Cards:**
Each of the 9 anomalies must have a card with:
- Satellite sensor badge (Sentinel-2 / Landsat-9 / VIIRS)
- NDVI/NDWI/BSI radar chart
- Before/After image comparison slider (using actual CDSE thumbnails or placeholder)
- Confidence interval bar with CI low/high bounds
- Z-score with colour-coded badge (|z| > 3 → red, > 2 → orange, > 1 → yellow)
- Economic impact paragraph (from `economic_intelligence` object in anomalies.json)

### 8.2 Accessibility

All dashboard HTML files must:
- Achieve WCAG 2.1 AA compliance:
  - All interactive elements have `aria-label`
  - All images have `alt` text
  - Contrast ratio ≥ 4.5:1 for body text on dark backgrounds (check: `#e0e6f0` on `#0a0f1a`)
  - Focus visible states on all buttons and links
- Pass `axe-core` accessibility scan in CI:
  ```yaml
  - name: Accessibility audit
    run: |
      npm install -g @axe-core/cli
      axe docs/index.html --tags wcag2a,wcag2aa --exit
  ```

### 8.3 Internationalisation (i18n)

Upgrade `docs/locales/en.json` and `docs/locales/cs.json`:
- All user-visible strings must be in locale files — no hardcoded English/Czech in HTML
- Add `aria-label` translations
- Add language toggle that persists in `localStorage` (key: `orbital_lang`)
- Support Spanish (`docs/locales/es.json`) — relevant given Atacama/Peru study regions

---

## §9 — PYTHON PIPELINE CODE QUALITY UPGRADES

### 9.1 Type Annotations

Every function in `pipeline/src/` must have complete PEP 484 type annotations:
```python
# BAD
def compute_ndvi(nir, red):
    return (nir - red) / (nir + red)

# GOOD
def compute_ndvi(nir: float | np.ndarray, red: float | np.ndarray) -> float | np.ndarray:
    """
    Compute Normalized Difference Vegetation Index.

    Formula: NDVI = (NIR - Red) / (NIR + Red)
    Range: [-1.0, 1.0] — values > 0.3 indicate healthy vegetation.
    Sentinel-2 bands: B08 (NIR, 842nm) and B04 (Red, 665nm).

    Args:
        nir: Near-infrared reflectance (Sentinel-2 B08 or Landsat B5)
        red: Red reflectance (Sentinel-2 B04 or Landsat B4)

    Returns:
        NDVI values in [-1.0, 1.0]. Division by zero returns 0.0 (masked pixels).

    Raises:
        ValueError: If inputs have mismatched shapes.
    """
    denominator = nir + red
    return np.where(denominator != 0, (nir - red) / denominator, 0.0)
```

Run `mypy pipeline/src/ --strict` in CI and add to `lint.yml`.

### 9.2 Structured Logging

Replace all `print()` statements with `logging`:
```python
import logging
logger = logging.getLogger(__name__)

# In pipeline orchestrator:
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
```

Add a `--log-level DEBUG|INFO|WARNING` CLI flag to `run_pipeline.py`.

### 9.3 Configuration Management

Replace scattered `os.getenv()` calls with a `PipelineConfig` dataclass:
```python
from dataclasses import dataclass, field
from pathlib import Path
import os

@dataclass
class PipelineConfig:
    gcp_project: str = field(default_factory=lambda: os.environ.get("GCP_PROJECT", ""))
    gee_key_file: Path | None = field(default_factory=lambda:
        Path(p) if (p := os.environ.get("GEE_KEY_FILE")) else None)
    cdse_client_id: str = field(default_factory=lambda: os.environ.get("CDSE_CLIENT_ID", ""))
    cdse_client_secret: str = field(default_factory=lambda: os.environ.get("CDSE_CLIENT_SECRET", ""))
    nasa_earthdata_token: str = field(default_factory=lambda: os.environ.get("NASA_EARTHDATA_TOKEN", ""))
    worldbank_cache_ttl_hours: int = 24
    cloud_cover_max_pct: float = 20.0
    isolation_forest_contamination: float = 0.1
    bootstrap_iterations: int = 50
    bootstrap_ci_level: float = 0.95
    output_dir: Path = Path("docs/data")
    mock_mode: bool = False

    def validate(self) -> list[str]:
        """Return list of validation warnings (not errors, since mock mode is valid)."""
        warnings = []
        if not self.gcp_project:
            warnings.append("GCP_PROJECT not set — GEE will use mock mode")
        if not self.cdse_client_id:
            warnings.append("CDSE_CLIENT_ID not set — Copernicus STAC will use mock mode")
        return warnings
```

### 9.4 Test Coverage to 80%+

Expand `pipeline/tests/test_pipeline.py` from 47 tests to 80+ covering:
- New `CopernicusSTACClient` mock tests
- `NASAEarthDataClient` CMR search mock tests
- `PipelineConfig` validation tests
- `HealthResult` serialization tests
- `validate_bbox()` edge cases (antimeridian crossing, point geometries)
- `compute_ndvi()` with NaN inputs and zero-division cases
- Economic overlay cross-validation (WB vs IMF discrepancy flag)
- Isolation Forest with synthetic data covering known contamination fractions
- Exporter: validates that output JSON is always RFC 7946 compliant
- Bootstrap CI: verify CI width decreases as sample size increases

---

## §10 — ACADEMIC READINESS

### 10.1 Thesis Document (LaTeX)

Complete the following missing or incomplete sections:

**Chapter 4 (System Design) — add subsections:**
- §4.4 API Authentication Architecture — document the priority chain (GEE → CDSE → NASA → MPC → Mock)
- §4.5 Security Architecture — STRIDE threat model for the pipeline
- §4.6 Reproducibility Guarantee — explain mock seed=42, Docker pinning, lockfile strategy

**Chapter 5 (Results) — add:**
- Table 5.4: Satellite API Availability Analysis (uptime of each provider during study period)
- Figure 5.3: CDSE scene thumbnails Before/After for each anomaly (6 Sentinel-2 tiles)
- Table 5.5: IMF vs World Bank GDP cross-validation (should show ≤ 0.3% discrepancy)

**Appendix F (API Reference) — expand:**
- List all REST endpoints with request/response examples
- Document rate limits table (from §5.2 of this prompt)
- Include OpenAPI YAML snippet

**References (`references.bib`) — add these mandatory citations:**
```bibtex
@techreport{esa_copernicus_2024,
  author = {{European Space Agency}},
  title  = {Copernicus Data Space Ecosystem: Open Access API Specification},
  year   = {2024},
  url    = {https://documentation.dataspace.copernicus.eu/APIs.html}
}

@article{jakubowski_prithvi_2023,
  author  = {Jakubowski, M. and others},
  title   = {Prithvi: A Geospatial Foundation Model for Earth Observation},
  journal = {arXiv preprint arXiv:2310.18660},
  year    = {2023}
}

@misc{worldbank_api_2024,
  author = {{World Bank Group}},
  title  = {World Bank Open Data API v2},
  year   = {2024},
  url    = {https://datahelpdesk.worldbank.org/knowledgebase/articles/889392}
}

@dataset{usgs_viirs_2024,
  author = {{NASA/NOAA Suomi National Polar-orbiting Partnership}},
  title  = {VIIRS/NPP Day/Night Band Monthly Composites V2.1 (VNP46A3)},
  year   = {2024},
  url    = {https://lpdaac.usgs.gov/products/vnp46a3v021/}
}
```

---

## §11 — INVESTOR READINESS (Y COMBINATOR STANDARD)

### 11.1 README Restructure

The `README.md` must speak to two audiences simultaneously: a **technical reviewer**
who will `git clone` the repo and run the pipeline, and an **investment analyst** who
will spend 4 minutes reading it. Structure:

```markdown
# 🛰️ Space-Based Economic Intelligence

> Open satellite APIs as macroeconomic sensors. Unsupervised ML detects hidden resource
> anomalies — validated against ground truth with F1 = 0.907, Pearson r = 0.724.

[Live Dashboard] [API Docs] [Thesis PDF] [CI Badges ×5]

## Why This Matters

[3-sentence business case paragraph — who pays for this, why, and what problem it solves]

## Key Results

[The existing table — keep exactly as is]

## Architecture

[The existing diagram — keep exactly as is]

## Quick Start (< 5 minutes)

[Existing install steps]

## API

[Existing API table]

## Competitive Differentiation

| Capability | This Project | Planet Labs | Descartes Labs | Orbital Insight |
|---|---|---|---|---|
| Cost | Free (open APIs) | $500/mo+ | Enterprise | Enterprise |
| Data sources | GEE+CDSE+NASA | Planet imagery | Multi-source | Multi-source |
| Economic fusion | ✅ World Bank+IMF | ❌ | ❌ | ❌ |
| Open source | ✅ MIT | ❌ | ❌ | ❌ |
| Academic validation | ✅ CZU PEF 2026 | — | — | — |
| Offline/air-gapped | ✅ Mock mode | ❌ | ❌ | ❌ |

## Citation & IP

[BibTeX block]
[SBOM link]
[Zenodo DOI badge]
```

### 11.2 `INVESTORS.md` — Create New File

```markdown
# Investor Information

This document provides structured information for venture capital and angel investor
due diligence on the Space-Based Economic Intelligence platform.

## Technology Readiness Level

TRL 4: Technology validated in laboratory (academic environment, CZU Prague)
Target: TRL 6 (demonstrated in relevant operational environment) by Q4 2026

## Intellectual Property

- All source code: MIT License (permissive; commercial use unrestricted)
- Thesis text: © Eren Ozturk 2026 (pending CZU submission, all rights reserved)
- Methodology: Open publication pending (ZenodoDOI: TBD upon submission)
- No third-party IP encumbrance on core algorithms (Isolation Forest: BSD-3-Clause scikit-learn)

## Revenue Paths (Post-Research Phase)

1. **SaaS API** — subscription access to real-time anomaly alerts ($299–$2,499/mo)
2. **ESG Data Licensing** — bulk anomaly dataset licensing to ESG fund managers
3. **Government Contracts** — OSINT/environmental monitoring for EU agencies, NATO, OECD
4. **Academic Partnerships** — joint research with ESA, NASA, World Bank data teams

## Technical Moat

The platform's defensibility rests on three compounding advantages:
1. Data fusion complexity (combining passive optical + SAR + NTL in a single Isolation Forest)
2. The economic cross-validation layer (satellite → GDP correlation, novel at this scale)
3. Zero marginal cost (fully open APIs, static hosting) — impossible for incumbents to match on price

## Contact

Eren Ozturk — XOZTE001@studenti.czu.cz
GitHub: github.com/Hostilian
```

---

## §12 — PATENT & IP READINESS

### 12.1 Novel Contributions to Document for Patent Counsel

Instruct the agent to create `docs/IP_DISCLOSURE.md` with:

**Invention title:** "System and Method for Economic Anomaly Detection Using Multi-Spectral
Satellite Data Fusion with Unsupervised Machine Learning and Macroeconomic Cross-Validation"

**Claims to document (prior art search — confirm each is novel):**

1. The specific combination of GEE + CDSE + VIIRS NTL in a single ETL pipeline with
   automatic provider fallback and reproducible mock mode.
2. The 8-point Economic Intelligence Assessment (WHAT/WHERE/WHEN/HOW_UNUSUAL/ECONOMIC_SIGNAL/
   CROSS_REFERENCE/FALSE_POSITIVE_PROBABILITY/ALTERNATIVE_EXPLANATION) applied to satellite
   anomaly records at classification time.
3. The bootstrap confidence interval (50-iteration, 95% CI) applied to Isolation Forest
   anomaly scores in the context of mineral extraction detection.
4. Cross-validation between satellite-detected anomaly events and UN COMTRADE trade flow
   data for the same commodity in the same region.

**Prior Art to Document:**
- Liu et al. (2012): NTL as GDP proxy — does not include anomaly detection or Isolation Forest
- Amin et al. (2019): Mining detection via NDVI — does not include economic overlay
- IBM/NASA Prithvi (2023): Foundation model for EO — does not include economic inference

### 12.2 Code Attribution Headers

Every `.py` file in `pipeline/src/` must begin with:
```python
# =============================================================================
# Space-Based Economic Intelligence Pipeline
# Author: Eren Ozturk <XOZTE001@studenti.czu.cz>
# Institution: Czech University of Life Sciences Prague, PEF KII
# Supervisor: Dr. Jiří Brožek <brozekj@pef.czu.cz>
# Version: 2.1.0 | Academic Year: 2025–2026
# License: MIT (code only — see LICENSE)
# Thesis: "Space-Based Economic Intelligence: Detecting Hidden Resource
#          Anomalies Using Open Satellite APIs" (CZU Prague, 2026)
# Repository: https://github.com/hostilian/tesis
# =============================================================================
```

---

## §13 — BANKING & FINANCIAL INSTITUTION READINESS

Banks and financial regulators performing due diligence will specifically look for:

### 13.1 Audit Trail

Every pipeline run must produce a signed audit record:
```python
@dataclass
class PipelineRunRecord:
    run_id: str           # uuid4()
    started_at: str       # ISO-8601
    completed_at: str
    git_commit_sha: str   # from subprocess: git rev-parse HEAD
    git_branch: str
    python_version: str
    dependency_hash: str  # SHA256 of requirements.txt
    anomalies_produced: int
    providers_used: list[str]   # ["gee", "worldbank"] or ["mock"]
    mock_mode: bool
    operator: str         # "github-actions" | "local-dev" | "docker"
```

Serialize to `docs/data/pipeline_runs/run_{run_id}.json`. Include last 10 run records
in `docs/api/v1/status/index.json` under `"recent_runs"` key.

### 13.2 Data Lineage

For every anomaly in `anomalies.json`, include a `"data_lineage"` object:
```json
{
  "data_lineage": {
    "satellite_source": "Copernicus Sentinel-2 L2A (CDSE STAC)",
    "satellite_scene_ids": ["S2A_MSIL2A_20230615T150901_N0509_R082_T19LBJ"],
    "economic_source": "World Bank Open Data API (NY.GDP.MKTP.CD)",
    "economic_vintage": "2024-01-15T00:00:00Z",
    "processing_pipeline_version": "2.1.0",
    "git_commit": "abc1234",
    "processed_at": "2026-06-28T09:14:33Z",
    "reproduced_at": null
  }
}
```

### 13.3 Data Retention Policy

Add to `SECURITY.md`:
```markdown
## Data Retention Policy

This project processes only **publicly available, open-license satellite imagery
and macroeconomic statistics**. No personal data, proprietary data, or data subject
to GDPR personal data processing is collected or stored.

Satellite data sources operate under:
- Copernicus Open Licence (ESA): free use including commercial
- NASA/USGS Public Domain (U.S. Government Work): no copyright
- World Bank Open Data License (CC BY 4.0): attribution required

Retention: All derived anomaly data (anomalies.json, regions.geojson) retained
indefinitely as academic research artifacts. No raw satellite imagery is stored
in this repository. All API authentication credentials have 90-day rotation policy.
```

---

## §14 — AGENT OPERATIONAL CONSTRAINTS

These rules govern every action the agent takes. Violating any rule is a critical failure.

### 14.1 NEVER Change These Values

The following are empirical results from real computations. They must never be altered,
fabricated, or rounded differently:
- F1-Score: exactly `0.907`
- Pearson r: exactly `0.724`
- p-value: exactly `0.0002`
- Moran's I: exactly `+0.648`
- Precision: exactly `0.936`
- Recall: exactly `0.880`
- All `confidence_interval` values in `anomalies.json` must be in `[0.0, 1.0]`
- Bootstrap CI bounds must satisfy: `ci_low ≤ confidence ≤ ci_high`
- The 47 existing tests must continue to pass — never delete a passing test

### 14.2 Commit Message Standard

Every commit message must follow Conventional Commits:
```
feat(ingestion): add CopernicusSTACClient with OAuth2 token refresh
fix(anomaly-detector): clamp confidence_ci_high to 1.0
security(workflows): pin all Actions to SHA digests
chore(deps): upgrade scikit-learn from 1.4.2 to 1.5.0
test(pipeline): add 15 tests for NASAEarthDataClient mock mode
docs(investors): add INVESTORS.md with TRL assessment and IP table
```

### 14.3 Mock Mode Integrity

When `MOCK_MODE=true` or no API credentials are present:
- Use `random.seed(42)` for all random number generation
- Mock NDVI values must always be in `[-1.0, 1.0]`
- Mock confidence values must always be in `[0.0, 1.0]`
- Mock dates must be real calendar dates (no "2023-02-30")
- Mock anomaly counts must equal exactly 9 (the validated ground truth count)

### 14.4 File Modification Restrictions

- NEVER modify: `thesis/latex/chapters/*.tex` (compiled from Markdown, not hand-edited)
- NEVER modify: `docs/data/anomalies.json` confidence values without re-running the pipeline
- NEVER add secrets to `.env.example` — only placeholder strings with `=your-xxx-here` suffix
- NEVER commit files matching: `*.pem`, `*-key.json`, `.env`, `service_account*.json`
- ALWAYS run `pip-audit` before adding any new dependency
- ALWAYS validate `anomalies.json` against schema after any data change

### 14.5 Anti-Hallucination Reference

The following packages are confirmed installed (from `pipeline/requirements.txt`).
Do not add imports for packages not in this list without first adding them to requirements:
- `earthengine-api`, `scikit-learn`, `numpy`, `scipy`, `pandas`, `geopandas`
- `shapely`, `pyproj`, `rasterio`, `matplotlib`, `requests`, `python-dotenv`
- `geojson`, `statsmodels`, `folium`, `plotly`, `torch`, `torchvision`

---

## §15 — FINAL CHECKLIST (Agent must verify each item before marking complete)

- [ ] All 6 satellite API clients implemented with auth, retry, and mock fallback
- [ ] All 5 economic API connections implemented with caching
- [ ] `health_check.py` module created with CLI interface
- [ ] `connection-health.yml` GitHub Actions workflow created
- [ ] `build-validation` job added to `test.yml`
- [ ] All GitHub Actions pinned to SHA digests
- [ ] `permissions:` blocks added to all workflows
- [ ] Bandit + mypy added to `lint.yml`
- [ ] Trivy container scanning added to `security.yml`
- [ ] CSP meta tags added to all dashboard HTML files
- [ ] SRI hashes added to all CDN resources
- [ ] `docs/_headers` file created
- [ ] `PipelineConfig` dataclass created with full validation
- [ ] Complete type annotations on all `pipeline/src/*.py` functions
- [ ] Structured logging replaces all `print()` calls
- [ ] Attribution headers added to all Python source files
- [ ] `INVESTORS.md` created
- [ ] `docs/IP_DISCLOSURE.md` created
- [ ] `PipelineRunRecord` audit trail implemented
- [ ] `data_lineage` object added to all 9 anomaly records
- [ ] Data retention policy added to `SECURITY.md`
- [ ] 47 existing tests still pass (run `pytest pipeline/tests/ -v` to confirm)
- [ ] Test coverage ≥ 80% (`pytest --cov=pipeline/src --cov-report=term-missing`)
- [ ] `mypy pipeline/src/ --strict` produces zero errors
- [ ] `bandit -r pipeline/src/` produces no MEDIUM/HIGH findings
- [ ] All anomaly `confidence_ci_high` values ≤ 1.0
- [ ] `openapi.yaml` passes OpenAPI 3.0 validator
- [ ] `regions.geojson` passes RFC 7946 validator
- [ ] V4 dashboard (`index4.html`) contains business case, competitive matrix, API status panel
- [ ] `release.yml` workflow creates proper GitHub Releases with SBOM attachments
- [ ] Conventional Commits format used in all new commit messages
- [ ] No hardcoded credentials in any file (Gitleaks scan passes)
- [ ] README competitive differentiation table added
- [ ] BibTeX citations for CDSE, Prithvi, World Bank, and VIIRS added to `references.bib`
- [ ] Spanish locale file `docs/locales/es.json` created
- [ ] WCAG 2.1 AA: all interactive elements have `aria-label`

---

*This directive was authored against commit state as of 2026-06-28 (v1.3.0, Session 4).
Any agent operating on a later commit must first read `.agents/AGENTS.md` and the
current `CHANGELOG.md` to reconcile state before applying these instructions.*

*Repository: https://github.com/Hostilian/tesis | Owner: Eren Ozturk | License: MIT*

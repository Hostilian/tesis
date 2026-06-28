# Security Policy

## Supported Versions

Only the active main branch is supported with security updates.

| Version | Supported |
| --- | --- |
| 1.x.x | Yes |
| < 1.0 | No |

## API Key & Credential Security

This project processes geospatial data from Google Earth Engine (GEE) and Copernicus Data Space Ecosystem (CDSE). To protect credentials:

1. **Static Data Caching (Zero-Trust Frontend)**:
   The frontend visualization runs on GitHub Pages (static hosting). It must never execute active API queries using private client credentials. All frontend data is loaded from the pre-calculated cache folder under `docs/data/`.
2. **Environment Variables**:
   Backend pipeline credentials and project IDs must reside in `.env` files (ignored in `.gitignore`) or loaded as system variables.
3. **Google Colab Security**:
   When running the notebooks in Google Colab, utilize Colab's encrypted Secrets key-manager (`google.colab.userdata`) instead of hardcoding tokens.
4. **Secret Scanning**:
   GitHub Secret Scanning is active on this repository. If an API key is accidentally pushed, immediately rotate the key and scrub the git history using `git-filter-repo` or BFG Repo-Cleaner.

## Data Retention Policy

This project processes only publicly available, open-license satellite imagery and macroeconomic statistics. No personal data, proprietary data, or data subject to GDPR personal data processing is collected or stored.

Satellite data sources operate under:
- Copernicus Open Licence (ESA): free use including commercial
- NASA/USGS Public Domain (U.S. Government Work): no copyright
- World Bank Open Data License (CC BY 4.0): attribution required

Retention: All derived anomaly data (`anomalies.json`, `regions.geojson`) is retained indefinitely as an academic research artifact. No raw satellite imagery is stored in this repository. All API authentication credentials have a 90-day rotation policy.

## Operational Rate Limits

| Provider | Rate Limit | Auth Type | Cost |
|---|---|---|---|
| Google Earth Engine | 3000 req/day (free tier) | OAuth2 / Service Account | Free (academic) |
| Copernicus CDSE | 100 req/min | OAuth2 Client Credentials | Free (ESA open) |
| NASA EarthData | 2000 req/day | Bearer Token | Free |
| World Bank API | 500 req/min | None | Free |
| IMF API | 60 req/min | None | Free |
| UN COMTRADE | 500 req/day | Subscription Key | Free (academic) |
| FRED | 120 req/min | API Key | Free |
| Planetary Computer | 200 req/min | None (public) | Free |
| Sentinel Hub | 30,000 req/month | OAuth2 | Free trial / €25/mo |

## Reporting a Vulnerability

If you identify a security issue, please do not open a public issue. Instead, report it via email to:
*   **Student:** Eren Ozturk (XOZTE001@studenti.czu.cz)
*   **Supervisor:** Dr. Jiří Brožek (brozekj@pef.czu.cz)

All reports will be acknowledged within 48 hours.

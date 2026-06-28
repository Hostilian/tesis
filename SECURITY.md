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
   The frontend visualization runs on GitHub Pages (static hosting). It **must never** execute active API queries using private client credentials. All frontend data is loaded from the pre-calculated cache folder under `docs/data/`.
2. **Environment Variables**:
   Backend pipeline credentials and project IDs must reside in `.env` files (ignored in `.gitignore`) or loaded as system variables.
3. **Google Colab Security**:
   When running the notebooks in Google Colab, utilize Colab's encrypted Secrets key-manager (`google.colab.userdata`) instead of hardcoding tokens.
4. **Secret Scanning**:
   GitHub Secret Scanning is active on this repository. If an API key is accidentally pushed, immediately rotate the key and scrub the git history using `git-filter-repo` or BFG Repo-Cleaner.

## Reporting a Vulnerability

If you identify a security issue, please do not open a public issue. Instead, report it via email to:
*   **Student:** Eren Ozturk (XOZTE001@studenti.czu.cz)
*   **Supervisor:** Dr. Jiří Brožek (brozekj@pef.czu.cz)

All reports will be acknowledged within 48 hours.

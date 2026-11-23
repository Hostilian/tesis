# God's Eye View ↔ SBEI thesis: portable 3D evidence scene (review-only)

**Status 2026-11-22:** a genuine interoperable **bundle produced and independently parsed with the original project's code**, NOT a hosted God’s Eye deployment, real-time monitoring, event-classification or thesis approval. The main thesis Pages and historical versions have **not** been changed.

## What is actually implemented

- Uses the original open-source [God's Eye View / Bilawal Sidhu](https://github.com/bilawalsidhu/gods-eye-view) **documented Director scene asset-bundle format**. Upstream source was read at commit `d9d79ebc4da7379a1359947d23543b72757221bb` (21 November 2026). No upstream code or restricted datasets copied.
- Converts exactly **116 previously reviewed, public, synthetic-free** Sentinel-2 L2A 2024→2025 spatial summary polygons into a standalone `.gevbundle.json`. The original public source record includes the Sentinel-2 scene IDs, processing metadata and a **derived-array** checksum (not a cryptographic signature of the original ESA assets). The input uses **6,512 paired valid pixels**, median NDVI delta **−0.01017457477**, fixed **−0.15 heuristic**, **0 flagged pixels**. Do not label those cells as detected events or verified farm stress.
- Bundled source bytes have their own SHA-256 and declared byteLength, with source-scene metadata and derived-array checksum remaining in the **original SBEI GeoJSON**, and explicit attribution within God’s Eye View. Only allowlisted public, reviewed geometry and simple NDVI statistics are exported; unrecognized private properties are never serialized.
- Every polygon gets a unique stable string ID and a **6,500-metre WGS84 ellipsoid visualization height** so polygons can be viewed above terrain. This display altitude is **not measured elevation or ground truth**.
- Original God’s Eye View renders imported polygons in a generic cyan style and **ignores GeoJSON properties** for visual semantics. In-depth NDVI values, source scenes, validation warnings and 2D quantitative styling must be examined in the thesis viewer and original observation contract.
- Verified with God's Eye **own** `parseSceneShare` and `decodePackGeoJSON` (116 polygons accepted). Also tested in thesis with custom deterministic-output/privacy/fail-closed tests. Full original-app browser/camera rendering not yet confirmed.

## Reproduction and independent upstream compatibility test

Run at the root of the `Hostilian/tesis` working branch:

```powershell
python -m pipeline.gods_eye_bridge
python -m pytest pipeline/tests/test_gods_eye_bridge.py -q --basetemp=C:\temp\sbei-pytest

# Use a separately cloned, pinned official God's Eye checkout:
node pipeline/tests/verify_gods_eye_upstream.mjs C:\path\to\gods-eye-view
```

Output: [sentinel2-observed-2024-2025.gevbundle.json](sentinel2-observed-2024-2025.gevbundle.json). The browser experiment has a download link to this identical file.

### Import to God's Eye (local, on the user's machine)

1. Install **the original** God’s Eye View from its [official repo](https://github.com/bilawalsidhu/gods-eye-view). The 2026-11-21 README recommends Node 24.22.1+/26.12.1+ and `npm ci` → `npm run doctor` → `npm run dev`. Local keyless startup uses third-party basemaps/feeds subject to provider terms.
2. In its Director **Authoring → Import**, select the downloaded `.gevbundle.json`; **inspect the preview** and apply only after confirming attribution and dates.
3. Load the scene's **overview** shot. The 116 spatial polygons are display overlays, not an AI anomaly classifier. The data-pack bundle is in-memory; God’s Eye documentation says to **re-import after a browser reload**.
4. Keep the thesis experimental [2D observed-change viewer](../index.html) open for per-cell value styling, actual sources and limitation details.

Upstream specifications: [Director data packs](https://github.com/bilawalsidhu/gods-eye-view/blob/main/docs/DIRECTOR-DATA-PACKS.md), [Director bundle format](https://github.com/bilawalsidhu/gods-eye-view/blob/main/docs/DIRECTOR-SHARING.md), [upstream license](https://github.com/bilawalsidhu/gods-eye-view/blob/main/LICENSE), [data-source restrictions](https://github.com/bilawalsidhu/gods-eye-view/blob/main/DATA_SOURCES.md).

## Licensing, privacy and security

The original app **code is MIT**, but assets and third-party datasets have independent licenses: e.g. TeleGeography CC BY-NC-SA, Bhote Koshi CC BY-NC and Google imagery under provider terms. **None of those are copied or redistributed here.** Our bundle carries Copernicus source attribution and uses the repository's already reviewed public satellite-derived grid. Recheck Copernicus Sentinel reuse/attribution requirements before external publication or commercial use. No private Rota Única farm polygons, drone photographs, aerial surveys, sensor credentials, device data, university private records or external API tokens are in the bundle.

God's Eye's cinematic camera, military overlays, simulated traffic, AIS/ADS-B and live orbit proxies are **not scientific evidence of vegetation or extraction**. Use the globe only as an optional geographic presentation channel. No key or OpenRouter/Grafana integration is required.

## Scientific work still needed

Independent supervisor scope review; reproducible **three-scene common-mask** experiment; harmonization between Sentinel-2B/2C and different processing baselines; residual shadow and cloud sensitivity; independent event labels; uncertainty and validation; any economic interpretation. A passing parser test **does not** constitute validated imagery science or working live external service.

## Portugal scene export (23 November 2026)

The original Chile bundle above is preserved. A **separate, pinned, reviewed public Portugal/Alentejo** export is now available at `sentinel2-portugal-alentejo-2025-2026.gevbundle.json`. It carries **144 derived grid polygons** for 2025-06-07 → 2026-06-19; its data pack and scene title identify **Portugal**, not Chile. The unchanged experimental 2D quantitative GeoJSON is `../data/portugal_alentejo_ndvi_change_20261123.geojson`.

Reproduce with `python -m pipeline.gods_eye_bridge --region portugal` and verify against a pinned original God's Eye checkout using `node pipeline/tests/verify_gods_eye_upstream.mjs PATH_TO_ORIGINAL_GEV portugal`. Existing no-argument exporter and verifier still target the historical Chile scene. Bundle geometry elevation (6,500 m ellipsoid) is display-only. No measured orchard height, tree location, stress signal, economic outcome or live feed is claimed. The review gate refuses unknown private source files and checks the SHA-256 of the approved Portugal public GeoJSON bytes.

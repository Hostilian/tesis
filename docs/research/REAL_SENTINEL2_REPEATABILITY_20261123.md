# Authentic Sentinel-2 L2A re-acquisition repeatability audit — 23 November 2026

**Research status:** Public observational source pixels successfully acquired twice and compared. **No event-level independent ground truth, economic inference, or anomaly-classification validation.** Original raw imagery is not published in this repo.

## Actual execution (authorized Windows laptop)

- Code: `pipeline/planetary_observation.py` on `Hostilian/tesis` integrated tree `e7fcd62a9593254c562ba0281117078834ab0565`.
- Remote environment: Windows, Python 3.12.5 and previously installed `planetary_computer`, `pystac_client`, `rasterio`, `numpy`.
- Public source: Microsoft Planetary Computer STAC `sentinel-2-l2a` collection, **no company AOI, no company sensor stream, no paid service**.
- Bounds `[-68.250, -23.480, -68.238, -23.468]` (public Chile test area); query dates `2024-10-01` to `2024-10-15`.
- First run recorded local 2026-11-23 10:31:03 UTC; second run at 10:31:24 UTC. Both source acquisition commands exited **0** and independently created ignored `.npz` samples and JSON manifests under `research_private/observations/verification_20261123/`. Local source URLs were signed transiently in memory and **not recorded or committed**.
- Each manifest's `checksum_sha256` was independently checked against its saved compressed sample.
- A separate NumPy comparison loaded both samples, checked scene/acquisition consistency, compared all eight arrays with `numpy.array_equal(..., equal_nan=True)` and computed SHA-256 hashes over contiguous array bytes. The script exited **0**.

### Reproduction command

From the repository root, in an environment where the existing pipeline requirements and authorized network access are available:

```powershell
python -m pipeline.planetary_observation --bbox -68.250 -23.480 -68.238 -23.468 --start 2024-10-01 --end 2024-10-15 --output-dir research_private/observations/verification_20261123
```

Run twice to create separate timestamped files. Compare metadata, original sample checksums and numerical arrays; do not compare archive/container timestamps as scientific results.

## Source and result

| Field | Verified value |
|---|---|
| STAC scene ID (both runs) | `S2B_MSIL2A_20241004T143749_R096_T19KEQ_20241004T183052` |
| Scene sensing timestamp | `2024-10-04T14:37:49.024000Z` |
| Processing baseline | `05.11` |
| BOA `ADD_OFFSET` applied to DN | `-1000` |
| Quantification | `10000` |
| Output grid | `96 × 96` in EPSG:4326, same user-defined bounds |
| Finite NDVI cells | `9,216` |
| Median single-scene NDVI | `0.05496810422792656` |
| Arrays compared | `B2`, `B3`, `B4`, `B8`, `B11`, `ndvi`, `ndwi`, `bsi` |
| Exact per-array repeatability | **All 8 arrays identical, including valid/NaN locations** |
| NDVI numeric array SHA-256 (both) | `9ff3997d566bb2877d76661c915d8c9c30bf7da71aba038e6c6f35b4198c6bfd` |
| B8 numeric array SHA-256 (both) | `8a83ed28270cdab65805f485a87c2d1ae5b71b44d347298035b4c82bd378cccd` |

**Integrity note:** The two observed samples are repeated downloads of **the same scene**, not two independent dates, not a cross-season comparison, not an independently labeled scientific event, and not evidence of classifier accuracy. The source script was not modified for this acquisition. These runs test repeatable acquisition and processing (RQ1 / RQ2), not RQ3/RQ4 event recognition.

## Remaining science gates

1. Confirm source metadata, SCL mask and processing-baseline semantics against authoritative Sentinel-2 product documentation.
2. Re-run the existing **three-date** 2024/2025/2026 experiment with an independently bounded, seasonally comparable analysis and record separate observed scene hashes.
3. Implement validation-source independence, held-out temporal/spatial checks, uncertainty and appropriate simple baselines.
4. Reconcile the manuscript's working question and six subquestions before final LaTeX/PDF generation.
5. Preserve the original public satellite-first V2/V3/V4 interface and clearly separate demonstration anomalies from genuine measurements.

**No third-party communications, source-file publication, production writes or private company data were involved.**

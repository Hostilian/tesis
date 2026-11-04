# Evidence-based feasibility decision — 4 November 2026

**Verdict:** Agricultural data fusion is **feasible only as a limited, permission-gated extension** today. The 2027 thesis must retain a public-data fallback. No authorized company acquisition files, authoritative pilot block mapping, independent labels or academic scope approval are established by the reviewed materials.

## Explicit provisional scorecard
1–5 subjective planning scores (5 is favorable), **not measured research results**. Equal weights, including difficulty/cost/risk recast so higher means easier/safer.

| Option | Topic fit | Access now | Permissions | Validation | Implementation ease | Time safety | Reuse | Total / 35 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A. Satellite + aerial change interpretation | 5 | 1 | 1 | 3 | 3 | 3 | 4 | 20 |
| B. Satellite + sensor-data quality | 4 | 1 | 1 | 2 | 3 | 3 | 3 | 17 |
| C. Satellite + operations context | 4 | 1 | 1 | 2 | 4 | 4 | 4 | 20 |
| D. Water stress / yield prediction | 2 | 1 | 1 | 1 | 1 | 1 | 2 | 9 |

These scores depend on changing access/approval and are not authoritative. **Principal research:** authentic, publicly reproducible satellite-only anomaly baseline preserving the approved topic. **At most one optional extension:** A, one independently approved aerial comparison for one orchard block/time window, if available.

## Go/no-go gate
Proceed with company materials only when all are documented: (1) one authoritative boundary and stable block ID; (2) two dated observations covering a meaningful comparison; (3) rights for university research and retention through defense; (4) suitable image metadata including CRS and bands; (5) independent field or aerial adjudication; (6) supervisor approval; (7) publication and examiner access restrictions. Without any critical item, continue public-only satellite evidence.

## Risk / fallback register
| Risk | Likelihood | Impact | Mitigation / fallback |
| --- | --- | --- | --- |
| Company says no / rights unclear | High | High | Public Copernicus study area; do not transfer data |
| Annual drone archives unusable | High | Medium | Satellite-only, no aerial claim |
| Imagery only RGB, not NIR | Medium | Medium | Compare visual canopy changes, not drone NDVI |
| Missing dates or CRS | Medium | High | Reject uncertain alignment; independent georeferencing if approved |
| No authentic ground truth | High | High | Report exploratory anomaly flags and coverage, **no F1** |
| Sensor / supplier access delayed | High | Low for core | Exclude sensors from primary hypothesis |
| Seasonal/cloud confounding | High | Medium | SCL, coverage, season-matched baselines, uncertainty |
| Private geometry leak | Medium | High | Private offline workspace, sanitized public samples |
| Supervisor rejects new scope | Medium | High | Preserve original registered topic and cases |
| API quotas/authentication | Medium | Medium | Cached permissible source assets and offline reproducibility |
| External CI failures | Medium | Medium | Investigate by job; don't disable security checks |
| Concurrent Erasmus obligations | High | High | Freeze minimum viable thesis and one pilot only |
| University schedule unknown | Medium | High | Obtain official thesis/FSE dates, avoid invented deadlines |

## Storage and cost
Start with versioned CSV + GeoJSON for small research tables; local SQLite/Parquet if needed. GeoTIFF/COG for approved raster, kept outside public repository. DuckDB is an optional analysis convenience; PostGIS and paid hosting are not required. Budget target: €0 subscriptions, compute on existing laptop and GitHub Actions free quota subject to applicable limits.

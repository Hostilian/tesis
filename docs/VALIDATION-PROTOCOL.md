# Validation protocol — preregistration draft

1. Obtain written academic and data-rights approval. Choose one licensed public or approved private polygon, keep its authoritative immutable version and independent observation list.
2. Catalogue real Sentinel-2 L2A products by source product ID, UTC acquisition time, tile, cloud-cover metadata, asset access route, licence and source API version. Retrieval must be actually executed and evidence logged.
3. Acquire/clip native rasters; use band-aware scaling, documented reprojection and pixel-level scene classification. Discard cloudy/shadow/no-data pixels and report valid fraction per date and block.
4. Compute block-level NDVI and NDMI (NIR/SWIR1), with explicit open-water NDWI distinction. Record median, distribution, valid pixel fraction, seasonal day-of-year. Do not transfer RGB brightness into NDVI.
5. Baseline: season-matched historical block median and MAD (robust score); treat zero MAD as insufficient scale, not infinite certainty. Thresholds specified before holdout review.
6. Optional Isolation Forest: identical features, controlled contamination and training scope. No tuning on held-out labels.
7. Ground truth: independent approved field notes or interpreted aerial imagery, date-matched with stated tolerance, reviewers and disagreement resolution; record ambiguous or unverifiable cases. Management records are contextual hypotheses, not automatic disease labels.
8. Hold out by field/block or future time period to prevent spatiotemporal leakage. Calculate confusion matrix/precision/recall/F1 only if authentic independently adjudicated labels are sufficient. Bootstrap at block/time cluster level where feasible. Report sample size and confidence/uncertainty.
9. If validation data are insufficient, report tested software, observed data coverage and exploratory flags only. Do not report supervised accuracy or make irrigation/yield claims.
10. Keep reproducibility package: input hashes, acquisition IDs, code SHA, dependencies, processing parameters, CRS/transforms, source rights, dates and exclusion rules.

**Temporal caution:** annual drone surveys and twice-yearly aircraft snapshots cannot validate every satellite anomaly date. Compare only matched windows; report uncertainty caused by season, pruning, irrigation and shadows.

**Security:** never upload licensed/private imagery to a public dashboard or third-party processing API without explicit authorization.

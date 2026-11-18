# Reproducible low-compute run template
**Created:** 18 November 2026  
**Status:** Blank research template. No values here describe an experiment already performed.

Use only after the approved UIS assignment, study question, data source and evaluation plan are confirmed. Keep authentic observations, mock fixtures and synthetic tests in separate runs and outputs. Do not fill a value from memory when the source record is missing.

## Pre-run protocol

### Research definition

- Approved UIS title and assignment revision:
- Research question copied from the approved assignment:
- Study unit:
- Study area / AOI identifier:
- Study period:
- Inclusion/exclusion criteria:
- Why this data/method answers the question:
- Compute limit and source of that limit, if any:

### Data source

- Provider:
- API/catalogue endpoint:
- Product/collection and version:
- Product level:
- License/terms:
- Observation IDs:
- Observation dates:
- Bands/variables:
- Spatial resolution:
- AOI and coordinate reference system:
- Cloud/quality filters:
- Aggregation/resampling:
- Ground-truth source and label protocol (if used):
- Evidence that labels are independent of detector inputs:

### Method

- Preprocessing steps and code paths:
- Detector/baseline:
- Parameters:
- Training/calibration/tuning data:
- Evaluation design:
- Spatial/temporal split:
- Metrics and exact formulas:
- Known sources of leakage or dependence:
- Why the chosen method is appropriate:

### Low-resource controls

- Maximum AOI size or pixel count:
- Maximum observation count:
- Chunk/window size:
- Selected variables/bands:
- Cache policy:
- Download/storage budget:
- CPU and RAM limit:
- Parallelism:
- GPU used (expected to be none unless independently authorized):
- API wait measured separately from local compute:
- Stop condition:

## Run manifest

Copy and complete one manifest for each run. Replace each null only with a recorded value. Do not copy mock values into an authentic run.

    {
      "run_id": null,
      "run_started_utc": null,
      "run_finished_utc": null,
      "data_mode": null,
      "provider": null,
      "collection": null,
      "product_version": null,
      "observation_ids": [],
      "observation_dates": [],
      "aoi_id": null,
      "aoi_checksum": null,
      "input_checksums": {},
      "code_repository": null,
      "git_commit": null,
      "command": null,
      "configuration_path": null,
      "configuration_checksum": null,
      "package_lock_or_environment": null,
      "seed": null,
      "preprocessing_version": null,
      "detector_name": null,
      "detector_parameters": {},
      "label_source": null,
      "label_protocol": null,
      "split_definition": null,
      "outputs": [],
      "output_checksums": {},
      "api_requests": [],
      "api_wait_seconds": null,
      "compute_wall_seconds": null,
      "peak_ram_mb": null,
      "cpu_model_and_threads": null,
      "storage_bytes": null,
      "repetitions": [],
      "verification_status": null,
      "limitations": []
    }

Allowed data_mode values should be controlled by the project, for example authentic_observed, mock_fixture or synthetic_test. A mock_fixture or synthetic_test run must never receive a scientific verification label.

## Benchmark procedure

1. Fix and record the environment, configuration, data, code revision and hardware.
2. Run one warm-up only if the protocol specifies it; record it separately.
3. Perform the predeclared number of measured repetitions on the same inputs.
4. Record acquisition/API latency separately from local processing.
5. State cache state, retries, failures and any excluded runs with reasons.
6. Report every repetition plus a defined summary statistic. Do not invent a mean or uncertainty.
7. Compare memory/runtime only across runs with equivalent data and environment.
8. Keep software-performance results separate from scientific accuracy.

## Scientific-evidence gate

Before reporting a predictive metric, verify all of these:

- [ ] Authentic input products and observation IDs are available.
- [ ] Labels come from a documented, independent source.
- [ ] Labeling method, annotator or reference process is recorded.
- [ ] Unit of analysis and sampling design are clear.
- [ ] Train/tune/test splits prevent leakage.
- [ ] Raw predictions and corresponding labels are preserved.
- [ ] The metric implementation and exact calculation can be rerun.
- [ ] Uncertainty and class imbalance are addressed appropriately.
- [ ] No mock/demo record appears as an observation.
- [ ] The limitation of the proxy and ground truth is explained by the student.

If a requirement is not met, do not report the predictive metric as validated. Describe only the software test or exploratory demonstration that the evidence actually supports.

## Post-run review

- Did any API return mock data, empty data, cached data or an error?
- Did input IDs and counts match the pre-run protocol?
- Did any observation fail a quality filter?
- Did processing exceed the recorded resource cap?
- Does the output preserve all source and code provenance?
- Can an independent reviewer reproduce the output from the recorded manifest?
- Is the result supported by the student's own analysis and the approved assignment?

## Claim record

| Proposed claim | Supporting run IDs/data | Calculation/source file | Reproduction status | Limitation | Student decision |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Do not complete the empty claim row until a real run exists.


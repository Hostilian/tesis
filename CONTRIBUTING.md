# Contributing to Space-Based Economic Intelligence

Thank you for contributing to this research codebase! To maintain academic rigor and technical scalability, please follow these development standards.

## Development Workflow

1. **Branching Model**:
   * `main`: Represents the stable, peer-reviewed production state and deployed site.
   * `develop`: Active integration branch for new features or case studies.
   * Feature Branches: Named as `feature/description` (e.g. `feature/sentinel5p-emissions`).
2. **Pull Requests (PR)**:
   * All PRs must target the `develop` branch.
   * Trigger the `.github/workflows/test.yml` and `.github/workflows/lint.yml` checks.
   * Require at least 1 reviewer approval before merging.

## Coding Standards

* **Python**:
  * Adhere to PEP 8 style guides (validated via Flake8 and formatted with Black).
  * Document all functions using **Google-style docstrings**.
  * Use relative coordinates and parameterized geometries instead of hardcoding raw pixel boundaries.
* **Frontend**:
  * Write pure vanilla ES6+ Javascript in `docs/app.js`.
  * Ensure CSS styling properties reside inside `docs/index.css` rather than writing ad-hoc inline styles.

## Extending the Pipeline (Adding a Case Study)

To monitor a new region:
1. Open [pipeline/run_pipeline.py](file:///d:/CODING/tesis/pipeline/run_pipeline.py).
2. Append a new bounding box geometry `[min_lon, min_lat, max_lon, max_lat]`.
3. Process relevant indices (NDVI for vegetation, NDWI for water, etc.) and add the study parameters to the `study_regions` list.
4. Execute `python pipeline/run_pipeline.py` to compile the outputs to `/docs/data/`.
5. Verify the map renders the new polygon by running unit tests.

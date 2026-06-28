# Appendix A: Full Code Repository Structure

This appendix illustrates the structured layout of the thesis software repository, mapping out data modules, dashboard components, and deployment pipelines. The repository is organized to enforce the decoupled architecture described in Chapter 4, separating the Python geospatial ingestion and modeling pipeline (`/pipeline`) from the static frontend visualization files (`/docs`).

```
space-economic-intelligence/
│
├── .github/                       # GitHub configurations
│   ├── ISSUE_TEMPLATE/            # Standardized project issue forms
│   │   ├── bug_report.md          # Technical pipeline bug logger
│   │   └── feature_request.md     # Extension request template
│   └── workflows/                 # CI/CD automated actions
│   │   ├── deploy.yml             # Automatic push-to-deploy for Pages
│   │   ├── test.yml               # Automated pytest runner
│   │   ├── lint.yml               # Flake8 and Black code format checks
│   │   └── data-refresh.yml       # Weekly cron automated pipeline
│   
├── docs/                          # Web visualization dashboard
│   ├── index.html                 # Semantic structure of the dashboard
│   ├── index.css                  # Animations and custom layout rules
│   ├── app.js                     # Maps, split-sliders, and radar logic
│   ├── assets/
│   │   └── images/                # Dual canvas before/after image files
│   └── data/
│       ├── anomalies.json         # Serialized ML outlier dataset
│       └── regions.geojson        # Study boundary polygon coordinates
│
├── pipeline/                      # Geospatial processing pipeline
│   ├── notebooks/                 # Jupyter Notebook workflows (01 - 07)
│   ├── src/                       # Production Python package source
│   │   ├── __init__.py            # Module initialization file
│   │   ├── utils.py               # Calculation formulas (NDVI, Z-score)
│   │   ├── ingestion.py           # GEE & CDSE satellite query interface
│   │   ├── preprocessing.py       # Cloud-masking and band scaling
│   │   ├── models.py              # Isolation Forest ML classifiers
│   │   └── exporter.py            # Serializers for GeoJSON outputs
│   ├── tests/
│   │   └── test_pipeline.py       # Unit test suite verifying logic
│   └── run_pipeline.py            # Headless command-line orchestrator
│
├── thesis/                        # LaTeX thesis sources
│   ├── chapters/                  # Chapter drafts (1-7) & Appendices
│   └── latex/
│       ├── main.tex               # Master typesetting document
│       └── references.bib         # BibTeX citation collection
│
├── SECURITY.md                    # Key protection and disclosure policy
├── CONTRIBUTING.md                # Development and branching standards
├── CHANGELOG.md                   # Project semver release logs
└── LICENSE                        # MIT Open License
```

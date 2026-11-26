# Reproducibility Guide (REPRODUCE.md)

This guide distinguishes **reproducible synthetic demonstrations** from research workflows that retrieve real observed pixels. Passing the demo pipeline or tests does not validate economic or environmental events. The current public anomaly records are unverified examples; see [Evidence status](docs/evidence.html) and [Validation gaps](THESIS_VALIDATION_GAPS.md).

---

## 💻 Option A: Running Locally (Python)

### 1. Prerequisite Environment
Ensure you have **Python 3.12+** installed on your host system.

### 2. Sandbox Setup
Initialize a clean virtual environment and load requirements:
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows PowerShell/Command
source .venv/bin/activate    # macOS/Linux terminal
pip install -r pipeline/requirements.txt
```

### 3. Run Pipeline Orchestrator
Execute the **synthetic demonstration** pipeline to exercise spectral indices, Isolation Forest and JSON output. It writes to the local `docs/` directory, so review changes before committing or publishing:
```bash
python pipeline/run_pipeline.py
```
*   **Source caveat:** The Sentinel-2 pixel arrays and monthly VIIRS values in this path are synthetic even when a metadata-only Earth Engine request is authenticated. The published site must not treat this run as a verified satellite observation.

### 4. Run Test Suite
Confirm the mathematical equations and index clipping routines are correct:
```bash
python -m pytest pipeline/tests/
```

### 5. Experimental observed-pixel acquisition (not published)

The fail-closed real-data preview is separate from the demonstrator:

```bash
earthengine authenticate
export GCP_PROJECT="your-authorized-project"
python -m pipeline.real_observation \
  --bbox -68.250 -23.480 -68.238 -23.468 \
  --start 2024-10-01 --end 2024-10-15
```

See [REAL_OBSERVATION.md](REAL_OBSERVATION.md). This command requires provider credentials and does not claim scientific verification or publish data. Raw pixel arrays and manifests are written under git-ignored `research_private/`.

---

## 🐳 Option B: Running with Docker (Isolated Container)

This option describes a containerized **demonstration**, not real observed-data validation. Confirm the Docker build and bundled system libraries in the target environment; CI test success alone does not verify local container reproducibility.

### 1. Build Docker Image
Run this command from the root directory:
```bash
docker build -t space-economic-pipeline -f pipeline/Dockerfile pipeline/
```

### 2. Run Containerized Ingestion
Execute the container:
```bash
docker run --rm -v "$(pwd)/docs/data:/app/docs/data" space-economic-pipeline
```
*Note: The `-v` flag mounts your local `/docs/data` folder to the container's output workspace, allowing the container to write fresh `anomalies.json` and `regions.geojson` cache files directly to your host directory.*

---

## 📚 Option C: Thesis Document Compilation (Markdown to LaTeX)

To keep the academic thesis chapters in sync between the living Markdown source and the LaTeX formatting, use the automated compilation script:

### 1. Compile Markdown Chapters to LaTeX
```bash
python thesis/convert_chapters.py
```
This parses files under `thesis/chapters/` and outputs aligned LaTeX source files (`.tex`) inside `thesis/latex/chapters/` (escaping special characters and rendering tables/lists cleanly).

### 2. Compile PDF Document (LaTeX)
Navigate to the LaTeX directory and run:
```bash
cd thesis/latex
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```
This generates a LaTeX PDF artifact, **not automatically a submission-ready thesis**. The existing checked-in PDF and LaTeX may contain older, unsupported benchmark claims. Reconcile them with the revised Markdown Chapters 5–7, confirm references, and verify the generated PDF before academic submission.


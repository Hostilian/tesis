# Reproducibility Guide (REPRODUCE.md)

This project is built under strict reproducibility guidelines. Follow these instructions to execute the satellite data pipeline and regenerate the economic anomaly datasets.

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
Execute the entry script to query APIs, compute spectral indices, run Isolation Forest models, and write results back to the frontend:
```bash
python pipeline/run_pipeline.py
```
*   **GEE Fallback**: If Earth Engine is not authenticated via `earthengine authenticate`, the pipeline automatically falls back to intelligent mock data generation, allowing successful execution and map rendering.

### 4. Run Test Suite
Confirm the mathematical equations and index clipping routines are correct:
```bash
python -m pytest pipeline/tests/
```

---

## 🐳 Option B: Running with Docker (Isolated Container)

This option encapsulates all system libraries (`gdal`, `proj`, `geos`) and locked dependency versions inside a single container image.

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
This generates the final compiled bachelor thesis paper `main.pdf`.


# Workspace Agent Instructions (AGENTS.md)

Welcome, AI agent! This is the workspace-scoped context and rules log for the **Space-Based Economic Intelligence** project. To keep the root repository clean, professional, and compliant with academic/financial audits, all agent instructions, rules, and reference logs are hidden in the `.agents/` directory.

---

## 🏛️ Decoupled Repository Architecture

The project has a clean separation of concerns:
1. **`/pipeline`**: Python ETL and ML pipeline.
   - Core ingestion (GEE, ESA CDSE, World Bank).
   - Core algorithms (Isolation Forest, Z-score).
   - Test suite (`pipeline/tests/test_pipeline.py`).
2. **`/docs`**: Web dashboard SPA.
   - PWA layout, Three.js globe, Leaflet GIS map.
   - Deployed on GitHub Pages.
   - Ingests data from `/docs/data/anomalies.json`.
3. **`/thesis`**: Academic chapters and LaTeX code.
   - Draft markdown files inside `thesis/chapters/`.
   - LaTeX source inside `thesis/latex/`.
   - Automated compiler scripts (`thesis/convert_chapters.py` and `thesis/compile_pdf.py`).

---

## 📚 Anti-Hallucination Reference Log

The primary package specifications, verified API endpoints, and academic ISO 690 citations are located in:
👉 [REFERENCE.md](file:///d:/CODING/tesis/.agents/REFERENCE.md)

Check this file to verify:
- Locked python package versions (e.g. numpy, pandas, earthengine-api, torch).
- Open satellite API URLs and credentials schema.
- Reference citations used in the paper.

---

## 🤖 Internal Developer Chatbot App

A local CLI chatbot companion is stored at:
👉 [.ai_chatbot/chatai.py](file:///d:/CODING/tesis/.ai_chatbot/chatai.py)

- **Launch Command**: `python .ai_chatbot/chatai.py`
- **Execution Settings**:
  - Automatically loads config from `~/.chatai/config.toml` (which is managed by `.ai_chatbot/config.py`).
  - Self-contained import resolutions via `sys.path` injection. Do not move or rename files in `.ai_chatbot` without updating this path hook.

---

## 🔧 Operational Guidelines

1. **Authentication**:
   - Google Earth Engine authentication is handled locally.
   - Custom client secret credentials, if present, reside in `client_secret.json` in the workspace root. Do NOT move it as the GEE client and notebooks look for it there.
   - Ensure `client_secret.json` is NEVER committed (it is gitignored).

2. **Running Tests**:
   - Run tests using: `python -m pytest pipeline/tests/ -v`

3. **Compiling Academic Drafts**:
   - Convert markdown chapters to LaTeX: `python thesis/convert_chapters.py`

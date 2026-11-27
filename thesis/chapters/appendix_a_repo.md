# Appendix A: Repository Structure

<!-- AI-assisted factual update 2026-11-27: pending supervisor permission -->

This appendix lists the main folders of the thesis repository (https://github.com/Hostilian/tesis). It was generated from `git ls-files` at commit `57e2a2a` (313 tracked files) and shows key folders only. The case study described in Chapters 3 and 5 uses the files marked "case study". Files marked "earlier demonstrator" belong to the first version of the project; they run on synthetic data and are not evidence for the results.

```
tesis/
|-- .github/workflows/              GitHub Actions (9 workflows)
|   |-- test.yml                    Python test suite
|   |-- lint.yml                    black, flake8 and mypy on pipeline/src
|   |-- security.yml                pip-audit, Bandit, CodeQL, Gitleaks, npm audit, fuzzing
|   |-- formal.yml                  builds the Lean proofs in formal/
|   |-- linux-run-kit.yml           reruns the case study on Ubuntu
|   |-- deploy.yml                  publishes docs/ to GitHub Pages
|   |-- data-refresh.yml            earlier demonstrator rehearsal (results not published)
|   |-- connection-health.yml       earlier demonstrator: checks GEE, CDSE, NASA, World Bank, IMF
|   `-- toolchain-smoke.yml         validates agent tool configs (MCP, Node adapters)
|
|-- pipeline/                       Python code
|   |-- case_studies/               case study: one JSON config per study area
|   |   |-- alqueva_olive.json      Alqueva: bounding box, pinned STAC item ids, thresholds
|   |   `-- neves_corvo_mine.json   Neves-Corvo: same fields
|   |-- run_case_study.py           case study: main run (STAC -> change map -> outputs)
|   |-- run_robustness.py           case study: threshold curve, bootstrap, second date pair
|   |-- run_interop_check.py        case study: same scenes from Planetary Computer
|   |-- verify_independent.py       case study: second implementation, shares no code
|   |-- run_soil_link.py            soil-laboratory link (pilot, not in the results)
|   |-- src/
|   |   |-- case_study.py           case study: reading, masking, indices, threshold, patches
|   |   |-- reference_cos.py        case study: DGT COS download and agreement tables
|   |   |-- robustness.py           case study: bootstrap and threshold-curve functions
|   |   |-- provider_pc.py          case study: Planetary Computer adapter
|   |   |-- soil_link.py            soil-laboratory link (pilot)
|   |   |-- ingestion.py            earlier demonstrator: GEE, CDSE, World Bank and other clients
|   |   |-- models.py               earlier demonstrator: Isolation Forest and z-score models
|   |   |-- api_server.py           earlier demonstrator: FastAPI server
|   |   `-- ...                     other earlier-demonstrator modules
|   |-- tests/                      pytest suite (18 files, incl. property tests)
|   |-- notebooks/                  earlier demonstrator notebooks 00-07
|   `-- run_pipeline.py             earlier demonstrator command line
|
|-- docs/                           GitHub Pages site
|   |-- case-study/
|   |   |-- index.html              case-study web page
|   |   |-- REPRODUCE.md            rerun instructions
|   |   `-- data/<case>/            published outputs: manifest.json, results.json,
|   |                               reference_cos.json, robustness.json,
|   |                               independent_check.json, figures, GeoJSON
|   |-- index.html, index3.html,    earlier demonstrator dashboards (V2, V3, V4)
|   |   index4.html
|   |-- index6.html, v6/            globe view of the case study (version 6)
|   |-- evidence.html               public statement of what is and is not evidence
|   |-- data/                       earlier demonstrator data (labelled synthetic) and
|   |                               coverage checks
|   `-- api/v1/                     static JSON API of the earlier demonstrator
|
|-- formal/                         Lean 4 proofs of the decision rules
|   `-- Formal/                     Indices, Threshold, Flags, Patches, Confusion, Count, Audit
|
|-- linux/                          scripts and Dockerfile to rerun everything on Linux
|-- research/                       background notes, benchmark and prototype scripts
|-- thesis/
|   |-- chapters/                   Markdown chapters and appendices
|   |-- latex/                      LaTeX copy (main.tex, chapters/, references.bib)
|   `-- tools/                      check_dois.py, slop_check.py and helpers
|
|-- AGENTS.md, CLAUDE.md            rules for AI agents working in the repository
|-- REPRODUCE.md                    how to reproduce the published results
`-- LICENSE                         MIT licence
```

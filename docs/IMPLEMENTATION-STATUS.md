# 4 November 2026 implementation and continuation record

Scope-safe PR branch: `research/real-data-agriculture-pilot`. No private Rota Única raw data used.

**Verified locally before push:** 11 isolated unit tests for public evidence labeling, historic-claim preservation, WGS84 polygon checks, STAC request-template generation, NDVI and MAD baseline; the synthetic CLI ran successfully in a Python 3.13 container. The existing full suite could **not** be cloned into the local test environment because outbound network resolution to GitHub was unavailable; rely on subsequent GitHub Actions results for repository-wide validation.

**New** `research_integrity.py` returns demonstration/unverified (never automatically Verified); the exporter is wired for public anomaly and API output sanitizing. **New** `agriculture_pilot.py` creates an offline discovery query and robust synthetic baseline, without authentic imagery ingestion. Current public asset retroactive labeling is proposed in PR and does not become deployed until review/merge.

**Critical blocked evidence:** official ČZU assignment and deadline; company imagery permission, authoritative pilot polygon and ground truth; verified live CDSE catalogue/asset requests; authenticated GEE credentials; full security workflow diagnosis. Desktop Commander was offline when checked. A GitHub Pages link to the current main deployment **does not** imply PR deployment.

## Verification checklist
- Run: `python -m unittest discover -s pipeline/tests -p 'test_research_guard.py' -v`
- Run: `python -m pipeline.run_agriculture_pilot` (synthetic only)
- Run: `python -m pipeline.src.research_integrity docs/data/anomalies.json`
- Run existing `pytest pipeline/tests -v` with installed requirements
- Confirm full CI and Pages output before changing official claims
- Preserve official registered title and supervisor review; no email to external contacts

## Review checkpoints
After PR CI: investigate preexisting failing API health/security jobs, then adjust code without disabling safety rules. Authenticate public STAC search/download only where permits and quotas allow; record authentic acquisition IDs. Never infer scientific validity from green CI alone.

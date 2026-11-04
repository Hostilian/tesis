# Scientific-integrity audit — 4 November 2026

## Verdict
**Current public anomalies are demonstrations.** All 10 records reviewed in `docs/data/anomalies.json` explicitly identify Mock Sentinel-2 or Mock VIIRS inputs while `verification.status` claims Verified (including Verified Critical). No supplied independent image/source acquisition manifests substantiate those cases. The existence of a source ID string, reference to a government agency, checksum, model score, or passing unit test does not establish ground truth.

## Evidence review
| Public claim | Evidence found in repository | Status and necessary action |
| --- | --- | --- |
| 10 anomalous events independently verified | Mock satellite lineage in all 10 exported records; status claims conflict | **Synthetic demonstration; remove Verified labels** |
| F1 0.907; precision 0.936; recall 0.880 | Headline in README and draft chapter, not reproduced from a documented authentic labelled holdout | **Unverified; reconstruct labels and held-out evaluation** |
| Pearson r 0.724; p = 0.0002 | Header and prose; authentic aligned NTL and GDP sample pairs not independently audited | **Unverified; archive data vintage and reproduce statistical notebook** |
| Moran's I +0.648 | Header, manuscript, no independently inspected spatial weights and input source | **Unverified; specify neighbourhood graph and reproduce** |
| 184 satellite tiles ingested | Chapter 5 narrative; no matching per-acquisition verified manifest demonstrated | **Unverified count** |
| Pipeline 9.0 ± 1.2 seconds | Header/README; not independently timed under a reproducible pinned environment | **Unverified benchmark** |
| Nine case-study events | README historically says nine, current JSON contains **10** | **Documentation inconsistency corrected** |
| API scene IDs in public records | Names under mock lineage, without original scene manifests | **Identifiers are not proof of acquisitions** |
| Tests and provenance hashes | Source-code unit tests; SHA-256 hashes of inputs | **Engineering checks only; not scientific validation** |

## Programme-level safeguards
- `pipeline/src/research_integrity.py` classifies suspicious lineage as synthetic even if an input falsely declares itself authentic.
- `pipeline/src/exporter.py` applies conservative status labels before serializing public anomalies and API endpoints.
- Historic status claims are retained as `verification.historical_status_claim` solely for audit, not as current verification.
- CI/publication gate rejects unsupported Verified status and unfounded cross-reference assertions.
- Authentic ingest **does not** itself confer a verified scientific status. Independent review and evidence remain manual academic tasks.

## Known methodological risks
Geographic case-study claims, local field changes, dates, socioeconomic explanations, apparent probabilities and quoted reference statements need primary-source reinspection. Pixel random train/test splits can leak spatial structure; simulated class labels cannot be used as independent ground truth. Continuous scheduled reruns may regenerate synthetic events when credentials are unavailable.

## Evidence location
`pipeline/run_pipeline.py`, `pipeline/src/ingestion.py`, `pipeline/src/provenance.py`, `pipeline/src/exporter.py`, `docs/data/anomalies.json`, `docs/api/v1/anomalies/`, `thesis/chapters/05_results.md`. This is an audit of inspected project materials, not certification of research results.

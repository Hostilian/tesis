# Thesis chapter revision map - evidence checklist
**Review date:** 18 November 2026  
**Use:** Student-facing revision checklist; not replacement thesis prose.  
**Academic-integrity boundary:** CZU Rector's Directive 7/2026 restricts AI use for formulating the student's own results, discussion and conclusions. Use this document to guide the author's own work and verify the current assignment.

## Governing decision

Keep the current approved UIS assignment as the scope authority. The working historical title is "Space-Based Economic Intelligence: Detecting Hidden Resource Anomalies Using Open Satellite APIs," but its current approval and exact objective must be checked in UIS. The best evidenced class fit is EIE67E Component-based SW Development. Its retrievable 2023/24 syllabus supports an architecture and software-quality focus; confirm the current 2026/27 specification before relying on detailed assessment terms.

## Front matter

- Replace no metadata until checked against the current CZU/PEF template and approved UIS assignment.
- Reconcile the PDF's department wording, academic year, date, language, author/supervisor fields and stated extent.
- Decide which source is authoritative: Markdown or LaTeX. Record which build generates the submitted PDF.
- Check abstract and keywords only after the actual method and student-authored findings are settled.
- Confirm whether the stated 35-40-page expectation means main body only; do not compare it directly to a 49-page PDF without counting front matter, references and appendices separately.

## Chapter 1 - Introduction

- Narrow the subject to one approved research question, one observable phenomenon, one study unit and one period.
- Replace language that treats satellite measures as direct or unalterable economic truth with carefully scoped observational proxies.
- Verify or remove "real-time," "economic intelligence," "hidden," and other promises the data cadence cannot support.
- Resolve whether Atacama lithium, Peru mining and Czech night lights are truly one coherent study. Do not retain unrelated case studies merely because they appear in the current draft.
- State why the selected problem is suitable for a component-based Informatics thesis.
- Connect to EIE67E through concrete engineering outcomes: reusable interfaces, adapters, modular components, profiling, testing, refactoring and a defensible UI/API/database design.
- Do not state the course requires or approves the scientific topic.

## Chapter 2 - Literature review

- Create a source ledger: exact claim, cited source, page/section, source type, direct URL/DOI, verification date and whether it actually supports the claim.
- Resolve R235: the DOI inspected points to a different conservation-governance paper than the bibliography title.
- Resolve R236: the DOI inspected points to a different coupled wave/current/sediment-model paper than the bibliography title.
- Verify R241 directly; the supplied DOI/title mapping may be wrong.
- Remove or consolidate duplicate R258 entries after checking in-text use.
- Check the bibliography against every in-text citation and vice versa.
- Verify current API/product statements using official provider documentation.
- The CZU AI directive permits limited literature-review assistance; disclose any AI-assisted content as required.

## Chapter 3 - Methodology

- Make the method answer the approved objective rather than fit existing numbers.
- Identify actual data provider, product, product level, spatial resolution, bands, observation dates, region/AOI, identifiers and acquisition parameters.
- Specify quality screening, masks, missing-data rules, transformations and every detector parameter.
- Separate data availability from economic interpretation.
- Verify the temporal/spatial frequency of every external economic indicator. Resolve the draft's annual country series versus regional quarterly claims.
- State ground-truth source, labeling protocol, independence, sampling, split and limits if supervised metrics are retained.
- If no independent ground truth exists, design an exploratory/software evaluation and do not call the output validated prediction.
- Include an exact command/run manifest, package versions, configuration and checksums.

## Chapter 4 - System design and implementation

Create an implementation matrix for every claimed feature: requirement, source path, implementation state, test, runtime evidence, deployment status and caveat.

- Align the architecture with EIE67E: source adapters; reusable components; clean interfaces; preprocessing; detector; evaluation; API; UI; provenance.
- Separate design-only features from implemented features and mock providers from live providers.
- Verify claims about GEE/CDSE APIs, Celery/Redis, provenance/cryptographic audit, webhooks, static deployment, proprietary engines and performance.
- A module's existence is not proof that an API or service works in production.
- Document failure handling, rate limits, caching, bounded memory and CPU needs where the system actually implements them.
- Verify diagrams, repository paths and version statements against the current branch.

## Chapter 5 - Results

The student must supply the empirical work. Do not generate replacement findings.

For every result, require:

- Exact authentic input manifest and data IDs.
- Source/date/region/product/provenance and processing configuration.
- Raw observation, label, prediction or benchmark data sufficient to reproduce it.
- Calculation script and exact command.
- A clear separation of exploratory visual output, software test and scientific observation.

Specific draft claims to verify or remove pending evidence:

- 184 scenes/tiles and region-wise counts.
- F1 0.907 and its TP/FP/FN/TN table.
- Pearson r 0.724 and p 0.0002 with stated quarterly/regional GDP sample.
- Moran's I 0.648 and z 8.92.
- Runtime 9.0 � 1.2 seconds and 310 MB RAM.
- Any claim that public anomaly events are real or independently verified.

A test-suite pass does not validate scientific findings. Mock data can test software behavior but not real-world accuracy.

## Chapter 6 - Discussion

Student-authored only under the current CZU AI policy.

Before drafting, the student should answer from their own evidence:

- What the measured results actually show and what they do not show.
- How method, sampling, spatial/temporal scale, proxy validity, labels and missing data limit interpretation.
- Which outcomes answer the approved question.
- Whether any comparison is fair and methodologically supported.
- Why deployment, investment, causality or lead-time claims are warranted-or why they should be removed.
- How the results compare with verified literature without overstating agreement.

Do not supply discussion prose, claim summaries or fabricated interpretations.

## Chapter 7 - Conclusion

Student-authored only under the current CZU AI policy.

Use a blank author-completed structure:

1. Restate the approved objective in the student's words.
2. State the actual work completed.
3. Answer the research question using only established results.
4. Name the strongest limitation.
5. Give the next research step without making a new unsupported claim.

Do not write thesis-ready conclusion text or copy existing unsupported metrics into the conclusion.

## Appendix A - Repository

- Regenerate the repository tree from the current reviewed branch.
- Remove stale paths; distinguish source, generated output, cache, fixture and private files.
- Exclude credentials and employer/private data.

## Appendix B - APIs

- Verify every endpoint, product, cadence, authentication method, quota and license against current official docs.
- Check whether NASA/VIIRS products described as monthly are actually monthly or daily inputs aggregated by the study.
- Distinguish tested-live endpoints from request templates, mocks and untested integrations.
- Record access date and API/version.

## Appendix C - Metadata and provenance

- Define required lineage and verification fields.
- Make status values consistent: mock input cannot be labelled scientifically "Verified."
- Preserve observation IDs, dates, provider, product, processing, code revision and reproducibility details.
- Explain missing reproduced_at rather than implying a reproduction.

## Appendix D - Visualization

- Validate paths, selectors and scripts; fix the reported invalid CSS literal.
- Check every chart/legend against actual data and uncertainty.
- Label fixtures/mock data visibly on every entry page and detail view.
- Test keyboard access, contrast, responsive behavior and empty/error states.

## Appendix E - Glossary

- Verify each definition at first use against source or technical documentation.
- Remove terms the final method does not use.
- Distinguish "anomaly," "proxy," "ground truth," "validation" and "verification."

## Appendix F - Acronyms

- Correct department and project expansions, including KII's official English name: Department of Information Engineering.
- Include only acronyms used in the final body.
- Check all expansions against official and technical sources.

## Final consistency gate

- One authoritative assignment and title.
- One research question, objective and method.
- No citation/DOI mismatch.
- Every empirical claim traceable to input and code.
- Mock/demo data labelled everywhere.
- Markdown/LaTeX/PDF agree.
- Length and formatting follow the current official template.
- Student-authored results, discussion and conclusion comply with CZU rules.
- No company/private information appears in public artifacts.


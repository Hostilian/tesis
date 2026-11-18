# Public evidence review — thesis project
**Review date:** 18 November 2026  
**Repository reviewed:** Hostilian/tesis  
**Purpose:** Public-safe project and chapter evidence review. This document does not assert supervisor approval, validate a scientific result, or replace the formal thesis assignment.

## Finding

The repository contains a substantial seven-chapter draft, six appendices, a software pipeline, public dashboard outputs, Markdown and LaTeX sources, and a generated PDF. The main research risk is that parts of the current narrative describe mock data and unverified metrics as empirical findings. Before polishing claims, the author needs a single assignment-aligned question, a traceable authentic data package, and a reproducible evaluation.

## Course fit: EIE67E Component-based SW Development

CZU’s current Moodle listing for WS 2026/27 identifies EIE67E and names Jiří Brožek as guarantor. The retrievable formal syllabus record is for WS 2023/24, so its details should be reconfirmed against current course materials. That syllabus covers application design, reusable code and component libraries, UI/database work, design patterns, profiling, refactoring and unit testing; its plan also names network/distributed objects. It lists a C#/.NET project and oral/project examination.

This makes a modular satellite-data pipeline a credible software-engineering fit: separate source adapters, preprocessing, detector, evaluation, API, visualization and provenance. It does not establish that satellite anomaly detection is the approved thesis topic, and it does not prove current assessment requirements. The actual UIS assignment and current course specification control.

Sources:
- [Current EIE67E course listing, CZU Moodle](https://moodle.czu.cz/course/search.php?perpage=all&search=se)
- [EIE67E syllabus, CZU IS, WS 2023/24](https://is.czu.cz/katalog/syllabus.pl?predmet=229754)
- [Jiří Brožek teaching profile](https://home.czu.cz/brozekj/pedagogika?editmode=0)

The current repository is primarily Python, whereas the retrievable 2023/24 syllabus lists a C#/.NET project. Confirm whether Python is acceptable under the current 2026/27 assignment before claiming course compliance; do not port components based on the historical syllabus alone.

## Supervisor prior-work check

The CZU teaching profile confirms Brožek’s role as guarantor of EIE67E and lists other teaching in principles of computers, computer architecture and object modelling. A public Theses.cz search indexes a 2012 CZU PEF dissertation attributed to Jiří Brožek titled “Distribuované objektové architektury” (“Distributed Object Architectures”). The direct record was not accessible in the review; verify identity, degree record and contents before citing it. The public publications page showed no entries in the inspected snapshot, which is not proof that no publications exist. No verified master’s thesis record is included here.

Source lead: [Theses.cz related-work search](https://theses.cz/th_search/prace_na_stejne_tema?ks=distribuovana+architektura).

### Additional supervisor-work evidence found on 18 November 2026

The earlier wording about a blank publications page was incomplete: the personal CZU profile's publication tab was blank in the inspected page, but the official CZU WhitePages search result and a CZU PEF publication record identify selected work. The 2015 chapter “Multidimensional Modelling from Open Data for Precision Agriculture” lists Jiří Brožek as coauthor. This is a grounded conceptual link to open-data modelling and agriculture, not approval of an orchard case or private employer data. A 2025 publisher record lists him as coauthor of “Effects of Normalised SSIM Loss on Super-Resolution Tasks” and credits him with visualization and review/editing. The CZU staff search result also lists AIDIGI (2023) and a virtual-reality questionnaire prototype (2021), but their technical details were not retrieved.

Theses.cz indexes the 2012 CZU PEF dissertation “Distribuované objektové architektury” by Jiří Brožek. Its indexed metadata supports the title, author, year, institution and doctoral-dissertation type; the direct record/PDF was not accessible, so the work's content has not been reviewed. A same-named 2011 South Bohemian University master's thesis surfaced, but identity is unverified and it is not attributed to this supervisor.

Sources: [CZU PEF publication record](https://www.pef.czu.cz/dl/96866); [Springer volume record](https://link.springer.com/book/10.1007/978-3-319-24626-0); [2025 publisher paper](https://www.techscience.com/CMES/v143n3/62840/html); [Theses.cz search record](https://theses.cz/th_search/prace_na_stejne_tema?ks=distribuovana+architektura).

## Computational-resource question

No source reviewed identifies the "first guy" or establishes a formal computational-power limit. An earlier Principles of Computers/Computer Architecture course-record lead is not evidence of who imposed the limit. Do not attribute the statement to that lecturer or to the supervisor. Until the original source is located, treat low compute as a prudent design preference: bound area and time, process small subsets, avoid unnecessary model training, use chunked processing and caching, and measure runtime/RAM reproducibly.

## Evidence integrity in the public project

The project’s published anomaly exports contain ten examples whose lineage names Mock Sentinel-2 or Mock VIIRS sources while public verification fields say “Verified” or “Verified (Critical)”; reproduced_at is null. A reviewed pipeline-run manifest identifies mock mode. Those records can demonstrate software/UI behavior, but they do not prove satellite observations, ground-truth correctness or real-world anomaly detection.

Keep mock examples visibly identified across JSON, API, dashboard, report exports and thesis text. An authentic empirical claim needs exact input identifiers, dates, provider/product, processing configuration, run record, code revision, outputs, independent labels if a metric is claimed, and reproducible calculations.

## Chapter-level risk summary

| Area | Main issue to resolve |
|---|---|
| Front matter | Department name and academic year/date on the existing PDF need reconciliation with the current official template and assignment. |
| 1. Introduction | EO is framed too directly as economic truth; “real-time” and multi-region scope need sources and a narrower approved question. |
| 2. Literature review | Verify each reference and whether it supports the associated claim. R235 and R236 have DOI/title mismatches in the inspected bibliography; R241 needs direct verification; R258 is duplicated. |
| 3. Methodology | Reconcile the proposed data sources, spatial/temporal units, API records, ground truth and economic indicator frequency. |
| 4. System design | Mark each component/capability as implemented, tested, mock, planned or unsupported; a module’s presence does not prove a live service works. |
| 5. Results | Scene counts and metrics require traceable authentic inputs, labels, run manifests, raw calculations and benchmark protocol. Do not report mock/demo outputs as empirical findings. |
| 6. Discussion | Claims depending on unverified metrics, causal meaning, investment value or lead time have no demonstrated basis in the inspected evidence. |
| 7. Conclusion | Do not repeat unverified findings; derive conclusions only from work actually performed and the approved method. |
| Appendices A–F | Check repository tree, APIs/products, metadata, visualization code, glossary and acronym definitions against current files and authoritative sources. |

This is an evidence checklist, not replacement prose for empirical chapters.

## Academic policy and deadlines

CZU Rector’s Directive 7/2026 permits AI assistance in the literature-review section for grammar/style, structure suggestions, stylistic reformulation and source search. It says AI may not formulate a student’s own results, discussion or conclusions. Other AI use must be explicitly allowed in the assignment, and generated content requires the directive’s disclosure/citation approach. See the [official directive](https://www.czu.cz/dl/155344?lang=cs).

PEF’s winter-semester calendar lists 30 November 2026 as the thesis deadline for the February FSE and 2–5 February 2027 as the FSE period. A separate PEF notice describes a March 2027 submission for a route involving repeat-year students and May/June FSE. A student’s applicable route must be checked in the current UIS record; neither route should be assumed from this public note.

- [PEF winter-semester dates](https://www.pef.czu.cz/en/r-9396-study/r-10426-study-news/important-dates-of-the-winter-semester.html)
- [PEF study-conclusion routes](https://www.pef.czu.cz/en/r-9396-study/r-10426-study-news/instructions-for-the-study-conclusion-of-students-of-the-las.html)

## Required evidence before claiming completion

- Exact current UIS assignment and supervisor-approved scope.
- A single research question, population, study unit and temporal window compatible with that assignment.
- Verifiable literature and corrected bibliography.
- Authentic data manifest and exact processing record, or an explicitly software-only/demo scope.
- Independently justified evaluation; no predictive accuracy claim without traceable labels and raw predictions.
- Reproducible software and benchmark records.
- Synchronized Markdown/LaTeX source and PDF generated from the approved source.
- Current institutional formatting, cover, language and submission requirements.
- Results, discussion and conclusion authored by the student in line with CZU policy.

## Sources and limits

This review draws on public CZU course/syllabus/profile pages, PEF dates, Rector’s Directive 7/2026, public repository contents and public Theses.cz search output. It does not contain private academic records, email content, company data, personal identifiers or confidential datasets. The direct UIS assignment, current EIE67E 2026/27 syllabus, direct dissertation record and computational-limit source remain unverified.

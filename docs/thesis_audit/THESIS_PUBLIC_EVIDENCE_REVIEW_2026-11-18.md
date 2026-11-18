# Public evidence review — thesis software project

**Review date:** 18 November 2026  
**Repository reviewed:** Hostilian/tesis  
**Purpose:** Evidence review of public project materials. This does not approve a thesis scope or validate a scientific result.

## Finding

The repository contains thesis chapters, software, dashboard outputs, Markdown and LaTeX sources, and a generated PDF. Parts of the narrative and public data describe mock inputs alongside scientific verification labels and historical metrics. Before presenting findings, map the full approved aims and connected questions to traceable authentic data, reproducible runs, and suitable independent evaluation references. Preserve the intended breadth; remove only elements that are demonstrably irrelevant, unsupported, unauthorized, or outside the formal assignment.

## Course fit and scope

The public course record lists EIE67E for WS 2026/27, but the detailed syllabus available in this review is historical. It describes reusable components, application design, UI/database work, patterns, profiling, refactoring and unit testing; it lists a C#/.NET project. Current requirements must be checked before claiming alignment. Treat EIE67E and the directly fitting data/software/statistics units as work-package candidates; Web Technologies depends on retaining a web artifact, and HCI depends on a genuine permitted evaluation. Course fit does not approve a thesis topic.

## Evidence integrity

The reviewed anomaly exports include examples whose lineage names mock Sentinel-2 or VIIRS inputs while status fields say “Verified” or “Verified (Critical)”; reproduction timestamps are null. A reviewed run manifest identifies mock mode. These support a software demonstration, not observed events, ground truth or validated real-world accuracy.

An empirical claim needs the exact input IDs and dates, provider/product, quality masks, processing configuration, run record, code revision, outputs, independent labels if relevant, and reproducible calculations. Software tests establish software behavior only; they do not validate satellite-science results.

## Chapter-level risk summary

| Area | Main issue to resolve |
|---|---|
| Front matter | Reconcile department, year, date and extent with the current official template and assignment. |
| 1. Introduction | Preserve all approved aims and connected questions; map them to relevant cases and evidence, and qualify Earth-observation proxies instead of presenting them as direct economic truth. |
| 2. Literature review | Verify reference identity and claim support. R235 and R236 have DOI/title mismatches in the inspected bibliography; R241 needs direct verification; R258 appears duplicated. |
| 3. Methodology | Reconcile data sources, spatial/temporal units, API records, validation reference and indicator frequency. |
| 4. System design | Mark each feature implemented, tested, mock, planned or unsupported; a module does not prove a live service. |
| 5. Results | Require traceable inputs, labels, run manifests, calculations and a benchmark protocol. Do not report demo outputs as empirical results. |
| 6. Discussion | Do not claim causal meaning, investment value or lead time without evidence appropriate to those claims. |
| 7. Conclusion | Derive conclusions only from work performed under the approved method. |
| Appendices | Check repository tree, APIs/products, metadata, visualization, glossary and acronyms against current files and authoritative sources. |

This is a review checklist, not replacement prose for empirical chapters.

## Academic-use boundary

CZU Rector’s Directive 7/2026 limits AI assistance and prohibits AI from formulating the student’s own results, discussion or conclusions unless the applicable assignment explicitly allows otherwise. Confirm the assignment’s exact rule and disclosure requirements. See the [official directive](https://www.czu.cz/dl/155344?lang=cs).

## Evidence required before claiming completion

- Current formal assignment and approved scope.
- Authentic inputs with product identity, dates, quality checks and license.
- Reproducible run command, configuration, software versions, commit, logs and outputs.
- Independent reference and justified evaluation design for any accuracy claim.
- Student-authored discussion and conclusion based on those results.

## Limits of this review

The current individual academic record and current detailed course materials were not available. This review does not contain private academic records, correspondence, partner imagery, boundaries, credentials or confidential datasets. It is not a comprehensive secret scan of all Git history, clones or external caches.

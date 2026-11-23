# LaTeX / Markdown evidence reconciliation — REVIEW ONLY (23 November 2026)

**Status:** The manuscript is a **working academic draft, not submission-ready**. This review branch does not update the public thesis website, registered thesis topic, or a supervisor-approved PDF.

## Confirmed discrepancy and repair

The previous checked-in LaTeX Chapters 5–7 described historical F1 = 0.907, Pearson r = 0.724, Moran's I, economic causation, verified mining events and 9-second benchmarks as demonstrated science. The corresponding Markdown Chapters 5–7 had already withdrawn those claims because the source imagery/labels or paired observed economic series had not been reproduced. This contradiction could mislead a thesis reader.

On the separate **review/thesis-latex-evidence-20261123** branch, the existing repository converter `thesis/convert_chapters.py` was applied ONLY to corrected Markdown Chapters 5–7, and the LaTeX abstract was rewritten to distinguish demonstrator functionality, authentic bounded Sentinel-2 observations and unverified empirical hypotheses. Previous source histories and the original archived manuscript were preserved.

## Checks completed

- Diff whitespace checks passed (`git diff --check`).
- Existing software suite for the parent integrated tree: **102 passed** on Windows, as documented in `docs/research/INTEGRATED_WINDOWS_TEST_EVIDENCE_20261123.md`.
- The public `main` website and the previous LaTeX PDFs remain unchanged.

## Checks NOT completed / remaining blockers

- **LaTeX was NOT compiled and no new thesis PDF was generated.** Pandoc/TeX compilers were not installed on the authorized Windows machine in this check.
- The converter is simplistic. It may leave raw URLs, blockquote markers, overwide tables, Unicode/escaping issues or other typesetting defects. The generated `.tex` files MUST be inspected, typeset and corrected before the manuscript can be called ready.
- The introductory hypotheses and the old three-question structure require reconciliation with the six current subquestions and selected API-first working question. Formal CZU thesis assignment/registered title and supervisor approval are still unverified.
- Bounded real satellite observations DO NOT establish independent anomaly classification accuracy; the original F1/GDP metrics must not re-enter the narrative as validated findings.
- An updated PDF must be built and visually checked only after content, bibliography, provenance and formatting issues have been resolved; do not publish or submit the old PDF.

## Preservation

The original files are retrievable from the prior commit `4b441db7eba2bb829c5ba730ae4a9a7e371b6c46` or the historical `shelf/manuscript-pre-validation-20261119` branch. Keep any build/test outputs separate from public sites until reviewed.

No email, Moodle submission, supervisor contact or external publishing was performed.

---
name: thesis-plain-english
description: Use when writing or editing anything a person will read in this thesis repository - literature review text, README, site copy, captions, emails, reports. Applies the project's plain-English style and the CZU AI-use boundary.
---

# Plain-English writing for this thesis

1. Read `docs/WRITING_STYLE.md` and follow it exactly.
2. Check which part of the thesis you are touching:
   - **Literature review (chapter 2), README, site, emails:** you may write and reword.
   - **Results, discussion, conclusion:** do not write prose. Give the author facts, numbers, tables and figure paths, each with its source file and JSON key.
   - **Introduction, methodology, system design, appendices:** only if the supervisor's assignment allows AI help. Otherwise give a fact list.
3. Every number needs a source: a file and key under `docs/case-study/data/`, or a run manifest. Never reuse F1 0.907, r 0.724 or Moran's I 0.648.
4. Every citation key must exist in `thesis/latex/references.bib` and pass `python -I docs/thesis_audit/check_dois.py thesis/latex/references.bib out.json`.
5. Before finishing, reread the text and:
   - delete filler and hype words (list in the style guide);
   - split sentences over 30 words;
   - replace vague claims with a number or "not measured".
6. Keep the Markdown chapter and its LaTeX copy (`thesis/latex/chapters/`) identical in content.
7. Commit with a message that names the section changed. Do not push without the owner's OK.

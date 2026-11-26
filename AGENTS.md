# Thesis agent rules

Read this before you change anything. It applies to every AI agent working in this repository (Claude Code, Codex and others).

## 1. What this thesis is

- **Registered working title:** *Space-Based Economic Intelligence: Detecting Hidden Resource Anomalies Using Open Satellite APIs*. CZU Prague, Faculty of Economics and Management, Department of Information Engineering (KII), bachelor thesis in English.
- **Aim:** show that free satellite data and open APIs can find and map surface change in a reproducible way, with every number traceable to its source and the uncertainty visible.
- **Empirical core (implemented):** the Portuguese Sentinel-2 case study in `pipeline/run_case_study.py` and `docs/case-study/`.
  - Alqueva irrigation area: NDVI change 2018 → 2025, the main case.
  - Neves-Corvo mine: bare-soil index change.
  - Both are checked against the official land-use map (DGT COS).
- **Proposed research questions** (wait for the supervisor's confirmation before treating them as final):
  1. How much surface change can a simple, transparent method find in free Sentinel-2 data, and how sensitive is it to the threshold?
  2. Can each result be traced from the catalogue entry to the map, and what does adding a second source take?
  3. At 10 m resolution, what can and cannot be said about orchard-scale change?
- The formal assignment in UIS and the supervisor's decisions override everything here. If they change, update this section.

## 2. Integrity rules (non-negotiable)

- Label every public number or layer as one of: **public observation**, **observation-derived result**, **unverified interpretation** or **synthetic demonstration**. Mock data is never evidence.
- Never claim a score, finding or validation unless data, code, timestamp and the exact command exist. A change flag says *where* the surface changed, never *why*.
- The old figures (F1 0.907, r 0.724, Moran's I 0.648, "9-second runtime") are untraceable. Don't reuse them as results.
- Every reference must resolve to a real publication. Check with `python -I thesis/tools/check_dois.py thesis/latex/references.bib out.json` (Crossref title match) before adding or citing one.
- **CZU Rector's Directive 7/2026, Art. 8:**
  - AI may help only in the literature review: grammar, style, structure, rewording, finding sources.
  - AI must not write the results, discussion or conclusions.
  - Any other use must be allowed in the supervisor's assignment.
  - AI use is cited and declared.

  Agents therefore supply evidence (tables, figures, numbers, fact lists) for those chapters, not finished prose. Never use tools meant to hide AI use.
- No confidential farm boundaries, private imagery, personal data, tokens, keys or restricted documents in this public repository or on GitHub Pages. Personal notes, email drafts and course details stay in `docs/thesis_audit/`, which is local and never committed.

## 3. How to work here

- **Commit each finished piece** with a clear message. **Do not push** until the owner says so.
- One shared checkout: `D:\CODING\tesis`. Before you switch branches, stash, reset or overwrite files, write it in the progress log. Use a separate `git worktree` for risky operations (merges, reruns).
- Progress logs, local only: `docs/thesis_audit/AGENT_PROGRESS.md` and `docs/thesis_audit/SHARED_PROGRESS_*.md`. Add what you did, which files you claimed, and any disagreement.
- Never force-push, rewrite history, or hide a failing test. Record the exact command and output.
- Before saying something works, run it:
  - `python -m pytest pipeline/tests -q`
  - `python pipeline/run_case_study.py run pipeline/case_studies/<case>.json` for data changes
  - a browser check for site changes
- Case-study outputs are hashed in their manifests. Regenerate them with the CLI; never edit them by hand.
- Sending emails, opening or merging PRs, or publishing needs the owner's explicit OK each time.

## 4. Writing style

Follow `docs/WRITING_STYLE.md` for anything a person will read: thesis text you are allowed to touch, README, the site, emails.

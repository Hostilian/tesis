# Operation Thesis Convergence — evidence audit and reviewable release checkpoint
**20 November 2026 · Branch-only implementation, NO external communications · Status: PARTIAL, SCIENTIFIC EXPLORATORY**

## 1. Repositories and preservation

| Repository | Baseline branch/SHA at start | Isolated branch and state |
|---|---|---|
| Public thesis `Hostilian/tesis` | `main@feed5e6fb17c4149c9c64b396b091776c2e32641` | `operation/thesis-convergence-20261120`: experimental source, tests, observed GeoJSON and docs committed; `preserve/main-20261120-feed5e6` saved |
| Public courses `Hostilian/EVORACLASSES` | `main@03332ea33ece1032a8975d65a49570deadbd59e8` | `operation/thesis-convergence-academic-20261120`: created but **no content changes** because phone tracker already contained current conditional deadlines |
| Private academic ledger `Hostilian/EVORA-STUDY-PROGRESS` | `main@318729520ddc2bd61b36a79432f6970fdc8cbaa4` | `operation/thesis-convergence-ledger-20261120`: source-gated five-course crosswalk; latest evidence shows **96** authored week-specific tracker tasks |
| Private `Hostilian/rota-unica-rd` | `main@ca2d9e7c8340e6a1ff1f9b67c3a1c3bbadcbcfa5` | `operation/thesis-convergence-private-20261120`: one internal decision brief with 19 Nov already-sent almond-template handoff and current drafts reconciled |

Additional private academic repos `EVORA-STUDY-PRIVATE`, `EVORA-MOODLE-PRIVATE`, `mds-ex77222` and public HCI app were inspected for operating rules and kept unchanged. Remote authorized machine: `LAPTOP-LH1B14NT` (Windows, Python 3.12). Existing thesis `index.html`, `index3.html`, `index4.html` and historical shelf refs unchanged.

**Public production checks 20 Nov:** `https://hostilian.github.io/tesis/`, `index3.html`, `index4.html` returned HTTP 200. Experimental `/experimental/geo-intelligence/` returned HTTP 404 on production by design: **not merged or deployed**. Locally under HTTP it returned HTML+research GeoJSON HTTP 200.

## 2. What actually functions

- **Authentic satellite data:** existing Planetary Computer + PySTAC Client + rasterio + NumPy source path. Two Sentinel-2 L2A scenes at 2024-10-04 and 2025-10-14, `s2:processing_baseline=05.11` for both.
- **Corrected scientific radiometry:** independently checked official ESA source and inspected actual scene metadata; BOA `(DN-1000)/10000`. A same-day preliminary output using `DN/10000` was **superseded by a corrective commit**. Git history preserves both.
- **Observed comparison result:** 6,512 paired usable pixels (of a 9,216-cell geographical preview grid), 116 grouped GeoJSON cells, paired median ΔNDVI `-0.010174574771930473`, 0 below the preset `-0.15` decline threshold.
- **Important epistemic limit:** this is a valid exploratory **index difference**, *not* evidence of independently validated anomalies, plant stages, economic events, model scores or field truth. Source scenes, acquisition dates, baseline offsets, mask, derived checksum and interpretive caveats are stored in derived GeoJSON.
- **Preview:** isolated Leaflet GeoJSON viewer with layer selector, real-scene IDs, source checksum, provenance, strong real-vs-unvalidated label, mapped cells, mobile layout, and honest no-data fallback. Uses existing Leaflet rather than building/integrating a second engine.
- **Unit/integration test evidence:** Windows `python -m pytest pipeline/tests -q --basetemp=C:/writable-external-temp --disable-warnings --maxfail=5` -> **102 passed in 17.87 s**. Suite uses fabricated fixtures for contract tests. **One existing suite path mutated `docs/data/financial_feed.json` by adding duplicate fixture entries; its local diff was privately saved and tracked file restored**. Repaired baseline of output remains clean. This side-effect is not yet fixed upstream.
- **Local browser smoke:** headless Chrome at desktop and 390px mobile view rendered 6,512, -0.0102, 116 with a loaded Leaflet layer; local screenshot and DOM inspection generated. No independent user study, keyboard screen-reader pass, or performance budget check.

## 3. Source-first tool integration

**Actually reused existing components:** Planetary Computer STAC/COGs, PySTAC Client, rasterio/WarperVRT, NumPy, thesis `GeospatialPreprocessor`, Leaflet, Python stdlib JSON/argparse, pytest and Chrome. No God’s Eye View clone or new full-stack app.

**Reviewed but deliberately not installed:** canonical MIT Ponytail original skill (local adaptation added), Grafana Skills/GCX/Alloy (no real persistent runtime telemetry), OpenRouter skills/model routing (no keys/cost/privacy approvals), optional ODM/WebODM (no authorized private imagery pipeline). [Catalog of 31 candidates](OPEN_SOURCE_REUSE_CATALOG_20261120.md) records licensing gaps. Some API license fields returned NOASSERTION: **do not vendor those projects until actual LICENSE/NOTICE review**. God’s Eye View **code MIT**, bundled noncommercial and ODbL datasets **not MIT**.

## 4. Academic urgency and honest phone tracking

**Earliest confirmed outstanding deliverable:** HCI Phase 2 **30 Nov**. Before that: 23 Nov 10:00 requested MDS visit (not confirmed), and 14:30 Statistics professor offered 226CLAV. Software Methods current assessed `reservas@UÉvora` is distinct from historic LAN Party/Eventastic. December 9 Test 2 continuous-route conditional, 14 Dec Part 1 project recorded, mid-Dec Data F2 provisional; January dates require current official confirmation.

Six authentic Moodle submission receipts already exist (Web T1, HCI Phase 1, HCI video, three Data deliveries). **No grades, attendance approvals, mock results, actual study hours, exam registration or user progress ticked by this operation.** Existing public phone tracker at `study/exam-sprint.html`: **96 authored week tasks** on 20 Nov source, five weekly per-course source-review prompts and carry-forward queue. The private 20 Nov crosswalk clarifies remaining gates. No personal progress was exposed to public Pages.

## 5. Rota Única and almond status — PRIVATE ONLY

19 Nov a **14-family proposed almond-stage visual template with sources was actually SENT to David**, as verified by Gmail `SENT` and three attachments. This is not final acceptance. Preserve the existing work; **no duplicate sending**. 20 Nov David and Beatriz follow-ups are currently **DRAFT**, not sent. Aquagri API host confirmed, version/namespace/read unverified; FieldClimate supplier fee quote and portal reading exist, **API inactive**; SG50 LTE/TTN claimed activity is not same-event AGROTICS proof; real sensor end-to-end receipt still unverified. Internal private note links vendor/phenology literature and explicit David decisions.

**Rota CI blocker confirmed:** both baseline branch and new private branch GitHub Actions run `Validate project references` fail with **`Verification failed: Byte count mismatch: INDEX.md`** at existing manifest verification. On private branch job 136438900814, **1,212 unit tests pass (5 skipped)** before the catalog check fails. This is NOT fixed by the new documentation-only commit. The established [catalog builder](https://github.com/Hostilian/rota-unica-rd/blob/main/catalog/build_reference_catalog.py) is the supported repair route, but its full provenance-preserving rebuild and post-rebuild verification were not performed in this pass. Do not fake green CI or rewrite archive hashes blindly.

## 6. Supervisor and manuscript gates

Prepared **UNSENT** supervisor email and one-page technical review in this branch. Working question A remains a proposed research formulation, **not formal assignment approval**; no independent extraction of the registered CZU thesis assignment. Manuscript Chapters 5–7 were already corrected in Markdown previously, but existing LaTeX/PDF may still contain unsupported results. **Manuscript/PDF reconciliation not completed.**

## 7. Quality gate summary

| Gate | Result | Evidence/remaining issue |
|---|---|---|
| Preservation | PASS for branch and main ref | Named preservation ref; live public V2/V3/V4 routes 200 |
| Functionality | PASS (experimental local) | 102 tests; real observation run; Chrome DOM smoke |
| Component integration | PASS (experimental only) | GeoJSON data loads and map renders; not production Pages |
| Input authenticity | PASS for selected source pixels | Real STAC Item IDs and signed COG reads, corrected ESA offset |
| Scientific validation | **NOT PASSED** | No event ground truth, multi-date evaluation, independent researcher or original economic-data evidence |
| License / dependency gate | PARTIAL | Existing libraries; 31 candidate triage, some license/transitive review incomplete |
| Data privacy | No private source in public new artifacts known | No formal third-party penetration/privacy audit |
| Usability / accessibility | PARTIAL | Desktop/mobile smoke; no keyboard/AT/user study or lighthouse score |
| Academic compliance | PARTIAL | Private source-grounded crosswalk, formal CZU/Moodle conditions still open |
| Reproducibility | PARTIAL | One real run repeated on connected Windows laptop; independent second-machine rerun not done |
| Operational Rota verifier | **FAILED** (baseline issue) | INDEX.md byte mismatch despite 1,212 suite tests passing |

## 8. Concrete next actions

1. **Graduation first:** prepare genuine HCI Phase 2 by 30 Nov; study Statistics and prepare for 23 Nov office meeting; verify exact MDS Part 1 brief before modifying old LAN Party project.
2. **Research:** independently inspect ESA baseline and cloud/QA uncertainties; extend two-scene to at least three seasonally aligned dates, with no model-score claim until independent labels exist.
3. **Manuscript:** regenerate aligned LaTeX from corrected Markdown and inspect the PDF and all numerical citations; obtain registered topic and supervisor acceptance.
4. **Website:** keep `main` unchanged; review experimental route with user before GitHub Pages promotion. Browser interactivity is local/prototype, not a publicly deployed result.
5. **Private Rota:** do not resend almond template; obtain David's selection and stage definitions. Fix pre-existing private catalog mismatch using provided builder in an isolated worktree before merging Rota brief. No operational provider/API key action without owner consent.
6. **Testing:** isolate side effects in existing financial-feed test so rerunning tests does not alter tracked data. Run lint/dependency security review and an independent scientific reproduction when possible.

**No emails, Slack/WhatsApp, academic submissions, supplier mutations, purchases, private-source publication, force-push or production-site replacements were performed by this operation.**

### Handoff pointers
[Thesis ADR](ADR-THESIS-CONVERGENCE-20261120.md) · [Reuse catalog](OPEN_SOURCE_REUSE_CATALOG_20261120.md) · [Skills](AGENT_SKILLS_SELECTION_20261120.md) · [Supervisor email draft](SUPERVISOR_UPDATE_DRAFT_20261120-NO-SEND.md) · [Supervisor brief](SUPERVISOR_TECHNICAL_BRIEF_20261120.md) · [Experimental README](../experimental/geo-intelligence/README.md).

**Rollback:** Production SHA `feed5e6fb17c4149c9c64b396b091776c2e32641` untouched and preservation ref `preserve/main-20261120-feed5e6`. Isolated branch can be reviewed without merging, and old public routes remain served; do not delete experimental history.

# Operation Thesis Convergence — 22 November 2026 handoff addendum

**Status: REVIEW BRANCH INTEGRATED; PRODUCTION UNCHANGED; SCIENCE EXPLORATORY; NO EXTERNAL SEND.**

## 1. What changed since the 20 November release audit

The public thesis `main` advanced independently to **`0dbcd8d6b50b4e3c106ef4543fe76257d778a56a`** with safe AI-toolchain additions. The scientific branch based on `feed5e6...` had 20 further commits. GitHub comparisons showed **disjoint changed paths** (15 scientific/new experimental files versus eight toolchain additions).

Created **`operation/thesis-convergence-integrated-20261122`** as a review-only merge of both histories. Merge commit **`6b39191bbbb64fc801829357f05e9af2a37ba951`** has main and `operation/thesis-convergence-20261120` as parents. GitHub confirmed main→review `ahead=21, behind=0` and research→review `ahead=9, behind=0`. New current-main preservation ref: **`preserve/main-20261122-0dbcd8`**. Neither production `main`, satellite default, `docs/index3.html` nor `docs/index4.html` was changed by this merge.

**NOTE:** Do not automatically merge to `main`. The integrated commit was assembled from Git blobs and verified by tree comparison, **not retested end-to-end on a newly running machine**. GitHub branch CI has not been confirmed. Existing security, accessibility, reproducibility and third-party license gates remain open.

## 2. Science and minimum software reuse

The existing `planetary-computer`, `pystac-client`, `rasterio`/WarpedVRT, NumPy and `GeospatialPreprocessor` implementations acquired two real public Sentinel-2 L2A products. Both selected scenes have processing baseline 05.11 and require BOA offset **-1000 DN** for the native PC assets; this correction is present in the branch code and source manifest. The observed exploratory comparison yielded **6,512** valid paired pixels, **116** GeoJSON blocks, a median NDVI change of **-0.01017457477** and **zero** pixels crossing the arbitrary illustrative threshold -0.15.

This is **not** proof of environmental/resource anomalies or any economic relationship. The 10 public anomaly records remain synthetic and the old V2/V3/V4 web experiences remain intact. The new experiment is at `docs/experimental/geo-intelligence/` in the review branch, **not available on production GitHub Pages** without an owner-approved promotion.

The trial explicitly reused **Leaflet** from the existing web stack, with GeoJSON as the interface. A full God's Eye View fork, paid image/model APIs, new database, Grafana backend or extra map rendering framework were **not** added. The [31-candidate reuse catalog](OPEN_SOURCE_REUSE_CATALOG_20261120.md) is an initial license-aware triage, not a completed transitive dependency/security audit.

## 3. Tests: truthful accounting

Prior Windows run on 20 November: **102 tests passed** in the full thesis suite, before the final `test_api_server.py` isolation patch. Another later focused run on the remote laptop: **28 tests passed** after Sentinel-2 radiometry correction. The final minimal patch **`24afed10b200984ba95b5a3cffe39c91d40b5eb0`** replaces webhook test writing to `docs/data/financial_feed.json` with standard pytest `tmp_path` and `monkeypatch`; a **new CI result for that patch is not verified**.

On 22 November, the authorized remote Windows laptop was **offline**. No new real-pixel acquisition, independent external reproduction, browser accessibility audit or latest-branch full CI test should be claimed. The previous screenshot + DOM smoke demonstrated local rendering only; GitHub Pages production experimental route is intentionally absent.

**Recheck command (after remote access returns):**
```powershell
python -m pytest pipeline/tests -q --basetemp=C:/Users/Hostilian/Documents/tesis-pytest-tmp-integration --disable-warnings --maxfail=3
```
Run in a clean checkout of the integrated review branch, with dependencies installed in a local ignored virtual environment. Confirm `git status --short` unchanged after tests; inspect `financial_feed.json`, dependency security, and CI. Then run existing scientific live script and compare exact source manifests. No synthetic fallback is acceptable for observed data.

## 4. Academic and course boundary

An independent HCI Phase 2 review-only branch, [`operation/hci-phase2-evidence-20261122`](https://github.com/Hostilian/AlunUE-Agua-Pelo-Caminho/tree/operation/hci-phase2-evidence-20261122), preserves the HCI app main state and adds a source-grounded Portuguese design dossier. It reuses the app's actual four tabs, scenario links to Phase 1, existing research kit/SUS and map engine. This is **not** a Moodle submission or grade. HCI Phase 2 is due **30 Nov** per prior instructor notice; official close hour and any additional rubric must be verified.

Current MDS project is **`reservas@UÉvora`**, not the historical LAN Party/Eventastic proposal. Its Part 1 deadline is recorded for **14 Dec** but exact rubric, part 2 and formal individual permission remain unresolved. Written final-exam plans do not automatically waive mandatory practical work or attendance conditions. Six previous Moodle submission email receipts remain credible specific receipt evidence, **not** grades or guaranteed credit.

On **23 Nov** a 10:00 Software Methods teacher visit is a student-requested placeholder (not confirmed); at **14:30** Statistics professor offered a conversation in office 226CLAV (student's acceptance remains an unsent draft). No attendance or professor agreement inferred.

## 5. Supervisor package and integrity

The unsent email and detailed one-page Markdown briefing are in `docs/research/` on the integrated review branch. A locally rendered one-page A4 PDF dated **22 Nov 2026** was provided to the user in the ChatGPT conversation; **not committed to this repository** and **not sent**. Source question A remains working wording, not a formal CZU assignment change. Existing manuscript Markdown Ch. 5–7 was revised previously; **the LaTeX and thesis PDF still require genuine reconciliation before submission**.

## 6. Private agricultural scope

Rota Única's internal decision brief remains in the **private** `operation/thesis-convergence-private-20261120` branch. No private farm geometry, lab rows, device credentials or commercial imagery were copied to public thesis assets. Previously documented private blockers remain live: authentic supplier API read, same-event TTN→AGROTICS proof, device-to-field mapping, independently observed almond-stage labels and David's acceptance/owner decisions. The private reference-catalog `INDEX.md` byte-count mismatch was **not** repaired here; previous Rota CI remains failed despite the offline unit tests reported in the private baseline.

## 7. Next execution gates (no approval implied)

1. **Graduation:** student review HCI Phase 2 and complete real required artifacts before 30 November; verify MDS actual `reservas@UÉvora` brief; study Statistics and seek explicit final-route/practical eligibility.
2. **Science:** cross-validate product metadata and SCL at native grid/resolution; add seasonally comparable observations and simple robust baseline; document exact acquisition and output hashes. Do **not** claim detection scores without independent labels.
3. **Release:** rerun full tests after webhook isolation, inspect merged workflow behavior, check external dependencies, local browser desktop/mobile, accessibility, and original routes. Production promotion only after user approval.
4. **Manuscript:** reconcile current Markdown/LaTeX/PDF, real references, unverified empirical claims and academic instructions; request supervisor decision from unsent draft.
5. **Rota:** preserve private operational statuses and avoid any credential/paid activation or duplicate outreach.

**Hard boundaries:** no emails, Slack/WhatsApp/DMs, external applications, Moodle submissions, paid API use, raw farm data export, forced ref updates, or public deployment were performed in this operation.

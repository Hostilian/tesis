# World Bank live/mock evidence and test-isolation audit — 22 November 2026

**Status:** experimental repair branch only; no change to `main`, registered thesis topic, public site, or university submissions.

## Failure reproduced

An existing `mock_mode=True` mineral-dependency test unexpectedly used the live World Bank endpoint. When the upstream endpoint returned HTTP 502, the HTTP fallback produced a shape not compatible with the expected World Bank observations (`KeyError: 'date'`). The first full rerun had **101 passing, 1 failing** test in 47.69 seconds. Separately, another supposedly mock GDP test used default live configuration and wrote new `vintage` timestamps into a tracked historical economic JSON cache. A financial webhook test previously appended test payloads into a tracked financial-feed file.

## Repair — reuse existing project code and pytest

1. **Offline fixtures:** `fetch_worldbank_indicator` uses the repository's existing deterministic `_mock_worldbank_values` immediately in `mock_mode=True`. It does not read the live cache, contact a service, or write live data.
2. **Live failure fails closed:** the real World Bank request no longer substitutes mock values upon API errors. An empty result stays missing, and `fetch_mineral_dependency_index` refuses to calculate a composite without both indicators.
3. **Do not trust old mixed caches:** live cache files now use a distinct `wb_live_v2_*` prefix, locally ignored. Previously tracked `wb_*.json` files were preserved as historical snapshots, not adopted as independently verified measurements.
4. **Explicit provenance:** economic observations distinguish `source` and `synthetic_data`. Derived mineral scores disclose whether the source was deterministic mock fixtures or a World Bank response. Their invented employment proxy and weighting are still illustrative, not external empirical measurements.
5. **Isolated existing tests:** the existing webhook test redirects its data file to pytest's `tmp_path`; existing GDP and mineral tests explicitly select mock mode, verify the labels, and fail if a network call is attempted.

## Repeatable local validation

On the remote Windows laptop using installed Python 3.12 and existing dependencies:

```powershell
python -m pytest pipeline/tests -q --disable-warnings --maxfail=2 --basetemp=C:\Users\Hostilian\Documents\tesis-pytest-verified-20261122
```

**Result: 102 passed in 19.84s.** The tracked `docs/data/financial_feed.json` and `docs/data/economic/wb_NY.GDP.MKTP.KD.ZG_CZE_2021_2025.json` SHA object IDs remained unchanged. Local audit receipts are saved privately under `C:\Users\Hostilian\Documents\ConvergenceAudits-20261122\`; these are not published evidence or a CI endorsement.

## Evidence boundaries / follow-up

- Passing offline unit tests does **not** confirm current live World Bank availability, data completeness, response schema for all indicators, or source-specific composite validity.
- Older economic mock fixtures, threshold heuristics, model scores, and generated financial data do **not** demonstrate a validated satellite/economics relationship.
- A future live evaluation needs an accessible response, indicator definitions and vintage, explicit missingness, and independent cross-checks. Do not cite a fixture as observed economic truth.
- A supervisor-reviewed formal thesis question, independent ground truth, controlled temporal experiment, and manuscript citation audit remain open.
- No provider settings, credentials, production branches, company records, emails, university submissions, or payments were changed by this repair.

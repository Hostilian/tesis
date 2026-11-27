"""Browser test of the published case-study page (docs/case-study/index.html).

Serves docs/ locally under /tesis/ (as on GitHub Pages) with http.server, opens
the page in headless Chromium and checks, for each case:

* the page loads with no console errors and no uncaught exceptions;
* the Key numbers table shows the numbers in results.json (formatted the way
  the page formats them);
* the Checks list reports the independent re-computation from
  independent_check.json.

Map tiles are answered with a 1x1 PNG, so no tile server is contacted.
Leaflet comes from its CDN; set TESIS_LEAFLET_DIR to a folder holding
leaflet.js and leaflet.css (version 1.9.4) to run fully offline. The test is
skipped, not failed, when Playwright, a browser or Leaflet is unavailable.

Run:  pip install playwright && python -m playwright install chromium
      python -m pytest pipeline/tests/test_case_study_page.py -q
"""

from __future__ import annotations

import base64
import functools
import http.server
import json
import os
import threading
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Iterator

import pytest

sync_api = pytest.importorskip("playwright.sync_api")

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
DATA = DOCS / "case-study" / "data"
CASES = ["alqueva_olive", "neves_corvo_mine"]
# Files the page requests with getJSON(path, optional=true).
OPTIONAL_FILES = {
    "reference_cos.json",
    "patches.geojson",
    "reference_cos2025v1.geojson",
    "independent_check.json",
    "robustness.json",
    "interop_planetary_computer.json",
}
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def fmt(x: Any, d: int = 0) -> str:
    """Python twin of the page's fmt(): en-GB grouping, round half away from zero."""
    if x is None:
        return "–"
    q = Decimal(x).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return f"{q:,.{d}f}"


def pct(x: Any, d: int = 1) -> str:
    return "–" if x is None else fmt(100 * x, d) + " %"


class _Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        if path.startswith("/tesis/"):
            path = path[len("/tesis") :]
        return super().translate_path(path)

    def log_message(self, *args: Any) -> None:
        pass


@pytest.fixture(scope="module")
def site() -> Iterator[str]:
    handler = functools.partial(_Handler, directory=str(DOCS))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/tesis/case-study/"
    srv.shutdown()
    srv.server_close()


@pytest.fixture(scope="module")
def browser() -> Iterator[Any]:
    with sync_api.sync_playwright() as p:
        b = None
        for kwargs in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
            try:
                b = p.chromium.launch(**kwargs)
                break
            except Exception:
                continue
        if b is None:
            pytest.skip("no Chromium-based browser available to Playwright")
        yield b
        b.close()


def _serve_leaflet(route: Any) -> None:
    local = os.environ.get("TESIS_LEAFLET_DIR")
    name = route.request.url.rsplit("/", 1)[-1]
    if local and (Path(local) / name).exists():
        ctype = "text/css" if name.endswith(".css") else "application/javascript"
        route.fulfill(
            body=(Path(local) / name).read_bytes(),
            content_type=ctype,
            headers={"Access-Control-Allow-Origin": "*"},
        )
        return
    route.continue_()


@pytest.mark.parametrize("case_id", CASES)
def test_case_study_page_shows_published_numbers(
    site: str, browser: Any, case_id: str
) -> None:
    results = json.loads((DATA / case_id / "results.json").read_text(encoding="utf-8"))
    ctx = browser.new_context(viewport={"width": 1366, "height": 900})
    page = ctx.new_page()
    errors: list[str] = []
    missing_files: list[str] = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on(
        "response", lambda r: missing_files.append(r.url) if r.status == 404 else None
    )
    page.on("pageerror", lambda e: errors.append(f"uncaught: {e}"))
    page.route(
        "**/server.arcgisonline.com/**",
        lambda r: r.fulfill(body=PNG_1PX, content_type="image/png"),
    )
    page.route(
        "**/*.tile.openstreetmap.org/**",
        lambda r: r.fulfill(body=PNG_1PX, content_type="image/png"),
    )
    page.route("**/cdn.jsdelivr.net/npm/leaflet@1.9.4/**", _serve_leaflet)
    try:
        page.goto(site + "#" + case_id, wait_until="load")
        if not page.evaluate("typeof window.L !== 'undefined'"):
            pytest.skip("Leaflet could not be loaded (offline? set TESIS_LEAFLET_DIR)")
        page.wait_for_selector("#numbers table", timeout=15_000)
        page.wait_for_selector(
            "#checks ul, #checks p:not(:has-text('Loading'))", timeout=15_000
        )
        page.wait_for_load_state("networkidle")

        assert page.locator("#case").input_value() == case_id
        table = page.locator("#numbers table").inner_text()
        c, cov, th = results["change"], results["coverage"], results["threshold"]
        expected = {
            "joint valid pixels": f"{fmt(cov['joint_valid_pixels_main'])} ({pct(cov['joint_valid_fraction_main'])})",
            "threshold": fmt(th["value"], 3),
            "control flagged share": pct(c["control_flagged_share_at_threshold"], 2),
            "increase area": f"{fmt(c['increase_area_ha'], 0)} ha ({pct(c['increase_share_of_valid'])})",
            "decrease area": f"{fmt(c['decrease_area_ha'], 0)} ha ({pct(c['decrease_share_of_valid'])})",
            "area of interest": f"{fmt(results['aoi']['area_km2'], 1)} km²",
            "dates": f"{results['dates']['before'][:10]} → {results['dates']['after'][:10]}",
        }
        missing = {k: v for k, v in expected.items() if v not in table}
        assert (
            not missing
        ), f"not shown in Key numbers: {missing}\n--- table ---\n{table}"

        ind_path = DATA / case_id / "independent_check.json"
        if ind_path.exists():
            ind = json.loads(ind_path.read_text(encoding="utf-8"))
            checks = page.locator("#checks").inner_text()
            if ind["all_match"]:
                assert f"all {len(ind['comparisons'])} headline numbers match" in checks
            else:
                assert "mismatch" in checks
        # The page asks for some per-case files with getJSON(..., optional=true) and
        # skips them when absent (e.g. no Planetary Computer cross-check for the mine).
        # Chromium logs each such 404 as a console error; those, and only those, are allowed.
        unexpected_404 = [
            u for u in missing_files if u.rsplit("/", 1)[-1] not in OPTIONAL_FILES
        ]
        assert unexpected_404 == [], unexpected_404
        real_errors = [
            e
            for e in errors
            if not (e.startswith("Failed to load resource") and "404" in e)
        ]
        assert real_errors == [], real_errors
        assert len(errors) - len(real_errors) == len(missing_files)
    finally:
        ctx.close()

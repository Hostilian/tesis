"""Offline tests for thesis/tools/question_worker.py. No network."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "thesis" / "tools"))

import question_worker as qw  # noqa: E402
from pipeline.src import llm_gateway as gw  # noqa: E402

BACKLOG_SAMPLE = """\
| # | Question | Who | Evidence |
|---|---|---|---|
| B2 ✔ | Done item, must be skipped | AI | x |
| B3 | Does the result hold for 2019? | AI | x |
| C1 | Are bootstrap CIs too narrow? | AI | x |
| A1 | Can the title stay? | SUPERVISOR | x |
| E1 | Write chapter 1 facts | AI (fact list only) | x |
"""


def test_open_ai_items_skips_done_and_non_ai_rows():
    items = qw.open_ai_items(BACKLOG_SAMPLE)
    ids = [i for i, _ in items]
    assert ids == ["B3", "C1", "E1"]  # B2 done, A1 not AI-owned


def test_prompt_for_picks_category_and_forces_headers():
    prompt, headers = qw.prompt_for("C1", "Are bootstrap CIs too narrow?")
    assert headers == [
        "## Test type",
        "## Data (synthetic or real run)",
        "## Pass/fail threshold",
        "## File to add it to",
    ]
    assert all(h in prompt for h in headers)


def test_prompt_for_e_category_forbids_prose():
    prompt, headers = qw.prompt_for("E1", "x")
    assert "results, discussion or conclusions" in prompt
    assert "## What NOT to write (AI boundary)" in headers


def test_unknown_category_uses_default_prompt():
    _, headers = qw.prompt_for("Z9", "x")
    assert headers == qw.DEFAULT_PROMPT[1]


def test_well_formed_checks_every_header_present():
    headers = ["## A", "## B"]
    assert qw.well_formed("## A\nfoo\n## B\nbar", headers)
    assert not qw.well_formed("## A\nfoo only", headers)


def ok_body(text: str) -> bytes:
    return json.dumps({"choices": [{"message": {"content": text}}]}).encode()


def test_run_item_success_first_try():
    provider = gw.ProviderConfig("openrouter", gw.OPENROUTER_BASE, "k")
    good = "## Test type\nx\n## Data (synthetic or real run)\nx\n## Pass/fail threshold\nx\n## File to add it to\nx"

    def transport(req, timeout):
        return 200, ok_body(good)

    text, fallback, warnings = qw.run_item(
        provider, "C1", "q", "cheap-model", transport=transport
    )
    assert not fallback and not warnings
    assert "FAILED" not in text and "FORMAT WARNING" not in text


def test_run_item_falls_back_when_cheap_model_rejected():
    provider = gw.ProviderConfig("openrouter", gw.OPENROUTER_BASE, "k")
    good = "## Checks\nx\n## Evidence\nx\n## Would change the thesis if\nx"
    calls = []

    def transport(req, timeout):
        body = json.loads(req.data)
        calls.append(body["model"])
        if body["model"] == "bad-cheap-model":
            return 400, b'{"error": "unknown model"}'
        return 200, ok_body(good)

    text, fallback, warnings = qw.run_item(
        provider, "Z9", "q", "bad-cheap-model", transport=transport
    )
    assert fallback is True
    assert calls == ["bad-cheap-model", gw.DEFAULT_MODEL]
    assert "FAILED" not in text


def test_run_item_retries_once_on_malformed_reply_then_accepts():
    provider = gw.ProviderConfig("openrouter", gw.OPENROUTER_BASE, "k")
    good = "## Checks\nx\n## Evidence\nx\n## Would change the thesis if\nx"
    calls = {"n": 0}

    def transport(req, timeout):
        calls["n"] += 1
        text = "I did not use the headers at all" if calls["n"] == 1 else good
        return 200, ok_body(text)

    text, fallback, warnings = qw.run_item(
        provider, "Z9", "q", "m", transport=transport
    )
    assert calls["n"] == 2
    assert "FAILED" not in text and "FORMAT WARNING" not in text


def test_run_item_never_raises_even_when_every_call_fails():
    provider = gw.ProviderConfig("openrouter", gw.OPENROUTER_BASE, "k")

    def transport(req, timeout):
        return 503, b"down"

    text, fallback, warnings = qw.run_item(
        provider, "Z9", "q", "m", transport=transport, sleep=lambda s: None
    )
    assert "FAILED" in text
    assert warnings


def test_build_context_contains_published_numbers_and_no_secrets():
    ctx = qw.build_context()
    assert "alqueva_olive" in ctx and "increase_area_ha" in ctx
    assert "run_case_study.py" in ctx
    assert len(ctx) < 6000
    assert "API_KEY" not in ctx


def test_build_context_survives_missing_files(tmp_path):
    ctx = qw.build_context(tmp_path)
    assert ctx.startswith("Repository facts")


def test_prompt_includes_context_and_forbids_questions_back():
    text, _ = qw.prompt_for("B3", "Other summers?", "CTX-MARKER")
    assert "CTX-MARKER" in text
    assert "do not ask the student questions" in text

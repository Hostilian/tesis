"""Offline tests for the model gateway. No network: transport is faked."""

from __future__ import annotations

import json

import pytest

from pipeline.src import llm_gateway as gw


def ok_body(text: str = "hello") -> bytes:
    return json.dumps({"choices": [{"message": {"content": text}}]}).encode()


def test_missing_openrouter_key_is_refused():
    with pytest.raises(gw.GatewayError, match="OPENROUTER_API_KEY"):
        gw.load_provider("openrouter", env={})


def test_omniroute_falls_back_to_public_openrouter_endpoint():
    # Matches the owner's own va_orchestrator.py fallback when no local proxy is set.
    p = gw.load_provider("omniroute", env={"OMNIROUTE_API_KEY": "x"})
    assert p.base_url == gw.OPENROUTER_BASE


def test_omniroute_uses_its_own_url_when_set():
    p = gw.load_provider(
        "omniroute",
        env={
            "OMNIROUTE_API_KEY": "x",
            "OMNIROUTE_BASE_URL": "http://localhost:20128/api/v1",
        },
    )
    assert p.base_url == "http://localhost:20128/api/v1"


def test_omniroute_still_needs_its_own_key():
    with pytest.raises(gw.GatewayError, match="OMNIROUTE_API_KEY"):
        gw.load_provider(
            "omniroute", env={"OMNIROUTE_BASE_URL": "https://r.example/v1"}
        )


def test_unknown_provider_refused():
    with pytest.raises(gw.GatewayError, match="unknown provider"):
        gw.load_provider("some-pool", env={"OPENROUTER_API_KEY": "x"})


def test_request_carries_bearer_header_and_returns_text():
    seen = {}

    def transport(req, timeout):
        seen["auth"] = req.get_header("Authorization")
        seen["url"] = req.full_url
        return 200, ok_body("answer")

    p = gw.load_provider("openrouter", env={"OPENROUTER_API_KEY": "sk-test-123456789"})
    out = gw.chat(p, [{"role": "user", "content": "q"}], transport=transport)
    assert out == "answer"
    assert seen["auth"] == "Bearer sk-test-123456789"
    assert seen["url"].endswith("/chat/completions")


def test_retries_rate_limit_then_succeeds():
    calls = []
    sleeps = []

    def transport(req, timeout):
        calls.append(1)
        return (429, b"slow down") if len(calls) < 2 else (200, ok_body("done"))

    p = gw.load_provider("openrouter", env={"OPENROUTER_API_KEY": "k"})
    assert gw.chat(p, [], transport=transport, sleep=sleeps.append) == "done"
    assert len(calls) == 2 and sleeps == [2.0]


def test_auth_failure_is_not_retried_and_key_is_redacted():
    calls = []

    def transport(req, timeout):
        calls.append(1)
        return 401, b'{"error": "bad key sk-secretsecret123"}'

    p = gw.load_provider("openrouter", env={"OPENROUTER_API_KEY": "sk-secretsecret123"})
    with pytest.raises(gw.GatewayError) as err:
        gw.chat(p, [], transport=transport)
    assert len(calls) == 1
    assert "sk-secretsecret123" not in str(err.value)


def test_gives_up_after_attempts_on_persistent_server_error():
    calls = []

    def transport(req, timeout):
        calls.append(1)
        return 503, b"unavailable"

    p = gw.load_provider("openrouter", env={"OPENROUTER_API_KEY": "k"})
    with pytest.raises(gw.GatewayError, match="503"):
        gw.chat(p, [], transport=transport, attempts=3, sleep=lambda s: None)
    assert len(calls) == 3

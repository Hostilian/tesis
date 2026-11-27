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


# ---- key-free providers: local OmniRoute and the owner's Claude CLI ----


def test_auto_prefers_openrouter_key_when_present():
    p = gw.auto_provider({"OPENROUTER_API_KEY": "k"}, probe=lambda _: True)
    assert p.name == "openrouter"


def test_auto_uses_local_omniroute_only_if_it_answers():
    p = gw.auto_provider({"CLAUDE_CLI_PATH": "claude"}, probe=lambda _: True)
    assert p.name == "omniroute-local" and p.base_url == gw.OMNIROUTE_LOCAL_BASE
    p = gw.auto_provider({"CLAUDE_CLI_PATH": "claude"}, probe=lambda _: False)
    assert p.name == "claude-cli"


def test_auto_can_skip_local_omniroute():
    env = {"CLAUDE_CLI_PATH": "claude", "GATEWAY_TRY_OMNIROUTE_LOCAL": "0"}
    assert gw.auto_provider(env, probe=lambda _: True).name == "claude-cli"


def test_local_probe_refuses_non_local_urls():
    assert gw._local_omniroute_up("https://openrouter.ai/api/v1") is False


def test_omniroute_local_sends_no_auth_header_without_key():
    seen = {}

    def transport(req, timeout):
        seen["auth"] = req.get_header("Authorization")
        seen["body"] = json.loads(req.data)
        return 200, ok_body("ok")

    p = gw.load_provider("omniroute-local", env={})
    assert gw.chat(p, [{"role": "user", "content": "q"}], transport=transport) == "ok"
    assert seen["auth"] is None
    assert seen["body"]["model"] == gw.OMNIROUTE_LOCAL_MODEL


def test_claude_cli_runs_with_tools_disabled_and_cheap_model():
    seen = {}

    def runner(argv, stdin, timeout):
        seen["argv"], seen["stdin"] = argv, stdin
        return 0, " answer \n", ""

    p = gw.ProviderConfig("claude-cli", "claude", "")
    out = gw.chat_cli(
        p,
        [{"role": "system", "content": "S"}, {"role": "user", "content": "Q"}],
        runner=runner,
    )
    assert out == "answer"
    a = seen["argv"]
    assert a[a.index("--tools") + 1] == ""
    assert a[a.index("--model") + 1] == "haiku"
    assert a[a.index("--system-prompt") + 1] == "S"
    assert seen["stdin"] == "Q"


def test_claude_cli_maps_openrouter_slugs_to_aliases():
    assert gw._cli_alias("anthropic/claude-sonnet-4.5") == "sonnet"
    assert gw._cli_alias("anthropic/claude-opus-4.6") == "opus"
    assert gw._cli_alias("something-else") == "haiku"


def test_claude_cli_retries_then_raises_clean_error():
    calls = []

    def runner(argv, stdin, timeout):
        calls.append(1)
        return 1, "", "boom sk-abcdefghijklmnop"

    p = gw.ProviderConfig("claude-cli", "claude", "")
    with pytest.raises(gw.GatewayError) as e:
        gw.chat_cli(p, [{"role": "user", "content": "q"}], runner=runner, sleep=lambda s: None)
    assert len(calls) == 2
    assert "sk-abcdefghijklmnop" not in str(e.value)


def test_fallback_models_differ_per_provider():
    assert gw.fallback_model(gw.ProviderConfig("claude-cli", "c", "")) == "sonnet"
    assert gw.fallback_model(gw.ProviderConfig("openrouter", "u", "k")) == gw.DEFAULT_MODEL

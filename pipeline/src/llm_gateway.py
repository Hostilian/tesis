"""Model gateway for OpenRouter (and any OpenAI-compatible router such as OmniRoute).

Pattern copied in simplified form from the owner's Venture Atlas control plane:
keys belong to the owner, are read at runtime from the environment (or from
Google Secret Manager when the owner configures it), and are never stored in
the repository. There is no key pooling, collection or sharing here.

Standard library only. Chat requests use the OpenAI-compatible
``/chat/completions`` route.

Environment variables (set by the owner, never committed):
  OPENROUTER_API_KEY     required for provider "openrouter"
  OMNIROUTE_BASE_URL     optional for provider "omniroute"; defaults to the
                         public OpenRouter endpoint if no local proxy is set
                         (same fallback as the owner's va_orchestrator.py)
  OMNIROUTE_MODEL        optional model override for provider "omniroute"
  OMNIROUTE_API_KEY      required for provider "omniroute"
  GATEWAY_MODEL          optional, default "anthropic/claude-opus-4.6"

Hermes is an agent runtime. In the owner's Hermes config it sends requests to
OpenRouter, so it is reached through the "openrouter" provider here.

Two providers need no API key in this repository at all:
  "omniroute-local"  the owner's own OmniRoute proxy on this laptop
                     (http://localhost:20128/v1 by default). OmniRoute keeps
                     its provider logins in its own encrypted store.
  "claude-cli"       the owner's own Claude Code CLI (``claude -p``), signed in
                     with their own Claude account. Runs with every tool
                     disabled, so it can only answer text.
"auto" picks the first one that is usable: OpenRouter key, OmniRoute key,
local OmniRoute (only if it answers), then the Claude CLI.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-opus-4.6"
OMNIROUTE_LOCAL_BASE = "http://localhost:20128/v1"
OMNIROUTE_LOCAL_MODEL = "auto/cheap"
# Claude CLI model aliases: cheapest first. "haiku" is the default for the
# repetitive question worker; "sonnet" is the one-time fallback.
CLAUDE_CLI_MODEL = "haiku"
CLAUDE_CLI_FALLBACK = "sonnet"
RETRY_STATUSES = {429, 500, 502, 503, 504}


class GatewayError(RuntimeError):
    """Raised for configuration or request failures. Never contains a key."""


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    base_url: str
    api_key: str


def _redact(text: str, secrets: Sequence[str]) -> str:
    out = text
    for s in secrets:
        if s:
            out = out.replace(s, "<redacted>")
    return re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "<redacted>", out)


def load_provider(name: str, env: Mapping[str, str] | None = None) -> ProviderConfig:
    """Build a provider from the owner's environment. Raises if its key is missing."""
    env = os.environ if env is None else env
    if name == "openrouter":
        key = env.get("OPENROUTER_API_KEY", "")
        base = env.get("OPENROUTER_BASE_URL", OPENROUTER_BASE)
        var = "OPENROUTER_API_KEY"
    elif name == "omniroute":
        key = env.get("OMNIROUTE_API_KEY", "")
        # Matches the owner's own eushop/va_orchestrator.py: when no local
        # OmniRoute proxy is configured, it falls back to the public OpenRouter
        # endpoint. That fallback is documented in their public config
        # (config/providers.json: baseUrlEnv "OMNIROUTE_BASE_URL"), not a secret.
        base = env.get("OMNIROUTE_BASE_URL", OPENROUTER_BASE)
        var = "OMNIROUTE_API_KEY"
    elif name == "omniroute-local":
        base = env.get("OMNIROUTE_BASE_URL", OMNIROUTE_LOCAL_BASE)
        return ProviderConfig(
            name=name,
            base_url=base.rstrip("/"),
            api_key=env.get("OMNIROUTE_API_KEY", ""),
        )
    elif name == "claude-cli":
        exe = env.get("CLAUDE_CLI_PATH") or shutil.which("claude")
        if not exe:
            raise GatewayError("the claude CLI was not found on PATH")
        return ProviderConfig(name=name, base_url=exe, api_key="")
    elif name == "auto":
        return auto_provider(env)
    else:
        raise GatewayError(
            f"unknown provider {name!r}; use 'openrouter', 'omniroute', "
            "'omniroute-local', 'claude-cli' or 'auto'"
        )
    if not key:
        raise GatewayError(f"{var} is not set; add your own key to the environment")
    return ProviderConfig(name=name, base_url=base.rstrip("/"), api_key=key)


Transport = Callable[[urllib.request.Request, float], tuple[int, bytes]]


def _local_omniroute_up(base: str, timeout: float = 3.0) -> bool:
    """True if a local OmniRoute answers at all (any HTTP status)."""
    if not base.startswith(("http://localhost", "http://127.0.0.1")):
        return False
    try:
        urllib.request.urlopen(  # noqa: S310 - localhost only
            base.rsplit("/v1", 1)[0] + "/", timeout=timeout
        ).close()
        return True
    except urllib.error.HTTPError:
        return True
    except (urllib.error.URLError, OSError):
        return False


def auto_provider(
    env: Mapping[str, str] | None = None,
    probe: Callable[[str], bool] = _local_omniroute_up,
) -> ProviderConfig:
    """First usable provider. Reads only the environment, never a file."""
    env = os.environ if env is None else env
    if env.get("OPENROUTER_API_KEY"):
        return load_provider("openrouter", env)
    if env.get("OMNIROUTE_API_KEY") and env.get("OMNIROUTE_BASE_URL"):
        return load_provider("omniroute", env)
    local = env.get("OMNIROUTE_BASE_URL", OMNIROUTE_LOCAL_BASE)
    if env.get("GATEWAY_TRY_OMNIROUTE_LOCAL", "1") == "1" and probe(local):
        return load_provider("omniroute-local", env)
    return load_provider("claude-cli", env)


def default_model(provider: ProviderConfig) -> str:
    if provider.name == "claude-cli":
        return CLAUDE_CLI_MODEL
    if provider.name == "omniroute-local":
        return os.environ.get("OMNIROUTE_MODEL", OMNIROUTE_LOCAL_MODEL)
    return os.environ.get("GATEWAY_MODEL", DEFAULT_MODEL)


def fallback_model(provider: ProviderConfig) -> str:
    if provider.name == "claude-cli":
        return CLAUDE_CLI_FALLBACK
    if provider.name == "omniroute-local":
        return "auto/best-free"
    return DEFAULT_MODEL


def _cli_alias(model: str | None) -> str:
    m = (model or "").lower()
    for alias in ("haiku", "sonnet", "opus"):
        if alias in m:
            return alias
    return CLAUDE_CLI_MODEL


CliRunner = Callable[[list[str], str, float], tuple[int, str, str]]


def _run_cli(argv: list[str], stdin: str, timeout: float) -> tuple[int, str, str]:
    try:
        r = subprocess.run(  # nosec B603 - fixed argv, no shell
            argv,
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"
    except OSError as exc:
        return 127, "", str(exc)


def chat_cli(
    provider: ProviderConfig,
    messages: list[dict[str, str]],
    model: str | None = None,
    *,
    timeout: float = 240.0,
    attempts: int = 2,
    runner: CliRunner = _run_cli,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Ask the owner's Claude CLI. Every tool is disabled: text in, text out."""
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    turns = [m for m in messages if m["role"] != "system"]
    if len(turns) == 1:
        prompt = turns[0]["content"]
    else:
        prompt = (
            "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in turns)
            + "\n\n[ASSISTANT]\n"
        )
    argv = [
        provider.base_url,
        "-p",
        "--model",
        _cli_alias(model),
        "--tools",
        "",
        "--no-session-persistence",
        "--strict-mcp-config",
        "--output-format",
        "text",
    ]
    if system:
        argv += ["--system-prompt", system]
    last = ""
    for i in range(1, attempts + 1):
        code, out, err = runner(argv, prompt, timeout)
        if code == 0 and out.strip():
            return out.strip()
        last = _redact((err or out)[:300], [])
        if i < attempts:
            sleep(5.0 * i)
    raise GatewayError(f"claude-cli failed (model {_cli_alias(model)}): {last}")


def _urlopen(req: urllib.request.Request, timeout: float) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(
            req, timeout=timeout
        ) as r:  # noqa: S310 (https endpoints only)
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def chat(
    provider: ProviderConfig,
    messages: list[dict[str, str]],
    model: str | None = None,
    *,
    max_tokens: int = 1200,
    temperature: float = 0.2,
    timeout: float = 90.0,
    attempts: int = 3,
    transport: Transport = _urlopen,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Send one chat request and return the assistant text.

    Retries on rate limits and server errors with exponential back-off.
    Authentication failures are not retried.
    """
    if provider.name == "claude-cli":
        return chat_cli(provider, messages, model, sleep=sleep)
    url = f"{provider.base_url}/chat/completions"
    body = json.dumps(
        {
            "model": model or default_model(provider),
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if provider.api_key:
        headers["Authorization"] = f"Bearer {provider.api_key}"
    if provider.name == "openrouter":
        headers["X-Title"] = "thesis-case-study"
    last = ""
    if (
        model is None
        and provider.name == "omniroute"
        and os.environ.get("OMNIROUTE_MODEL")
    ):
        body = json.dumps(
            {**json.loads(body), "model": os.environ["OMNIROUTE_MODEL"]}
        ).encode("utf-8")
    for i in range(1, attempts + 1):
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        status, raw = transport(req, timeout)
        if status == 200:
            data = json.loads(raw.decode("utf-8"))
            try:
                return str(data["choices"][0]["message"]["content"])
            except (KeyError, IndexError, TypeError) as exc:
                raise GatewayError("unexpected response shape") from exc
        last = _redact(raw.decode("utf-8", "replace")[:300], [provider.api_key])
        if status not in RETRY_STATUSES or i == attempts:
            raise GatewayError(f"{provider.name} returned HTTP {status}: {last}")
        sleep(2.0**i)
    raise GatewayError(f"{provider.name} failed: {last}")

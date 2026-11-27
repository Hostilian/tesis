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
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-opus-4.6"
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
    else:
        raise GatewayError(
            f"unknown provider {name!r}; use 'openrouter' or 'omniroute'"
        )
    if not key:
        raise GatewayError(f"{var} is not set; add your own key to the environment")
    return ProviderConfig(name=name, base_url=base.rstrip("/"), api_key=key)


Transport = Callable[[urllib.request.Request, float], tuple[int, bytes]]


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
    url = f"{provider.base_url}/chat/completions"
    body = json.dumps(
        {
            "model": model or os.environ.get("GATEWAY_MODEL", DEFAULT_MODEL),
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
    ).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json",
    }
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

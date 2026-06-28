"""
http_resilience.py — Shared transport utilities for external API access.

Provides a single retry/backoff policy and a lightweight circuit breaker so
the pipeline can degrade cleanly into mock mode when external services are
unavailable or rate-limited.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import logging
import random
import time
from typing import Any, Callable, Optional

import requests

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 5
    base_delay: float = 1.5
    max_delay: float = 30.0
    jitter: float = 0.25
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504)


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout: float = 30.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    opened_at: Optional[float] = None
    trial_successes: int = 0
    half_open_success_threshold: int = 1
    last_failure: Optional[str] = None

    def allow_request(self, now: Optional[float] = None) -> bool:
        now = time.time() if now is None else now

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.opened_at is not None and (now - self.opened_at) >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.trial_successes = 0
                return True
            return False

        return True

    def record_success(self) -> None:
        self.failure_count = 0
        self.last_failure = None

        if self.state == CircuitState.HALF_OPEN:
            self.trial_successes += 1
            if self.trial_successes >= self.half_open_success_threshold:
                self.state = CircuitState.CLOSED
                self.opened_at = None
                self.trial_successes = 0

    def record_failure(self, reason: str, now: Optional[float] = None) -> None:
        now = time.time() if now is None else now
        self.failure_count += 1
        self.last_failure = reason

        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = now
            self.trial_successes = 0


@dataclass
class ResilientHTTPClient:
    session: requests.Session = field(default_factory=requests.Session)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    circuit_breaker: CircuitBreaker = field(default_factory=CircuitBreaker)

    def request_json(
        self,
        method: str,
        url: str,
        *,
        timeout: float = 10.0,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_body: Optional[dict[str, Any]] = None,
        data_body: Optional[dict[str, Any]] = None,
        fallback: Optional[Callable[[], Any]] = None,
        service_name: str = "external-api",
    ) -> Any:
        if not self.circuit_breaker.allow_request():
            logger.warning("Circuit breaker open for %s; using fallback.", service_name)
            if fallback is not None:
                return fallback()
            raise RuntimeError(f"Circuit breaker open for {service_name}")

        last_error: Optional[Exception] = None
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            try:
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    timeout=timeout,
                    headers=headers,
                    params=params,
                    json=json_body,
                    data=data_body,
                )
                if response.status_code in self.retry_policy.retry_statuses:
                    raise requests.HTTPError(
                        f"{service_name} returned {response.status_code}",
                        response=response,
                    )

                response.raise_for_status()
                self.circuit_breaker.record_success()
                return response.json()
            except Exception as exc:  # network failures, bad JSON, HTTP errors
                last_error = exc
                self.circuit_breaker.record_failure(str(exc))

                if attempt >= self.retry_policy.max_attempts:
                    logger.warning(
                        "%s failed after %d attempts: %s",
                        service_name,
                        attempt,
                        exc,
                    )
                    break

                delay = self._compute_delay(attempt)
                logger.info(
                    "%s attempt %d/%d failed: %s. Retrying in %.2fs.",
                    service_name,
                    attempt,
                    self.retry_policy.max_attempts,
                    exc,
                    delay,
                )
                time.sleep(delay)

        if fallback is not None:
            return fallback()

        if last_error is not None:
            raise last_error

        raise RuntimeError(f"{service_name} request failed without a captured exception")

    def _compute_delay(self, attempt: int) -> float:
        backoff = self.retry_policy.base_delay * (2 ** (attempt - 1))
        backoff = min(backoff, self.retry_policy.max_delay)
        jitter = random.uniform(0.0, self.retry_policy.jitter)
        return backoff + jitter


def stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=_json_default).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_default(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "item"):
        return value.item()
    return str(value)

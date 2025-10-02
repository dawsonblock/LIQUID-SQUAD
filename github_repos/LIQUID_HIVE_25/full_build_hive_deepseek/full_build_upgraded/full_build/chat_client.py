"""
Enhanced chat client and model tiering abstraction.

This module defines a robust interface for integrating language models
into the self‑loop system.  It builds upon the previous simple
implementation by introducing HTTP‑based model clients with timeouts,
retry logic and circuit‑breaker support.  These enhancements improve
reliability and make it easier to swap in different back‑ends such as
HuggingFace Inference Endpoints, vLLM servers or other hosted
services.  The `TieredChatClient` wraps multiple models of
different sizes and escalates to larger ones when smaller models
return unsatisfactory outputs or experience transient failures.
"""

from __future__ import annotations

import time
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class BaseChatClient:
    """Abstract base class for chat clients.

    Subclass this and implement the asynchronous `generate` method to
    integrate your LLM.  Each call should return a string response.
    """

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> str:
        raise NotImplementedError


@dataclass
class HttpModel(BaseChatClient):
    """Simple HTTP client for text generation models.

    Instances of this class communicate with a text generation API via
    POST requests.  The `base_url` should point at an endpoint
    compatible with the OpenAI chat completion API or a similar JSON
    format.  If an API key is required, supply it via the `api_key`
    parameter; the key will be passed in an Authorization header.

    A retry decorator handles transient network failures and
    transport‑level timeouts.  For more advanced control (e.g.
    circuit‑breaker patterns), use `TieredChatClient`.
    """

    base_url: str
    api_key: Optional[str] = None
    timeout: float = 20.0

    def __post_init__(self) -> None:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        self._client: httpx.AsyncClient = httpx.AsyncClient(
            base_url=self.base_url, timeout=self.timeout, headers=headers
        )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
    )
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> str:
        """Send a chat completion request and return the generated content.

        The payload format matches the OpenAI Chat Completion API.
        """
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        response = await self._client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


class CircuitBreaker:
    """Simple failure counter for circuit breaking.

    When a client returns errors more than `fail_threshold` times in
    succession, the circuit opens and will remain open for
    `cool_down` seconds.  During the open period, calls will be
    skipped.  Use `record` to update state after each call.
    """

    def __init__(self, fail_threshold: int = 5, cool_down: float = 30.0) -> None:
        self.failures: int = 0
        self.fail_threshold: int = fail_threshold
        self.cool_down: float = cool_down
        self._open_until: float = 0.0

    def allow(self) -> bool:
        return time.time() >= self._open_until

    def record(self, ok: bool) -> None:
        if ok:
            self.failures = 0
        else:
            self.failures += 1
            if self.failures >= self.fail_threshold:
                self._open_until = time.time() + self.cool_down


class TieredChatClient(BaseChatClient):
    """Chat client that supports multiple model tiers.

    Supply model instances for the tiers you wish to use (typically
    small, medium and large).  When generating a response, the
    smallest tier is attempted first.  If that call fails or if an
    escalation predicate deems the output unsatisfactory, the next
    larger tier is used, and so on.  Circuit breakers prevent
    repeated calls to a tier that is known to be failing.
    """

    def __init__(
        self,
        small: BaseChatClient,
        medium: Optional[BaseChatClient] = None,
        large: Optional[BaseChatClient] = None,
        should_escalate: Optional[Callable[[str, float], bool]] = None,
        fail_threshold: int = 5,
        cool_down: float = 30.0,
    ) -> None:
        self.models: Dict[str, Optional[BaseChatClient]] = {
            "small": small,
            "medium": medium or small,
            "large": large or medium or small,
        }
        self.should_escalate = should_escalate or (lambda _ans, _conf: False)
        # Each tier gets its own circuit breaker
        self.circuits: Dict[str, CircuitBreaker] = {
            tier: CircuitBreaker(fail_threshold=fail_threshold, cool_down=cool_down)
            for tier in self.models
        }

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 512,
        tier: str = "small",
    ) -> str:
        tiers_order = ["small", "medium", "large"]
        start_idx = tiers_order.index(tier)
        last_err: Optional[str] = None
        for t in tiers_order[start_idx:]:
            model = self.models.get(t)
            if model is None or not self.circuits[t].allow():
                continue
            try:
                answer = await model.generate(messages, temperature=temperature, max_tokens=max_tokens)
                self.circuits[t].record(True)
                # In a more sophisticated system, parse a confidence score
                # from the answer.  Here we assume 0.0 as a placeholder.
                if not self.should_escalate(answer, 0.0):
                    return answer
                last_err = "escalation triggered"
            except Exception as exc:
                # Record the failure and continue to the next tier
                self.circuits[t].record(False)
                last_err = str(exc)
                continue
        return f"[TieredChatClient] No response available. Last error: {last_err}" if last_err else "[TieredChatClient] No response available"
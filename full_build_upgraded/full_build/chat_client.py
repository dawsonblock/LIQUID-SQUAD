"""
Enhanced chat client and model tiering abstraction.

This module defines abstractions for integrating language models into the
self-loop system.  The `HttpModel` wraps an HTTP text generation endpoint,
while `TieredChatClient` manages multiple model tiers with retry logic and
circuit breaking so production systems can fail over gracefully.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class BaseChatClient:
    """Abstract base class for chat clients."""

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> str:
        raise NotImplementedError


@dataclass
class HttpModel(BaseChatClient):
    """HTTP client for text generation models compatible with OpenAI/vLLM APIs."""

    base_url: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    timeout: float = 30.0

    def __post_init__(self) -> None:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, headers=headers)

    async def aclose(self) -> None:
        await self._client.aclose()

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
    )
    async def _post_completion(
        self,
        payload: Dict[str, object],
    ) -> Dict[str, object]:
        response = await self._client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> str:
        payload: Dict[str, object] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if self.model:
            payload["model"] = self.model

        data = await self._post_completion(payload)

        content: Optional[str] = None
        if isinstance(data, dict):
            choices = data.get("choices", [])
            if choices:
                # OpenAI-style structure
                choice = choices[0]
                if isinstance(choice, dict):
                    message = choice.get("message")
                    if isinstance(message, dict):
                        content = message.get("content")
                    elif "text" in choice:
                        # vLLM text completions
                        candidate = choice.get("text")
                        if isinstance(candidate, str):
                            content = candidate
                elif isinstance(choice, str):
                    content = choice

        if content is None or not str(content).strip():
            raise ValueError("Empty response from model")
        return str(content)


class CircuitBreaker:
    """Minimal circuit breaker for transient model failures."""

    def __init__(self, fail_threshold: int = 3, cool_down: float = 60.0) -> None:
        self.fail_threshold = fail_threshold
        self.cool_down = cool_down
        self._consecutive_failures = 0
        self._open_until: float = 0.0

    def allow(self) -> bool:
        if self._open_until and time.time() < self._open_until:
            return False
        return True

    def record(self, success: bool) -> None:
        if success:
            self._consecutive_failures = 0
            self._open_until = 0.0
            return
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.fail_threshold:
            self._open_until = time.time() + self.cool_down
            self._consecutive_failures = 0


class TieredChatClient(BaseChatClient):
    """Wrapper that escalates between model tiers when necessary."""

    def __init__(
        self,
        small: BaseChatClient,
        medium: Optional[BaseChatClient] = None,
        large: Optional[BaseChatClient] = None,
        should_escalate: Optional[Callable[[str, float], bool]] = None,
        fail_threshold: int = 3,
        cool_down: float = 60.0,
    ) -> None:
        self.models: Dict[str, Optional[BaseChatClient]] = {
            "small": small,
            "medium": medium or small,
            "large": large or medium or small,
        }
        if should_escalate is None:
            def default_escalate(answer: str, _confidence: float) -> bool:
                if not answer:
                    return True
                stripped = answer.strip()
                if len(stripped) < 20:
                    return True
                refusal_patterns = ["I can't", "I cannot", "I'm unable", "I am unable", "I don't know"]
                return any(pattern.lower() in stripped.lower() for pattern in refusal_patterns)
            self.should_escalate = default_escalate
        else:
            self.should_escalate = should_escalate

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
    ) -> Tuple[str, str]:
        tiers_order = ["small", "medium", "large"]
        if tier not in tiers_order:
            raise ValueError(f"Unknown tier '{tier}'")
        start_idx = tiers_order.index(tier)

        last_error: Optional[str] = None
        fallback: Optional[Tuple[str, str]] = None

        for t in tiers_order[start_idx:]:
            model = self.models.get(t)
            if model is None:
                continue
            circuit = self.circuits.get(t)
            if circuit and not circuit.allow():
                last_error = f"circuit_open:{t}"
                continue
            try:
                answer = await model.generate(messages, temperature=temperature, max_tokens=max_tokens)
                if circuit:
                    circuit.record(True)
                escalate = False
                try:
                    escalate = self.should_escalate(answer, 0.0)
                except Exception:
                    escalate = True
                if not escalate:
                    return answer, t
                if fallback is None:
                    fallback = (answer, t)
                last_error = "escalation_triggered"
            except Exception as exc:  # pragma: no cover - defensive
                if circuit:
                    circuit.record(False)
                last_error = str(exc)
                continue

        if fallback is not None:
            return fallback

        return (
            f"[TieredChatClient] No response available. Last error: {last_error}",
            tiers_order[-1],
        )

    async def aclose(self) -> None:
        await asyncio.gather(
            *[
                model.aclose() for model in self.models.values()
                if hasattr(model, "aclose") and callable(getattr(model, "aclose"))
            ],
            return_exceptions=True,
        )

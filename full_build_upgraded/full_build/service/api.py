"""HTTP API service for the LLM self-loop system.

This module defines FastAPI endpoints that expose the self-loop
capabilities.  It offers JSON responses as well as a Server-Sent Events
(SSE) stream so the frontend can render real-time reasoning traces.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Awaitable, Callable, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from prometheus_client import make_asgi_app

from full_build.self_loop import IterationRecord, SelfLoopResult
from full_build.ops_security.security import RateLimiter
from full_build.ops_security.observability import record_error, record_request

ProgressHandler = Callable[[str, Optional[Callable[[IterationRecord], Awaitable[None]]]], Awaitable[SelfLoopResult]]

# Global handler and retriever checker to be injected at startup
self_loop_handler: Optional[ProgressHandler] = None
retriever_health_check: Optional[Callable[[], bool]] = None


class AskRequest(BaseModel):
    question: str


class IterationPayload(BaseModel):
    step: str
    content: str
    round: int
    timestamp: str
    confidence: Optional[float] = None


class AskResponse(BaseModel):
    answer: str
    citations: list[str] = []
    iterations: list[IterationPayload] = []
    model_tier: Optional[str] = None
    retrieval_mode: str = "disabled"
    duration_ms: Optional[int] = None
    rounds: int = 1

    model_config = {
        "protected_namespaces": (),
    }


# Dependency for authentication
async def verify_auth(authorization: str = Header(default="")) -> str:
    auth_token = os.getenv("AUTH_TOKEN")
    if not auth_token:
        return "anonymous"

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")

    token = authorization[7:].strip()
    if not token or token != auth_token:
        raise HTTPException(status_code=401, detail="unauthorized")

    return token


def _serialize_iteration(record: IterationRecord) -> IterationPayload:
    return IterationPayload(
        step=record.step,
        content=record.content,
        round=record.round,
        timestamp=record.timestamp,
        confidence=record.confidence,
    )


def _serialize_result(result: SelfLoopResult) -> AskResponse:
    return AskResponse(
        answer=result.answer,
        citations=result.citations,
        iterations=[_serialize_iteration(it) for it in result.iterations],
        model_tier=result.model_tier,
        retrieval_mode=result.retrieval_mode,
        duration_ms=result.total_duration_ms,
        rounds=result.rounds,
    )


# Create FastAPI app
app = FastAPI(title="LLM Hive API", version="1.1.0")

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins:
    origins = [o.strip() for o in cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=True,
    )

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Rate limiter instance
rate_limiter = RateLimiter()


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/ready")
async def ready() -> dict:
    retrieval_mode = os.getenv("RETRIEVAL_MODE", "disabled")

    if retrieval_mode != "disabled" and retriever_health_check is not None:
        try:
            is_ready = retriever_health_check()
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=503, detail=f"retrieval check failed: {exc}") from exc
        if not is_ready:
            raise HTTPException(status_code=503, detail="retrieval services not ready")

    return {"ready": True}


def _ensure_handler() -> ProgressHandler:
    if self_loop_handler is None:
        raise HTTPException(status_code=500, detail="handler_not_configured")
    return self_loop_handler


@app.post("/ask")
async def ask(payload: AskRequest, user_id: str = Depends(verify_auth)) -> AskResponse:
    handler = _ensure_handler()

    rate_limit_qps = int(os.getenv("RATE_LIMIT_QPS", "5"))
    rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    if not rate_limiter.allow(user_id, "/ask", limit=rate_limit_qps, window=rate_limit_window):
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")

    start_time = time.time()
    try:
        result = await handler(payload.question, progress_callback=None)
        return _serialize_result(result)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        record_error("/ask", "internal_error")
        raise HTTPException(status_code=500, detail="internal_error") from exc
    finally:
        record_request("/ask", time.time() - start_time)


@app.post("/ask/stream")
async def ask_stream(payload: AskRequest, user_id: str = Depends(verify_auth)) -> StreamingResponse:
    handler = _ensure_handler()

    rate_limit_qps = int(os.getenv("RATE_LIMIT_QPS", "5"))
    rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    if not rate_limiter.allow(user_id, "/ask/stream", limit=rate_limit_qps, window=rate_limit_window):
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")

    start_time = time.time()
    queue: asyncio.Queue[Optional[dict]] = asyncio.Queue()

    async def progress(record: IterationRecord) -> None:
        await queue.put({"type": "iteration", "data": _serialize_iteration(record).model_dump()})

    async def run_loop() -> None:
        try:
            result = await handler(payload.question, progress_callback=progress)
            await queue.put({"type": "final", "data": _serialize_result(result).model_dump()})
        except Exception as exc:  # pragma: no cover - defensive
            record_error("/ask/stream", "internal_error")
            await queue.put({"type": "error", "detail": str(exc)})
        finally:
            await queue.put(None)

    task = asyncio.create_task(run_loop())

    async def event_generator():
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield f"data: {json.dumps(item)}\n\n"
        finally:
            await task
            record_request("/ask/stream", time.time() - start_time)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def set_self_loop_handler(handler: Optional[ProgressHandler]) -> None:
    global self_loop_handler
    self_loop_handler = handler
    rate_limiter.reset()


def set_retriever_health_check(checker: Optional[Callable[[], bool]]) -> None:
    global retriever_health_check
    retriever_health_check = checker

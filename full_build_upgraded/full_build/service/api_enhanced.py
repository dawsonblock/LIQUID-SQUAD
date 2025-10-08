"""Enhanced HTTP API service with caching, validation, and improved features.

This module extends the base API with:
- Response caching
- Input validation
- Structured logging
- Conversation management
- Export functionality
- Enhanced security headers
- More detailed metrics
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from typing import Awaitable, Callable, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel, Field
from prometheus_client import make_asgi_app

from full_build.self_loop import IterationRecord, SelfLoopResult
from full_build.ops_security.security import RateLimiter
from full_build.ops_security.observability import (
    record_error,
    record_request,
    record_selfloop_execution,
    record_cache_hit,
    record_cache_miss,
    update_cache_size,
)
from full_build.response_cache import get_cache
from full_build.input_validation import QuestionValidator, validate_ask_request
from full_build.conversation_manager import get_conversation_manager
from full_build.export_utils import export_result
from full_build.logging_config import get_logger, request_id_var, user_id_var, LogTimer

# Get logger
logger = get_logger(__name__)

ProgressHandler = Callable[[str, Optional[Callable[[IterationRecord], Awaitable[None]]]], Awaitable[SelfLoopResult]]

# Global handler and retriever checker
self_loop_handler: Optional[ProgressHandler] = None
retriever_health_check: Optional[Callable[[], bool]] = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=5000)
    conversation_id: Optional[str] = None
    use_cache: bool = True
    max_rounds: Optional[int] = Field(None, ge=1, le=10)
    conf_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


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
    from_cache: bool = False
    conversation_id: Optional[str] = None

    model_config = {
        "protected_namespaces": (),
    }


class ExportResponse(BaseModel):
    content: str
    format: str


class HealthResponse(BaseModel):
    ok: bool
    timestamp: str


class StatsResponse(BaseModel):
    cache: dict
    conversations: dict


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


def _serialize_result(
    result: SelfLoopResult,
    from_cache: bool = False,
    conversation_id: Optional[str] = None,
) -> AskResponse:
    return AskResponse(
        answer=result.answer,
        citations=result.citations,
        iterations=[_serialize_iteration(it) for it in result.iterations],
        model_tier=result.model_tier,
        retrieval_mode=result.retrieval_mode,
        duration_ms=result.total_duration_ms,
        rounds=result.rounds,
        from_cache=from_cache,
        conversation_id=conversation_id,
    )


# Middleware to add security headers
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Create FastAPI app
app = FastAPI(
    title="LLM Hive API - Enhanced",
    version="2.0.0",
    description="Production-ready API with caching, validation, and conversation management",
)

# Add security headers middleware
@app.middleware("http")
async def security_middleware(request, call_next):
    return await add_security_headers(request, call_next)

# Middleware for request ID tracking
@app.middleware("http")
async def request_id_middleware(request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins:
    origins = [o.strip() for o in cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        allow_credentials=True,
        expose_headers=["X-Request-ID"],
    )

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Rate limiter instance
rate_limiter = RateLimiter()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    from datetime import datetime
    return HealthResponse(ok=True, timestamp=datetime.utcnow().isoformat() + "Z")


@app.get("/ready")
async def ready() -> dict:
    retrieval_mode = os.getenv("RETRIEVAL_MODE", "disabled")

    if retrieval_mode != "disabled" and retriever_health_check is not None:
        try:
            is_ready = retriever_health_check()
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"retrieval check failed: {exc}") from exc
        if not is_ready:
            raise HTTPException(status_code=503, detail="retrieval services not ready")

    return {"ready": True}


@app.get("/stats", response_model=StatsResponse)
async def stats(user_id: str = Depends(verify_auth)) -> StatsResponse:
    """Get system statistics."""
    cache = get_cache()
    conv_manager = get_conversation_manager()
    
    return StatsResponse(
        cache=cache.stats(),
        conversations=conv_manager.stats(),
    )


def _ensure_handler() -> ProgressHandler:
    if self_loop_handler is None:
        raise HTTPException(status_code=500, detail="handler_not_configured")
    return self_loop_handler


@app.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, user_id: str = Depends(verify_auth)) -> AskResponse:
    """Enhanced ask endpoint with caching and validation."""
    # Set user context for logging
    user_id_var.set(user_id)
    
    handler = _ensure_handler()

    # Rate limiting
    rate_limit_qps = int(os.getenv("RATE_LIMIT_QPS", "5"))
    rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    if not rate_limiter.allow(user_id, "/ask", limit=rate_limit_qps, window=rate_limit_window):
        logger.warning(f"Rate limit exceeded for user {user_id}")
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")

    # Input validation
    validation_result = validate_ask_request(
        payload.question,
        max_rounds=payload.max_rounds,
        conf_threshold=payload.conf_threshold,
    )
    if not validation_result.is_valid:
        logger.warning(f"Invalid input: {validation_result.to_dict()}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_error",
                "details": validation_result.to_dict(),
            },
        )

    # Sanitize question
    validator = QuestionValidator()
    sanitized_question = validator.sanitize(payload.question)

    # Check cache if enabled
    cache = get_cache()
    result = None
    from_cache = False

    if payload.use_cache:
        retrieval_mode = os.getenv("RETRIEVAL_MODE", "disabled")
        result = cache.get(
            sanitized_question,
            retrieval_mode=retrieval_mode,
        )
        if result:
            record_cache_hit()
            from_cache = True
            logger.info(f"Cache hit for question: {sanitized_question[:50]}...")
        else:
            record_cache_miss()

    # Execute self-loop if not cached
    if result is None:
        start_time = time.time()
        try:
            with LogTimer(logger, "self_loop_execution"):
                result = await handler(sanitized_question, progress_callback=None)
            
            # Cache the result
            if payload.use_cache:
                retrieval_mode = os.getenv("RETRIEVAL_MODE", "disabled")
                cache.put(sanitized_question, result, retrieval_mode=retrieval_mode)
                update_cache_size(cache.stats()["size"])
            
            # Record metrics
            final_confidence = 0.0
            if result.iterations:
                for it in reversed(result.iterations):
                    if it.confidence is not None:
                        final_confidence = it.confidence
                        break
            
            record_selfloop_execution(
                iterations=result.rounds,
                confidence=final_confidence,
                duration_ms=result.total_duration_ms,
                model_tier=result.model_tier,
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Self-loop execution failed", exc_info=True)
            record_error("/ask", "internal_error")
            raise HTTPException(status_code=500, detail="internal_error") from exc
        finally:
            record_request("/ask", time.time() - start_time)

    # Handle conversation if conversation_id provided
    conversation_id = payload.conversation_id
    if conversation_id or user_id != "anonymous":
        conv_manager = get_conversation_manager()
        conversation = conv_manager.get_or_create_conversation(user_id, conversation_id)
        conversation.add_turn(
            question=sanitized_question,
            answer=result.answer,
            citations=result.citations,
            model_tier=result.model_tier,
            rounds=result.rounds,
            duration_ms=result.total_duration_ms,
        )
        conversation_id = conversation.conversation_id

    return _serialize_result(result, from_cache=from_cache, conversation_id=conversation_id)


@app.post("/ask/stream")
async def ask_stream(payload: AskRequest, user_id: str = Depends(verify_auth)) -> StreamingResponse:
    """Streaming endpoint for real-time iteration updates."""
    user_id_var.set(user_id)
    handler = _ensure_handler()

    # Rate limiting
    rate_limit_qps = int(os.getenv("RATE_LIMIT_QPS", "5"))
    rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    if not rate_limiter.allow(user_id, "/ask/stream", limit=rate_limit_qps, window=rate_limit_window):
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")

    # Input validation
    validation_result = validate_ask_request(payload.question)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_error",
                "details": validation_result.to_dict(),
            },
        )

    validator = QuestionValidator()
    sanitized_question = validator.sanitize(payload.question)

    start_time = time.time()
    queue: asyncio.Queue[Optional[dict]] = asyncio.Queue()

    async def progress(record: IterationRecord) -> None:
        await queue.put({"type": "iteration", "data": _serialize_iteration(record).model_dump()})

    async def run_loop() -> None:
        try:
            result = await handler(sanitized_question, progress_callback=progress)
            await queue.put({"type": "final", "data": _serialize_result(result).model_dump()})
        except Exception as exc:
            logger.error("Stream execution failed", exc_info=True)
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


@app.post("/ask/export")
async def export_ask_result(
    payload: AskRequest,
    format: str = Query("markdown", regex="^(json|markdown|md|html)$"),
    user_id: str = Depends(verify_auth),
) -> Response:
    """Execute a query and export the result in the specified format."""
    user_id_var.set(user_id)
    
    # Execute the query (reuse ask logic)
    response = await ask(payload, user_id)
    
    # Convert to SelfLoopResult for export
    result = SelfLoopResult(
        answer=response.answer,
        citations=response.citations,
        iterations=[
            IterationRecord(
                step=it.step,
                content=it.content,
                round=it.round,
                timestamp=it.timestamp,
                confidence=it.confidence,
            )
            for it in response.iterations
        ],
        model_tier=response.model_tier or "unknown",
        retrieval_mode=response.retrieval_mode,
        total_duration_ms=response.duration_ms or 0,
        rounds=response.rounds,
    )
    
    # Export
    exported = export_result(result, format=format)
    
    # Set appropriate content type
    if format == "json":
        media_type = "application/json"
        filename = "result.json"
    elif format in ["markdown", "md"]:
        media_type = "text/markdown"
        filename = "result.md"
    elif format == "html":
        media_type = "text/html"
        filename = "result.html"
    else:
        media_type = "text/plain"
        filename = "result.txt"
    
    return Response(
        content=exported,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.delete("/cache")
async def clear_cache(user_id: str = Depends(verify_auth)) -> dict:
    """Clear the response cache."""
    cache = get_cache()
    cache.clear()
    logger.info(f"Cache cleared by user {user_id}")
    return {"ok": True, "message": "Cache cleared"}


@app.get("/conversations")
async def list_conversations(user_id: str = Depends(verify_auth)) -> dict:
    """List all conversations for the current user."""
    conv_manager = get_conversation_manager()
    conversations = conv_manager.get_user_conversations(user_id)
    
    return {
        "conversations": [conv.get_summary() for conv in conversations],
        "total": len(conversations),
    }


@app.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user_id: str = Depends(verify_auth),
) -> dict:
    """Get a specific conversation."""
    conv_manager = get_conversation_manager()
    conversation = conv_manager.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return conversation.to_dict()


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(verify_auth),
) -> dict:
    """Delete a conversation."""
    conv_manager = get_conversation_manager()
    conversation = conv_manager.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    conv_manager.delete_conversation(conversation_id)
    logger.info(f"Conversation {conversation_id} deleted by user {user_id}")
    
    return {"ok": True, "message": "Conversation deleted"}


def set_self_loop_handler(handler: Optional[ProgressHandler]) -> None:
    global self_loop_handler
    self_loop_handler = handler
    rate_limiter.reset()


def set_retriever_health_check(checker: Optional[Callable[[], bool]]) -> None:
    global retriever_health_check
    retriever_health_check = checker

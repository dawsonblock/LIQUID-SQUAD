"""HTTP API service for the LLM self-loop system.

This module defines a FastAPI application that wraps the core
capabilities of the self-loop system.  It provides endpoints for
health checking, readiness, metrics, and a simple `/ask` endpoint
that proxies a question through the self-loop.  Authentication and
rate limiting are enforced via the `ops_security` hooks.  Basic
observability is provided by recording request durations and
errors.  The actual self-loop orchestration is injected via a
callable to keep the API layer free of business logic.

To run this service in production, use Uvicorn or another ASGI
server: `uvicorn full_build.service.api:app --host 0.0.0.0 --port 8000`.
"""

from __future__ import annotations

import os
import time
from typing import Callable, Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import make_asgi_app

from full_build.ops_security.security import Authenticator, RateLimiter
from full_build.ops_security.observability import record_request, record_error

# Global handler and retriever checker to be injected at startup
self_loop_handler: Optional[Callable[[str], str]] = None
retriever_health_check: Optional[Callable[[], bool]] = None


class AskRequest(BaseModel):
    """Pydantic model for the `/ask` endpoint request body."""
    question: str


class AskResponse(BaseModel):
    """Pydantic model for the `/ask` endpoint response."""
    answer: str
    citations: Optional[list[str]] = None


# Dependency for authentication
async def verify_auth(authorization: str = Header(default="")) -> str:
    """Verify Bearer token from Authorization header."""
    auth_token = os.getenv("AUTH_TOKEN")
    if not auth_token:
        # No auth required if AUTH_TOKEN not set
        return "anonymous"

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")

    token = authorization[7:].strip()
    if not token or token != auth_token:
        raise HTTPException(status_code=401, detail="unauthorized")

    return token


# Create FastAPI app
app = FastAPI(title="LLM Hive API", version="1.0.0")

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
    """Liveness probe endpoint."""
    return {"ok": True}


@app.get("/ready")
async def ready() -> dict:
    """Readiness probe endpoint.
    
    Checks downstream services only when retrieval is enabled.
    """
    retrieval_mode = os.getenv("RETRIEVAL_MODE", "disabled")
    
    if retrieval_mode != "disabled":
        # Check if retriever is healthy
        if retriever_health_check is not None:
            try:
                is_ready = retriever_health_check()
                if not is_ready:
                    raise HTTPException(status_code=503, detail="retrieval services not ready")
            except Exception as e:
                raise HTTPException(status_code=503, detail=f"retrieval check failed: {str(e)}")
    
    return {"ready": True}


@app.post("/ask")
async def ask(
    payload: AskRequest,
    user_id: str = Depends(verify_auth),
) -> AskResponse:
    """Proxy a question through the self-loop and return its answer.

    The Authorization header must contain a valid Bearer token if AUTH_TOKEN is set.
    Rate limiting is enforced per user.
    """
    # Check rate limit
    rate_limit_qps = int(os.getenv("RATE_LIMIT_QPS", "5"))
    rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    if not rate_limiter.allow(user_id, "/ask", limit=rate_limit_qps, window=rate_limit_window):
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")
    
    if self_loop_handler is None:
        raise HTTPException(status_code=500, detail="handler_not_configured")
    
    start_time = time.time()
    try:
        # Call the self loop handler
        result = await self_loop_handler(payload.question)
        
        # Extract citations if present (simple heuristic)
        citations = None
        # Could parse [N] style citations from result if needed
        
        return AskResponse(answer=result, citations=citations)
    except Exception as exc:
        record_error("/ask", "internal_error")
        raise HTTPException(status_code=500, detail="internal_error") from exc
    finally:
        record_request("/ask", time.time() - start_time)


def set_self_loop_handler(handler: Callable[[str], str]) -> None:
    """Inject the self-loop handler at startup."""
    global self_loop_handler
    self_loop_handler = handler
    rate_limiter.reset()


def set_retriever_health_check(checker: Callable[[], bool]) -> None:
    """Inject the retriever health check at startup."""
    global retriever_health_check
    retriever_health_check = checker

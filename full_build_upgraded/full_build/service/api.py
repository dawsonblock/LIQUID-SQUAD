"""HTTP API service for the LLM self‑loop system.

This module defines a FastAPI application that wraps the core
capabilities of the self‑loop system.  It provides endpoints for
health checking, readiness, metrics, and a simple `/ask` endpoint
that proxies a question through the self‑loop.  Authentication and
rate limiting are enforced via the `ops_security` hooks.  Basic
observability is provided by recording request durations and
errors.  The actual self‑loop orchestration is injected via a
callable to keep the API layer free of business logic.

To run this service in production, use Uvicorn or another ASGI
server: `uvicorn full_build.service.api:app --host 0.0.0.0 --port 8000`.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

from fastapi import FastAPI, HTTPException, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from full_build.ops_security.security import Authenticator, RateLimiter
from full_build.ops_security.observability import record_request, record_error

# These callables will be provided by the application at startup.
# The API layer does not import the self‑loop directly to avoid
# circular dependencies during initialization.
self_loop_handler: Optional[Callable[[str], str]] = None


class AskRequest(BaseModel):
    """Pydantic model for the `/ask` endpoint request body."""

    question: str


def create_app(
    auth: Optional[Authenticator] = None,
    rate_limiter: Optional[RateLimiter] = None,
    allowed_origins: Optional[list[str]] = None,
    loop_handler: Optional[Callable[[str], str]] = None,
) -> FastAPI:
    """Factory to create the FastAPI application.

    Parameters:
        auth: Authenticator instance for token verification.
        rate_limiter: RateLimiter instance to enforce per‑user quotas.
        allowed_origins: List of allowed origins for CORS.  If None,
            CORS is disabled.
        loop_handler: Callable that takes a question string and
            returns an answer string.  If None, the `/ask` endpoint
            will raise an error.
    """
    # Default to dummy instances to simplify testing if none provided
    auth = auth or Authenticator(valid_tokens=set())
    rate_limiter = rate_limiter or RateLimiter()
    global self_loop_handler
    self_loop_handler = loop_handler

    app = FastAPI(title="LLM Hive API")
    # Configure CORS
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_methods=["POST", "GET"],
            allow_headers=["Authorization", "Content‑Type"],
        )

    @app.get("/healthz")
    async def healthz() -> dict[str, bool]:
        """Liveness probe endpoint."""
        return {"ok": True}

    @app.get("/readyz")
    async def readyz() -> dict[str, bool]:
        """Readiness probe endpoint.  Always returns ready."""
        return {"ready": True}

    @app.post("/ask")
    async def ask(
        payload: AskRequest = Body(...),
        authorization: Optional[str] = Header(default=""),
    ) -> dict[str, str]:
        """Proxy a question through the self‑loop and return its answer.

        The Authorization header must contain a valid token if the
        authenticator requires one.  Rate limiting is enforced by
        identifying the user via their token.  If the token is
        absent, an empty string is used as the identity.
        """
        user_id = authorization or ""
        if not auth.verify(user_id):
            raise HTTPException(status_code=401, detail="unauthorized")
        # Check rate limit per user and endpoint
        if not rate_limiter.allow(user_id, "/ask", limit=5, window=60):
            raise HTTPException(status_code=429, detail="rate limit exceeded")
        if self_loop_handler is None:
            raise HTTPException(status_code=500, detail="self loop handler not configured")
        start_time = time.time()
        try:
            # call the self loop; this may be synchronous or asynchronous
            result = self_loop_handler(payload.question)
            return {"answer": result}
        except Exception as exc:
            record_error("/ask", str(exc))
            raise HTTPException(status_code=500, detail="internal error") from exc
        finally:
            record_request("/ask", time.time() - start_time)

    return app


# Create a default application instance for Uvicorn auto‑detection.  In
# this context, self_loop_handler is unconfigured; it should be set
# explicitly before handling requests.
app = create_app()
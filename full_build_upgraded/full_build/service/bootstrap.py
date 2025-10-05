"""Bootstrap script to assemble components and launch the API service.

This module wires together the chat client, retrieval engine, verifiers,
and self-loop controller, then registers them with the FastAPI app.
It is intended to be run via `python -m full_build.service.bootstrap` or
through the Docker entrypoint.  Configuration is read from environment
variables via the settings module.
"""

from __future__ import annotations

import logging

from full_build.config.settings import settings
from full_build.chat_client import HttpModel, TieredChatClient
from full_build.self_loop import self_loop, Deps, Verifiers, Retriever
from full_build.retrieval import create_retriever
from full_build.verifiers.code_verifier import run_code_tests
from full_build.verifiers.math_verifier import run_math_check
from full_build.verifiers.retrieval_verifier import validate_citations
from full_build.service.api import app, set_self_loop_handler, set_retriever_health_check

logger = logging.getLogger(__name__)


def build_chat_client() -> TieredChatClient:
    """Instantiate a TieredChatClient using environment variables.

    Uses PRIMARY_MODEL_URL as the primary model and BACKUP_MODEL_URL
    as the backup model if provided.
    """
    if not settings.PRIMARY_MODEL_URL:
        raise RuntimeError("PRIMARY_MODEL_URL must be set in the environment")
    
    primary = HttpModel(
        base_url=settings.PRIMARY_MODEL_URL,
        api_key=settings.MODEL_API_KEY,
        model=settings.MODEL_NAME,
        timeout=30.0
    )
    
    backup = None
    if settings.BACKUP_MODEL_URL:
        backup = HttpModel(
            base_url=settings.BACKUP_MODEL_URL,
            api_key=settings.MODEL_API_KEY,
            model=settings.MODEL_NAME,
            timeout=30.0
        )
    
    return TieredChatClient(
        small=primary,
        medium=backup,
        large=backup,
        fail_threshold=3,
        cool_down=60.0
    )


def build_verifiers() -> Verifiers:
    """Build verifiers for code, math, and retrieval."""
    code_exec_enabled = settings.CODE_EXEC.lower() == "on"
    
    async def code_verifier(answer: str):
        return await run_code_tests(answer, exec_enabled=code_exec_enabled)
    
    async def math_verifier(answer: str):
        return await run_math_check(answer)
    
    def retrieval_verifier(answer: str, min_cites: int = 1):
        return validate_citations(answer, min_cites=min_cites)
    
    return Verifiers(
        code=code_verifier,
        math=math_verifier,
        retrieval=retrieval_verifier if settings.RETRIEVAL_MODE != "disabled" else None
    )


def build_retriever() -> Retriever | None:
    """Build retriever based on RETRIEVAL_MODE setting."""
    if settings.RETRIEVAL_MODE == "disabled":
        return None
    
    retriever_impl = create_retriever(
        mode=settings.RETRIEVAL_MODE,
        qdrant_url=settings.QDRANT_URL,
        es_url=settings.ES_URL,
        embedding_model=settings.EMBEDDING_MODEL
    )
    
    def search(query: str, k: int):
        try:
            return retriever_impl.query(query, k=k)
        except Exception as e:
            logger.warning(f"Retrieval failed: {e}")
            return []
    
    return Retriever(search=search)


def make_app():
    """Build and configure the FastAPI application."""
    # Validate settings
    settings.validate()
    
    # Build components
    client = build_chat_client()
    verifiers = build_verifiers()
    retriever = build_retriever()
    
    # Create dependencies
    deps = Deps(
        client=client,
        verifiers=verifiers,
        retriever=retriever,
        max_rounds=settings.MAX_ROUNDS,
        conf_threshold=settings.CONFIDENCE_THRESHOLD,
        retrieval_mode=settings.RETRIEVAL_MODE,
    )

    # Create async handler
    async def handler(question: str, progress_callback=None):
        return await self_loop(question, deps, progress_callback=progress_callback)
    
    # Inject handler into API
    set_self_loop_handler(handler)
    
    # Inject retriever health check
    if retriever is not None:
        def health_check() -> bool:
            try:
                # Simple health check: try to query with empty string
                retriever.search("", 1)
                return True
            except Exception:
                return False
        set_retriever_health_check(health_check)
    else:
        set_retriever_health_check(None)
    
    return app


def main() -> None:
    """Entry point for launching the API service."""
    import uvicorn
    
    # Build app
    app_instance = make_app()
    
    # Run Uvicorn
    uvicorn.run(
        app_instance,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()

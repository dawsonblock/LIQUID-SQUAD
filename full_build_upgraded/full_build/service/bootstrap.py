"""Bootstrap script to assemble components and launch the API service.

This module wires together the chat client, router, retrieval engine
and self‑loop controller, then registers them with the FastAPI app.
It is intended to be run via `python -m full_build.service.bootstrap` or
through the Docker entrypoint.  Configuration is read from environment
variables.
"""

from __future__ import annotations

import os
import asyncio
import logging
from typing import Callable

from full_build.chat_client import HttpModel, TieredChatClient
from full_build.router.main import route_prompt
from full_build.self_loop import SelfLoop
from full_build.retrieval import QdrantESRetriever, Document
from full_build.service.api import create_app
from full_build.ops_security.security import Authenticator, RateLimiter

logger = logging.getLogger(__name__)


def build_chat_client() -> TieredChatClient:
    """Instantiate a TieredChatClient using environment variables.

    Environment variables:
        SMALL_MODEL_URL, SMALL_MODEL_KEY
        MEDIUM_MODEL_URL, MEDIUM_MODEL_KEY
        LARGE_MODEL_URL, LARGE_MODEL_KEY
    """
    # Helper to create an HttpModel or fallback to None
    def make_model(base_url_var: str, key_var: str) -> HttpModel | None:
        url = os.getenv(base_url_var)
        if not url:
            return None
        key = os.getenv(key_var)
        return HttpModel(base_url=url, api_key=key)
    small = make_model("SMALL_MODEL_URL", "SMALL_MODEL_KEY")
    medium = make_model("MEDIUM_MODEL_URL", "MEDIUM_MODEL_KEY")
    large = make_model("LARGE_MODEL_URL", "LARGE_MODEL_KEY")
    # Ensure at least the small model is defined
    if small is None:
        raise RuntimeError("SMALL_MODEL_URL must be set in the environment")
    return TieredChatClient(small=small, medium=medium, large=large)


def build_retriever() -> QdrantESRetriever:
    """Instantiate the Qdrant + Elasticsearch retriever using environment variables."""
    qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
    es_hosts = [os.getenv("ES_URL", "http://elasticsearch:9200")]
    return QdrantESRetriever(qdrant_url=qdrant_url, es_hosts=es_hosts)


def build_self_loop(chat_client: TieredChatClient, retriever: QdrantESRetriever) -> SelfLoop:
    """Construct the SelfLoop with retrieval and optional critic client.

    The critic client is instantiated from the environment variables
    `DEEPSEEK_URL` and `DEEPSEEK_API_KEY`.  If both are set, the
    critic will call DeepSeek V3 for critique; otherwise the primary
    chat client will be used for critiques.
    """
    # Retrieval wrapper: returns list of Document from query
    def search(query: str, k: int) -> list[Document]:
        return retriever.query(query, k=k)
    # Critic client for DeepSeek V3
    ds_url = os.getenv("DEEPSEEK_URL")
    ds_key = os.getenv("DEEPSEEK_API_KEY")
    critic = None
    if ds_url:
        critic = HttpModel(base_url=ds_url, api_key=ds_key)
    return SelfLoop(chat_client, rag_search=search, critic_client=critic)


def build_api(loop_handler: Callable[[str], str]) -> any:
    """Build the FastAPI application with security hooks and the given handler."""
    # Accept comma separated tokens in environment variable AUTH_TOKENS
    tokens_env = os.getenv("AUTH_TOKENS", "")
    valid_tokens = {tok.strip() for tok in tokens_env.split(",") if tok.strip()}
    auth = Authenticator(valid_tokens=valid_tokens)
    limiter = RateLimiter()
    allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if os.getenv("CORS_ALLOW_ORIGINS") else None
    return create_app(auth=auth, rate_limiter=limiter, allowed_origins=allowed_origins, loop_handler=loop_handler)


def main() -> None:
    """Entry point for launching the API service."""
    # Build components
    chat = build_chat_client()
    retriever = build_retriever()
    self_loop = build_self_loop(chat, retriever)
    # Synchronous handler to fit the FastAPI interface
    def handler(question: str) -> str:
        path, tier = route_prompt(question)
        # call asynchronous self_loop synchronously
        answer, _conf = asyncio.get_event_loop().run_until_complete(
            self_loop.self_loop(question, path)
        )
        return answer
    # Create app
    app = build_api(handler)
    # Run Uvicorn if executed as a script
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
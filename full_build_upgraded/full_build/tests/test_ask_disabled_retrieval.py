"""Test /ask endpoint with disabled retrieval."""

import pytest
from fastapi.testclient import TestClient

from full_build.service.api import app
from full_build.self_loop import IterationRecord, SelfLoopResult


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_ask_disabled_retrieval(client, monkeypatch):
    """Test /ask with RETRIEVAL_MODE=disabled returns answer."""
    monkeypatch.setenv("RETRIEVAL_MODE", "disabled")
    monkeypatch.delenv("AUTH_TOKEN", raising=False)
    
    # Mock the handler
    from full_build.service import api
    
    async def mock_handler(question: str, progress_callback=None) -> SelfLoopResult:
        return SelfLoopResult(
            answer=f"Answer to: {question}",
            citations=[],
            iterations=[],
            model_tier="small",
            retrieval_mode="disabled",
            total_duration_ms=42,
            rounds=1,
        )
    
    api.set_self_loop_handler(mock_handler)
    
    response = client.post("/ask", json={"question": "What is 2+2?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"].startswith("Answer to")
    assert data["model_tier"] == "small"
    assert isinstance(data["iterations"], list)


def test_ask_rate_limit(client, monkeypatch):
    """Test that rate limiting works."""
    monkeypatch.setenv("RETRIEVAL_MODE", "disabled")
    monkeypatch.setenv("RATE_LIMIT_QPS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW", "60")
    monkeypatch.delenv("AUTH_TOKEN", raising=False)
    
    # Mock the handler
    from full_build.service import api
    
    async def mock_handler(question: str, progress_callback=None) -> SelfLoopResult:
        return SelfLoopResult(
            answer="Answer",
            citations=[],
            iterations=[],
            model_tier="small",
            retrieval_mode="disabled",
            total_duration_ms=10,
            rounds=1,
        )
    
    api.set_self_loop_handler(mock_handler)
    
    # First two requests should succeed
    response1 = client.post("/ask", json={"question": "test1"})
    assert response1.status_code == 200
    
    response2 = client.post("/ask", json={"question": "test2"})
    assert response2.status_code == 200
    
    # Third request should be rate limited
    response3 = client.post("/ask", json={"question": "test3"})
    assert response3.status_code == 429
    assert response3.json()["detail"] == "rate_limit_exceeded"


def test_ask_handler_not_configured(client, monkeypatch):
    """Test /ask returns 500 when handler not configured."""
    monkeypatch.setenv("RETRIEVAL_MODE", "disabled")
    monkeypatch.delenv("AUTH_TOKEN", raising=False)
    
    # Clear the handler
    from full_build.service import api
    api.set_self_loop_handler(None)
    
    response = client.post("/ask", json={"question": "test"})
    assert response.status_code == 500
    assert response.json()["detail"] == "handler_not_configured"


def test_ask_stream_returns_events(client, monkeypatch):
    """Test the streaming endpoint emits iteration and final events."""
    monkeypatch.setenv("RETRIEVAL_MODE", "disabled")
    monkeypatch.delenv("AUTH_TOKEN", raising=False)

    from full_build.service import api

    async def mock_handler(question: str, progress_callback=None) -> SelfLoopResult:
        record = IterationRecord(
            step="plan",
            content="- step one",
            round=1,
            timestamp="2024-01-01T00:00:00Z",
            confidence=None,
        )
        iterations = [record]
        if progress_callback:
            await progress_callback(record)
        return SelfLoopResult(
            answer="Final answer",
            citations=[],
            iterations=iterations,
            model_tier="small",
            retrieval_mode="disabled",
            total_duration_ms=5,
            rounds=1,
        )

    api.set_self_loop_handler(mock_handler)

    with client.stream("POST", "/ask/stream", json={"question": "hello"}) as response:
        assert response.status_code == 200
        chunks = [chunk.decode("utf-8") for chunk in response.iter_raw() if chunk]

    data_events = [line[len("data: "):].strip() for chunk in chunks for line in chunk.splitlines() if line.startswith("data:")]
    assert any("\"type\": \"iteration\"" in event for event in data_events)
    assert any("\"type\": \"final\"" in event for event in data_events)

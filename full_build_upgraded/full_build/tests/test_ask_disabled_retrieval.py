"""Test /ask endpoint with disabled retrieval."""

import pytest
from fastapi.testclient import TestClient
from full_build.service.api import app


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
    
    async def mock_handler(question: str) -> str:
        return f"Answer to: {question}"
    
    api.set_self_loop_handler(mock_handler)
    
    response = client.post("/ask", json={"question": "What is 2+2?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "2+2" in data["answer"]


def test_ask_rate_limit(client, monkeypatch):
    """Test that rate limiting works."""
    monkeypatch.setenv("RETRIEVAL_MODE", "disabled")
    monkeypatch.setenv("RATE_LIMIT_QPS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW", "60")
    monkeypatch.delenv("AUTH_TOKEN", raising=False)
    
    # Mock the handler
    from full_build.service import api
    
    async def mock_handler(question: str) -> str:
        return "Answer"
    
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

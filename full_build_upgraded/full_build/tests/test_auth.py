"""Test authentication."""

import pytest
from fastapi.testclient import TestClient

from full_build.service.api import app
from full_build.self_loop import SelfLoopResult


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_ask_without_auth_token_not_set(client, monkeypatch):
    """Test /ask without auth when AUTH_TOKEN is not set (should succeed)."""
    monkeypatch.delenv("AUTH_TOKEN", raising=False)
    
    # Mock the handler
    from full_build.service import api
    
    async def mock_handler(question: str, progress_callback=None) -> SelfLoopResult:
        return SelfLoopResult(
            answer="Mock answer",
            citations=[],
            iterations=[],
            model_tier="small",
            retrieval_mode="disabled",
            total_duration_ms=12,
            rounds=1,
        )
    
    api.set_self_loop_handler(mock_handler)
    
    response = client.post("/ask", json={"question": "test"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Mock answer"


def test_ask_with_invalid_token(client, monkeypatch):
    """Test /ask with invalid token returns 401."""
    monkeypatch.setenv("AUTH_TOKEN", "valid-token-123")
    
    response = client.post(
        "/ask",
        json={"question": "test"},
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "unauthorized"


def test_ask_with_valid_token(client, monkeypatch):
    """Test /ask with valid Bearer token."""
    monkeypatch.setenv("AUTH_TOKEN", "valid-token-123")
    
    # Mock the handler
    from full_build.service import api
    
    async def mock_handler(question: str, progress_callback=None) -> SelfLoopResult:
        return SelfLoopResult(
            answer="Mock answer",
            citations=[],
            iterations=[],
            model_tier="small",
            retrieval_mode="disabled",
            total_duration_ms=12,
            rounds=1,
        )
    
    api.set_self_loop_handler(mock_handler)
    
    response = client.post(
        "/ask",
        json={"question": "test"},
        headers={"Authorization": "Bearer valid-token-123"}
    )
    assert response.status_code == 200
    assert "answer" in response.json()


def test_ask_without_bearer_prefix(client, monkeypatch):
    """Test /ask with token but no Bearer prefix returns 401."""
    monkeypatch.setenv("AUTH_TOKEN", "valid-token-123")
    
    response = client.post(
        "/ask",
        json={"question": "test"},
        headers={"Authorization": "valid-token-123"}
    )
    # Should fail without Bearer prefix
    assert response.status_code == 401

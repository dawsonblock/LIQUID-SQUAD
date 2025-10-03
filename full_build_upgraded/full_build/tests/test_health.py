"""Test health endpoint."""

import pytest
from fastapi.testclient import TestClient
from full_build.service.api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test that /health returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_ready_endpoint_disabled_retrieval(client, monkeypatch):
    """Test that /ready returns 200 when retrieval is disabled."""
    monkeypatch.setenv("RETRIEVAL_MODE", "disabled")
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"ready": True}

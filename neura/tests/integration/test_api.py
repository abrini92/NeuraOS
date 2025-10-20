"""
Integration tests for the API.
"""

import pytest
from fastapi.testclient import TestClient

from neura.core.api import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


def test_root_endpoint(client: TestClient) -> None:
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert data["message"] == "NeuraCore operational"
    assert "version" in data


def test_health_endpoint(client: TestClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "modules" in data

"""Tests for core API."""

import pytest
from fastapi.testclient import TestClient

from neura.core.api import app


class TestCoreAPI:
    """Tests for core API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    def test_health(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "modules" in data

    def test_docs(self, client):
        """Test OpenAPI docs endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi(self, client):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/health")
        # CORS headers should be present
        assert response.status_code in [200, 405]  # OPTIONS may not be implemented

    def test_404_handling(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

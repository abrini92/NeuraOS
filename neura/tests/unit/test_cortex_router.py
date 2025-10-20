"""Tests for cortex router."""

import pytest
from fastapi.testclient import TestClient

from neura.core.api import app


class TestCortexRouter:
    """Tests for cortex API router."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_cortex_info(self, client):
        """Test cortex info endpoint."""
        response = client.get("/api/cortex/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Cortex"

    def test_cortex_status(self, client):
        """Test cortex status endpoint."""
        response = client.get("/api/cortex/status")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert isinstance(data["available"], bool)

    def test_cortex_models(self, client):
        """Test list models endpoint."""
        response = client.get("/api/cortex/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)

"""Tests for policy router."""

import pytest
from fastapi.testclient import TestClient

from neura.core.api import app


class TestPolicyRouter:
    """Tests for policy API router."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_policy_info(self, client):
        """Test policy info endpoint."""
        response = client.get("/api/policy/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Policy"

    def test_policy_status(self, client):
        """Test policy status endpoint."""
        response = client.get("/api/policy/status")
        assert response.status_code == 200
        data = response.json()
        assert "opa_available" in data
        assert isinstance(data["opa_available"], bool)

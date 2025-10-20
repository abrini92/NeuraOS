"""Tests for motor router."""

import pytest
from fastapi.testclient import TestClient

from neura.core.api import app


class TestMotorRouter:
    """Tests for motor API router."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_motor_info(self, client):
        """Test motor info endpoint."""
        response = client.get("/api/motor/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Motor"

    def test_motor_status(self, client):
        """Test motor status endpoint."""
        response = client.get("/api/motor/status")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert isinstance(data["available"], bool)

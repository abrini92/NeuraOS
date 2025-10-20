"""
Integration tests for Cortex API endpoints.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from neura.core.api import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


class TestCortexEndpoints:
    """Test Cortex API endpoints."""

    def test_cortex_info(self, client: TestClient) -> None:
        """Test /api/cortex/ endpoint."""
        response = client.get("/api/cortex/")
        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "cortex"
        assert data["status"] == "operational"
        assert "endpoints" in data

    @patch("neura.cortex.engine.OllamaClient.generate")
    def test_generate_text(self, mock_generate: MagicMock, client: TestClient) -> None:
        """Test /api/cortex/generate endpoint."""
        from neura.core.types import Result
        from neura.cortex.types import GenerateResponse

        # Mock successful generation
        mock_response = GenerateResponse(
            text="I am Neura, a local-first cognitive OS.",
            model="mistral",
            tokens_generated=10,
            finished=True,
            context_used=False,
        )
        mock_generate.return_value = Result.success(mock_response)

        response = client.post(
            "/api/cortex/generate",
            json={
                "prompt": "Who are you?",
                "model": "mistral",
                "temperature": 0.7,
                "stream": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "I am Neura, a local-first cognitive OS."
        assert data["model"] == "mistral"
        assert data["finished"] is True

    @patch("neura.cortex.engine.OllamaClient.generate")
    def test_generate_with_error(
        self, mock_generate: MagicMock, client: TestClient
    ) -> None:
        """Test generation error handling."""
        from neura.core.types import Result

        # Mock failure
        mock_generate.return_value = Result.failure("Ollama connection failed")

        response = client.post(
            "/api/cortex/generate",
            json={"prompt": "Test"},
        )

        assert response.status_code == 500
        assert "Ollama connection failed" in response.json()["detail"]

    @patch("neura.cortex.engine.OllamaClient.list_models")
    def test_list_models(self, mock_list_models: MagicMock, client: TestClient) -> None:
        """Test /api/cortex/models endpoint."""
        from neura.core.types import Result
        from neura.cortex.types import OllamaModelInfo

        # Mock models
        models = [
            OllamaModelInfo(name="mistral", size="7B", modified_at="2024-01-01"),
            OllamaModelInfo(name="llama3", size="8B", modified_at="2024-01-02"),
        ]
        mock_list_models.return_value = Result.success(models)

        response = client.get("/api/cortex/models")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "mistral"
        assert data[1]["name"] == "llama3"

    @patch("neura.cortex.engine.OllamaClient.check_status")
    def test_status_available(
        self, mock_check_status: MagicMock, client: TestClient
    ) -> None:
        """Test /api/cortex/status endpoint when Ollama is available."""
        from neura.cortex.types import OllamaStatus

        # Mock available status
        status = OllamaStatus(
            available=True,
            version="0.1.0",
            models=["mistral", "llama3"],
        )
        mock_check_status.return_value = status

        response = client.get("/api/cortex/status")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert data["version"] == "0.1.0"
        assert len(data["models"]) == 2

    @patch("neura.cortex.engine.OllamaClient.check_status")
    def test_status_unavailable(
        self, mock_check_status: MagicMock, client: TestClient
    ) -> None:
        """Test /api/cortex/status endpoint when Ollama is unavailable."""
        from neura.cortex.types import OllamaStatus

        # Mock unavailable status
        status = OllamaStatus(
            available=False,
            error="Connection refused",
        )
        mock_check_status.return_value = status

        response = client.get("/api/cortex/status")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert data["error"] == "Connection refused"

    def test_invalid_request(self, client: TestClient) -> None:
        """Test invalid generation request."""
        # Empty prompt
        response = client.post(
            "/api/cortex/generate",
            json={"prompt": ""},
        )

        assert response.status_code == 422  # Validation error

    def test_invalid_temperature(self, client: TestClient) -> None:
        """Test invalid temperature value."""
        response = client.post(
            "/api/cortex/generate",
            json={"prompt": "Test", "temperature": 3.0},
        )

        assert response.status_code == 422  # Validation error

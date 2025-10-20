"""
Unit tests for Cortex module.

Tests the OllamaClient with mocked HTTP responses.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import Response

from neura.cortex.engine import OllamaClient
from neura.cortex.types import (
    CortexConfig,
    GenerateRequest,
    OllamaModelInfo,
    OllamaStatus,
)


@pytest.fixture
def cortex_config() -> CortexConfig:
    """Create a test configuration."""
    return CortexConfig(
        ollama_host="http://localhost:11434",
        default_model="mistral",
        default_temperature=0.7,
        default_max_tokens=100,
        timeout=10,
    )


@pytest.fixture
def ollama_client(cortex_config: CortexConfig) -> OllamaClient:
    """Create an OllamaClient instance for testing."""
    return OllamaClient(cortex_config)


class TestOllamaClient:
    """Test OllamaClient class."""

    @pytest.mark.asyncio
    async def test_generate_success(self, ollama_client: OllamaClient) -> None:
        """Test successful text generation."""
        # Mock HTTP response
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "I am Neura, a local-first cognitive OS.",
            "done": True,
        }

        with patch.object(ollama_client._client, "post", return_value=mock_response):
            request = GenerateRequest(
                prompt="Who are you?",
                model="mistral",
                temperature=0.7,
            )

            result = await ollama_client.generate(request)

            assert result.is_success()
            assert result.data is not None
            assert result.data.text == "I am Neura, a local-first cognitive OS."
            assert result.data.model == "mistral"
            assert result.data.finished is True

    @pytest.mark.asyncio
    async def test_generate_with_context(self, ollama_client: OllamaClient) -> None:
        """Test generation with context from memory."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Based on context, Neura is a cognitive OS.",
            "done": True,
        }

        with patch.object(ollama_client._client, "post", return_value=mock_response):
            request = GenerateRequest(
                prompt="What is Neura?",
                context=["Neura is local-first", "Neura is ethical"],
            )

            result = await ollama_client.generate(request)

            assert result.is_success()
            assert result.data.context_used is True

    @pytest.mark.asyncio
    async def test_generate_api_error(self, ollama_client: OllamaClient) -> None:
        """Test handling of API errors."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(ollama_client._client, "post", return_value=mock_response):
            request = GenerateRequest(prompt="Test")

            result = await ollama_client.generate(request)

            assert result.is_failure()
            assert "500" in result.error

    @pytest.mark.asyncio
    async def test_generate_connection_error(self, ollama_client: OllamaClient) -> None:
        """Test handling of connection errors."""
        from httpx import ConnectError

        with patch.object(
            ollama_client._client,
            "post",
            side_effect=ConnectError("Connection refused"),
        ):
            request = GenerateRequest(prompt="Test")

            result = await ollama_client.generate(request)

            assert result.is_failure()
            assert "Cannot connect" in result.error

    @pytest.mark.asyncio
    async def test_list_models_success(self, ollama_client: OllamaClient) -> None:
        """Test listing models."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "mistral", "size": "7B", "modified_at": "2024-01-01"},
                {"name": "llama3", "size": "8B", "modified_at": "2024-01-02"},
            ]
        }

        with patch.object(ollama_client._client, "get", return_value=mock_response):
            result = await ollama_client.list_models()

            assert result.is_success()
            assert len(result.data) == 2
            assert result.data[0].name == "mistral"
            assert result.data[1].name == "llama3"

    @pytest.mark.asyncio
    async def test_check_status_available(self, ollama_client: OllamaClient) -> None:
        """Test status check when Ollama is available."""
        version_response = MagicMock(spec=Response)
        version_response.status_code = 200
        version_response.json.return_value = {"version": "0.1.0"}

        models_response = MagicMock(spec=Response)
        models_response.status_code = 200
        models_response.json.return_value = {
            "models": [{"name": "mistral"}, {"name": "llama3"}]
        }

        async def mock_get(url, **kwargs):
            if "version" in url:
                return version_response
            return models_response

        with patch.object(ollama_client._client, "get", side_effect=mock_get):
            status = await ollama_client.check_status()

            assert status.available is True
            assert status.version == "0.1.0"
            assert len(status.models) == 2

    @pytest.mark.asyncio
    async def test_check_status_unavailable(self, ollama_client: OllamaClient) -> None:
        """Test status check when Ollama is unavailable."""
        from httpx import ConnectError

        with patch.object(
            ollama_client._client,
            "get",
            side_effect=ConnectError("Connection refused"),
        ):
            status = await ollama_client.check_status()

            assert status.available is False
            assert status.error is not None


class TestGenerateRequest:
    """Test GenerateRequest model."""

    def test_generate_request_defaults(self) -> None:
        """Test default values."""
        request = GenerateRequest(prompt="Test prompt")

        assert request.prompt == "Test prompt"
        assert request.model == "mistral"
        assert request.temperature == 0.7
        assert request.max_tokens == 2048
        assert request.stream is False
        assert request.context is None

    def test_generate_request_validation(self) -> None:
        """Test validation."""
        # Temperature out of range
        with pytest.raises(Exception):
            GenerateRequest(prompt="Test", temperature=3.0)

        # Empty prompt
        with pytest.raises(Exception):
            GenerateRequest(prompt="")
